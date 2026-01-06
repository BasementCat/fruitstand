from functools import wraps

import flask_login
from flask import current_app, abort


def users_enabled_required(callback):
    """\
    Decorator to require user management to be enabled for a view.  If not, the
    request is aborted with a 404 error as though the view was not defined.
    """

    @wraps(callback)
    def users_enabled_required_wrap(*args, **kwargs):
        if not current_app.config['ENABLE_USERS']:
            abort(404)

        return callback(*args, **kwargs)

    return users_enabled_required_wrap


def login_fresh(*args, **kwargs):
    """\
    Wrapper around flask_login `login_fresh` accounting for user enablement
    """

    if current_app.config['ENABLE_USERS']:
        return flask_login.login_fresh(*args, **kwargs)

    return True


def login_remembered(*args, **kwargs):
    """\
    Wrapper around flask_login `login_remembered` accounting for user enablement
    """

    if current_app.config['ENABLE_USERS']:
        return flask_login.login_remembered(*args, **kwargs)

    return False


def login_user(*args, **kwargs):
    """\
    Wrapper around flask_login `login_user` accounting for user enablement
    """

    if current_app.config['ENABLE_USERS']:
        return flask_login.login_user(*args, **kwargs)

    return False


def logout_user(*args, **kwargs):
    """\
    Wrapper around flask_login `logout_user` accounting for user enablement
    """

    if current_app.config['ENABLE_USERS']:
        return flask_login.logout_user(*args, **kwargs)

    return True


def confirm_login(*args, **kwargs):
    """\
    Wrapper around flask_login `confirm_login` accounting for user enablement
    """

    if current_app.config['ENABLE_USERS']:
        return flask_login.confirm_login(*args, **kwargs)


def login_required(callback):
    """\
    Implementation of flask_login's `login_required` decorator - performs the
    same checks, but if users are not enabled, allows the request to continue
    """

    @wraps(callback)
    def login_required_wrap(*args, **kwargs):
        if current_app.config['ENABLE_USERS']:
            if not flask_login.current_user.is_authenticated:
                return current_app.login_manager.unauthorized()

        return callback(*args, **kwargs)

    return login_required_wrap


def admin_required(callback):
    """\
    Much like login_required, but additionally checks to ensure that the logged
    in user is also an admin
    """

    @wraps(callback)
    def admin_required_wrap(*args, **kwargs):
        if current_app.config['ENABLE_USERS']:
            if not flask_login.current_user.is_admin:
                # TODO: should this be configurable?
                if not kwargs.get('user_id') or str(kwargs['user_id']) != flask_login.current_user.get_id():
                    abort(403, "You do not have permission to access this page.")

        return callback(*args, **kwargs)

    # Wrap this check in login_required as a login is still required when enabled
    return login_required(admin_required_wrap)
