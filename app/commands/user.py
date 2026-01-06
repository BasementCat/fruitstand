import sys

import click
from flask.cli import FlaskGroup
from sqlalchemy.exc import IntegrityError

from app.models import User
from app import db


@click.group('user', cls=FlaskGroup)
def cli():
    pass


@cli.command('create')
@click.option('-u', '--username', help="Username to create", prompt=True)
@click.option('-e', '--email', help="Email for the user", prompt=True)
@click.option('-p', '--password', help="Password for the user", prompt=True, hide_input=True)
@click.option('-a', '--admin', is_flag=True, help="This user is an admin")
@click.option('-d', '--disabled', is_flag=True, help="This user is disabled")
@click.option('-t', '--timezone', help="Timezone for the user", prompt=True)
@click.option('--ignore-exists', is_flag=True, help="Ignore if the user exists, for automation of initial user creation")
def create_user(username, email, password, admin, disabled, timezone, ignore_exists):
    user = User(
        username=username,
        email=email,
        is_admin=bool(admin),
        is_enabled=not bool(disabled),
        timezone=timezone,
    )
    user.password = password
    db.session.add(user)
    try:
        db.session.commit()
        sys.stderr.write(f"Created user #{user.id} {user.username}\n")
    except IntegrityError as e:
        db.session.rollback()
        user = User.get_by_username(username)
        assert user
        sys.stderr.write(f"Username {user.username} already exists as #{user.id}\n")
        if ignore_exists:
            sys.stderr.write(f"Ignoring because of --ignore-exists\n")
        else:
            sys.exit(1)
