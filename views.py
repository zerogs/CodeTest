from app import app
from flask import render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user
from models import db, User, Teacher, Student
from datetime import datetime
from pony.orm import db_session
from forms import LoginForm, CreateTeacherForm, RegCodeForm
from secrets import token_hex



def authorized():
    if not current_user:
        return False

    try:
        return current_user.is_authenticated()
    except:
        return current_user.is_authenticated


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def login():
    if authorized():
        if current_user.is_admin:
            return redirect(url_for('admin'))
        if Teacher.get(id=current_user.id):
            return redirect(url_for('teacher'))
        if Student.get(id=current_user.id):
            return redirect(url_for('student'))


    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        login = form.username.data
        password = form.password.data
        user = User.get(login=login)
        correct = user.check_password(password)
        if correct:
            login_user(user, remember=True, force=True)
            user.last_login = datetime.now()
            if current_user.is_admin:
                return redirect(url_for('admin'))
            if Teacher.get(id=current_user.id):
                return redirect(url_for('teacher'))
            if Student.get(id=current_user.id):
                return redirect(url_for('student'))

    return render_template('login.html', form=form, title="Авторизация")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if not authorized():
        return redirect(url_for('login'))
    return render_template('admin/index.html')


@app.route('/admin/create_teacher', methods=['GET', 'POST'])
def create_teacher():
    if not authorized() and not current_user.is_admin:
        return redirect(url_for('login'))

    form = CreateTeacherForm(request.form)
    reg_code = token_hex(7)
    form.reg_code.data = reg_code
    if request.method == 'POST' and form.validate_on_submit():

        surname = form.surname.data
        name = form.name.data
        patronymic = form.patronymic.data
        faculty = form.faculty.data
        form_reg_code = form.reg_code.data
        t = Teacher(
            surname=surname,
            name=name,
            patronymic=patronymic,
            faculty=faculty,
            reg_code=form_reg_code,
            activated=False
        )
        return redirect(url_for('show_code', reg_code=reg_code))

    return render_template('admin/create_teacher.html', form=form, reg_code=reg_code)


@app.route('/enter', methods=['GET', 'POST'])
def enter_code():
    form = RegCodeForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        print('eee')
        code = form.reg_code.data
        return redirect(url_for('update_profile'))

    return render_template('user/enter_code.html', form=form)


@app.route('/code', methods=['GET', 'POST'])
def show_code():
    reg_code = request.args.get('reg_code', None)
    return render_template('user/show_code.html', reg_code=reg_code)


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    return render_template('user/update_profile.html')


@app.route('/teacher')
def teacher():
    return render_template('teacher/index.html')

@app.route('/student')
def student():
    return render_template('student/index.html')
