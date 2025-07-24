from typing import Optional, Literal

import requests
import arrow

from app import cache
from app.lib.cache import make_key_with_args


class ZenQuotesAPI:
    base_url: str = "https://zenquotes.io"

    def __init__(self, api_key: Optional[str]=None, fetch_image: bool=False):
        self.api_key = api_key
        self.fetch_image = fetch_image if api_key else False

    def _make_request(self, mode: str, **kwargs):
        params = {'api': mode}
        if self.api_key:
            params['key'] = self.api_key
        params.update(kwargs)
        res = requests.get(self.base_url, params=params)
        res.raise_for_status()
        return res.json()

    def fetch_quote(self, mode: Literal['random', 'author', 'today'], author_slug: Optional[str]=None):
        if mode == 'author' and not (author_slug and self.api_key):
            mode = 'random'

        if mode == 'random':
            # Actual random mode returns one quote; we want many
            mode = 'quotes'

        expiry = 3600
        if mode == 'today':
            # Today's quote would only be updated at midnight CST
            midnight_cst = arrow.utcnow() \
                .to('America/Chicago') \
                .shift(days=1) \
                .replace(hour=0, minute=0, second=0, microsecond=0)
            expiry = (midnight_cst - arrow.utcnow()).total_seconds()

        key = make_key_with_args('fs-zq', *(self.api_key, self.fetch_image, author_slug), callback=mode)
        quotes = cache.get(key)
        if not quotes:
            quotes = self._make_request(mode, author=author_slug)

        if mode == 'today':
            out = quotes[0]
        else:
            out = quotes.pop()

        cache.set(key, expiry, quotes)
        return out
