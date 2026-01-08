from app.lib.screen import Screen

from .view import bp


class Error(Screen):
    key = "fruitstand/error"
    title = "Error"
    description = "Render an error"
    blueprint = bp
    route = 'fruitstand_error.render'
    _is_system = True
