from flask import Blueprint, g, render_template


bp = Blueprint('fruitstand_colortest', __name__, template_folder='templates', static_folder='static')


@bp.get('/')
def render():
    return g.screen.render_template('main.html.j2')
