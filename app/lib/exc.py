import sys
import uuid


class ScreenError(Exception):
    def __init__(self, display, title=None, message='Internal Error', display_id=None, playlist_screen_id=None, playlist_id=None, screen_cls_key=None):
        title = title or self.__class__.__name__
        super().__init__(title, message, display_id, playlist_screen_id, playlist_id, screen_cls_key)
        self.display = display
        self.title = title
        self.message = message
        self.display_id = display_id
        self.playlist_screen_id = playlist_screen_id
        self.playlist_id = playlist_id
        self.screen_cls_key = screen_cls_key
        eid = list(str(uuid.uuid4()).replace('-', ''))
        self.id = '{}-{}'.format(''.join(eid[:4]), ''.join(eid[4:8]))

    def get_error_context(self):
        return {
            'title': self.title,
            'message': self.message,
            'id': self.id,
        }

    def log(self):
        sys.stderr.write('ERROR #{}: {}: {} (display={}, playlist={}, playlist_screen={}, screen={})\n'.format(
            self.id, self.title, self.message, self.display_id, self.playlist_id,
            self.playlist_screen_id, self.screen_cls_key
        ))

    @classmethod
    def from_exc(cls, display, other_exc, **kwargs):
        new_kw = {'title': 'Internal Error', 'message': 'Internal Error'}
        if isinstance(other_exc, ScreenError):
            for k in ('title', 'message', 'display_id', 'playlist_screen_id', 'playlist_id', 'screen_cls_key'):
                v = getattr(other_exc, k, None)
                if v:
                    new_kw[k] = v
        new_kw.update(kwargs)
        out = cls(display, **new_kw)
        # Maintain the ID
        if isinstance(other_exc, ScreenError):
            out.id = other_exc.id
        return out


class ScreenLoadError(ScreenError):
    pass


class DisplayNotFound(ScreenLoadError):
    pass


class DisplayAuthError(ScreenLoadError):
    pass


class DisplayNotAuthenticated(DisplayAuthError):
    pass


class DisplayPendingApproval(DisplayAuthError):
    def log(self):
        pass


class DisplayNotApproved(DisplayAuthError):
    pass


class PlaylistNotFound(ScreenLoadError):
    pass


class ScreenNotFound(ScreenLoadError):
    pass
