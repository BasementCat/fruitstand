from typing import Any, Optional, Union, Dict
import pickle

from flask import request
import arrow
import sqlalchemy_utils as sau

from app import db
from app.constants import DISPLAY_SPEC, COLOR_SPEC


class Base(db.Model):
    __abstract__ = True


class Screen(Base):
    __tablename__ = 'screen'
    id = db.Column(db.BigInteger(), primary_key=True)
    key = db.Column(db.Unicode(64), nullable=False, unique=True)
    present = db.Column(db.Boolean(), nullable=False, default=True)
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
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
                screen_obj = cls(key=screen_class.key)
                db.session.add(screen_obj)
                existing[screen_class.key] = screen_obj
            screen_obj.present = True
            screen_obj.title = screen_class.title
            screen_obj.description = screen_class.description
        db.session.commit()


class Playlist(Base):
    __tablename__ = 'playlist'
    id = db.Column(db.BigInteger(), primary_key=True)
    name = db.Column(db.UnicodeText(), nullable=False)
    description = db.Column(db.UnicodeText())
    default_refresh_interval = db.Column(db.Integer(), nullable=False, default=1800)


class PlaylistScreen(Base):
    __tablename__ = 'playlist_screen'
    id = db.Column(db.BigInteger(), primary_key=True)
    order = db.Column(db.Integer(), nullable=False, default=0)
    refresh_interval = db.Column(db.Integer())
    playlist_id = db.Column(db.BigInteger(), db.ForeignKey(Playlist.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_pls_playlist'), nullable=False)
    playlist = db.relationship(Playlist, backref=db.backref('playlist_screens', cascade='all,delete', order_by=order.asc()))
    screen_id = db.Column(db.BigInteger(), db.ForeignKey(Screen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_pls_screen'), nullable=False)
    screen = db.relationship(Screen, backref=db.backref('playlist_screens', cascade='all,delete', order_by=order.asc()))


class Config(Base):
    __tablename__ = 'config'
    id = db.Column(db.BigInteger(), primary_key=True)
    screen_id = db.Column(db.BigInteger(), db.ForeignKey(Screen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_config_screen'))
    screen = db.relationship(Screen, backref=db.backref('config', cascade='all,delete'))
    playlist_screen_id = db.Column(db.BigInteger(), db.ForeignKey(PlaylistScreen.id, onupdate='CASCADE', ondelete='CASCADE', name='fk_config_playlist_screen'))
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


class Display(Base):
    __tablename__ = 'display'
    id = db.Column(db.BigInteger(), primary_key=True)
    key = db.Column(db.Unicode(64), nullable=False, unique=True)
    name = db.Column(db.UnicodeText(), nullable=False)
    created_at = db.Column(sau.ArrowType(), nullable=False, default=arrow.utcnow)
    last_seen_at = db.Column(sau.ArrowType(), nullable=False, default=arrow.utcnow)
    display_spec = db.Column(sau.ChoiceType(choices=[(k, v['name']) for k, v in DISPLAY_SPEC.items()]), nullable=False)
    color_spec = db.Column(sau.ChoiceType(choices=[(k, v['name']) for k, v in COLOR_SPEC.items()]), nullable=False)
    width = db.Column(db.Integer(), nullable=False, default=0)
    height = db.Column(db.Integer(), nullable=False, default=0)
    playlist_id = db.Column(db.BigInteger(), db.ForeignKey(Playlist.id, onupdate='CASCADE', ondelete='SET NULL', name='fk_display_playlist'))
    playlist = db.relationship(Playlist, backref='displays')
    last_playlist_screen_id = db.Column(db.BigInteger(), db.ForeignKey(PlaylistScreen.id, onupdate='CASCADE', ondelete='SET NULL', name='fk_display_last_pls_id'))
    last_playlist_screen = db.relationship(PlaylistScreen)

    @classmethod
    def sync(cls):
        key = request.args.get('k')
        if key:
            update_params = {
                'last_seen_at': arrow.utcnow(),
                'display_spec': request.args.get('ds'),
                'color_spec': request.args.get('cs'),
                'width': request.args.get('w'),
                'height': request.args.get('h'),
            }
            create_params = dict(update_params)
            create_params.update({
                'key': key,
                'name': key,
            })
            display = cls.query.filter(cls.key == key).first()
            if display:
                for k, v in update_params.items():
                    setattr(display, k, v)
            else:
                display = cls(**create_params)
                db.session.add(display)
            db.session.commit()
            return display