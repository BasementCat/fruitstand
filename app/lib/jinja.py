from flask import current_app
from markupsafe import Markup
import arrow

from app.constants import DISPLAY_SPEC, COLOR_SPEC
from app.lib.user import users_enabled


jinja_env = {
    'filters': {},
    'globals': {},
}

def _j_apply(dest):
    def _j_apply_dec(name=None):
        def _j_apply_impl(cb):
            jinja_env[dest][name or cb.__name__] = cb
            return cb
        return _j_apply_impl
    return _j_apply_dec

jfilter = _j_apply('filters')
jglobal = _j_apply('globals')

def apply_jinja_to_env(env):
    env.filters.update(jinja_env['filters'])
    env.globals.update(jinja_env['globals'])

def apply_jinja_env(app):
    apply_jinja_to_env(app.jinja_env)


@jfilter('bool')
def bool_flt(value):
    return bool(value)


@jfilter()
def label(value, level='default'):
    return Markup(f'<span class="label label-{level}">{value}</span>')


@jfilter()
def typed_label(value, false_is_danger=True):
    if value is None:
        return label('None')
    elif value is True:
        return label('Yes', level='success')
    elif value is False:
        return label('No', level='danger' if false_is_danger else 'default')
    return value


@jfilter()
def status_label(value):
    lcls = 'default'
    if value in ('pending', 'deprecated'):
        lcls = 'warning'
    elif value == 'active':
        lcls = 'success'
    elif value in ('disapproved', 'disabled'):
        lcls = 'danger'
    return label(value, level=lcls)


@jfilter()
def plural(value, singular, plural=None):
    if value in (1, -1):
        suffix = singular
    else:
        suffix = plural or (singular + 's')
    return f'{value} {suffix}'


@jfilter()
def dt(value, format='MMM Do, YYYY h:mm a', timezone=None, no_markup=False):
    if value is not None:
        # TODO: user tz
        timezone = timezone or current_app.config['TIMEZONE']
        value = arrow.get(value)
        value_utc = value.to('UTC')
        value_utc_s = value_utc.format(format)
        value_tz = value.to(timezone)
        value_tz_s = value_tz.format(format)
        if no_markup:
            return value_tz_s
        return Markup(f'<abbr title="{timezone} - {value_utc_s} UTC">{value_tz_s}</abbr>')
    return value


@jfilter()
def display_spec(value):
    ds = DISPLAY_SPEC.get(value)
    if not ds:
        return label(f'Unknown ({value})', level='danger')
    elif ds['key'] == 'static':
        return label(ds['name'], level='primary')
    elif ds['key'] == 'dynamic':
        return label(ds['name'], level='info')
    elif ds['key'] == 'browser':
        return label(ds['name'], level='success')
    else:
        return label(ds['name'], level='default')


@jfilter()
def color_spec(value):
    cs = COLOR_SPEC.get(value)
    if not cs:
        return label(f'Unknown ({value})', level='danger')
    elif cs['key'] == '1b':
        return label(cs['name'], level='default')
    elif cs['key'] == '3b':
        return label(cs['name'], level='primary')
    elif cs['key'] == '3b7':
        return label(cs['name'], level='warning')
    elif cs['key'] == '16b':
        return label(cs['name'], level='info')
    elif cs['key'] == 'full':
        return label(cs['name'], level='success')
    else:
        return label(cs['name'], level='default')


@jfilter()
def fixed(value, d=2):
    if value is not None:
        if d:
            value = f'{{:0.{d}f}}'.format(value)
        else:
            value = str(int(value))
    return value


@jfilter()
def percent(value, d=0):
    if value is not None:
        value *= 100
        value = fixed(value, d=d)
        value += '%'
    return value


@jglobal()
def if_plural(value, plural, singular):
    if value in (1, -1):
        return singular
    return plural


@jglobal()
def now():
    return arrow.utcnow()


jglobal()(users_enabled)
