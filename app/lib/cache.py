from typing import Optional, Any, Self, Callable
import os
import tempfile
import hashlib
import pickle

from flask import Flask
import arrow


class CacheDriver:
    driver_name: str = None

    @classmethod
    def _get_driver(cls, driver_name: str) -> Optional[Self]:
        drivers = {d.driver_name: d for d in cls.__subclasses__()}
        return drivers.get(driver_name)

    def __init__(self, app: Flask):
        pass

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError()

    def set(self, key: str, expiry: int, data: Any) -> bool:
        raise NotImplementedError()

    def delete(self, key: str) -> bool:
        raise NotImplementedError()


class Cache:
    def __init__(self, app: Optional[Flask]=None):
        self.driver: Optional[CacheDriver] = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.driver = CacheDriver._get_driver(app.config.get('CACHE_DRIVER'))

    def get_or_fetch(self, key: str, expiry: int, callback: Callable[..., Optional[Any]], *args, **kwargs) -> Optional[Any]:
        res = self.get(key)
        if res is None:
            res = callback(*args, **kwargs)
            if res is not None:
                self.set(key, expiry, res)
        return res

    def get(self, key: str) -> Optional[Any]:
        if self.driver is not None:
            return self.driver.get(key)
        return None

    def set(self, key: str, expiry: int, data: Any) -> bool:
        if self.driver is not None:
            return self.driver.set(key, expiry, data)
        return True

    def delete(self, key: str) -> bool:
        if self.driver is not None:
            return self.driver.delete(key)
        return True


class FilesystemDriver(CacheDriver):
    driver_name: str = 'filesystem'

    def __init__(self, app: Flask):
        if app.config.get('FILESYSTEM_CACHE_DIR'):
            self.cache_dir = app.config['FILESYSTEM_CACHE_DIR']
        else:
            self.cache_dir = os.path.join(tempfile.gettempdir(), app.config.get('FILESYSTEM_CACHE_SUBDIR', 'fruitstand'))
            os.makedirs(self.cache_dir, exist_ok=True)

        if not os.path.is_dir(self.cache_dir):
            raise RuntimeError("Filesystem cache dir does not exist or is not a directory: " + self.cache_dir)

    def _get_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, hashlib.new('sha256', key).hexdigest())

    def _load_key(self, key: str) -> Optional[Any]:
        filename = self._get_path(key)
        if os.is_file(filename):
            try:
                with open(filename, 'rb') as fp:
                    res = pickle.load(fp)
                if res and arrow.get(res['expires']) > arrow.utcnow():
                    return res
            except:
                pass

            os.unlink(filename)

    def get(self, key: str) -> Optional[Any]:
        res = self._load_key(key)
        if res:
            return res['data']

    def set(self, key: str, expiry: int, data: Any) -> bool:
        filename = self._get_path(key)
        with open(filename, 'wb') as fp:
            obj = {'expires': str(arrow.utcnow().shift(seconds=expiry)), 'data': data}
            pickle.dump(obj, fp)
            return True
        return False

    def delete(self, key: str) -> bool:
        filename = self._get_path(key)
        if os.is_file(filename):
            os.unlink(filename)
            return True
        return False


class DatabaseDriver(CacheDriver):
    driver_name: str = 'database'

    def __init__(self, app: Flask):
        from app import db
        from app.models import Cache as CacheModel
        self.db = db
        self.CacheModel = CacheModel

    def get(self, key: str) -> Optional[Any]:
        obj = self.CacheModel.query.get(key)
        if obj:
            if obj.expires > arrow.utcnow():
                try:
                    return pickle.loads(obj.data)
                except:
                    pass
            self.db.session.delete(obj)
            self.db.session.commit()

    def set(self, key: str, expiry: int, data: Any) -> bool:
        obj = self.CacheModel.query.get(key)
        if not obj:
            obj = self.CacheModel(key=key)
            self.db.session.add(obj)
        obj.expires = arrow.utcnow().shift(seconds=expiry)
        obj.data = pickle.dumps(data)
        self.db.session.commit()
        return True

    def delete(self, key: str) -> bool:
        obj = self.CacheModel.query.get(key)
        if obj:
            self.db.session.delete(obj)
            self.db.session.commit()
            return True
        return False
