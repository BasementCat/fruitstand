from typing import Optional, Any, Dict, Self
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
    _is_system: bool = False

    def __init__(self, display: Display, playlist: Optional[Playlist], playlist_screen: Optional[PlaylistScreen], screen_config: Dict[str, Any], playlist_config: Dict[str, Any], context: Dict[str, Any], system: bool=False):
        self.display = display
        self.playlist = playlist
        self.playlist_screen = playlist_screen
        self.screen_config = dict(screen_config)
        self.playlist_config = dict(playlist_config)
        self.config = {}
        self.config.update(self.screen_config)
        self.config.update(self.playlist_config)
        self.context = dict(context)
        self.system = system

        loader = FileSystemLoader([
            os.path.join(current_app.root_path, current_app.template_folder, 'screen_templates'),
            os.path.join(self.get_path(), 'templates'),
        ])
        self.jinja_env = Environment(
            loader=loader,
            autoescape=select_autoescape()
        )
        apply_jinja_to_env(self.jinja_env)

    @property
    def refresh_interval(self):
        if self.system:
            # won't have playlist/playlist_screen
            return 600

        return self.playlist_screen.refresh_interval or self.playlist.default_refresh_interval

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
    def load_for_render(cls, display_id: Optional[int]=None, playlist_id: Optional[int]=None, playlist_screen_id: Optional[int]=None) -> Self:
        if display_id:
            display = Display.query.get(display_id)
        else:
            display = Display.sync()
        if not display:
            raise DisplayNotFound(display_id)

        system = False
        screen_cls_key = None
        extra_context = {}

        if current_app.config['ENABLE_DISPLAY_AUTH']:
            # Display must have passed a valid secret key
            if not (display.display_secret and display.display_secret.status != 'disabled'):
                system = True
                screen_cls_key = 'fruitstand/error'
                extra_context.update({
                    'error': {
                        'title': "Unauthenticated",
                        'message': "This screen is not authenticated.",
                    }
                })

        # If we've already set the class to load because of the above error, then skip this part
        # auth takes precedence over approval
        if not screen_cls_key and current_app.config['ENABLE_DISPLAY_APPROVAL']:
            # Display must have been approved by someone prior to rendering
            if display.status == 'pending':
                system = True
                screen_cls_key = 'fruitstand/approval_code'
            elif display.status == 'disapproved':
                system = True
                screen_cls_key = 'fruitstand/error'
                extra_context.update({
                    'error': {
                        'title': "Disapproved",
                        'message': "This screen is not approved.",
                    }
                })

        playlist = playlist_screen = None
        playlist_config = {}
        screen_config = {}
        if not system:
            playlist, playlist_screen = display.get_playlist_screen(
                playlist_id=playlist_id,
                playlist_screen_id=playlist_screen_id,
            )
            if not (playlist and playlist_screen):
                raise PlaylistNotFound((playlist_id, playlist_screen_id, display.id))

            screen_cls_key = playlist_screen.screen.key
            playlist_config = Config.load(screen=playlist_screen.screen, playlist_screen=playlist_screen)
            screen_config = Config.load(screen=playlist_screen.screen)

        screen_cls = cls.get(screen_cls_key)
        if not screen_cls:
            raise ScreenNotFound((
                screen_cls_key,
                playlist.id if playlist else None,
                playlist_screen.id if playlist_screen else None,
                display.id
            ))

        context = {'metrics': {}, 'extra': extra_context}
        for k in ('metrics', 'extra'):
            # JSON args
            try:
                context[k].update(json.loads(request.args.get(k, '{}')))
            except:
                pass
        context.update(display.get_context())

        return screen_cls(display, playlist, playlist_screen, screen_config, playlist_config, context, system=system)
