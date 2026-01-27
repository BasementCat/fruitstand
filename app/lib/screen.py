from typing import Optional, Any, Dict, Self
import json
import os
import inspect

from flask import Blueprint, Flask, url_for, request, current_app
from flask_wtf import FlaskForm
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Display, DisplayProxy, Config, Playlist, PlaylistScreen
from app.lib.jinja import apply_jinja_to_env
from app.lib import exc


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

    def __init__(self, display: Display, playlist: Optional[Playlist], playlist_screen: Optional[PlaylistScreen], screen_config: Dict[str, Any], playlist_config: Dict[str, Any], context: Dict[str, Any]):
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

    @property
    def refresh_interval(self):
        if not (self.playlist_screen and self.playlist):
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
        display = Display.sync(display_id=display_id)
        exc_args = {
            'display': display,
            'display_id': display_id,
            'playlist_id': playlist_id,
            'playlist_screen_id': playlist_screen_id,
        }

        context = {'metrics': {}, 'extra': {}}
        for k in ('metrics', 'extra'):
            # JSON args
            try:
                context[k].update(json.loads(request.args.get(k, '{}')))
            except:
                pass

        try:
            if not (display.key and display.display):
                # no display was found or could be synced
                raise exc.DisplayNotFound(**exc_args)

            context.update(display.display.get_context())

            if current_app.config['ENABLE_DISPLAY_AUTH']:
                # Display must have passed a valid secret key
                if not (display.display_secret and display.display_secret.status != 'disabled'):
                    raise exc.DisplayNotAuthenticated(
                        title='Unauthenticated',
                        message="This display is not authenticated.",
                        **exc_args,
                    )

            if current_app.config['ENABLE_DISPLAY_APPROVAL']:
                # Display must have been approved by someone prior to rendering
                if display.status == 'pending':
                    raise exc.DisplayPendingApproval(**exc_args)
                elif display.status == 'disapproved':
                    raise exc.DisplayNotApproved(
                        title='Disapproved',
                        message="This display is not approved.",
                        **exc_args,
                    )

            playlist, playlist_screen = display.display.get_playlist_screen(
                playlist_id=playlist_id,
                playlist_screen_id=playlist_screen_id,
            )
            if not (playlist and playlist_screen):
                raise exc.PlaylistNotFound(title='Playlist Not Found', message="This display does not have a playlist configured.", **exc_args)

            screen_cls_key = playlist_screen.screen.key
            playlist_config = Config.load(screen=playlist_screen.screen, playlist_screen=playlist_screen)
            screen_config = Config.load(screen=playlist_screen.screen)

            exc_args['screen_cls_key'] = screen_cls_key
            screen_cls = cls.get(screen_cls_key)
            if not screen_cls:
                raise exc.ScreenNotFound(**exc_args)
        except exc.ScreenError as e:
            e.log()
            display = e.display
            screen_cls_key = e.error_screen_cls_key
            screen_cls = cls.get(screen_cls_key)
            playlist = playlist_screen = None
            screen_config = playlist_config = {}
            context['extra'].update({'error': e.get_error_context()})

        return screen_cls(display, playlist, playlist_screen, screen_config, playlist_config, context)
