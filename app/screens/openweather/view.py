from flask import Blueprint, g, render_template
import arrow

from app.lib.jinja import dt
from .api import OpenWeatherAPI


bp = Blueprint('fruitstand_openweather', __name__, template_folder='templates', static_folder='static')


@bp.get('/')
def render():
    api = OpenWeatherAPI(**g.screen.config)
    forecast = api.get_forecast()
    air_pollution = api.get_air_pollution()
    in_24_h = arrow.utcnow().shift(days=1)
    graph_data = [
        {
            'label': dt(h['dt'], format='ha', no_markup=True),
            'temp': h['temp'],
            'precip': h['pop'],
            'humid': h['humidity'] / 100.0,
        }
        for h in forecast['hourly']
        if arrow.get(h['dt']) <= in_24_h
    ]
    return g.screen.render_template('main.html.j2', forecast=forecast, air_pollution=air_pollution, graph_data=graph_data)
