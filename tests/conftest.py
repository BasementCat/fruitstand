import tempfile
import os
from functools import wraps
from contextlib import contextmanager

import pytest

from app import create_app, db


@contextmanager
def _gen_app():
    with tempfile.TemporaryDirectory(prefix='fruitstand-testing') as tempdir:
        db_path = os.path.join(tempdir, 'database.sqlite')
        db_uri = f'sqlite:///{db_path}'
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'testing secret key',
            'SQLALCHEMY_DATABASE_URI': db_uri,
            'BOOTSTRAP_SERVE_LOCAL': True,
            'TIMEZONE': 'America/Chicago',
            'CACHE_DRIVER': 'database',
            # 'ENABLE_USERS': True,
            # 'ENABLE_DISPLAY_APPROVAL': True,
            # 'ENABLE_DISPLAY_AUTH': True,
        })

        with app.app_context():
            db.create_all()
            yield app


def with_app(callback):
    @wraps(callback)
    def with_app_wrap(*a, **ka):
        with _gen_app() as app:
            return callback(*a, app=app, **ka)
    return with_app_wrap


@pytest.fixture()
def app():
    with _gen_app() as app:
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()
