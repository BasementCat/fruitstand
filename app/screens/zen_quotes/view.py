from flask import Blueprint, g, render_template

from .api import ZenQuotesAPI


bp = Blueprint('fruitstand_zenquotes', __name__, template_folder='templates', static_folder='static')


@bp.get('/')
def render():
    api = ZenQuotesAPI(api_key=g.screen.config.get('api_key'), fetch_image=g.screen.config.get('display_image'))
    quote = api.fetch_quote(g.screen.config['mode'], author_slug=g.screen.config.get('author_slug'))
    return g.screen.render_template('main.html.j2', quote=quote)
