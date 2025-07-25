from app.lib.screen import Screen

from .view import bp


class ColorTest(Screen):
    key = "fruitstand/color_test"
    title = "Color Test"
    description = "Display many pretty colors for testing"
    blueprint = bp
    route = 'fruitstand_colortest.render'
