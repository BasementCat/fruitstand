from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class PlaylistEditForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    default_refresh_interval = IntegerField("Default Refresh Interval", validators=[DataRequired(), NumberRange(min=1)], default=1800, description="Default refresh interval to send after rendering, in seconds")
    submit = SubmitField("Save Playlist")