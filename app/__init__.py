import os
import importlib

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

from app.lib.screen import Screen
from app.lib.jinja import apply_jinja_env


db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.config.from_prefixed_env()
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': os.environ.get('FLASK_SQLALCHEMY_DATABASE_URI'),
        'BOOTSTRAP_SERVE_LOCAL': os.environ.get('FLASK_BOOTSTRAP_SERVE_LOCAL'),
        'SCREEN_IMPORTS': os.environ.get('FLASK_SCREEN_IMPORTS'),
    })
    app.config['SCREEN_IMPORTS'] = list(filter(None, map(str.strip, (app.config['SCREEN_IMPORTS'] or '').split(','))))
    app.config['SCREEN_IMPORTS'] += [
        'app.screens.zen_quotes',
    ]

    Bootstrap(app)
    db.init_app(app)
    Migrate(app, db)
    apply_jinja_env(app)

    from app import models

    from app.views import screen as screen_view

    app.register_blueprint(screen_view.bp, url_prefix='/screen')

    for mod in app.config['SCREEN_IMPORTS']:
        importlib.import_module(mod)

    Screen.install_all(app)

    return app
