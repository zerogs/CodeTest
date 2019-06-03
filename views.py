from app import app, group_lists, ALLOWED_EXTENSIONS
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from models import db, Admin,User, Teacher, Student, Variant, Group, Attempt, Course, Lab, Test, generate_password_hash
from pony.orm import select, desc
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from datetime import datetime
from secrets import token_hex
from csvhandler import csv_reader
from flask import send_from_directory
from script_check import script_check
from shutil import rmtree
from pathlib import Path
import os



def authorized():
    if not current_user:
        return False
    auth = current_user.is_authenticated
    if callable(auth):
        return auth()
    return auth

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

        return redirect(url_for('student_courses'))

    return render_template('student/registration-student.html', student=student)


@app.route('/teacher-<tid>/create_course/', methods=['GET', 'POST'])
def create_course(tid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=tid)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))

    show = isinstance(current_user, Admin)

    groups = select(group.code for group in Group)[:]

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

    return render_template('teacher/course-creation.html', show=show, groups=groups, teacher=teacher, cuser=current_user)


@app.route('/teacher-<teacherid>/course_edit/<courseid>', methods=['GET', 'POST'])
def course_edit(courseid, teacherid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=teacherid)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))

    show = isinstance(Admin.get(id=current_user.id), Admin)
    course = Course.get(id=courseid, teacher=Teacher.get(id=teacherid))
    teachers = select((t.id, t.surname + ' ' + t.name[0] + '. ' + t.patronymic[0] + '.') for t in Teacher)[:]
    change_course_teacher = False
    cg = course.groups
    groups = select(group.code for group in Group)[:]

    form = request.form
    if request.method == 'POST' and 'update' in request.form:
        title = form.get('nameInput') or course.title

        if show:
            tid = form.get('teacherInput')

            if tid != 'Преподаватель':
                new_teacher = Teacher.get(id=tid)
                change_course_teacher = True

        if change_course_teacher:
            # if title == '':
            #     title = course.title

            group_codes = request.form.getlist('group[]')
            try:
                group_codes.remove('Группа')
            except ValueError:
                pass

            labs = select(l for l in Lab if  Course.get(id=courseid) in l.courses)[:]
            groups = select(g for g in Group if Course.get(id=courseid) in g.courses)[:]

            Course.get(id=courseid).delete()

            c = Course(
                title=title,
                teacher=new_teacher
            )

            for lab in labs:
                c.labs.add(lab)
            for group in groups:
                c.groups.add(group)

        else:
            # if not title:  # might be empty string
            #     title = course.title

            group_codes = request.form.getlist('group[]')
            try:
                group_codes.remove('Группа')
            except ValueError:
                pass

            # course.title = title

            for g in cg:
                if g.code not in group_codes:
                    for lab in course.labs:
                        lab.groups.remove(g)
                    course.groups.remove(g)

            for code in group_codes:
                g = Group.get(code=code)
                if g not in cg:
                    course.groups.add(g)

        return redirect(url_for('course_list', id=teacherid))

    return render_template('teacher/course-item.html',teacher=teacher, show=show, course=course, groups=groups, cg=cg,
                           teachers=teachers, cuser=current_user)

@app.route('/teacher-<id>/courses/', methods=['GET', 'POST'])
def course_list(id):
    if current_user.id != int(id):
        return redirect(url_for("login"))

    teacher = Teacher.get(id=id)
    out = []
    for course in select(c for c in Course if c.teacher.id == id).order_by(lambda c: c.id):
        s = ' '.join(g.code for g in sorted(course.groups, key=lambda g: g.code))
        out.append((course.id, course.title, s))

    return render_template('teacher/courses.html', courses=out, teacher=teacher, cuser=current_user)


@app.route('/teacher-<id>/course_delete/<cid>', methods=['GET', 'POST'])
def course_delete(id, cid):
    if not Admin.get(id=current_user.id):
        if current_user.id != int(id):
            return redirect(url_for("login"))
    Course[cid].delete()

    return redirect(url_for('course_list', id=id))



@app.route('/teacher-<id>/create_lab/', methods=['GET', 'POST'])
def create_lab(id):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher[id]
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))

    show = isinstance(Admin.get(id=current_user.id), Admin)

    allcourses = select(c for c in Course if c.teacher == teacher)[:]
    teacherFio = select(t.fullname for t in Teacher if t.id == id)[:]
    allgroups = set()
    for course in allcourses:
        for group in course.groups:
            allgroups.add(group.code)

    form = request.form
    if request.method == "POST" and 'create' in request.form:
        title = form.get('titleInput')

        if title == '':
            flash("Укажите название предмета!", "warning")
            return render_template('teacher/lab-creation.html', show=show, courses=allcourses, groups=sorted(allgroups))

        courseid = form.get('course')
        groups = form.getlist('group[]')

        if 'Группа' in groups:
            groups.remove('Группа')

        course = Course.get(id=courseid)

        l = Lab(
            title=title,
            teacher=teacher,
            course=course
        )

        course.labs.add(l)
        for group in groups:
            g = Group.get(code=group)
            if g not in course.groups:
                flash('Группа ' + g.code + ' не записана на предмет ' + course.title + '!', "warning")
                return render_template('teacher/lab-creation.html', teacher=teacher, show=show, courses=allcourses,
                                       groups=allgroups,
                                       teacherFio=teacherFio)
            g.labs.add(l)

        flash("Лабораторная работа " + title + " создана!", "success")

    return render_template('teacher/lab-creation.html',teacher=teacher, show=show, courses=allcourses, groups=allgroups,
                           teacherFio=teacherFio, cuser=current_user)


@app.route('/teacher-<id>/course-<cid>/labs', methods=['GET', 'POST'])
def labs_list(id, cid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=id)
    course = Course[cid]
    if course.teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('course_list', id=current_user.id))

    course = Course.get(id=cid)

    # labs = select(c.labs for c in Course if c.id == cid)
    labs = Course[cid].labs
    labs = sorted(labs, key=lambda l: l.id)
    out = []
    for lab in labs:
        groups = [g for g in lab.groups]
        group_names = ', '.join(sorted([g.code for g in groups]))
        out.append((lab.id, lab.title, course.title, group_names))

    return render_template('teacher/labs.html',group_list=False, labs=out, teacher=teacher, course=course,
                           cuser=current_user)


@app.route('/teacher-<tid>/lab-<lid>/edit', methods=['GET', 'POST'])
def lab_edit(tid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=tid)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))
    show = isinstance(current_user, Admin)

    lab = Lab.get(id=lid)

    lg = lab.groups
    groups = select(group.code for group in Group)[:]

    courses = []

    cquery = select(course.title for course in Course)[:]
    for course in cquery:
        courses.append(course)
    form = request.form
    missing = False

    if request.method == "POST" and 'update' in request.form:
        title = form.get('titleInput') or lab.title
        group_codes = form.getlist('group[]')

        if 'Группа' in group_codes:
            group_codes.remove('Группа')

        for g in lg:
            if g.code not in group_codes:
                lab.groups.remove(g)
        for code in group_codes:
            g = Group.get(code=code)
            if g not in lg:
                if g in lab.course.groups:
                    lab.groups.add(g)
                else:
                    flash("Группа " + g.code + " не записана на предмет!", "warning")
                    return render_template('teacher/lab-item.html', lab=lab, lg=lg, courses=courses, groups=groups,
                                           teacher=teacher)

        flash('Данные успешно обновлены!', 'success')

    return render_template('teacher/lab-item.html', lab=lab, lg=lg, courses=courses, groups=groups, teacher=teacher,
                           cuser=current_user)


@app.route('/teacher-<id>/course-<cid>/lab-<lid>/delete', methods=['GET', 'POST'])
def lab_delete(id, cid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=id)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))
    lab = Lab.get(id=lid)

    try:
        lab.delete()
    except AttributeError:
        flash('Ошибка удаления!', 'danger')

    return redirect(url_for('labs_list', id=id, cid=cid))


@app.route('/teacher-<id>/course-<cid>/add_lab', methods=['GET', 'POST'])
def add_existing_lab(id, cid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))

    course = Course.get(id=cid)

    labs = select(l for l in Lab if l.teacher == teacher)

    form = request.form
    if request.method == "POST" and 'add' in request.form:
        titles = form.getlist('lab[]')
        if 'Лабораторная работа' in titles:
            titles.remove('Лабораторная работа')

        for title in titles:
            l = Lab.get(title=title)
            if l not in course.labs:
                course.labs.add(l)

        return redirect(url_for('labs_list', id=teacher.id, cid=course.id))

    return render_template('teacher/lab-add-to-course.html', labs=labs, teacher=teacher, cuser=current_user)

@app.route('/teacher-<id>/group<code>/course-<cid>/labs', methods=['GET', 'POST'])
def group_labs_list(id, cid, code):
    group_list = True
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    course = Course[cid]
    if course.teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('course_list', id=current_user.id))

    group = Group.get(code=code)
    course = Course.get(id=cid)

    labs = select(g.labs for g in Group if g.code == code)

    out = []
    s = ''
    sc = ''
    for lab in labs:
        out.append((lab.id, lab.title, sc, s))
        s = ''

    return render_template('teacher/labs.html',group_list=group_list,group=group, labs=out, teacher=teacher, course=course,
                           cuser=current_user)


@app.route('/teacher-<id>/group<code>/course-<cid>/lab-<lid>/delete', methods=['GET', 'POST'])
def group_lab_delete(id, code, cid, lid):
    if current_user.id != int(id):
        return redirect(url_for("login"))

    lab = Lab.get(id=lid)
    group = Group.get(code=code)
    for student in group.students:
        for var in lab.variants:
            if var in student.variants:
                student.variants.remove(var)
    group.labs.remove(lab)

    return redirect(url_for('group_labs_list', id=id, code=code, cid=cid))


@app.route('/teacher-<id>/group<code>/course-<cid>/lab<lid>/distribute_variants', methods=['GET', 'POST'])
def dist_vars(id, code, cid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    group = Group.get(code=code)
    course = Course.get(id=cid)
    lab = Lab.get(id=lid)

    students = group.students
    studvars = []

    students = sorted(students, key=lambda stud: stud.surname + stud.name)
    for student in students:
        found = False
        for var in student.variants:
            if var.lab == lab:
                studvars.append((student, var))
                found = True
        if not found:
            studvars.append((student, None))

    vars = lab.variants
    vars = sorted(vars, key=lambda var: var.number)

    form = request.form
    if request.method == 'POST' and 'distrib' in request.form:
        variants = form.getlist('variant[]')

        equalvars = set()
        for i in variants:
            for v in variants:
                if i == v:
                    continue
                # if i == '#' or v == '#':
                if '#' in (i, v):
                    continue
                else:
                    if i.split(',')[1] == v.split(',')[1]:
                        equalvars.add(i)
                        equalvars.add(v)
        if len(equalvars) != 0:
            flash('Один и тот же вариант выдан нескольким студентам!', 'warning')
            return render_template('teacher/variant-dist.html', lab=lab, group=group, course=course, students=studvars,
                                   vars=vars, teacher=teacher, cuser=current_user)

        for item in variants:
            if item != '#':
                item = item.split(',')
                stud = Student.get(id=item[0])
                var = Variant.get(number=item[1], lab=lab)
                if var not in stud.variants:
                    var.student = stud
        flash("Данные успешно обновлены!", "success")


    return render_template('teacher/variant-dist.html',lab=lab, group=group, course=course, students=studvars, vars=vars,
                           teacher=teacher, cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variants/', methods=['GET', 'POST'])
def variant_list(tid, cid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    course = Course.get(id=cid)
    lab = Lab.get(id=lid)

    variants = select(l.variants for l in Lab if l.id == lid)

    return render_template('teacher/variants.html', lab=lab, variants=variants, teacher=teacher, course=course,
                           cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/attempts', methods=['GET', 'POST'])
def variant_attempts(tid, cid, lid, vid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)
    attempts = var.attempts
    attempts = sorted(attempts, key=lambda a: a.dt, reverse=True)
    table_data = []
    for attempt in attempts:
        student = Student[attempt.studentID]
        table_data.append((attempt, student.group.code, student.fullname))


    return render_template('teacher/attempts.html', var=var, table_data=table_data, cuser=current_user, lab=lab,
                           cid=cid, teacher=teacher)


@app.route('/teacher-<tid>/last_attempts', methods=['GET', 'POST'])
def all_attempts(tid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    attempts = select(a for a in Attempt if a.variant.lab.teacher == teacher).order_by(lambda a: desc(a.dt))[:20]
    table_data = []
    for attempt in attempts:
        student = Student[attempt.studentID]
        table_data.append((attempt, student.group.code, student.fullname, (attempt.variant.lab.id, attempt.variant.lab.title),
                           (attempt.variant.lab.course.id, attempt.variant.lab.course.title), attempt.variant))

    return render_template('teacher/all-attempts.html',teacher=teacher, table_data=table_data, cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/attempt-<aid>/delete')
def attempt_delete(tid, cid, lid, vid, aid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))
    course = Course[cid]
    attempt = Attempt[aid]
    if course in teacher.courses:
        path = Path(attempt.source)
        if path.is_file():
            os.remove(attempt.source)
        attempt.delete()

    return redirect(url_for("variant_attempts", tid=tid, cid=cid, lid=lid, vid=vid))

@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/attempt-<aid>', methods=['GET', 'POST'])
def attempt_info(tid, cid, lid, vid, aid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)
    attempt = Attempt.get(id=aid)
    student = Student.get(id=attempt.studentID)
    program = attempt.source

    with open(program, "r") as fh:
        code = fh.read()

    return render_template('teacher/attempt-code.html', lab=lab, var=var, attempt=attempt, student=student, code=code,
                           cuser=current_user, teacher=teacher)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/attempt-<aid>/check', methods=['GET', 'POST'])
def attempt_check(tid, cid, lid, vid, aid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    attempt = Attempt[aid]
    lab = Lab[lid]
    var = Variant[vid]
    student = Student[attempt.studentID]
    tests = var.tests
    res = False

    prg_path = attempt.source
    lang = attempt.language
    counter = 0
    for test in tests:
        counter += 1
        out = script_check(prg_path, lang, test.input, test.output)
        if out[0] != "Completed":
            attempt.result = "Решение неверно!"
            error = [test.input, test.output, out[1], counter, len(tests), test.id]
            return render_template('teacher/attempt-check.html', attempt=attempt, lab=lab, var=var, student=student,
                                   error=error, cuser=current_user, res=res, teacher=teacher)
    attempt.result = 'Решение верно!'
    res = True

    return render_template('teacher/attempt-check.html', attempt=attempt, lab=lab, var=var, student=student,
                           cuser=current_user, res=res, teacher=teacher)

@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/create_variant/', methods=['GET', 'POST'])
def create_variant(tid, cid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    course = Course.get(id=cid)
    lab = Lab.get(id=lid)
    groups = select(g for g in Group if course in g.courses).prefetch(Student)

    groups = sorted(groups, key=lambda group: group.code)
    data = []
    for group in groups:
        data.append((group.code, sorted(group.students, key=lambda stud : stud.surname)))

    form = request.form
    if request.method == "POST" and 'create' in request.form:
        number = form.get('numberInput')
        title = form.get('nameInput')
        description = form.get('descriptionInput')
        studentid = form.get('student')

        for sym in number:
            if not sym.isdigit():
                flash('Поле номера варианта содержит символы! Номер может быть только числом!', 'warning')
                return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher,
                                       cuser=current_user)
        if Variant.get(number=number, lab=lab):
            flash('Вариант с введённым номером уже существует!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher,
                                   cuser=current_user)
        if number == '':
            flash('Не задан номер варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher,
                                   cuser=current_user)
        if title == '':
            flash('Не указано название варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher,
                                   cuser=current_user)
        if description == '':
            flash('Не указано описания варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher,
                                   cuser=current_user)

        if studentid == 'Студент':
            v = Variant(
                number=number,
                title=title,
                description=description,
                lab=lab
            )
        else:
            v = Variant(
                number=number,
                title=title,
                description=description,
                student=Student.get(id=studentid),
                lab=lab
            )
        flash('Вариант задания для лабораторной работы успешно создан!', "success")

    return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher, cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/edit', methods=['GET', 'POST'])
def variant_edit(tid, cid, lid, vid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)

    form = request.form
    if request.method == "POST" and 'update' in request.form:
        number = form.get('numberInput')
        title = form.get('nameInput')
        desc = form.get('descriptionInput')

        for sym in number:
            if not sym.isdigit():
                flash('Поле номера варианта содержит символы! Номер может быть только числом!', 'warning')
                return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var,
                                       cuser=current_user)
        if Variant.get(number=number, lab=lab):
            flash('Вариант с введённым номером уже существует!', 'warning')
            return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var, cuser=current_user)
        if number == '':
            flash('Не задан номер варианта!', 'warning')
            return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var, cuser=current_user)
        if title == '':
            flash('Не указано название варианта!', 'warning')
            return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var, cuser=current_user)
        if desc == '':
            flash('Не указано описания варианта!', 'warning')
            return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var, cuser=current_user)
        if number == '':
            number = var.number
        if title == '':
            title = var.title
        if desc == '':
            desc = var.description

        var.number = number
        var.title = title
        var.description = desc

        flash('Данные варианта обновлены успешно!', 'success')

    return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var, cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/delete', methods=['GET', 'POST'])
def variant_delete(tid, cid, lid, vid):
    if current_user.id != int(tid):
        return redirect(url_for("login"))
    var = Variant.get(id=vid)
    var.delete()

    return redirect(url_for('variant_list', tid=tid, cid=cid, lid=lid))


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/tests', methods=['GET', 'POST'])
def test_list(tid, cid, lid, vid,):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)

    return render_template('teacher/tests.html',cid=cid, teacher=teacher, lab=lab, var=var,cuser=current_user)


@app.route('/teacher-<tid>/lab-<lid>/variant-<vid>/create_test', methods=['GET', 'POST'])
def create_test(tid, lid, vid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)

    form = request.form
    if request.method == 'POST' and 'create' in request.form:
        input = form.get('inputInput')
        output = form.get('outputInput')

        if input == '':
            flash('Не указаны входные данные!', 'warning')
            return render_template('teacher/test-creation.html', teacher=teacher, lab=lab, var=var)
        if output == '':
            flash('Не указаны выходные данные!', 'warning')
            return render_template('teacher/test-creation.html', teacher=teacher, lab=lab, var=var)

        t = Test(
            input=input,
            output=output,
            variant=var
        )
        flash('Тест для варианта ' + str(var.number) +' успешно создан!', 'success')

    return render_template('teacher/test-creation.html', teacher=teacher, lab=lab, var=var,cuser=current_user)

@app.route('/teacher-<tid>/lab-<lid>/variant-<vid>/test-<tsid>/edit', methods=['GET', 'POST'])
def test_edit(tid, lid, vid, tsid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    lab = Lab.get(id=lid)
    var = Variant.get(id=vid)
    test = Test.get(id=tsid)

    form = request.form
    if request.method == "POST" and 'update' in request.form:
        inpt = form.get('inputInput')
        outpt = form.get('outputInput')

        if inpt == '':
            inpt = test.input
        if outpt == '':
            outpt = test.output

        test.input = inpt
        test.output = outpt

        flash('Данные теста успешно обновлены!', 'success')

    return render_template('teacher/test-item.html', teacher=teacher, lab=lab, var=var, test=test,cuser=current_user)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/test-<tsid>/delete', methods=['GET', 'POST'])
def test_delete(tid, cid, lid, vid, tsid):
    if current_user.id != int(tid):
        return redirect(url_for("login"))
    test = Test.get(id=tsid)
    test.delete()

    return redirect(url_for('test_list', tid=tid, cid=cid, lid=lid, vid=vid))


@app.route('/admin/group_create/', methods=['GET', 'POST'])
def group_create():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    form = request.form
    if request.method == 'POST' and 'groupList' in request.files:
        filename = group_lists.save(request.files['groupList'])
        group_code = form.get("groupCodeInput")

        if group_code == '':
            flash("Укажите название группы!", "warning")
            return render_template("admin/group-create.html", cuser=current_user)

        if Group.get(code=group_code) is None:
            pass
        else:
            flash("Группа с таким номером уже существует!", "danger")
            return render_template("admin/group-create.html", cuser=current_user)

        try:
            with open(filename) as obj:
                lst = csv_reader(obj)
        except IOError:
            flash("Ошибка чтения файла!", "danger")
            return render_template("admin/group-create.html", cuser=current_user)
        except KeyError:
            flash("Неверная структура файла!", "danger")
            return render_template("admin/group-create.html", cuser=current_user)

        g = Group(
            code=group_code
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
        flash("Группа " + group_code + " успешно создана!", "success")

    return render_template("admin/group-create.html", cuser=current_user)


@app.route('/teacher-<tid>/groups', methods=['GET', 'POST'] )
def group_list(tid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    courses = teacher.courses
    groups = []
    for course in courses:
        for group in course.groups:
            if group not in groups:
                groups.append(group)
    out = []
    cs = []
    for group in groups:
        for course in group.courses:
            if course in teacher.courses:
                cs.append((course.title, course.id))
        cs = sorted(cs)
        out.append((group.id, group.code, cs))
        cs = []

    out = sorted(out)

    return render_template('teacher/groups.html', teacher=teacher, groups=out, cuser=current_user)


@app.route('/group-<gid>/students', methods=['GET', 'POST'])
def student_list(gid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = Teacher.get(id=current_user.id)
    if teacher.id != current_user.id and not Admin.get(id=current_user.id):
        return redirect(url_for('login'))

    group = Group.get(id=gid)
    students = group.students

    students = sorted(students, key=lambda stud: stud.surname + stud.name)

    return render_template('teacher/students.html', teacher=current_user, group=group, students=students)


@app.route('/', methods=['GET', 'POST'])
def login():
    #TODO password reset
    if authorized():
        if Teacher.get(id=current_user.id):
            return redirect(url_for('course_list', id=current_user.id))
        if Student.get(id=current_user.id):
            return redirect(url_for('student_courses'))
        if current_user.is_admin:
            return redirect(url_for('admin'))

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
                    return redirect(url_for('course_list', id=current_user.id))
                if Student.get(id=current_user.id):
                    return redirect(url_for('student_courses'))
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
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))
    groups = select(g for g in Group)
    teachers = select(t for t in Teacher)
    return render_template('admin/index.html', groups=groups, teachers=teachers, cuser=current_user)


@app.route('/student/courses', methods=['GET', 'POST'])
def student_courses():
    if not authorized():
        return redirect(url_for('login'))
    student = Student.get(id=current_user.id)
    if not isinstance(student, Student):
        return redirect(url_for('login'))

    courses = student.group.courses

    out = []
    for course in courses:
        teacher = course.teacher
        out.append((course.id, course.title, teacher.surname + " " + teacher.name + " " + teacher.patronymic))
    out = sorted(out, key=lambda c: c[0])

    return render_template('student/courses.html', courses=out, student=student, cuser=current_user)


@app.route('/student/course-<cid>/labs', methods=['GET', 'POST'])
def student_course_labs(cid):
    if not authorized():
        return redirect(url_for('login'))
    student = Student.get(id=current_user.id)
    if not isinstance(student, Student):
        return redirect(url_for('login'))

    course = Course.get(id=cid)
    group = current_user.group

    labs = select(l for l in Lab if course == l.course  and group in l.groups)

    return render_template('student/labs.html', labs=labs, course=course, cuser=current_user)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/student/lab-<lid>/review', methods=['GET', 'POST'])
def student_lab_page(lid):
    if not authorized():
        return redirect(url_for('login'))
    student = Student.get(id=current_user.id)
    if not isinstance(student, Student):
        return redirect(url_for('login'))
    lab = Lab.get(id=lid)
    var = Variant.get(student=student, lab=lab)
    if var is None:
        return redirect(url_for('student_course_labs', cid=lab.course.id))
    attempts = []
    if var.attempts is not None:
        no_attempts = False
        for attempt in var.attempts:
            if attempt.studentID == student.id:
                attempts.append(attempt)
        attempts = sorted(attempts, key=lambda a: a.dt, reverse=True)
    else:
        no_attempts = True

    if request.method == 'POST' and 'downloadProgram' in request.form:
        file = request.files['programFile']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], student.group.code, str(student.id), str(lab.id))
            program = Path(path + '/' + filename)
            if program.is_file():
                filename = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + filename
            file.save(os.path.join(os.getcwd(), path, filename))
            a = Attempt(
                studentID=student.id,
                variant=var,
                dt=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                source=os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], student.group.code, str(student.id),
                                    str(lab.id), filename),
                result="Не проверено",
                language="python"
            )

            attempt = a
            lab = Lab[lid]
            prg_path = attempt.source
            lang = attempt.language
            counter = 0
            for test in var.tests:
                counter += 1
                out = script_check(prg_path, lang, test.input, test.output)
                if out[0] != "Completed":
                    attempt.result = "Решение неверно!"
                    error = [test.input, test.output, out[1], counter, len(var.tests), test.id]
                    return render_template('student/variant_info.html', var=var, lab=lab, attempts=attempts,
                                           cuser=current_user,
                                           no_attempts=no_attempts)

            attempt.result = 'Решение верно!'
            res = True

    return render_template('student/variant_info.html', var=var, lab=lab, attempts=attempts, cuser=current_user,
                           no_attempts=no_attempts)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin/courses')
def admin_course_list():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    courses = select(c for c in Course)
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
        teacherFio = course.teacher.surname + ' ' + course.teacher.name[0] + '. ' + course.teacher.patronymic[0] + '.'
        out.append((course.id, course.title, teacherFio, s, course.teacher.id))
        s = ''

    out = sorted(out)

    return render_template('admin/courses.html', courses=out, cuser=current_user)

@app.route('/admin/groups', methods=['GET', 'POST'] )
def admin_group_list():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    groups = select(g for g in Group)[:]

    out = []
    for group in groups:
        out.append((group.id, group.code))

    out = sorted(out)

    return render_template('admin/groups.html', groups=out, cuser=current_user)


@app.route('/admin/group<id>/delete', methods=['GET', 'POST'])
def admin_delete_group(id):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    group = Group.get(id=id)
    if group.students is not None:
        for student in group.students:
            student_delete(student.id)
    group.delete()

    return redirect(admin_group_list)


@app.route('/admin/group<code>/students', methods=['GET', 'POST'] )
def admin_student_list(code):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    group = Group.get(code=code)
    students = group.students
    students = sorted(students, key=lambda stud: stud.surname + stud.name)

    return render_template('admin/students.html', group=group, students=students, cuser=current_user)

def student_delete(id):
    student = Student[id]
    code = student.group.code
    attempts = select(a for a in Attempt if a.studentID == id)
    path = os.path.join(app.config['UPLOAD_FOLDER'], code, str(student.id))
    rmtree(path)  # deleting lab folder and files included
    for attempt in attempts:
        attempt.delete()
    student.delete()

@app.route('/admin/student-<id>/delete')
def admin_student_delete(id):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))
    code = Student[id].group.code
    student_delete(id)

    return redirect(url_for(admin_student_list, code=code))

@app.route('/admin/add_student', methods=['GET', 'POST'] )
def admin_add_student():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    groups = select(g for g in Group)
    form = request.form
    if request.method == "POST" and 'update' in request.form:
        surname = form.get('surnameInput')
        name = form.get('nameInput')
        patronymic = form.get('patronymicInput')
        group = Group.get(code=form.get('group'))
        reg_code = token_hex(7)
        s = Student(
            surname=surname,
            name=name,
            patronymic=patronymic,
            group=group,
            reg_code=reg_code,
            activated=False
        )
        flash('Студент успешно создан и добавлен в группу ' + group.code + '!' + " Регистрационный код " + reg_code +' .',
              'success')

    return render_template('admin/add-student.html', groups=groups, cuser=current_user)

#TODO teacher delete, course copying to other teacher, or delete all connected data
@app.route('/admin/teachers', methods=['GET', 'POST'])
def admin_teachers_list():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    teachers = select(t for t in Teacher)[:]

    return render_template('admin/teachers.html', teachers=teachers, cuser=current_user)


@app.route('/admin/create_teacher', methods=['GET', 'POST'])
def create_teacher():
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
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
            return render_template('admin/create_teacher.html',reg_code=reg_code, cuser=current_user)

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

    return render_template('admin/create_teacher.html',reg_code=reg_code, cuser=current_user)


@app.route('/admin/teacher<id>/edit', methods=['GET', 'POST'])
def admin_teacher_edit(id):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    teacher = Teacher.get(id=id)

    form = request.form
    if request.method == 'POST' and 'updateForm' in request.form:
        if form.get('inputPassword') != form.get('inputRepassword'):
            flash("Введённые пароли не совпадают!", "warning")
            return render_template('admin/teacher-edit.html', teacher=teacher, cuser=current_user)

        name = form.get('nameInput')
        surname = form.get('surnameInput')
        patronymic = form.get('patronymicInput')
        faculty = form.get('facultyInput')
        department = form.get('departmentInput')
        email = form.get('emailInput')
        password = form.get('inputPassword')

        if name != '':
            teacher.name = name
        if surname != '':
            teacher.surname = surname
        if patronymic != '':
            teacher.patronymic = patronymic
        if faculty != '':
            teacher.faculty = faculty
        if department != '':
            teacher.department = department
        if email != '':
            teacher.email = email
        if password != '':
            teacher.password = generate_password_hash(password)

        flash('Данные преподавателя успешно обновлены!', 'success')



    return render_template('admin/teacher-edit.html', teacher=teacher, cuser=current_user)


@app.route('/admin/teacher<id>/delete', methods=['GET', 'POST'])
def admin_teacher_delete(id):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    teacher = Teacher[id]
    teachers = select(t for t in Teacher if t != teacher)[:]

    if request.method == "POST" and 'delete_all' in request.form:
        attempts = select(a for a in Attempt if a.variant.lab.teacher == teacher)[:]
        for attempt in attempts:
            path = os.path.dirname(attempt.source)
            rmtree(path)
        teacher.delete()
        return redirect(url_for('admin'))

    if request.method == "POST" and 'delete_and_copy' in request.form:
        new_teacher = Teacher[request.form.get('teacher')]
        courses = select(c for c in Course if c.teacher == teacher)[:]
        labs = select(l for l in Lab if l.teacher == teacher)[:]
        for course in courses:
            course.teacher = new_teacher
        for lab in labs:
            lab.teacher = new_teacher
        teacher.delete()
        return redirect(url_for('admin'))

    return render_template('admin/teacher-delete.html', teachers=teachers, current_teacher=teacher, cuser=current_user)


@app.route('/admin/student<id>/edit', methods=['GET', 'POST'])
def admin_student_edit(id):
    if not authorized():
        return redirect(url_for('login'))
    admin = Admin.get(id=current_user.id)
    if not admin:
        return redirect(url_for('login'))

    student = Student.get(id=id)

    groups = []
    query = select(group.code for group in Group)[:]
    for group in query:
        groups.append(group)

    form = request.form
    if request.method == "POST" and 'update' in request.form:
        surname = form.get('surnameInput')
        name = form.get('nameInput')
        patronymic = form.get('patronymicInput')
        login = form.get('loginInput')
        group = form.get('group')
        email = form.get('emailInput')

        if surname == '':
            surname = student.surname
        if name == '':
            name = student.name
        if patronymic == '':
            patronymic = student.patronymic
        if login == '':
            login = student.login
        if email == '':
            email = student.email
        #TODO what to do with existing student labs?
        if group != student.group.code:
            activated = student.activated
            student.delete()
            s = Student(
                surname=surname,
                name=name,
                patronymic=patronymic,
                login=login,
                group=Group.get(code=group),
                email=email,
                activated=activated
            )

        student.surname = surname
        student.name = name
        student.patronymic = patronymic
        student.login = login
        student.email = email

        flash('Данные студента успешно обновлены!', 'success')

    return render_template('admin/student-edit.html', cuser=current_user, student=student, groups=groups)




