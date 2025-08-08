from flask import Blueprint, render_template


bp = Blueprint('index', __name__)


@bp.route('/', methods=['GET'])
def index():
    return render_template('index/index.html.j2')
