from flask import url_for
from markupsafe import Markup
import arrow

from app.lib.jinja import jfilter, jglobal, fixed


METRICS = {
    'temp': {
        'suffixes': {
            'standard': 'K',
            'imperial': 'F',
            'metric': 'C',
        },
        'convert_to_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: (v + 459.67) * (5.0 / 9.0),
            'metric': lambda v: v + 273.15,
        },
        'convert_from_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: (v * (9.0 / 5.0)) - 459.67,
            'metric': lambda v: v - 273.15,
        },
    },
    'pressure': {
        'suffixes': {
            'standard': 'hPa',
            'imperial': 'inHg',
            'metric': 'mmHg',
        },
        'convert_to_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v * 33.86389,
            'metric': lambda v: v * 1.333224,
        },
        'convert_from_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v * 0.02953,
            'metric': lambda v: v * 0.75006375541921,
        },
    },
    'speed': {
        'suffixes': {
            # TODO: unsure if this is correct
            'standard': 'm/s',
            'imperial': 'mph',
            'metric': 'kph',
        },
        'convert_to_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v * 0.44704,
            'metric': lambda v: v / 3.6,
        },
        'convert_from_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v / 0.44704,
            'metric': lambda v: v * 3.6,
        },
    },
    'distance': {
        'suffixes': {
            # TODO: unsure if this is correct
            'standard': 'm',
            'imperial': 'mi',
            'metric': 'km',
        },
        'convert_to_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v * 1609.344,
            'metric': lambda v: v * 1000.0,
        },
        'convert_from_standard': {
            'standard': lambda v: v,
            'imperial': lambda v: v / 1609.344,
            'metric': lambda v: v / 1000,
        },
    }
}



@jfilter()
def weather_suffix(units, what='temp'):
    return METRICS.get(what, {}).get('suffixes', {}).get(units, '???')


@jfilter()
def weather_convert(value, to_units, what, d=2, from_units='standard'):
    value = METRICS[what]['convert_to_standard'][from_units](value)
    value = METRICS[what]['convert_from_standard'][to_units](value)
    value = fixed(value, d=d)
    suffix = weather_suffix(to_units, what=what)
    return Markup(f'{value} <span class="suffix">{suffix}</span>')


@jglobal()
def get_conditions_image(forecast):
    """\
    Takes the "current" key or a daily item
    """
    id = forecast['weather'][0]['id']
    if 'moonrise' in forecast:
        now = arrow.utcnow()
        moonrise = arrow.get(forecast['moonrise'])
        moonset = arrow.get(forecast['moonset'])
        moon = ((now >= moonrise and now < moonset) or (moonrise > moonset and now >= moonrise)) and forecast['moon_phase'] > 0 and forecast['moon_phase'] < 1
    else:
        moon = False

    day = forecast['weather'][0]['icon'].endswith('d')
    windy = forecast.get('wind_speed', 0) >= 32.2 or forecast.get('wind_gust', 0) >= 40.2
    cloudy = forecast['clouds'] > 60.25

    image_name = None
    # see https://github.com/lmarzen/esp32-weather-epd/blob/main/platformio/src/display_utils.cpp
    if id in (
        200, # Thunderstorm  thunderstorm with light rain     11d
        201, # Thunderstorm  thunderstorm with rain           11d
        202, # Thunderstorm  thunderstorm with heavy rain     11d
        210, # Thunderstorm  light thunderstorm               11d
        211, # Thunderstorm  thunderstorm                     11d
        212, # Thunderstorm  heavy thunderstorm               11d
        221, # Thunderstorm  ragged thunderstorm              11d
    ):
        if not cloudy and day:
            image_name = 'wi-day-thunderstorm'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-thunderstorm'
        else:
            image_name = 'wi-thunderstorm'
    elif id in (
        230, # Thunderstorm  thunderstorm with light drizzle  11d
        231, # Thunderstorm  thunderstorm with drizzle        11d
        232, # Thunderstorm  thunderstorm with heavy drizzle  11d
    ):
        if not cloudy and day:
            image_name = 'wi-day-storm-showers'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-storm-showers'
        else:
            image_name = 'wi-storm-showers'
    # Group 3xx: Drizzle
    elif id in (
        300, # Drizzle       light intensity drizzle          09d
        301, # Drizzle       drizzle                          09d
        302, # Drizzle       heavy intensity drizzle          09d
        310, # Drizzle       light intensity drizzle rain     09d
        311, # Drizzle       drizzle rain                     09d
        312, # Drizzle       heavy intensity drizzle rain     09d
        313, # Drizzle       shower rain and drizzle          09d
        314, # Drizzle       heavy shower rain and drizzle    09d
        321, # Drizzle       shower drizzle                   09d
    ):
        if not cloudy and day:
            image_name = 'wi-day-showers'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-showers'
        else:
            image_name = 'wi-showers'
    # Group 5xx: Rain
    elif id in (
        500, # Rain          light rain                       10d
        501, # Rain          moderate rain                    10d
        502, # Rain          heavy intensity rain             10d
        503, # Rain          very heavy rain                  10d
        504, # Rain          extreme rain                     10d
    ):
        if not cloudy and day and windy:
            image_name = 'wi-day-rain-wind'
        elif not cloudy and day:
            image_name = 'wi-day-rain'
        elif not cloudy and not day and moon and windy:
            image_name = 'wi-night-alt-rain-wind'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-rain'
        elif windy:
            image_name = 'wi-rain-wind'
        else:
            image_name = 'wi-rain'
    elif id == 511: # Rain          freezing rain                    13d
        if not cloudy and day:
            image_name = 'wi-day-rain-mix'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-rain-mix'
        else:
            image_name = 'wi-rain-mix'
    elif id in (
        520, # Rain          light intensity shower rain      09d
        521, # Rain          shower rain                      09d
        522, # Rain          heavy intensity shower rain      09d
        531, # Rain          ragged shower rain               09d
    ):
        if not cloudy and day:
            image_name = 'wi-day-showers'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-showers'
        else:
            image_name = 'wi-showers'
    # Group 6xx: Snow
    elif id in (
        600, # Snow          light snow                       13d
        601, # Snow          Snow                             13d
        602, # Snow          Heavy snow                       13d
    ):
        if not cloudy and day and windy:
            image_name = 'wi-day-snow-wind'
        elif not cloudy and day:
            image_name = 'wi-day-snow'
        elif not cloudy and not day and moon and windy:
            image_name = 'wi-night-alt-snow-wind'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-snow'
        elif windy:
            image_name = 'wi-snow-wind'
        else:
            image_name = 'wi-snow'
    elif id in (
        611, # Snow          Sleet                            13d
        612, # Snow          Light shower sleet               13d
        613, # Snow          Shower sleet                     13d
    ):
        if not cloudy and day:
            image_name = 'wi-day-sleet'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-sleet'
        else:
            image_name = 'wi-sleet'
    elif id in (
        615, # Snow          Light rain and snow              13d
        616, # Snow          Rain and snow                    13d
        620, # Snow          Light shower snow                13d
        621, # Snow          Shower snow                      13d
        622, # Snow          Heavy shower snow                13d
    ):
        if not cloudy and day:
            image_name = 'wi-day-rain-mix'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-alt-rain-mix'
        else:
            image_name = 'wi-rain-mix'
    # Group 7xx: Atmosphere
    elif id == 701: # Mist          mist                             50d
        if not cloudy and day:
            image_name = 'wi-day-fog'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-fog'
        else:
            image_name = 'wi-fog'
    elif id == 711: # Smoke         Smoke                            50d
        image_name = 'wi-smoke'
    elif id == 721: # Haze          Haze                             50d
        if day and not cloudy:
            image_name = 'wi-day-haze'
        else:
            image_name = 'wi-dust'
    elif id == 731: # Dust          sand/dust whirls                 50d
        image_name = 'wi-sandstorm'
    elif id == 741: # Fog           fog                              50d
        if not cloudy and day:
            image_name = 'wi-day-fog'
        elif not cloudy and not day and moon:
            image_name = 'wi-night-fog'
        else:
            image_name = 'wi-fog'
    elif id == 751: # Sand          sand                             50d
        image_name = 'wi-sandstorm'
    elif id == 761: # Dust          dust                             50d
        image_name = 'wi-dust'
    elif id == 762: # Ash           volcanic ash                     50d
        image_name = 'wi-volcano'
    elif id == 771: # Squall        squalls                          50d
        image_name = 'wi-cloudy-gusts'
    elif id == 781: # Tornado       tornado                          50d
        image_name = 'wi-tornado'
    # Group 800: Clear
    elif id == 800: # Clear         clear sky                        01d 01n
        if windy:
            image_name = 'wi-strong-wind'
        elif not day and moon:
            image_name = 'wi-night-clear'
        elif not day and not moon:
            image_name = 'wi-stars'
        else:
            image_name = 'wi-day-sunny'
    # Group 80x: Clouds
    elif id == 801: # Clouds        few clouds: 11-25%               02d 02n
        if windy:
            image_name = 'wi-strong-wind'
        elif not day and moon:
            image_name = 'wi-night-alt-partly-cloudy'
        elif not day and not moon:
            image_name = 'wi-stars'
        else:
            image_name = 'wi-day-sunny-overcast'
    elif id in (
        802, # Clouds        scattered clouds: 25-50%         03d 03n
        803, # Clouds        broken clouds: 51-84%            04d 04n
    ):
        if windy and day:
            image_name = 'wi-day-cloudy-gusts'
        elif windy and not day and moon:
            image_name = 'wi-night-alt-cloudy-gusts'
        elif windy and not day and not moon:
            image_name = 'wi-cloudy-gusts'
        elif not day and moon:
            image_name = 'wi-night-alt-cloudy'
        elif not day and not moon:
            image_name = 'wi-cloud'
        else:
            image_name = 'wi-day-cloudy'
    elif id == 804: # Clouds        overcast clouds: 85-100%         04d 04n
        if windy:
            image_name = 'wi-cloudy-gusts'
        else:
            image_name = 'wi-cloudy'
    else:
        if id >= 200 and id < 300:
            image_name = 'wi-thunderstorm'
        elif id >= 300 and id < 400:
            image_name = 'wi-showers'
        elif id >= 500 and id < 600:
            image_name = 'wi-rain'
        elif id >= 600 and id < 700:
            image_name = 'wi-snow'
        elif id >= 700 and id < 800:
            image_name = 'wi-fog'
        elif id >= 800 and id < 900:
            image_name = 'wi-cloudy'
        else:
            image_name = 'wi-na'

    return url_for('fruitstand_openweather.static', filename=f'images/{image_name}.svg')
