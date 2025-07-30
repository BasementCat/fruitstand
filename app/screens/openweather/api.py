from typing import Optional, Literal, Dict

import requests
import arrow

from app import cache
from app.lib.cache import make_key_with_args


class OpenWeatherAPI:
    base_url: str = 'https://api.openweathermap.org/data'
    api_versions: Dict[str, str] = {
        'onecall': '3.0',
        'air_pollution': '2.5',
    }

    def __init__(self, appid, lat, lon, units, **kwargs):
        self.appid = appid
        self.lat = lat
        self.lon = lon
        self.units = units

    def _build_base_url(self, api: str) -> str:
        return f"{self.base_url}/{self.api_versions[api]}/{api}"

    def _make_request(self, api: str, **kwargs):
        url = self._build_base_url(api)
        params = dict({'appid': self.appid}, **kwargs)
        def _fetch(url, params):
            res = requests.get(url, params=params)
            res.raise_for_status()
            return res.json()
        return cache.get_or_fetch(f'openweather-api-{api}', 600, _fetch, url, params)

    def get_forecast(self):
        return self._make_request('onecall', lat=self.lat, lon=self.lon, units=self.units)

    def get_air_pollution(self):
        return self._make_request('air_pollution', lat=self.lat, lon=self.lon)
