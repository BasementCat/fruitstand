import os
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import pytest
from flask import request

from app.lib.screen import Screen, DisplayNotFound, PlaylistNotFound, ScreenNotFound
from tests.conftest import with_app


class MockScreen(Screen):
    key = 'mock-screen'
    blueprint = MagicMock()

class MockScreenSub1(MockScreen):
    key = 'mock-screen-subclass-1'
    blueprint = MagicMock()


# TODO: test init
# TODO: test render template


def test_get_path():
    path = MockScreen.get_path()
    assert path == os.path.dirname(__file__)


@patch(__name__ + '.MockScreenSub1.mount')
@patch(__name__ + '.MockScreen.mount')
@patch('app.lib.screen.Screen.mount')
def test_install_all_and_get(mock_base_mount, mock_s_mount, mock_ss1_mount):
    mock_app = MagicMock()
    Screen.install_all(mock_app)
    mock_base_mount.assert_not_called()
    mock_s_mount.assert_called_once_with(mock_app)
    mock_ss1_mount.assert_called_once_with(mock_app)
    assert 'mock-screen' in Screen.get_all()
    assert 'mock-screen-subclass-1' in Screen.get_all()
    assert Screen.get('mock-screen') is MockScreen
    assert Screen.get('invalid-screen') is None


# TODO: test mount


@patch('app.lib.screen.Display')
class TestLoadDisplay(TestCase):
    def test_with_display_id(self, mock_display_cls):
        mock_display = MagicMock()
        mock_display_cls.query.get.return_value = mock_display
        mock_display_cls.sync.return_value = None
        res = Screen._load_display(display_id=1)
        mock_display_cls.query.get.assert_called_once_with(1)
        mock_display_cls.sync.assert_not_called()
        self.assertEqual(res, mock_display)

    def test_with_display_id__invalid(self, mock_display_cls):
        mock_display_cls.query.get.return_value = None
        mock_display_cls.sync.return_value = None
        with self.assertRaises(DisplayNotFound):
            res = Screen._load_display(display_id=1)
        mock_display_cls.query.get.assert_called_once_with(1)
        mock_display_cls.sync.assert_not_called()

    def test_no_display_id(self, mock_display_cls):
        mock_display = MagicMock()
        mock_display_cls.query.get.return_value = None
        mock_display_cls.sync.return_value = mock_display
        res = Screen._load_display()
        mock_display_cls.query.get.assert_not_called()
        mock_display_cls.sync.assert_called_once_with()
        self.assertEqual(res, mock_display)

    def test_no_display_id__not_loaded(self, mock_display_cls):
        mock_display_cls.query.get.return_value = None
        mock_display_cls.sync.return_value = None
        with self.assertRaises(DisplayNotFound):
            res = Screen._load_display()
        mock_display_cls.query.get.assert_not_called()
        mock_display_cls.sync.assert_called_once_with()


class TestLoadPlaylistAndPlaylistScreen(TestCase):
    def test_with_ids(self):
        mock_display = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist_screen = MagicMock()
        mock_display.get_playlist_screen.return_value = (mock_playlist, mock_playlist_screen)
        res = Screen._load_playlist_and_playlist_screen(mock_display, playlist_id=1, playlist_screen_id=2)
        mock_display.get_playlist_screen.assert_called_once_with(playlist_id=1, playlist_screen_id=2)
        self.assertEqual(res, (mock_playlist, mock_playlist_screen))

    def test_without_ids(self):
        mock_display = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist_screen = MagicMock()
        mock_display.get_playlist_screen.return_value = (mock_playlist, mock_playlist_screen)
        res = Screen._load_playlist_and_playlist_screen(mock_display)
        mock_display.get_playlist_screen.assert_called_once_with(playlist_id=None, playlist_screen_id=None)
        self.assertEqual(res, (mock_playlist, mock_playlist_screen))

    def test_not_loaded(self):
        mock_display = MagicMock()
        mock_display.get_playlist_screen.return_value = (None, None)
        with self.assertRaises(PlaylistNotFound):
            res = Screen._load_playlist_and_playlist_screen(mock_display)
        mock_display.get_playlist_screen.assert_called_once_with(playlist_id=None, playlist_screen_id=None)


@patch('app.lib.screen.Screen.get')
class TestLoadScreenClass(TestCase):
    def test_loaded(self, mock_get_screen_cls):
        mock_screen_cls = MagicMock()
        mock_get_screen_cls.return_value = mock_screen_cls
        mock_pls = MagicMock()
        mock_pls.screen = MagicMock(key='foo')
        res = Screen._load_screen_class(MagicMock(), MagicMock(), mock_pls)
        mock_get_screen_cls.assert_called_once_with('foo')
        self.assertEqual(res, mock_screen_cls)

    def test_not_loaded(self, mock_get_screen_cls):
        mock_get_screen_cls.return_value = None
        mock_pls = MagicMock()
        mock_pls.screen = MagicMock(key='foo')
        with self.assertRaises(ScreenNotFound):
            res = Screen._load_screen_class(MagicMock(), MagicMock(), mock_pls)
        mock_get_screen_cls.assert_called_once_with('foo')


@patch('app.lib.screen.Config')
class TestLoadConfig(TestCase):
    def test_load(self, mock_config):
        conf1 = MagicMock()
        conf2 = MagicMock()
        mock_config.load.side_effect = [conf1, conf2]
        mock_pls = MagicMock()
        res = Screen._load_config(mock_pls)
        mock_config.load.assert_has_calls([
            call(screen=mock_pls.screen, playlist_screen=mock_pls),
            call(screen=mock_pls.screen),
        ])
        self.assertEqual(res, (conf1, conf2))


class TestLoadContext(TestCase):
    @with_app
    def test_load(self, app):
        with app.test_request_context():
            mock_display = MagicMock()
            res = Screen._load_context(mock_display)
            self.assertEqual(res, {'metrics': {}})

    @with_app
    def test_load__invalid_metrics_json(self, app):
        with app.test_request_context('/?metrics=asdlfkjsld'):
            mock_display = MagicMock()
            res = Screen._load_context(mock_display)
            self.assertEqual(res, {'metrics': {}})

    @with_app
    def test_load__valid_metrics_json(self, app):
        with app.test_request_context('/?metrics={"foo":"bar"}'):
            mock_display = MagicMock()
            res = Screen._load_context(mock_display)
            self.assertEqual(res, {'metrics': {'foo': 'bar'}})

    @with_app
    def test_load__with_display_context(self, app):
        with app.test_request_context():
            mock_display = MagicMock()
            mock_display.get_context.return_value = {'foo': 'bar'}
            res = Screen._load_context(mock_display)
            self.assertEqual(res, {'metrics': {}, 'foo': 'bar'})



@patch('app.lib.screen.Screen._load_display')
@patch('app.lib.screen.Screen._load_playlist_and_playlist_screen')
@patch('app.lib.screen.Screen._load_screen_class')
@patch('app.lib.screen.Screen._load_config')
@patch('app.lib.screen.Screen._load_context')
class TestLoadForRender(TestCase):
    def test_load(self, mock_lctx, mock_lconf, mock_lsc, mock_lpl, mock_ldisp):
        mock_display = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist_screen = MagicMock()
        mock_screen_cls = MagicMock()
        mock_pls_config = MagicMock()
        mock_scr_config = MagicMock()
        mock_ctx = MagicMock()

        mock_ldisp.return_value = mock_display
        mock_lpl.return_value = (mock_playlist, mock_playlist_screen)
        mock_lsc.return_value = mock_screen_cls
        mock_lconf.return_value = (mock_pls_config, mock_scr_config)
        mock_lctx.return_value = mock_ctx

        res = Screen.load_for_render(display_id=1, playlist_id=2, playlist_screen_id=3)
        mock_ldisp.assert_called_once_with(display_id=1)
        mock_lpl.assert_called_once_with(mock_display, playlist_id=2, playlist_screen_id=3)
        mock_lsc.assert_called_once_with(mock_display, mock_playlist, mock_playlist_screen)
        mock_lconf.assert_called_once_with(mock_playlist_screen)
        mock_lctx.assert_called_once_with(mock_display)
        mock_screen_cls.assert_called_once_with(mock_display, mock_playlist, mock_playlist_screen, mock_scr_config, mock_pls_config, mock_ctx)
        self.assertEqual(res, mock_screen_cls.return_value)
