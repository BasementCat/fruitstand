from wtforms import PasswordField
from wtforms.widgets.core import Input


class FilledPasswordInput(Input):
    input_type = 'password'
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]
    # NOTE: if someone actually sets a password to this, it'll break
    # less than ideal but probably not likely
    _DUMMY_VALUE = '__DUMMY_VALUE__1259fce9-60d8-46d6-82f7-3c68c55dae5c__'

    def __init__(self, hide_value=True):
        super().__init__()
        self.hide_value = hide_value

    def __call__(self, field, **kwargs):
        if self.hide_value and field.data:
            kwargs['value'] = self._DUMMY_VALUE
        return super().__call__(field, **kwargs)


class FilledPasswordField(PasswordField):
    widget = FilledPasswordInput()

    def process_data(self, value):
        # store original value
        self._original_value = value
        super().process_data(value)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        # if the submitted value is the dummy value then use the original value
        if self.data == self.widget._DUMMY_VALUE:
            self.data = getattr(self, '_original_value', None)