import os
import tempfile
import json
import uuid
import urllib.parse
import subprocess

from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, send_file
import arrow

from app import db
from app.models import Display, Playlist, Screen
from app.constants import DISPLAY_SPEC, COLOR_SPEC
from app.forms import DisplayEditForm
from app.lib.metric import Metric
from app.lib.screen import Screen as BaseScreen


bp = Blueprint('display', __name__)


@bp.route('/render', methods=['GET'])
def render():
    display = Display.sync()
    if not display:
        abort(404)

    playlist, playlist_screen = display.get_playlist_screen(
        playlist_id=int(request.args.get('debug_playlist', 0)) or None,
        playlist_screen_id=int(request.args.get('debug_playlist_screen', 0)) or None,
    )
    screen_cls = None
    if playlist_screen:
        screen_cls = BaseScreen.get(playlist_screen.screen.key)

    if not (playlist and playlist_screen and screen_cls):
        abort(404)

    args = {
        'playlist_screen_id': playlist_screen.id,
        'display_id': display.id,
        'metrics': json.dumps(Metric.get_metrics()),
    }

    # TODO: if display spec is browser, just return the rendered route as-is
    url = url_for(screen_cls.route, **args, _external=True)
    path = os.path.join(tempfile.gettempdir(), 'fs-render-' + str(uuid.uuid4()) + '.png')

    try:
        subprocess.check_call(['npm', 'run', 'render', '--', '--url', url, '--width', str(display.width), '--height', str(display.height), '--path', path])
        # TODO: load png
        # TODO: convert to color spec
        # TODO: rerender as bmp (direct or send_file)
        # TODO: add refresh interval header
        return send_file(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)

    # TODO: error handling - ideally render pretty error screen but worst case text/plain


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
    )
