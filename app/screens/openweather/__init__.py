from flask import url_for
import arrow

from app.lib.screen import Screen

from .view import bp
from .config import OpenWeatherConfigForm
from . import jinja, metrics


class OpenWeather(Screen):
    key = "fruitstand/openweather"
    title = "OpenWeather"
    description = "Display weather forecast from OpenWeatherMap.org"
    blueprint = bp
    route = 'fruitstand_openweather.render'
    config_form = OpenWeatherConfigForm
    default_config = {
        'appid': None,
        'lat': None,
        'lon': None,
        'units': 'imperial',
    }
