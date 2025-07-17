from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField

from app.models import Playlist


class PlaylistEditForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    default_refresh_interval = IntegerField("Default Refresh Interval", validators=[DataRequired(), NumberRange(min=1)], default=1800, description="Default refresh interval to send after rendering, in seconds")
    submit = SubmitField("Save Playlist")


class DisplayEditForm(FlaskForm):
    name = StringField('Display Name', validators=[DataRequired()])
    playlist = QuerySelectField('Playlist',
        validators=[Optional()],
        query_factory=lambda: Playlist.query.order_by(Playlist.name.asc()),
        get_pk=lambda o: o.id,
        get_label=lambda o: o.name,
        allow_blank=True,
        blank_text="None",
    )
    submit = SubmitField("Save Display")
