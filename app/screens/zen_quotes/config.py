from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, Optional, DataRequired
from wtforms import StringField, SelectField, BooleanField, SubmitField
from app.lib.forms import FilledPasswordField


class ZenQuotesConfigForm(FlaskForm):
    mode = SelectField(
        'Fetch Mode',
        choices=[
            ('random', 'Random Quote'),
            ('today', 'Quote of the Day'),
            ('author', 'Specific Author'),
        ],
        validators=[DataRequired()]
    )
    author = StringField('Author Slug', validators=[], description="If fetch mode is author, fetch quotes from this author (requires an API key)")
    api_key = FilledPasswordField('API Key', validators=[], description="Optional API key to allow for increased request limits and images")
    display_image = BooleanField('Display background image behind quote')
    submit = SubmitField("Save Config")

    def validate_author(form, field):
        if form.mode.data == 'author' and not field.data:
            raise ValidationError("Author slug is required if fetch mode is author")

    def validate_api_key(form, field):
        if not field.data:
            if form.mode.data == 'author':
                raise ValidationError("An API key is required when fetch mode is author")
            if form.display_image.data:
                raise ValidationError("An API key is required to fetch images")
