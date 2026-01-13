from flask import Blueprint, render_template, abort, redirect, url_for, request, flash

from app.models import Screen, PlaylistScreen, Config, Playlist
from app.forms import PlaylistEditForm
from app.lib.screen import Screen as ScreenBase
from app.lib.user import login_required
from app import db


bp = Blueprint('playlist', __name__)


@bp.route('/', methods=['GET'])
@bp.route('/list', methods=['GET'])
@login_required
def list():
    playlists = Playlist.query.order_by(Playlist.name.asc())
    return render_template('playlist/list.html.j2', playlists=playlists)


@bp.route('/edit/new', methods=['GET', 'POST'])
@bp.route('/edit/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def edit(playlist_id=None):
    playlist = None
    if playlist_id:
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            abort(404)

    form = PlaylistEditForm(obj=playlist)
    if form.validate_on_submit():
        playlist = playlist or Playlist()
        form.populate_obj(playlist)
        db.session.add(playlist)
        db.session.commit()
        flash(f"Saved playlist {playlist.name}", 'success')
        return redirect(url_for('.list'))

    return render_template('playlist/edit.html.j2', playlist=playlist, form=form)


@bp.route('/edit/<int:playlist_id>/screens', methods=['GET', 'POST'])
@login_required
def edit_screens(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        abort(404)

    if request.method == 'POST':
        # Remap orders so each PLS has a unique order value & they are adjacent
        playlist_screens = PlaylistScreen.query.filter(PlaylistScreen.playlist == playlist).order_by(PlaylistScreen.order.asc()).all()
        playlist_screens_by_id = {pls.id: pls for pls in playlist_screens}
        for i, pls in enumerate(playlist_screens):
            pls.order = i
        orders = [pls.order for pls in playlist_screens]
        if orders:
            min_order = min(orders)
            max_order = max(orders)
        else:
            min_order = max_order = 1

        if request.form.get('action') == 'add_screen':
            screen = Screen.query.get(request.form.get('screen_id'))
            if screen:
                if request.form.get('where') == 'start':
                    db.session.add(PlaylistScreen(playlist=playlist, screen=screen, order=min_order - 1))
                elif request.form.get('where') == 'end':
                    db.session.add(PlaylistScreen(playlist=playlist, screen=screen, order=max_order + 1))
                else:
                    flash("Invalid location to add screen", 'danger')
            else:
                flash("Invalid screen ID to add", 'danger')
        elif request.form.get('action') == 'move':
            pls_id = int(request.form.get('playlist_screen_id', 0))
            if pls_id:
                pls_by_order = {pls.order: pls for pls in playlist_screens}
                move_pls = playlist_screens_by_id.get(pls_id)
                if move_pls:
                    move_order = None
                    if request.form.get('direction') == 'up':
                        move_order = move_pls.order - 1
                    else:
                        move_order = move_pls.order + 1
                    move_to_pls = pls_by_order.get(move_order)
                    if move_order is not None and move_to_pls:
                        move_to_pls.order = move_pls.order
                        move_pls.order = move_order
                    else:
                        # This is ok
                        # flash("Could not find playlist screen to move to", 'danger')
                        pass
                else:
                    flash("Could not find playlist screen to move", 'danger')
            else:
                flash("Invalid playlist screen", 'danger')
        elif request.form.get('action') == 'configure':
            pls = playlist_screens_by_id.get(int(request.form.get('playlist_screen_id', 0)))
            if not pls:
                flash("Invalid playlist screen", 'danger')
            elif request.form.get('configure_action') == 'delete':
                Config.query.filter(Config.playlist_screen == pls).delete()
                flash("Deleted configuration for playlist entry", 'info')
            elif request.form.get('configure_action') == 'refresh_interval':
                pls.refresh_interval = int(request.form.get('refresh_interval', 1800))
                if pls.refresh_interval < 0:
                    pls.refresh_interval = None
                db.session.commit()
            else:
                flash("Invalid configure action", 'danger')
        elif request.form.get('action') == 'delete':
            pls = playlist_screens_by_id.get(int(request.form.get('playlist_screen_id', 0)))
            if pls:
                db.session.delete(pls)
                flash("Deleted playlist entry", 'info')
            else:
                flash("Invalid playlist screen", 'danger')

        db.session.commit()
        return redirect(url_for('.edit_screens', playlist_id=playlist_id))

    screens = Screen.query.order_by(Screen.title.asc())
    return render_template('playlist/edit_screens.html.j2', playlist=playlist, screens=screens)


@bp.route('/delete/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def delete(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        abort(404)

    if request.method == 'POST':
        db.session.delete(playlist)
        db.session.commit()
        flash(f"Deleted playlist {playlist.name}", 'info')
        return redirect(url_for('.list'))

    has_config = any((pls.config for pls in playlist.playlist_screens))

    return render_template('playlist/delete.html.j2', playlist=playlist, has_config=has_config)
