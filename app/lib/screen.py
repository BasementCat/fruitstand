from typing import Optional, Any, Dict

from flask import Blueprint, Flask, url_for
from flask_wtf import FlaskForm


class Screen:
    _all_screens = {}

    key: str = None
    title: str = None
    description: Optional[str] = None
    blueprint: Blueprint = None
    route: str = None
    config_form: Optional[FlaskForm] = None
    default_config: Dict[str, Any] = {}

    def __init__(self, screen_config: Dict[str, Any], playlist_config: Dict[str, Any], context: Dict[str, Any]):
        self.screen_config = dict(screen_config)
        self.playlist_config = dict(playlist_config)
        self.config = {}
        self.config.update(self.screen_config)
        self.config.update(self.playlist_config)
        self.context = dict(context)

        self.setup()

    @classmethod
    def install_all(cls, app: Flask):
        queue = [cls]
        while queue:
            s_cls = queue.pop()
            if s_cls.key:
                cls._all_screens[s_cls.key] = s_cls
                s_cls.mount(app)
            queue += s_cls.__subclasses__()

    @classmethod
    def get_all(cls):
        return dict(cls._all_screens)

    @classmethod
    def get(cls, key):
        return cls.get_all().get(key)

    @classmethod
    def mount(cls, app: Flask):
        app.register_blueprint(cls.blueprint, url_prefix='/screens/render/' + cls.key)

    def setup(self):
        pass

    def preload(self):
        pass

    def load(self):
        pass

    def render(self):
        # get external url to route
        # ext. headless browser, screenshot
        # return PIL image?
        pass
