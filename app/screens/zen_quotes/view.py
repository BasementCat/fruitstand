from flask import Blueprint


bp = Blueprint('fruitstand_zenquotes', __name__)


@bp.get('/')
def render():
    return 'hello world'
