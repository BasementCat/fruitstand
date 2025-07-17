from flask import Blueprint, render_template, abort, redirect, url_for, request, flash

from app.models import Screen, PlaylistScreen, Config
from app.lib.screen import Screen as ScreenBase
from app import db


bp = Blueprint('screen', __name__)

@bp.route('/', methods=['GET'])
@bp.route('/list', methods=['GET'])
def list():
    Screen.sync(ScreenBase.get_all().values())

    return render_template('screen/list.html.j2', screens=Screen.all_by_key(), screen_classes=ScreenBase.get_all())


@bp.route('/toggle/<int:screen_id>', methods=['POST'])
def toggle(screen_id):
    s = Screen.query.get(screen_id)
    if not s:
        abort(404)

    s.enabled = bool(int(request.form.get('enabled', 0)))
    db.session.commit()

    return redirect(url_for('.list'))


@bp.route('/configure/<int:screen_id>', methods=['GET', 'POST'])
@bp.route('/configure/<int:screen_id>/<int:playlist_screen_id>', methods=['GET', 'POST'])
def configure(screen_id, playlist_screen_id=None):
    db_screen = Screen.query.get(screen_id)
    if not db_screen:
        abort(404)

    screen_cls = ScreenBase.get(db_screen.key)
    if not (screen_cls and screen_cls.config_form):
        abort(404)

    db_pls = None
    if playlist_screen_id:
        db_pls = PlaylistScreen.query.get(playlist_screen_id)
        if not db_pls:
            abort(404)

    config = dict(screen_cls.default_config)
    config.update(Config.load(screen=db_screen))
    if db_pls:
        config.update(Config.load(screen=db_screen, playlist_screen=db_pls))

    form = screen_cls.config_form(data=config)
    if form.validate_on_submit():
        # Because config starts out as a copy of the default config it should have all fields
        for k, v in form.data.items():
            if k in config:
                config[k] = v
        Config.save(config, screen=db_screen, playlist_screen=db_pls)
        msg = f"Saved configuration for {db_screen.title}"
        if db_pls:
            msg += f' in playlist {db_pls.playlist.name}'
        flash(msg, 'success')
        if db_pls:
            return redirect(url_for('playlist.edit_screens', playlist_id=db_pls.playlist.id))
        return redirect(url_for('.list'))

    if db_pls:
        flash("You are editing the configuration for a screen within a playlist, these settings only apply to that playlist", 'info')
    else:
        flash("You are editing the global configuration for a screen, these settings apply to all playlists that don't have their own configuration", 'info')

    return render_template('screen/configure.html.j2', screen=db_screen, form=form)
