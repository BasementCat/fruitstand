from typing import Optional, Any, Dict, Self
import json
import os
import inspect

from flask import Blueprint, Flask, url_for, request
from flask_wtf import FlaskForm

from app.models import Display, Config, Playlist, PlaylistScreen


class ScreenError(Exception):pass
class ScreenLoadError(ScreenError):pass
class DisplayNotFound(ScreenLoadError):pass
class PlaylistNotFound(ScreenLoadError):pass
class ScreenNotFound(ScreenLoadError):pass


class Screen:
    _all_screens = {}

    key: str = None
    title: str = None
    description: Optional[str] = None
    blueprint: Blueprint = None
    route: str = None
    config_form: Optional[FlaskForm] = None
    default_config: Dict[str, Any] = {}

    def __init__(self, display: Display, playlist: Playlist, playlist_screen: PlaylistScreen, screen_config: Dict[str, Any], playlist_config: Dict[str, Any], context: Dict[str, Any]):
        self.display = display
        self.playlist = playlist
        self.playlist_screen = playlist_screen
        self.screen_config = dict(screen_config)
        self.playlist_config = dict(playlist_config)
        self.config = {}
        self.config.update(self.screen_config)
        self.config.update(self.playlist_config)
        self.context = dict(context)

    @classmethod
    def get_path(cls):
        return os.path.dirname(inspect.getfile(cls))

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

    @classmethod
    def load_for_render(cls, display_id: Optional[int]=None, playlist_id: Optional[int]=None, playlist_screen_id: Optional[int]=None) -> Self:
        if display_id:
            display = Display.query.get(display_id)
        else:
            display = Display.sync()
        if not display:
            raise DisplayNotFound(display_id)

        playlist, playlist_screen = display.get_playlist_screen(
            playlist_id=playlist_id,
            playlist_screen_id=playlist_screen_id,
        )
        if not (playlist and playlist_screen):
            raise PlaylistNotFound((playlist_id, playlist_screen_id, display.id))

        screen_cls = cls.get(playlist_screen.screen.key)
        if not screen_cls:
            raise ScreenNotFound((playlist_screen.screen.key, playlist.id, playlist_screen.id, display.id))

        playlist_config = Config.load(screen=playlist_screen.screen, playlist_screen=playlist_screen)
        screen_config = Config.load(screen=playlist_screen.screen)

        context = {'metrics': {}}
        try:
            context['metrics'] = json.loads(request.args.get('metrics', ''))
        except:
            pass
        context.update(display.get_context())

        return screen_cls(display, playlist, playlist_screen, screen_config, playlist_config, context)
