from app import app, group_lists, programs
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from models import db, Admin,User, Teacher, Student, Group, Course, Lab,  generate_password_hash
from pony.orm import select
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


@app.route('/update_teacher/<id>', methods=['GET', 'POST'])
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


@app.route('/<tid>/create_course/', methods=['GET', 'POST'])
def create_course(tid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    show = isinstance(current_user, Admin)

    groups = []
    query = select(group.code for group in Group)[:]
    for group in query:
        groups.append(group)

    form = request.form
    if request.method == 'POST' and 'create' in request.form:
        title = form.get('nameInput')

        if title == '':
            flash("Не указано название предмета!", "warning")
            return render_template('teacher/course-creation.html', show=show, groups=groups)

        group_codes = request.form.getlist('group[]')
        try:
            group_codes.remove('Группа')
        except ValueError:
            pass

        c = Course(
            title=title,
            teacher=teacher
        )

        for code in group_codes:
            g = Group.get(code=code)
            c.groups.add(g)

        flash("Предмет создан!", "success")

    return render_template('teacher/course-creation.html', show=show, groups=groups, teacher=teacher)


@app.route('/<teacherid>/course_edit/<courseid>', methods=['GET', 'POST'])
def course_edit(courseid, teacherid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=teacherid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))
    show = isinstance(current_user, Admin)
    course = Course.get(id=courseid, teacher=Teacher.get(id=teacherid))
    cg = course.groups
    groups = []
    query = select(group.code for group in Group)[:]
    for group in query:
        groups.append(group)

    form = request.form
    if request.method == 'POST' and 'update' in request.form:
        title = form.get('nameInput')

        if title == '':
            title = course.title

        group_codes = request.form.getlist('group[]')
        try:
            group_codes.remove('Группа')
        except ValueError:
            pass

        course.title = title
        cglst = []
        for g in cg:
            cglst.append(g.code)

        for code in group_codes:
            if code not in cglst:
                g = Group.get(code=code)
                course.groups.add(g)
        for g in cglst:
            if g not in group_codes:
                grp = Group.get(code=g)
                course.groups.remove(grp)

        return redirect(url_for('courses',id=teacherid))

    return render_template('teacher/course-item.html', show=show, course=course, groups=groups, cg=cg)


@app.route('/teacher-<id>/create_lab/', methods=['GET', 'POST'])
def create_lab(id):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    show = isinstance(current_user, Admin)

    allcourses = select(c.title for c in Course)[:]
    allgroups = select(group.code for group in Group)[:]

    form = request.form
    if request.method == "POST" and 'create' in request.form:
        title = form.get('titleInput')

        if title == '':
            flash("Укажите название предмета!", "warning")
            return render_template('teacher/lab-creation.html', show=show, courses=allcourses, groups=allgroups)

        courses = form.getlist('course[]')
        groups = form.getlist('group[]')

        try:
            courses.remove('Предмет')
            groups.remove('Группа')
        except ValueError:
            pass

        l = Lab(
            title=title,
            teacher=teacher
        )

        for course in courses:
            c = Course.get(title=course)
            l.courses.add(c)

        for group in groups:
            g = Group.get(code=group)
            l.groups.add(g)

        flash("Лабораторная работа " + title +  " создана!", "success")

    return render_template('teacher/lab-creation.html',show=show, courses=allcourses, groups=allgroups)


@app.route('/teacher-<id>/course-<cid>/labs', methods=['GET', 'POST'])
def labs_list(id, cid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    course = Course.get(id=cid)

    labs = select(c.labs for c in Course if c.id == cid)

    out = []
    s = ''
    sc = ''
    for lab in labs:
        for group in lab.groups:
            s += group.code + ","
        s = sorted(s.split(','))
        for i in s:
            if i == '':
                s.remove(i)
        s = ','.join(s)
        for c in lab.courses:
            sc += c.title + ','
        sc = sorted(sc.split(','))
        for i in sc:
            if i == '':
                sc.remove(i)
        sc = ','.join(sc)
        out.append((lab.id, lab.title, sc, s))
        s = ''


    return render_template('teacher/labs.html', labs=out, teacher=teacher, title=course.title)


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


@app.route('/teacher-<id>/courses/')
def courses(id):
    if current_user.id != int(id):
        return redirect(url_for("login"))

    teacher = Teacher.get(id=id)
    courses = teacher.courses
    out = []
    s = ''
    for course in courses:
        for group in course.groups:
            s += group.code + " "
        s = sorted(s.split(' '))
        for i in s:
            if i == ' ':
                s.remove(i)
        s = ' '.join(s)
        out.append((course.id, course.title, s))
        s = ''

    out = sorted(out)

    return render_template('teacher/courses.html', courses=out, teacher=teacher)


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

        try:
            with open(filename) as obj:
                lst = csv_reader(obj)
        except IOError:
            flash("Ошибка чтения файла!", "danger")
            return render_template("teacher/group-create.html")
        except KeyError:
            flash("Неверная структура файла!", "danger")
            return render_template("teacher/group-create.html")

        g = Group(
            code=group_name
        )

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
