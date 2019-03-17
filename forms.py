from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, ValidationError


def is_user_exist(form, field):
    if not User.get(login=field.data):
        raise ValidationError("Пользователь `%s` не найден" % field.data)

class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", [DataRequired(), is_user_exist]) # validators
    password = PasswordField("Пароль", [DataRequired()])