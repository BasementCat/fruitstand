import os
import tempfile
import json
import uuid
import urllib.parse
import subprocess
from io import BytesIO

from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, send_file, current_app
import arrow
import requests

from app import db
from app.models import Display, Playlist, Screen
from app.constants import DISPLAY_SPEC, COLOR_SPEC
from app.forms import DisplayEditForm
from app.lib.metric import Metric
from app.lib.screen import Screen as BaseScreen
from app.lib.image import convert_colors


bp = Blueprint('display', __name__)


@bp.route('/render', methods=['GET'])
def render():
    screen = BaseScreen.load_for_render(
        playlist_id=int(request.args.get('debug_playlist_id', 0)) or None,
        playlist_screen_id=int(request.args.get('debug_playlist_screen_id', 0)) or None,
    )

    args = {
        'playlist_screen_id': screen.playlist_screen.id,
        'display_id': screen.display.id,
        'metrics': json.dumps(Metric.get_metrics()),
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
    headers = {'X-Refresh-Time': screen.playlist_screen.refresh_interval or screen.playlist.default_refresh_interval}
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
            im = convert_colors(screen.display.color_spec, path)
            out = BytesIO()
            im.save(out, 'bmp')
            l = out.tell()
            out.seek(0)
            payload = out
            headers.update({'Content-length': l, 'Content-type': 'image/bmp'})
        finally:
            if os.path.exists(path):
                os.unlink(path)

    # TODO: error handling - ideally render pretty error screen but worst case text/plain
    return payload, headers


@bp.route('/', methods=['GET'])
@bp.route('/list', methods=['GET'])
def list():
    displays = Display.query.order_by(Display.name.asc()).all()
    return render_template('display/list.html.j2', displays=displays)


@bp.route('/edit/<int:display_id>', methods=['GET', 'POST'])
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
def demo():
    playlists = Playlist.query.order_by(Playlist.name.asc()).all()
    screens = Screen.query.order_by(Screen.title.asc()).all()

    return render_template('display/demo.html.j2',
        playlists=playlists,
        screens=screens,
        DISPLAY_SPEC=DISPLAY_SPEC,
        COLOR_SPEC=COLOR_SPEC,
        metric_inputs=Metric.get_all_demo_inputs(),
        metric_classes=Metric.get_metric_classes(),
    )


@bp.route('/demo/params', methods=['POST'])
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
