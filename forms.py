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


def reg_code(form, field):
    if User.get(reg_code=field.data) and User.get(reg_code=field.data).activated:
        raise ValidationError("Пользователя с регистрационным кодом " + field.data + " уже существует!")
    if not User.get(reg_code=field.data):
        raise ValidationError("Пользователя с регистрационным кодом " + field.data + " не существует!")


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", [DataRequired(), is_user_exist]) # validators
    password = PasswordField("Пароль", [DataRequired()])


class CreateTeacherForm(FlaskForm):
    surname = StringField("Фамилия преподавателя", [DataRequired()])
    name = StringField("Имя преподавателя", [DataRequired()])
    patronymic = StringField("Отчество преподавателя", [DataRequired()])
    faculty = StringField("Кафедра преподавателя", [DataRequired()])
    reg_code = StringField(("Регистрационный код", [DataRequired(), reg_code]))


class RegCodeForm(FlaskForm):
    reg_code = StringField("Регистрационный код", [DataRequired(), reg_code])