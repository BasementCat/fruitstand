from app.lib.screen import Screen

from .view import bp
from .config import ZenQuotesConfigForm


class ZenQuotes(Screen):
    key = "fruitstand/zenquotes"
    title = "Zen Quotes"
    description = "Display a random quote from Zen Quotes"
    blueprint = bp
    route = 'fruitstand_zenquotes.render'
    config_form = ZenQuotesConfigForm
    default_config = {
        'mode': 'random',
        'author': None,
        'api_key': None,
        'display_image': False,
    }
