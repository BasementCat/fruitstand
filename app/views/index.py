from flask import Blueprint, render_template

from app.lib.user import login_required


bp = Blueprint('index', __name__)


@bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index/index.html.j2')
