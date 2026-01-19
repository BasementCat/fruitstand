import sys
import time

import click
from flask import current_app
from flask.cli import FlaskGroup
from sqlalchemy import text, create_engine

from app import db


@click.group('util', cls=FlaskGroup)
def cli():
    pass


@cli.command('test-db')
@click.option('-t', '--timeout', type=int, default=60, help="Exit with an error if the database is not ready after this many seconds")
@click.option('-d', '--delay', type=int, default=1, help="Initial delay for connection failures")
@click.option('-f', '--falloff', type=float, default=1.2, help="Multiplier for the delay")
@click.option('-D', '--max-delay', type=float, default=10, help="Maximum delay")
def test_db(timeout, delay, falloff, max_delay):
    candidate_connect_args = [
        # pymysql
        {'read_timeout': 10, 'write_timeout': 10, 'connect_timeout': 10},
        # mysqldb, sqlite
        {'connect_timeout': 10},
    ]
    engine = None
    for connect_args in candidate_connect_args:
        try:
            engine = create_engine(
                current_app.config['SQLALCHEMY_DATABASE_URI'],
                pool_pre_ping=True,
                pool_timeout=10,
                connect_args=connect_args,
            )
            break
        except:
            pass

    if not engine:
        sys.stderr.write("[E] Failed to create engine with timeout\n")
        sys.exit(3)

    start = time.monotonic()
    while True:
        try:
            val = None
            with engine.connect() as connection:
                result = connection.execute(text("select 1;"))
                for row in result:
                    val = row[0]
                    break
            if val == 1:
                sys.stderr.write("[I] Connected to database after {:1.2f}s\n".format(time.monotonic() - start))
                sys.exit(0)
            else:
                sys.stderr.write("[E] Unexpected result, 'select 1;' returned {}\n".format(repr(val)))
                sys.exit(2)
        except Exception as e:
            duration = time.monotonic() - start
            if duration >= timeout:
                sys.stderr.write("[E] Failed to connect to database after {:1.2f}s (timeout {:d}s), got {}: {}\n".format(
                    duration,
                    timeout,
                    e.__class__.__name__,
                    str(e)
                ))
                sys.exit(1)
            sys.stderr.write("[W] Failed to connect to database, trying again in {:1.2f}s\n".format(delay))
            if delay:
                time.sleep(delay)
            delay = min(max_delay, delay * falloff)
