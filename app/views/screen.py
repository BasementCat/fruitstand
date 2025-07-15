from flask import Blueprint, render_template

from app.models import Screen as ScreenModel
from app.lib.screen import Screen


bp = Blueprint('screen', __name__)

@bp.route('/', methods=['GET'])
@bp.route('/list', methods=['GET'])
def list():
    ScreenModel.sync(Screen.get_all().values())

    return render_template('screen/list.html.j2', screens=ScreenModel.all_by_key())
