from app import app, group_lists, programs
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from models import db, User, Teacher, Student, Group,  generate_password_hash
from datetime import datetime
from secrets import token_hex
from csvhandler import csv_reader


def authorized():
    if not current_user:
        return False
    try:
        return current_user.is_authenticated()
    except:
        return current_user.is_authenticated


@app.route('/update_profile/<id>', methods=['GET', 'POST'])
def update_teacher_profile(id):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))
    form = request.form
    if request.method == 'POST' and 'updateForm' in request.form:
        if form.get('inputPassword') != form.get('inputRepassword'):
            flash("Введённые пароли не совпадают!", "warning")
            return render_template('teacher/registration-teacher.html', teacher=teacher)
        else:
            teacher.login = form.get("loginInput")
            teacher.email = form.get("emailInput")
            teacher.password = generate_password_hash(form.get("inputPassword"))
            teacher.activated = True
            flash("Данные обновлены успешно!", "success")
    return render_template('teacher/registration-teacher.html', teacher=teacher)


@app.route('/update_student/<id>', methods=['GET', 'POST'])
def update_student_profile(id):
    if not authorized():
        return redirect(url_for('login'))
    student = User.get(id=id)
    if student.id != current_user.id:
        return redirect(url_for('login'))
    form = request.form

    if request.method == 'POST' and 'updateForm' in request.form:
        if form.get('inputPassword') != form.get('inputRepassword'):
            flash("Введённые пароли не совпадают!", "warning")
            return render_template('student/registration-student.html', student=student)
        else:
            student.login = form.get("loginInput")
            student.email = form.get("emailInput")
            student.password = generate_password_hash(form.get("inputPassword"))
            student.activated = True
            flash("Данные обновлены успешно!", "success")
    return render_template('student/registration-student.html', student=student)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def login():
    '''
    if authorized():
        if Teacher.get(id=current_user.id):
            return redirect(url_for('courses', id=current_user.id))
        if Student.get(id=current_user.id):
            return redirect(url_for('student'))
        if current_user.is_admin:
            return redirect(url_for('admin'))
    '''
    form = request.form
    if request.method == 'POST' and 'authForm' in request.form:
        login = form.get("inputLogin")
        password = form.get("inputPassword")

        user = User.get(login=login)
        if user:
            correct = user.check_password(password)
            if correct:
                login_user(user, remember=True, force=True)
                user.last_login = datetime.now()
                if Teacher.get(id=current_user.id):
                    return redirect(url_for('courses',id=current_user.id))
                if Student.get(id=current_user.id):
                    return redirect(url_for('student'))
                if current_user.is_admin:
                    return redirect(url_for('admin'))
            else:
                flash("Некорректный логин или пароль", "danger")
        else:
            flash("Некорректный логин или пароль", "danger")

    if request.method == 'POST' and 'regForm' in request.form:
        code = form.get("inputCode")
        if code == "":
            flash("Некорректный регистрационный код", "warning")
            return render_template('login.html')
        user = User.get(reg_code=code)
        if user:
            if isinstance(user, Teacher):
                login_user(user, remember=True, force=True)
                user.last_login = datetime.now()
                return redirect(url_for('update_teacher_profile', id=user.id))
            if isinstance(user, Student):
                login_user(user, remember=True, force=True)
                user.last_login = datetime.now()
                return redirect(url_for('update_student_profile', id=user.id))
        else:
            flash("Некорректный регистрационный код")

    return render_template('login.html')


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

    form = request.form
    reg_code = token_hex(7)
    if request.method == 'POST' and 'createTeacherForm' in request.form:
        name = form.get('nameInput')
        surname = form.get('surnameInput')
        patronymic = form.get('patronymicInput')
        faculty = form.get('facultyInput')
        department = form.get('departmentInput')
        email = form.get('emailInput')
        reg_code_final = form.get('regcodeInput')
        if reg_code_final == '':
            reg_code_final = reg_code
        if name == '' or surname == '' or patronymic == '':
            flash("Обязательно поле не заполнено!", "warning")
            return render_template('admin/create_teacher.html',reg_code=reg_code)

        t = Teacher(
            surname=surname,
            name=name,
            patronymic=patronymic,
            faculty=faculty,
            department=department,
            email=email,
            reg_code=reg_code_final,
            activated=False
        )
        reg_code = token_hex(7)
        flash("Учётная запись преподавателя успешно создана! Регистрационный код: " + reg_code_final, "success")

    return render_template('admin/create_teacher.html',reg_code=reg_code)


@app.route('/courses/<id>')
def courses(id):
    if current_user.id != int(id):
        return redirect(url_for("login"))

    teacher = Teacher.get(id=id)
    courses = teacher.courses
    out = []
    s = ''
    i = 0
    for course in courses:
        i += 1
        for group in courses.groups:
            s += group.code + " "
        out.append((i, course.title, s))

    return render_template('teacher/courses.html', courses=out)


@app.route('/group_create/', methods=['GET', 'POST'])
def group_create():
    user = User.get(id=current_user.id)
    if not isinstance(user, Teacher):
        return redirect(url_for('login'))

    form = request.form
    if request.method == 'POST' and 'groupList' in request.files:
        filename = group_lists.save(request.files['groupList'])
        group_name = form.get("groupCodeInput")

        if group_name == '':
            flash("Укажите название группы!", "warning")
            return render_template("teacher/group-create.html")

        g = Group(
            code=group_name
        )
        try:
            with open(filename) as obj:
                lst = csv_reader(obj)
        except IOError:
            flash("Ошибка чтения файла!", "danger")
            return render_template("teacher/group-create.html")
        except KeyError:
            flash("Неверная структура файла!", "danger")
            return render_template("teacher/group-create.html")

        for i in lst:
            reg_code = token_hex(7)
            Student(
                surname=i[0],
                name=i[1],
                patronymic=i[2],
                reg_code=reg_code,
                group=g,
                activated=False
            )
        flash("Группа " + group_name + " успешно создана!", "success")

    return render_template("teacher/group-create.html")


@app.route('/student')
def student():
    return render_template('student/index.html')
