from unittest import TestCase
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
import time
import threading

from app.lib.cache import (
    make_key_with_args,
    Cache,
    FilesystemDriver,
    DatabaseDriver,
)
from app import create_app, db


@patch('app.lib.cache.hashlib')
class TestMakeKeyWithArgs(TestCase):
    def test_no_args(self, mock_hl):
        mock_hl.new.return_value.hexdigest.return_value = 'testhash'
        res = make_key_with_args('foo')
        self.assertEqual(res, 'foo-testhash')
        mock_hl.new.assert_called_once_with('sha256', b'{}')

    def test_only_args(self, mock_hl):
        mock_hl.new.return_value.hexdigest.return_value = 'testhash'
        res = make_key_with_args('foo', 'bar', 3, 'baz')
        self.assertEqual(res, 'foo-testhash')
        mock_hl.new.assert_called_once_with('sha256', b'bar3baz{}')

    def test_only_callback(self, mock_hl):
        mock_hl.new.return_value.hexdigest.return_value = 'testhash'
        res = make_key_with_args('foo', callback='asdf')
        self.assertEqual(res, 'foo-asdf-testhash')
        mock_hl.new.assert_called_once_with('sha256', b'{}')

    def test_only_kwargs(self, mock_hl):
        mock_hl.new.return_value.hexdigest.return_value = 'testhash'
        res = make_key_with_args('foo', b='bar', a='baz', c=3)
        self.assertEqual(res, 'foo-testhash')
        mock_hl.new.assert_called_once_with('sha256', b"{'a': 'baz', 'b': 'bar', 'c': '3'}")

    def test_all_args(self, mock_hl):
        mock_hl.new.return_value.hexdigest.return_value = 'testhash'
        res = make_key_with_args('foo', 'bar', 'baz', callback='asdf', b='bar', a='baz')
        self.assertEqual(res, 'foo-asdf-testhash')
        mock_hl.new.assert_called_once_with('sha256', b"barbaz{'a': 'baz', 'b': 'bar'}")


@patch('app.lib.cache.Cache.init_app')
class TestCache__Init(TestCase):
    def test_no_app(self, mock_init_app):
        c = Cache()
        self.assertIsNone(c.driver)
        mock_init_app.assert_not_called()

    def test_with_app(self, mock_init_app):
        mockapp = MagicMock()
        c = Cache(app=mockapp)
        self.assertIsNone(c.driver)
        mock_init_app.assert_called_once_with(mockapp)


@patch('app.lib.cache.CacheDriver._get_driver')
class TestCache__InitApp(TestCase):
    def test_no_configured_driver(self, mock_get_driver):
        mockapp = MagicMock(config={})
        c = Cache()
        c.init_app(mockapp)
        self.assertEqual(c.driver, mock_get_driver.return_value.return_value)
        mock_get_driver.assert_called_once_with(None)
        mock_get_driver.return_value.assert_called_once_with(mockapp)

    def test_with_configured_driver(self, mock_get_driver):
        mockapp = MagicMock(config={'CACHE_DRIVER': 'foo'})
        c = Cache()
        c.init_app(mockapp)
        self.assertEqual(c.driver, mock_get_driver.return_value.return_value)
        mock_get_driver.assert_called_once_with('foo')
        mock_get_driver.return_value.assert_called_once_with(mockapp)


@patch('app.lib.cache.make_key_with_args', return_value='testkey')
@patch('app.lib.cache.Cache.get', return_value=None)
@patch('app.lib.cache.Cache.set')
class TestCache__GetOrFetch(TestCase):
    def test_key_in_cache(self, mock_set, mock_get, mock_mk_key):
        mock_get.return_value = 'testval'
        mock_callback = MagicMock()
        mock_callback.__name__ = 'testcbname'
        mock_callback.return_value = None
        c = Cache()
        res = c.get_or_fetch('foo', 3, mock_callback, 'bar', baz='quux')
        self.assertEqual(res, 'testval')
        mock_mk_key.assert_called_once_with('foo', 'bar', callback='testcbname', baz='quux')
        mock_get.assert_called_once_with('testkey')
        mock_callback.assert_not_called()
        mock_set.assert_not_called()

    def test_key_not_in_cache__nothing_fetched(self, mock_set, mock_get, mock_mk_key):
        mock_callback = MagicMock()
        mock_callback.__name__ = 'testcbname'
        mock_callback.return_value = None
        c = Cache()
        res = c.get_or_fetch('foo', 3, mock_callback, 'bar', baz='quux')
        self.assertIsNone(res)
        mock_mk_key.assert_called_once_with('foo', 'bar', callback='testcbname', baz='quux')
        mock_get.assert_called_once_with('testkey')
        mock_callback.assert_called_once_with('bar', baz='quux')
        mock_set.assert_not_called()

    def test_key_not_in_cache__value_fetched(self, mock_set, mock_get, mock_mk_key):
        mock_callback = MagicMock()
        mock_callback.__name__ = 'testcbname'
        mock_callback.return_value = 'testval'
        c = Cache()
        res = c.get_or_fetch('foo', 3, mock_callback, 'bar', baz='quux')
        self.assertEqual(res, 'testval')
        mock_mk_key.assert_called_once_with('foo', 'bar', callback='testcbname', baz='quux')
        mock_get.assert_called_once_with('testkey')
        mock_callback.assert_called_once_with('bar', baz='quux')
        mock_set.assert_called_once_with('testkey', 3, 'testval')



class TestCache__Get(TestCase):
    def test_no_driver(self):
        c = Cache()
        res = c.get('foo')
        self.assertIsNone(res)

    def test_with_driver(self):
        mock_driver = MagicMock()
        c = Cache()
        c.driver = mock_driver
        res = c.get('foo')
        self.assertEqual(res, mock_driver.get.return_value)
        mock_driver.get.assert_called_once_with('foo')


class TestCache__Set(TestCase):
    def test_no_driver(self):
        c = Cache()
        res = c.set('foo', 3, 'bar')
        self.assertTrue(res)

    def test_with_driver(self):
        mock_driver = MagicMock()
        c = Cache()
        c.driver = mock_driver
        res = c.set('foo', 3, 'bar')
        self.assertEqual(res, mock_driver.set.return_value)
        mock_driver.set.assert_called_once_with('foo', 3, 'bar')


class TestCache__Delete(TestCase):
    def test_no_driver(self):
        c = Cache()
        res = c.delete('foo')
        self.assertTrue(res)

    def test_with_driver(self):
        mock_driver = MagicMock()
        c = Cache()
        c.driver = mock_driver
        res = c.delete('foo')
        self.assertEqual(res, mock_driver.delete.return_value)
        mock_driver.delete.assert_called_once_with('foo')


class BaseCacheDriverTest:
    def setUp(self):
        self.base_tempdir = os.path.join(tempfile.gettempdir(), 'fruitstand-tests')
        self.cache_tempdir = os.path.join(self.base_tempdir, 'cache')
        self.db_tempdir = os.path.join(self.base_tempdir, 'database')
        os.makedirs(self.cache_tempdir, exist_ok=True)
        os.makedirs(self.db_tempdir, exist_ok=True)
        config = {
            'FILESYSTEM_CACHE_DIR': self.cache_tempdir,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///{}'.format(
                os.path.abspath(os.path.join(self.db_tempdir, 'test.sqlite3'))
            ),
        }
        self.app = create_app(config=config)
        self.driver = self.DriverClass(self.app)
        with self.app.app_context():
            db.create_all()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        del self.driver
        del self.app
        shutil.rmtree(self.base_tempdir)
        del self.cache_tempdir
        del self.db_tempdir
        del self.base_tempdir

    def test_get_set(self):
        with self.app.app_context():
            d = self.driver
            self.assertIsNone(d.get('testkey'))
            self.assertTrue(d.set('testkey', 1, 'testval'))
            self.assertEqual(d.get('testkey'), 'testval')
            d.delete('testkey')
            self.assertIsNone(d.get('testkey'))

    def test_expire(self):
        with self.app.app_context():
            d = self.driver
            d.set('testkey', 1, 'testval')
            self.assertEqual(d.get('testkey'), 'testval')
            time.sleep(1)
            self.assertIsNone(d.get('testkey'))

    def test_concurrent_wait(self):
        n_threads = 10
        r_threads = []
        errors = []
        err_lock = threading.Lock()
        def err(part, msg, *a, exc=None, **ka):
            msg = msg.format(*a, **ka)
            if exc:
                msg += f': {exc.__class__.__name__}:{exc}'
            msg = f'{threading.current_thread().name}:{part} - {msg}'
            with err_lock:
                errors.append(msg)

        def runner(bs, n):
            with self.app.app_context():
                d = self.DriverClass(self.app)
                r = list(range(n_threads))
                bs[0].wait()
                try:
                    res = d.get('testkey')
                    if res is not None:
                        err('get_1_nx', 'value should be none, is {}', res)
                except Exception as e:
                    err('get_1_nx', 'exception', exc=e)

                bs[1].wait()
                try:
                    res = d.set('testkey', 1, n)
                    if res is not True:
                        err('set_1', 'failed to set')
                except Exception as e:
                    err('set_1', 'exception', exc=e)

                bs[2].wait()
                try:
                    res = d.get('testkey')
                    if res not in r:
                        err('get_1', 'value {} not in {}', res, r)
                except Exception as e:
                    err('get_1', 'exception', exc=e)

                bs[3].wait()
                try:
                    d.delete('testkey')
                except Exception as e:
                    err('del_1', 'exception', exc=e)

                bs[4].wait()
                try:
                    res = d.get('testkey')
                    if res is not None:
                        err('get_2_nx', 'deleted key present, is {}', res)
                except Exception as e:
                    err('get_2_nx', 'exception', exc=e)

                bs[5].wait()
                try:
                    res = d.set('testkey', 1, n)
                    if res is not True:
                        err('set_2', 'failed to set')
                except Exception as e:
                    err('set_2', 'exception', exc=e)

                bs[6].wait()
                try:
                    res = d.get('testkey')
                    if res not in r:
                        err('get_2', 'value {} not in {}', res, r)
                except Exception as e:
                    err('get_2', 'exception', exc=e)

                time.sleep(1)
                bs[7].wait()
                try:
                    res = d.get('testkey')
                    if res is not None:
                        err('get_2_exp', 'expired key present, is {}', res)
                except Exception as e:
                    err('get_2_exp', 'exception', exc=e)

                with err_lock:
                    r_threads.append(1)

        bs = [threading.Barrier(n_threads) for _ in range(8)]
        threads = [threading.Thread(target=runner, args=(bs, i)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for e in errors:
            print(e)
        self.assertEqual(errors, [])
        self.assertEqual(len(r_threads), n_threads)

    def test_concurrent_nowait(self):
        n_threads = 10
        r_threads = []
        errors = []
        err_lock = threading.Lock()
        def err(part, msg, *a, exc=None, **ka):
            msg = msg.format(*a, **ka)
            if exc:
                msg += f': {exc.__class__.__name__}:{exc}'
            msg = f'{threading.current_thread().name}:{part} - {msg}'
            with err_lock:
                errors.append(msg)

        def runner(n):
            with self.app.app_context():
                d = self.DriverClass(self.app)
                r = list(range(n_threads))
                error_key = 'get_1_nx'
                try:
                    res = d.get('testkey')
                except Exception as e:
                    err('get_1_nx', 'exception', exc=e)

                try:
                    res = d.set('testkey', 1, n)
                    if res is not True:
                        err('set_1', 'failed to set')
                except Exception as e:
                    err('set_1', 'exception', exc=e)

                try:
                    res = d.get('testkey')
                    if res is not None:
                        if res not in r:
                            err('get_1', 'value {} not in {}', res, r)
                except Exception as e:
                    err('get_1', 'exception', exc=e)

                try:
                    d.delete('testkey')
                except Exception as e:
                    err('del_1', 'exception', exc=e)

                try:
                    res = d.get('testkey')
                except Exception as e:
                    err('get_2_nx', 'exception', exc=e)

                try:
                    res = d.set('testkey', 1, n)
                    if res is not True:
                        err('set_2', 'failed to set')
                except Exception as e:
                    err('set_2', 'exception', exc=e)

                try:
                    res = d.get('testkey')
                    if res is not None:
                        if res not in r:
                            err('get_2', 'value {} not in {}', res, r)
                except Exception as e:
                    err('get_2', 'exception', exc=e)

                time.sleep(1)
                try:
                    res = d.get('testkey')
                except Exception as e:
                    err('get_2_exp', 'exception', exc=e)

                with err_lock:
                    r_threads.append(1)

        threads = [threading.Thread(target=runner, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for e in errors:
            print(e)
        self.assertEqual(errors, [])
        self.assertEqual(len(r_threads), n_threads)


class TestFilesystemDriver(BaseCacheDriverTest, TestCase):
    DriverClass = FilesystemDriver


class TestDatabaseDriver(BaseCacheDriverTest, TestCase):
    DriverClass = DatabaseDriver
