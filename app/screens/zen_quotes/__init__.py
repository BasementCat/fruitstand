from app.lib.screen import Screen

from .view import bp


class ZenQuotes(Screen):
    key = "fruitstand/zenquotes"
    title = "Zen Quotes"
    description = "Display a random quote from Zen Quotes"
    blueprint = bp
    route = 'fruitstand_zenquotes.render'
