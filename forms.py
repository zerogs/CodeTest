from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from models import User


def is_login_free(form, field):
    if User.get(login=field.data):
        raise ValidationError("Логин занят, придумайте другое.")


def is_email_free(form, field):
    if User.get(email=field.data):
        raise ValidationError("Данный e-mail уже используется, воспользуйтесь восстановлением пароля.")


def is_user_exist(form, field):
    if not User.get(login=field.data):
        raise ValidationError("Пользователь `%s` не найден" % field.data)


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", [DataRequired(), is_user_exist]) # validators
    password = PasswordField("Пароль", [DataRequired()])