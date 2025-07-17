from flask import Blueprint, render_template, abort, flash, redirect, url_for
import arrow

from app import db
from app.models import Display, Playlist, Screen
from app.constants import DISPLAY_SPEC, COLOR_SPEC
from app.forms import DisplayEditForm


bp = Blueprint('display', __name__)


@bp.route('/render', methods=['GET'])
def render():
    display = Display.sync()
    if not display:
        abort(404)

    return 'foo'


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
