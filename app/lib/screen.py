from typing import Optional, Any, Dict, Self, Tuple
import json
import os
import inspect

from flask import Blueprint, Flask, url_for, request, current_app
from flask_wtf import FlaskForm
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Display, Config, Playlist, PlaylistScreen
from app.lib.jinja import apply_jinja_to_env


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

        loader = FileSystemLoader([
            os.path.join(current_app.root_path, current_app.template_folder, 'screen_templates'),
            os.path.join(self.get_path(), 'templates'),
        ])
        self.jinja_env = Environment(
            loader=loader,
            autoescape=select_autoescape()
        )
        apply_jinja_to_env(self.jinja_env)

    def render_template(self, template_name, **kwargs):
        kwargs.update({
            'screen': self,
            'display': self.display,
            'context': self.context,
            'url_for': current_app.url_for,
        })
        template = self.jinja_env.get_template(template_name)
        return template.render(**kwargs)



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
    def _load_display(cls, display_id: Optional[int]=None) -> Display:
        if display_id:
            display = Display.query.get(display_id)
        else:
            display = Display.sync()

        if not display:
            raise DisplayNotFound(display_id)

        return display

    @classmethod
    def _load_playlist_and_playlist_screen(cls, display: Display, playlist_id: Optional[int]=None, playlist_screen_id: Optional[int]=None) -> Tuple[Playlist, PlaylistScreen]:
        playlist, playlist_screen = display.get_playlist_screen(
            playlist_id=playlist_id,
            playlist_screen_id=playlist_screen_id,
        )
        if not (playlist and playlist_screen):
            raise PlaylistNotFound((playlist_id, playlist_screen_id, display.id))
        return playlist, playlist_screen

    @classmethod
    def _load_screen_class(cls, display: Display, playlist: Playlist, playlist_screen: PlaylistScreen) -> Self:
        screen_cls = cls.get(playlist_screen.screen.key)
        if not screen_cls:
            raise ScreenNotFound((playlist_screen.screen.key, playlist.id, playlist_screen.id, display.id))
        return screen_cls

    @classmethod
    def _load_config(cls, playlist_screen: PlaylistScreen) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return (
            Config.load(screen=playlist_screen.screen, playlist_screen=playlist_screen),
            Config.load(screen=playlist_screen.screen),
        )

    @classmethod
    def _load_context(cls, display: Display) -> dict:
        context = {'metrics': {}}
        try:
            context['metrics'] = json.loads(request.args.get('metrics', ''))
        except:
            pass
        context.update(display.get_context())
        return context

    @classmethod
    def load_for_render(cls, display_id: Optional[int]=None, playlist_id: Optional[int]=None, playlist_screen_id: Optional[int]=None) -> Self:
        display = cls._load_display(display_id=display_id)
        playlist, playlist_screen = cls._load_playlist_and_playlist_screen(
            display,
            playlist_id=playlist_id,
            playlist_screen_id=playlist_screen_id,
        )
        screen_cls = cls._load_screen_class(display, playlist, playlist_screen)
        playlist_config, screen_config = cls._load_config(playlist_screen)
        context = cls._load_context(display)

        return screen_cls(display, playlist, playlist_screen, screen_config, playlist_config, context)
