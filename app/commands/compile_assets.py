import os
import subprocess
import json
import threading
import signal
import time

import click
from flask import current_app
from flask.cli import FlaskGroup

from app.lib.screen import Screen


@click.group('compile', cls=FlaskGroup)
def cli():
    pass


def get_dirs(src_dir, dest_dir=None, join=':'):
    dest_dir = dest_dir or src_dir
    base_src_dir = os.path.join(current_app.root_path, f'src/{src_dir}')
    base_dest_dir = os.path.join(current_app.root_path, current_app.static_folder, dest_dir)
    screens = list(Screen.get_all().values())
    candidate_dirs = [(base_src_dir, base_dest_dir)] + [(os.path.join(s.get_path(), f'src/{src_dir}'), os.path.join(s.get_path(), f'static/{dest_dir}')) for s in screens]
    candidate_dirs = filter(lambda paths: os.path.isdir(paths[0]), candidate_dirs)
    if join:
        candidate_dirs = map(lambda paths: join.join(paths), candidate_dirs)
    candidate_dirs = list(candidate_dirs)
    if not candidate_dirs:
        raise RuntimeError("No candidate dirs to compile")

    return base_src_dir, candidate_dirs


@cli.command('sass')
@click.option('--env', default='prod', type=click.Choice(['dev', 'prod']), help="Compile for a given target environment")
@click.option('--watch', is_flag=True, help="Watch for changes")
def sass(env, watch):
    static_sass_dir, candidate_dirs = get_dirs('sass', 'css')

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


@cli.command('js')
@click.option('--env', default='prod', type=click.Choice(['dev', 'prod']), help="Compile for a given target environment")
@click.option('--watch', is_flag=True, help="Watch for changes")
def js(env, watch):
    command = 'js:{}:{}'.format('watch' if watch else 'build', env)
    src_dirs = [d[0] for d in get_dirs('js', join=False)[1]]

    def _resolve_package_json_dir(path):
        while os.path.isdir(path):
            package_json = os.path.join(path, 'package.json')
            if os.path.isfile(package_json):
                path = os.path.normpath(os.path.abspath(path))
                return path
            path = os.path.join(path, '..')

    def _filter_package_json_cmd(path):
        if path:
            try:
                with open(os.path.join(path, 'package.json'), 'r') as fp:
                    data = json.load(fp)
                    script = data.get('scripts', {}).get(command)
                    if script:
                        return True
            except:
                pass
        return False

    valid_dirs = list(filter(_filter_package_json_cmd, map(_resolve_package_json_dir, src_dirs)))
    procs = []
    stop_event = threading.Event()

    def _sig_handler(signo, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, _sig_handler)

    for d in valid_dirs:
        procs.append(subprocess.Popen(
            ['npm', 'run', command],
            cwd=d,
        ))

    while not stop_event.is_set():
        any_alive = False
        for p in procs:
            if p.poll() is None:
                any_alive = True
                break
        if any_alive:
            time.sleep(0.1)
        else:
            stop_event.set()

    def stop_procs(sig):
        for p in procs:
            if p.poll() is None:
                p.send_signal(sig)
        if signal != signal.SIGKILL:
            for p in procs:
                if p.poll() is None:
                    p.wait(1)
        return not any((p.poll() is None for p in procs))

    if not stop_procs(signal.SIGINT):
        if not stop_procs(signal.SIGTERM):
            stop_procs(signal.SIGKILL)
