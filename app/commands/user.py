import sys

import click
from flask.cli import FlaskGroup
from sqlalchemy.exc import IntegrityError
import tabulate

from app.models import User
from app import db


@click.group('user', cls=FlaskGroup)
def cli():
    pass


@cli.command('list')
def list_users():
    users = User.query.order_by(User.username.asc()).all()
    headers = ['ID', 'Username', 'Slug', 'Email', 'Admin?', 'Enabled?', 'Timezone']
    rows = []
    for u in users:
        rows.append([
            u.id,
            u.username,
            u.username_slug,
            u.email,
            'Yes' if u.is_admin else '',
            '' if u.is_enabled else 'No',
            u.timezone,
        ])
    print(tabulate.tabulate(rows, headers=headers))


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


@cli.command('edit')
@click.argument('user_id')
@click.option('-u', '--username', help="Change username")
@click.option('-e', '--email', help="Change email")
@click.option('-p', '--password', help="Change password")
@click.option('-P', '--ask-password', help="Prompt to change password", is_flag=True)
@click.option('--admin/--no-admin', is_flag=True, default=None, help="Set or clear admin flag")
@click.option('--enabled/--no-enabled', is_flag=True, default=None, help="Set or clear enabled flag")
@click.option('-t', '--timezone', help="Change timezone")
def edit_user(user_id, username, email, password, ask_password, admin, enabled, timezone):
    user = User.query.get(user_id)
    if not user:
        sys.stderr.write(f"No such user ID #{user_id}\n")
        sys.exit(1)

    if ask_password:
        password = click.prompt("Password", hide_input=True)

    if username is not None:
        user.username = username

    if email is not None:
        user.email = email

    if password is not None:
        user.password = password

    if admin is not None:
        user.is_admin = admin

    if enabled is not None:
        user.is_enabled = enabled

    if timezone is not None:
        user.timezone = timezone

    db.session.commit()
    sys.stderr.write(f"Saved user #{user_id} {user.username}\n")


@cli.command('delete')
@click.argument('user_id')
@click.option('-f', '--force', is_flag=True, help="Force deletion; do not confirm")
def delete_user(user_id, force):
    user = User.query.get(user_id)
    if not user:
        sys.stderr.write(f"No such user ID #{user_id}\n")
        sys.exit(1)

    if not force:
        if not click.confirm(f"Are you sure you want to delete user #{user_id} {user.username}"):
            sys.stderr.write("Aborted\n")
            sys.exit(0)

    db.session.delete(user)
    db.session.commit()
    sys.stderr.write(f"Deleted user #{user_id}\n")
