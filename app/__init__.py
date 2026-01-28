import os
import importlib
import traceback

from werkzeug.exceptions import HTTPException
from flask import Flask, g, request, abort, render_template
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
    from app.lib.screen import Screen
    from app.lib import exc

    app = Flask(__name__)

    load_dotenv()
    app.config.from_prefixed_env(prefix='FRUITSTAND')
    app.config['CACHE_DRIVER'] = app.config.get('CACHE_DRIVER', 'filesystem')
    app.config['BROWSER'] = app.config.get('BROWSER', 'chrome')
    app.config['SCREEN_IMPORTS'] = list(filter(None, map(str.strip, (app.config.get('SCREEN_IMPORTS') or '').split(','))))
    app.config['SCREEN_IMPORTS'] += [
        'app.screens.zen_quotes',
        'app.screens.openweather',
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
        util as util_commands,
    )

    app.cli.add_command(compile_assets_commands.cli)
    app.cli.add_command(user_commands.cli)
    app.cli.add_command(util_commands.cli)

    # Do this last; lets screens add jinja stuff
    apply_jinja_env(app)

    @app.before_request
    def load_pls_config():
        if request.args.get('_render_display'):
            g.display = models.Display.sync(display_id=int(request.args.get('display_id', 0)))
            g.screen = Screen.load_for_render(g.display, playlist_screen_id=int(request.args.get('playlist_screen_id', 0)))

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e

        if g.get('display'):
            # Note that as Screen.load_for_render() has already been called, if the display doesn't exist in the DB, that already will have raised DisplayNotFound
            # In all cases of other exceptions, the display proxy will have a real display instance associated
            context = Screen.load_context(g.display)
            if isinstance(e, exc.DisplayPendingApproval):
                return render_template('screen_templates/pending_approval.html.j2', display=g.display, context=context)

            if not isinstance(e, exc.ScreenError):
                traceback.print_exception(e)
                e = exc.ScreenError.from_exc(g.display, e)
                e.log()

            return render_template('screen_templates/error.html.j2', display=g.display, context=context, error=e)

        return app.handle_exception(e)

    return app
