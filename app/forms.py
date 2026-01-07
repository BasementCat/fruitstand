from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, PasswordField, EmailField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
import flask_login
import pytz

from app.models import Playlist, User, Display
from app.constants import DISP_STATUS


class PlaylistEditForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    default_refresh_interval = IntegerField("Default Refresh Interval", validators=[DataRequired(), NumberRange(min=1)], default=1800, description="Default refresh interval to send after rendering, in seconds")
    submit = SubmitField("Save Playlist")


def DisplayEditForm(obj=None, **kwargs):
    class DisplayEditFormImpl(FlaskForm):
        name = StringField('Display Name', validators=[DataRequired()])
        if current_app.config['ENABLE_DISPLAY_APPROVAL']:
            form_status = SelectField("Status", choices=[(k, v) for k, v in DISP_STATUS.items()], validators=[DataRequired()])
        playlist = QuerySelectField('Playlist',
            validators=[Optional()],
            query_factory=lambda: Playlist.query.order_by(Playlist.name.asc()),
            get_pk=lambda o: o.id,
            get_label=lambda o: o.name,
            allow_blank=True,
            blank_text="None",
        )
        submit = SubmitField("Save Display")

        def populate_obj(self, obj):
            old_status = obj.status
            super().populate_obj(obj)
            if current_app.config['ENABLE_DISPLAY_APPROVAL']:
                if obj.status == 'pending' and old_status != 'pending':
                    # status has changed from another status to pending so regenerate/set the code
                    obj.approval_code = Display.generate_approval_code()
                elif obj.status != 'pending':
                    # has either been approved or rejected so clear the code
                    obj.approval_code = None

    return DisplayEditFormImpl(obj=obj, **kwargs)


class UserLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


def UserEditForm(obj=None, **kwargs):
    class UserEditFormImpl(FlaskForm):
        if not obj or (flask_login.current_user.is_authenticated and flask_login.current_user.is_admin):
            username = StringField("Username", validators=[DataRequired()])
        email = EmailField("Email Address", validators=[DataRequired()])
        if obj:
            set_password = PasswordField("Password", description="Only enter a new password if you wish to change it")
            retype_password = PasswordField("Password", description="Enter the same password again to change it")
        else:
            password = PasswordField("Password", description="Enter a strong unique password for the account", validators=[DataRequired()])
            retype_password = PasswordField("Password", description="Enter the same password again", validators=[DataRequired()])
        if flask_login.current_user.is_authenticated and flask_login.current_user.is_admin:
            is_admin = BooleanField("Is Administrator?")
            is_enabled = BooleanField("Is Enabled?", default=True)
        timezone = SelectField("Timezone", choices=[(tz, tz) for tz in pytz.all_timezones], validators=[DataRequired()])
        if obj:
            submit = SubmitField("Save User")
        else:
            submit = SubmitField("Create User")

        def validate_username(self, field):
            query = User.get_by_username(field.data, return_query=True)
            if obj:
                query = query.filter(User.id != obj.id)
            if query.count():
                raise ValidationError("Username must be unique")

        def validate_set_password(self, field):
            if field.data and field.data != self.retype_password.data:
                raise ValidationError("Passwords must match")

        def validate_password(self, field):
            if field.data != self.retype_password.data:
                raise ValidationError("Passwords must match")

        def populate_obj(self, popobj):
            super().populate_obj(popobj)
            if obj:
                if self.set_password.data and self.retype_password.data:
                    popobj.password = self.set_password.data
            else:
                popobj.password = self.password.data

    return UserEditFormImpl(obj=obj, **kwargs)