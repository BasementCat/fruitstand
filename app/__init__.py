import os
import importlib

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

from app.lib.screen import Screen
from app.lib.jinja import apply_jinja_env
from app.lib.cache import Cache


db = SQLAlchemy()
cache = Cache()


def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.config.from_prefixed_env(prefix='FRUITSTAND')
    app.config['CACHE_DRIVER'] = app.config.get('CACHE_DRIVER', 'filesystem')
    app.config['SCREEN_IMPORTS'] = list(filter(None, map(str.strip, (app.config.get('SCREEN_IMPORTS') or '').split(','))))
    app.config['SCREEN_IMPORTS'] += [
        'app.screens.zen_quotes',
    ]

    Bootstrap(app)
    db.init_app(app)
    Migrate(app, db)
    apply_jinja_env(app)
    cache.init_app(app)

    from app import models

    from app.views import (
        screen as screen_view,
        playlist as playlist_view,
        display as display_view,
    )

    app.register_blueprint(screen_view.bp, url_prefix='/screen')
    app.register_blueprint(playlist_view.bp, url_prefix='/playlist')
    app.register_blueprint(display_view.bp, url_prefix='/display')

    for mod in app.config['SCREEN_IMPORTS']:
        importlib.import_module(mod)

    Screen.install_all(app)

    return app
