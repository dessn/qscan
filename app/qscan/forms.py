from wtforms import TextField, SubmitField, validators
from flask.ext.wtf import Form

class UserForm(Form):
    """Form for signing up to scan."""

    user = TextField('user', [validators.Required()])
    submit = SubmitField('submit')
