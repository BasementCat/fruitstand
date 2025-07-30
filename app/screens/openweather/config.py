from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SelectField, SubmitField
from app.lib.forms import FilledPasswordField


class OpenWeatherConfigForm(FlaskForm):
    appid = FilledPasswordField("API Key/AppID", validators=[DataRequired()], description="API key for OpenWeatherMap.org")
    lat = StringField('Latitude', validators=[DataRequired()], description="Latitude of the location for which to retrieve weather information")
    lon = StringField('Longitude', validators=[DataRequired()], description="Longitude of the location for which to retrieve weather information")
    units = SelectField('Units', validators=[DataRequired()], choices=[('standard', 'Standard'), ('imperial', 'Imperial'), ('metric', 'Metric')], default='imperial', description="Units to display information")
    submit = SubmitField("Save Config")
