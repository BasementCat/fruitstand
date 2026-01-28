from typing import Any, Optional, Union, Dict, Tuple, Self, Literal
import pickle
import hashlib
import base64
import json
import os
import hmac
import random

from flask import request, current_app
import arrow
from sqlalchemy import event
import sqlalchemy_utils as sau
import slugify

from app import db
from app.constants import DISPLAY_SPEC, COLOR_SPEC, DISP_STATUS, SECRET_STATUS
from app.lib.user import login_user


class Base(db.Model):
    __abstract__ = True


class UserPassword:
    """\
    Represents a user password hash and supports verification.  This could
    relatively easily be extended to support multiple hashing algorithms and
    configurations
    """

    def __init__(
        self,
        sl: int=16,  # Salt length
        s: Optional[bytes]=None,  # Salt, generated if not specified
        n: int=2**14,  # Memory cost, 16MB
        r: int=8,  # block size, 1024 bytes
        p: int=5,  # parallelism
        raw: Optional[bytes]=None,  # Raw hashed value
    ):
        # Currently, the only supported algorithm is scrypt and the parameters are not configurable
        # This should be good for most use cases
        # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#scrypt
        self.sl = sl
        self.s = s or os.urandom(self.sl)
        self.n = n
        self.r = r
        self.p = p
        self.raw = raw

    @property
    def as_string(self) -> str:
        """\
        Return a storable representation of this hash with the parameters
        """

        return json.dumps({
            'sl': self.sl,
            's': base64.b64encode(self.s).decode('ascii'),
            'n': self.n,
            'r': self.r,
            'p': self.p,
            'raw': base64.b64encode(self.raw).decode('ascii'),
        })

    @classmethod
    def from_string(cls, value: str) -> Self:
        """\
        Given the stored string representation, return an instance with those
        same parameters set
        """

        props = json.loads(value)
        for k in ('s', 'raw'):
            props[k] = base64.b64decode(props[k].encode('ascii'))
        return cls(**props)

    def hash(self, value: Union[str, bytes]) -> bytes:
        """\
        Hash the given password string using the stored parameters
        """

        if isinstance(value, str):
            value = value.encode('utf-8')

        return hashlib.scrypt(
            value,
            salt=self.s,
            n=self.n,
            r=self.r,
            p=self.p,
        )

    def set_hash(self, value: Union[str, bytes]):
        """\
        Hash the given password string and store it
        """

        self.raw = self.hash(value)

    def compare_hash(self, value: Union[str, bytes]) -> bool:
        """\
        Hash the given password string and compare it to the stored one
        """

        given_hash = self.hash(value)
        return hmac.compare_digest(given_hash, self.raw)

    def __str__(self) -> str:
        """\
        Used in cases where this object would be displayed by accident
        """

        return '********'

    def __eq__(self, other: Union[Self, str, bytes]) -> bool:
        """\
        Determine if this hash is equal to another value
        """

        if isinstance(other, self.__class__):
            return self.compare_hash(other.raw)
        return self.compare_hash(other)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    username = db.Column(db.UnicodeText(), nullable=False)
    username_slug = db.Column(db.Unicode(128), nullable=False, unique=True)
    email = db.Column(db.Unicode(256), nullable=False)
    raw_password = db.Column(db.Text(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False, default=False, server_default='0')
    is_enabled = db.Column(db.Boolean(), nullable=False, default=True, server_default='1')
    timezone = db.Column(db.Text(), nullable=False, default='UTC', server_default='UTC')

    @property
    def password(self) -> UserPassword:
        return UserPassword.from_string(self.raw_password)

    @password.setter
    def password(self, value: str):
        pw = UserPassword()
        pw.set_hash(value)
        self.raw_password = pw.as_string

    @classmethod
    def get_by_username(cls, username: str, return_query: bool=False):
        slug = slugify.slugify(username)
        query = cls.query.filter(cls.username_slug == slug)
        if return_query:
            return query
        return query.first()

    @classmethod
    def login(cls, username: str, password: str, **kwargs) -> Union[Self, Literal[False]]:
        user = cls.get_by_username(username)
        if user and user.password == password:
            if login_user(user, **kwargs):
                return user
        return False

    # properties required for flask-login
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.is_enabled

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


@event.listens_for(User.username, 'set')
@event.listens_for(User.username, 'modified')
def update_user_slug(target, value, oldvalue, initiator):
    target.username_slug = slugify.slugify(value)


class Screen(Base):
    __tablename__ = 'screen'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    key = db.Column(db.Unicode(64), nullable=False, unique=True)
    present = db.Column(db.Boolean(), nullable=False, default=True)
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    system = db.Column(db.Boolean(), nullable=False, default=False)
    title = db.Column(db.UnicodeText(), nullable=False)
    description = db.Column(db.UnicodeText())

    @classmethod
    def all_by_key(cls):
        return {s.key: s for s in cls.query.order_by(cls.title.asc())}

    @classmethod
    def sync(cls, screen_classes):
        existing = cls.all_by_key()
        for screen_obj in existing.values():
            screen_obj.present = False

        for screen_class in screen_classes:
            screen_obj = existing.get(screen_class.key)
            if not screen_obj:
                screen_obj = cls(key=screen_class.key, enabled=screen_class._is_system)
                db.session.add(screen_obj)
                existing[screen_class.key] = screen_obj
            screen_obj.present = True
            screen_obj.system = screen_class._is_system
            screen_obj.title = screen_class.title
            screen_obj.description = screen_class.description
        db.session.commit()


class Playlist(Base):
    __tablename__ = 'playlist'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    name = db.Column(db.UnicodeText(), nullable=False)
    description = db.Column(db.UnicodeText())
    default_refresh_interval = db.Column(db.Integer(), nullable=False, default=1800)


class PlaylistScreen(Base):
    __tablename__ = 'playlist_screen'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    order = db.Column(db.Integer(), nullable=False, default=0)
    refresh_interval = db.Column(db.Integer())
    playlist_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(Playlist.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_pls_playlist'), nullable=False)
    playlist = db.relationship(Playlist, backref=db.backref('playlist_screens', cascade='all,delete', order_by=order.asc()))
    screen_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(Screen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_pls_screen'), nullable=False)
    screen = db.relationship(Screen, backref=db.backref('playlist_screens', cascade='all,delete', order_by=order.asc()))


class Config(Base):
    __tablename__ = 'config'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    screen_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(Screen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_config_screen'))
    screen = db.relationship(Screen, backref=db.backref('config', cascade='all,delete'))
    playlist_screen_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(PlaylistScreen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_config_playlist_screen'))
    playlist_screen = db.relationship(PlaylistScreen, backref=db.backref('config', cascade='all,delete'))
    key = db.Column(db.Unicode(64), nullable=False)
    value_serialized = db.Column(db.Text(), nullable=False)

    @property
    def value(self) -> Any:
        try:
            return pickle.loads(self.value_serialized.encode('ascii'))
        except:
            return None

    @value.setter
    def value(self, value: Any):
        self.value_serialized = pickle.dumps(value, protocol=0)

    @classmethod
    def for_screen_or_pls(cls, screen: Optional[Union[Screen, int]] = None, playlist_screen: Optional[Union[PlaylistScreen, int]] = None) -> Dict[str, Any]:
        screen = None if screen is None else (screen.id if isinstance(screen, Screen) else screen)
        playlist_screen = None if playlist_screen is None else (playlist_screen.id if isinstance(playlist_screen, PlaylistScreen) else playlist_screen)
        query = cls.query.filter(cls.screen_id == screen, cls.playlist_screen_id == playlist_screen)
        return (
            screen,
            playlist_screen,
            query,
        )

    @classmethod
    def load(cls, screen: Optional[Union[Screen, int]] = None, playlist_screen: Optional[Union[PlaylistScreen, int]] = None) -> Dict[str, Any]:
        _, _, query = cls.for_screen_or_pls(screen=screen, playlist_screen=playlist_screen)
        return {
            c.key: c.value
            for c in query
        }

    @classmethod
    def save(cls, config: Dict[str, Any], screen: Optional[Union[Screen, int]] = None, playlist_screen: Optional[Union[PlaylistScreen, int]] = None):
        screen, playlist_screen, query = cls.for_screen_or_pls(screen=screen, playlist_screen=playlist_screen)
        configs = {
            c.key: c
            for c in query
        }
        for k, v in config.items():
            if k not in configs:
                c = cls(screen_id=screen, playlist_screen_id=playlist_screen, key=k, value='')
                db.session.add(c)
                configs[k] = c
            configs[k].value = v
        db.session.commit()


class DisplaySecret(Base):
    __tablename__ = 'display_secret'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    name = db.Column(db.UnicodeText(), nullable=False)
    key = db.Column(db.String(128), nullable=False, unique=True)
    status = db.Column(sau.ChoiceType(choices=[(k, v) for k, v in SECRET_STATUS.items()]), nullable=False, default='active', server_default='active')

    # for forms to work
    @property
    def form_status(self):
        return self.status.code

    @form_status.setter
    def form_status(self, value):
        self.status = value


class DisplayProxy:
    """\
    Proxy class for displays in the case that a display can't actually be
    loaded.  This class allows for capturing the required parameters for
    rendering, in order to display errors.
    """

    @classmethod
    def generate_approval_code(cls):
        if current_app.config['ENABLE_DISPLAY_APPROVAL']:
            return str(random.randint(100000, 999999))

    def __init__(self, display_id: Optional[int]=None):
        if display_id is not None:
            display = Display.query.get(display_id) if display_id else None
            if display:
                self._update_from_display(display)
                return

        key = request.args.get('k')
        sk = request.args.get('sk')
        secret = None
        if sk:
            # always update; we don't care about whether it exists or status
            secret = DisplaySecret.query.filter(DisplaySecret.key == sk).first()
        self.id = None
        self.key = key
        self.status = 'pending' if current_app.config['ENABLE_DISPLAY_APPROVAL'] else 'active'
        self.approval_code = self.generate_approval_code()
        self.name = key
        self.created_at = arrow.utcnow()
        self.last_seen_at = arrow.utcnow()
        self.display_spec = request.args.get('ds') or 'static'
        self.color_spec = request.args.get('cs') or '1b'
        self.image_format = request.args.get('i') or 'BMP'
        self.image_bit_depth = request.args.get('ib')
        self.width = request.args.get('w') or 480
        self.height = request.args.get('h') or 320
        self.playlist = None
        self.last_playlist_screen = None
        self.display_secret = secret

    def _update_display(self, display):
        """Update the given display with parameters from this instance"""
        if display:
            for k, v in self.update_params.items():
                setattr(display, k, v)
        else:
            display = Display(**self.create_params)
            db.session.add(display)
        db.session.commit()
        return display

    def _update_from_display(self, display):
        """Update this instance with properties from the given display"""
        self._display = display
        self.id = display.id
        self.key = display.key
        self.status = display.status
        self.approval_code = display.approval_code
        self.name = display.name
        self.created_at = display.created_at
        self.last_seen_at = display.last_seen_at
        self.display_spec = display.display_spec
        self.color_spec = display.color_spec
        self.image_format = display.image_format
        self.image_bit_depth = display.image_bit_depth
        self.width = display.width
        self.height = display.height
        self.playlist = display.playlist
        self.last_playlist_screen = display.last_playlist_screen
        self.display_secret = display.display_secret

    @property
    def update_params(self):
        return {
            'last_seen_at': self.last_seen_at,
            'display_spec': self.display_spec,
            'color_spec': self.color_spec,
            'width': self.width,
            'height': self.height,
            'display_secret': self.display_secret,
        }

    @property
    def create_params(self):
        out = dict(self.update_params)
        out.update({
            'key': self.key,
            'name': self.key,
            'status': self.status,
            'approval_code': self.approval_code,
            # Set image details on create only; this allows for editing later
            'image_format': self.image_format,
            'image_bit_depth': self.image_bit_depth,
        })
        return out

    @property
    def display(self):
        if not hasattr(self, '_display'):
            self._display = None
            if self.key:
                self._display = self._update_display(Display.query.filter(Display.key == self.key).first())
                self._update_from_display(self._display)
        return self._display


class Display(Base):
    __tablename__ = 'display'
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    key = db.Column(db.Unicode(64), nullable=False, unique=True)
    status = db.Column(sau.ChoiceType(choices=[(k, v) for k, v in DISP_STATUS.items()]), nullable=False, default='active', server_default='active')
    approval_code = db.Column(db.Unicode(36))
    name = db.Column(db.UnicodeText(), nullable=False)
    created_at = db.Column(sau.ArrowType(), nullable=False, default=arrow.utcnow)
    last_seen_at = db.Column(sau.ArrowType(), nullable=False, default=arrow.utcnow)
    display_spec = db.Column(sau.ChoiceType(choices=[(k, v['name']) for k, v in DISPLAY_SPEC.items()]), nullable=False)
    color_spec = db.Column(sau.ChoiceType(choices=[(k, v['name']) for k, v in COLOR_SPEC.items()]), nullable=False)
    image_format = db.Column(sau.ChoiceType(choices=[('BMP', 'BMP'), ('JPEG', 'JPEG'), ('PNG', 'PNG')]), nullable=False, default='BMP', server_default='BMP')
    image_bit_depth = db.Column(db.Integer())
    width = db.Column(db.Integer(), nullable=False, default=0)
    height = db.Column(db.Integer(), nullable=False, default=0)
    playlist_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(Playlist.id, onupdate='CASCADE', ondelete='SET NULL', name='fk_display_playlist'))
    playlist = db.relationship(Playlist, backref='displays')
    last_playlist_screen_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(PlaylistScreen.id, onupdate='CASCADE', ondelete='SET NULL', name='fk_display_last_pls_id'))
    last_playlist_screen = db.relationship(PlaylistScreen)
    display_secret_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey(DisplaySecret.id, onupdate='CASCADE', ondelete='SET NULL', name='fk_display_display_secret_id'))
    display_secret = db.relationship(DisplaySecret, backref='displays')

    # for forms to work
    @property
    def form_status(self):
        return self.status.code

    @form_status.setter
    def form_status(self, value):
        self.status = value

    @classmethod
    def sync(cls, display_id: Optional[int]=None):
        proxy = DisplayProxy(display_id=display_id)
        # force sync in case of no display_id
        _ = proxy.display
        return proxy

    def get_playlist_screen(self, playlist_id: Optional[int]=None, playlist_screen_id: Optional[int]=None) -> Tuple[Optional[Playlist], Optional[PlaylistScreen]]:
        if playlist_id:
            playlist = Playlist.query.get(playlist_id)
        else:
            playlist = self.playlist

        if not playlist:
            return None, None

        pls_by_id = {pls.id: pls for pls in playlist.playlist_screens}
        if not playlist_screen_id and pls_by_id:
            pls_ids = list(pls_by_id.keys())
            if self.last_playlist_screen_id:
                # TODO: time-based
                try:
                    idx = pls_ids.index(self.last_playlist_screen_id)
                    playlist_screen_id = self.last_playlist_screen_id = pls_ids[(idx + 1) % len(pls_ids)]
                except (ValueError, IndexError):
                    playlist_screen_id = self.last_playlist_screen_id = pls_ids[0]
            else:
                playlist_screen_id = self.last_playlist_screen_id = pls_ids[0]
            db.session.commit()

        playlist_screen = pls_by_id.get(playlist_screen_id)

        return playlist, playlist_screen

    def get_context(self):
        return {
            'display_spec': self.display_spec,
            'color_spec': self.color_spec,
            'width': self.width,
            'height': self.height,
        }


class Cache(Base):
    __tablename__ = 'cache'
    key = db.Column(db.String(128), primary_key=True)
    expires = db.Column(sau.ArrowType(), nullable=False)
    data = db.Column(db.LargeBinary(), nullable=False)
