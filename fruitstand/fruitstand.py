import os
import logging

import bottle
from bottle import Bottle, static_file, view, run, debug

from bottleutils.apps import setup

# TODO: import apps as individual apps

app = Bottle()

apps = [
    # [app module, app mountpoint],
]

plugins = [
]

setup(app, apps, plugins)

# TODO: needs to handle screen assets
# @app.route('/assets/<filen:path>')
# def static_files(filen):
#     return static_file(filen, root = os.path.join(os.path.dirname(__file__), "assets"))

# @app.route('')
# @app.route('/')
# @view('index.html')
# def index():
#     # Since we don't actually have a real use for the home page, redirect to events
#     return bottle.redirect('/event/')
#     # Someday we'll maybe have real content here
#     return {}

if __name__ == "__main__":
    debug(True)
    run(host = '0.0.0.0', app = app, reloader = True)