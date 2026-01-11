import os
import importlib

from flask import Flask, g, request, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

from app.lib.jinja import apply_jinja_env
from app.lib.cache import Cache


db = SQLAlchemy()
cache = Cache()
login_manager = LoginManager()


def create_app():
    from app.lib.screen import Screen, ScreenLoadError

    app = Flask(__name__)

    load_dotenv()
    app.config.from_prefixed_env(prefix='FRUITSTAND')
    app.config['CACHE_DRIVER'] = app.config.get('CACHE_DRIVER', 'filesystem')
    app.config['BROWSER'] = app.config.get('BROWSER', 'chrome')
    app.config['SCREEN_IMPORTS'] = list(filter(None, map(str.strip, (app.config.get('SCREEN_IMPORTS') or '').split(','))))
    app.config['SCREEN_IMPORTS'] += [
        'app.screens.zen_quotes',
        'app.screens.openweather',
        # Internal/system screens
        'app.screens.approval_code',
        'app.screens.error',
    ]
    if app.debug:
        app.config['SCREEN_IMPORTS'].append('app.screens.color_test')
    app.config['TIMEZONE'] = app.config.get('TIMEZONE', 'UTC')
    app.config['ENABLE_USERS'] = bool(app.config.get('ENABLE_USERS', False))
    app.config['ENABLE_DISPLAY_APPROVAL'] = bool(app.config.get('ENABLE_DISPLAY_APPROVAL', False))
    app.config['ENABLE_DISPLAY_AUTH'] = bool(app.config.get('ENABLE_DISPLAY_AUTH', False))

    Bootstrap(app)
    db.init_app(app)
    Migrate(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "user.login"

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(user_id)

    from app.views import (
        index as index_view,
        screen as screen_view,
        playlist as playlist_view,
        display as display_view,
        user as user_view
    )

    app.register_blueprint(index_view.bp)
    app.register_blueprint(screen_view.bp, url_prefix='/screen')
    app.register_blueprint(playlist_view.bp, url_prefix='/playlist')
    app.register_blueprint(display_view.bp, url_prefix='/display')
    app.register_blueprint(user_view.bp, url_prefix='/user')

    for mod in app.config['SCREEN_IMPORTS']:
        importlib.import_module(mod)

    Screen.install_all(app)

    from app.commands import (
        compile_assets as compile_assets_commands,
        user as user_commands,
    )

    app.cli.add_command(compile_assets_commands.cli)
    app.cli.add_command(user_commands.cli)

    # Do this last; lets screens add jinja stuff
    apply_jinja_env(app)

    @app.before_request
    def load_pls_config():
        if request.args.get('_render_display'):
            display_id = int(request.args.get('display_id', 0))
            if display_id:
                pls_id = int(request.args.get('playlist_screen_id', 0))
                try:
                    g.screen = Screen.load_for_render(display_id=display_id, playlist_screen_id=pls_id)
                except ScreenLoadError:
                    abort(404)
            else:
                abort(404)
    return app
