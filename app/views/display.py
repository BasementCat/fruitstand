import os
import tempfile
import json
import uuid
import urllib.parse
import subprocess
from io import BytesIO
import functools

from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, send_file, current_app, jsonify
import arrow
import requests

from app import db
from app.models import Display, Playlist, Screen, DisplaySecret
from app.constants import DISPLAY_SPEC, COLOR_SPEC
from app.forms import DisplayEditForm, DisplaySecretEditForm
from app.lib.metric import Metric
from app.lib.screen import Screen as BaseScreen
from app.lib.image import convert_colors
from app.lib.user import login_required, admin_required


bp = Blueprint('display', __name__)


@bp.route('/render', methods=['GET'])
def render():
    screen = BaseScreen.load_for_render(
        playlist_id=int(request.args.get('debug_playlist_id', 0)) or None,
        playlist_screen_id=int(request.args.get('debug_playlist_screen_id', 0)) or None,
    )

    args = {
        'playlist_screen_id': screen.playlist_screen.id if screen.playlist_screen else None,
        'display_id': screen.display.id,
        'metrics': json.dumps(Metric.get_metrics()),
        '_render_display': 1,
    }

    if current_app.config.get('INTERNAL_WEB_HOST'):
        # the _external argument doesn't work here as it uses the configured host
        # (or host header, probably localhost) and this is not going to be valid
        # in certain environments like Docker, so "fix" it
        url = 'http://{}{}'.format(
            current_app.config['INTERNAL_WEB_HOST'],
            url_for(screen.route, **args)
        )
    else:
        url = url_for(screen.route, **args, _external=True)
    headers = {
        'X-Refresh-Time': screen.refresh_interval,
    }
    if screen.display.display_spec == 'browser':
        payload = requests.get(url).content
        headers.update({'Content-length': len(payload), 'Content-type': 'text/html'})
    else:
        path = os.path.join(tempfile.gettempdir(), 'fs-render-' + str(uuid.uuid4()) + '.png')
        try:
            subprocess.check_call([
                'npm', 'run', 'render', '--',
                '--url', url,
                '--width', str(screen.display.width),
                '--height', str(screen.display.height),
                '--path', path,
                '--browser', current_app.config['BROWSER'],
            ])
            im = convert_colors(screen.display.image_bit_depth, screen.display.color_spec, path)
            out = BytesIO()
            fmt = screen.display.image_format.code.lower()
            im.save(out, fmt)
            l = out.tell()
            out.seek(0)
            payload = out
            headers.update({'Content-length': l, 'Content-type': f'image/{fmt}'})
        finally:
            if os.path.exists(path):
                os.unlink(path)

    # TODO: error handling - ideally render pretty error screen but worst case text/plain
    return payload, headers


@bp.route('/', methods=['GET'])
@bp.route('/list', methods=['GET'])
@login_required
def list():
    raw_displays = Display.query.order_by(Display.name.asc()).all()
    if current_app.config['ENABLE_DISPLAY_APPROVAL']:
        displays = {
            'pending': {
                'title': 'Pending',
                'displays': [],
            },
            'active': {
                'title': 'Active',
                'displays': [],
            },
            'disapproved': {
                'title': 'Disapproved',
                'displays': [],
            },
        }
        for d in raw_displays:
            displays[d.status]['displays'].append(d)
    else:
        displays = {
            'all': {
                'title': None,
                'displays': raw_displays
            }
        }
    return render_template('display/list.html.j2', displays=displays.values())


@bp.route('/edit/<int:display_id>', methods=['GET', 'POST'])
@login_required
def edit(display_id):
    display = Display.query.get(display_id)
    if not display:
        abort(404)

    form = DisplayEditForm(obj=display)
    if form.validate_on_submit():
        form.populate_obj(display)
        db.session.commit()
        flash(f"Saved display {display.name}", 'success')
        return redirect(url_for('.list'))

    return render_template('display/edit.html.j2', display=display, form=form)


@bp.route('/demo', methods=['GET'])
@login_required
def demo():
    playlists = Playlist.query.order_by(Playlist.name.asc()).all()
    screens = Screen.query.order_by(Screen.title.asc()).all()
    secrets = DisplaySecret.query.order_by(DisplaySecret.name.asc()).all()

    return render_template('display/demo.html.j2',
        playlists=playlists,
        screens=screens,
        secrets=secrets,
        DISPLAY_SPEC=DISPLAY_SPEC,
        COLOR_SPEC=COLOR_SPEC,
        metric_inputs=Metric.get_all_demo_inputs(),
        metric_classes=Metric.get_metric_classes(),
    )


@bp.route('/demo/params', methods=['POST'])
@login_required
def demo_params():
    data = {}
    for k, v in request.form.items():
        sk, mk = k.split(';')
        if v:
            try:
                v = float(v)
            except:
                pass
        else:
            v = None
        data.setdefault(sk, {})[mk] = v

    out = {}
    for mc in Metric.get_metric_classes():
        v = mc.format_demo_inputs(data.get(mc.key, {}))
        if v is not None:
            out[mc.param] = v

    return '&'.join(map(lambda v: '='.join(v), out.items())), {'content-type': 'text/plain'}


def display_auth_required(callback):
    @functools.wraps(callback)
    def display_auth_required_wrap(*a, **ka):
        if not current_app.config['ENABLE_DISPLAY_AUTH']:
            abort(404)
        return callback(*a, **ka)
    return display_auth_required_wrap


@bp.route('/secrets', methods=['GET'])
@bp.route('/secrets/list', methods=['GET'])
@display_auth_required
@admin_required
def secret_list():
    secrets = DisplaySecret.query.all()
    return render_template('display/secrets/list.html.j2', secrets=secrets)


@bp.route('/secrets/edit/<int:secret_id>', methods=['GET', 'POST'])
@bp.route('/secrets/edit/new', methods=['GET', 'POST'])
@display_auth_required
@admin_required
def secret_edit(secret_id=None):
    secret = None
    if secret_id:
        secret = DisplaySecret.query.get(secret_id)
        if not secret:
            flash("The requested secret was not found", 'danger')
            return redirect(url_for('.secret_list'))

    form = DisplaySecretEditForm(obj=secret)
    if form.validate_on_submit():
        secret = secret or DisplaySecret()
        form.populate_obj(secret)
        db.session.add(secret)
        db.session.commit()
        if secret_id:
            flash(f"Saved changes to secret {secret.name}.", 'info')
        else:
            flash(f"Created new secret {secret.name}.", 'success')
        return redirect(url_for('.secret_list'))

    if secret and len(secret.displays):
        flash("This secret is currently in use; if disabled, it will no longer be treated as valid.", 'warning')

    return render_template('display/secrets/edit.html.j2', secret=secret, form=form)


@bp.route('/secrets/delete/<int:secret_id>', methods=['GET', 'POST'])
@display_auth_required
@admin_required
def secret_delete(secret_id):
    secret = DisplaySecret.query.get(secret_id)
    if not secret:
        flash("The requested secret was not found", 'danger')
        return redirect(url_for('.secret_list'))

    if request.method == 'POST':
        db.session.delete(secret)
        db.session.commit()
        flash(f"Deleted secret {secret.name}", 'danger')
        return redirect(url_for('.secret_list'))

    return render_template('display/secrets/delete.html.j2', secret=secret)