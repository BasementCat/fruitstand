import os
import subprocess

import click
from flask import current_app
from flask.cli import FlaskGroup

from app.lib.screen import Screen


@click.group('compile', cls=FlaskGroup)
def cli():
    pass


@cli.command('sass')
@click.option('--env', default='prod', type=click.Choice(['dev', 'prod']), help="Compile for a given target environment")
@click.option('--watch', is_flag=True, help="Watch for changes")
def sass(env, watch):
    static_sass_dir = os.path.join(current_app.root_path, 'src/sass')
    static_dir = os.path.join(current_app.root_path, current_app.static_folder, 'css')
    screens = list(Screen.get_all().values())
    candidate_dirs = [(static_sass_dir, static_dir)] + [(os.path.join(s.get_path(), 'src/sass'), os.path.join(s.get_path(), 'static/css')) for s in screens]
    candidate_dirs = filter(lambda paths: os.path.isdir(paths[0]), candidate_dirs)
    candidate_dirs = list(map(lambda paths: ':'.join(paths), candidate_dirs))
    if not candidate_dirs:
        raise RuntimeError("No candidate dirs to compile")

    command = ['npm', 'run', 'sass', '--']
    command += candidate_dirs
    command += [
        f'--load-path={static_sass_dir}',
        '--style=' + ('compressed' if env == 'prod' else 'expanded'),
        '--error-css' if env == 'dev' else '--no-error-css',
        '--no-source-map',
        '--watch' if watch else None,
    ]
    subprocess.check_call(list(filter(None, command)))
