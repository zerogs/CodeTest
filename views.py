from app import app, group_lists, programs
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from models import db, Admin,User, Teacher, Student, Variant, Group, Course, Lab, Test, generate_password_hash
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


@app.route('/teacher-<tid>/create_course/', methods=['GET', 'POST'])
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


@app.route('/teacher-<teacherid>/course_edit/<courseid>', methods=['GET', 'POST'])
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

    return render_template('teacher/course-item.html',teacher=teacher, show=show, course=course, groups=groups, cg=cg)

@app.route('/teacher-<id>/courses/', methods=['GET', 'POST'])
def course_list(id):
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


@app.route('/teacher-<id>/course_delete/<cid>', methods=['GET', 'POST'])
def course_delete(id, cid):
    if current_user.id != int(id):
        return redirect(url_for("login"))
    course = Course.get(id=cid)
    course.delete()

    return redirect(url_for('course_list', id=id))



@app.route('/teacher-<id>/create_lab/', methods=['GET', 'POST'])
def create_lab(id):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    show = isinstance(current_user, Admin)

    allcourses = select(c.title for c in Course if c.teacher == teacher)[:]
    allgroups = []
    for course in allcourses:
        for group in Course.get(title=course).groups:
            if group.code not in allgroups:
                allgroups.append(group.code)

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
                if g not in c.groups:
                    flash('Группа ' + g.code + ' не записана на предмет ' + c.title + '! Группа не будет привязана к данной лабораторной работе.', "warning")
                l.groups.add(g)


        flash("Лабораторная работа " + title +  " создана!", "success")

    return render_template('teacher/lab-creation.html',teacher=teacher, show=show, courses=allcourses, groups=allgroups)


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
            if group in course.groups:
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
        sc = ''

    return render_template('teacher/labs.html',group_list=False, labs=out, teacher=teacher, course=course)


@app.route('/teacher-<tid>/lab-<lid>/edit', methods=['GET', 'POST'])
def lab_edit(tid, lid):
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=tid)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))
    show = isinstance(current_user, Admin)

    lab = Lab.get(id=lid)

    lg = lab.groups
    groups = []
    gquery = select(group.code for group in Group)[:]
    for group in gquery:
        groups.append(group)

    lc = lab.courses
    courses = []

    cquery = select(course.title for course in Course)[:]
    for course in cquery:
        courses.append(course)
    form = request.form

    if request.method == "POST" and 'update' in request.form:
        title = form.get('titleInput')

        if title == '':
            title = lab.title

        group_codes = form.getlist('group[]')
        try:
            group_codes.remove('Группа')
        except ValueError:
            pass

        course_titles = form.getlist('course[]')
        try:
            course_titles.remove('Предмет')
        except ValueError:
            pass

        lab.title = title
        missing = False
        for c in lc:
            if c.title not in course_titles:
                lab.courses.remove(c)
        for c in course_titles:
            crs =  Course.get(title=c)
            if crs not in lc:
                lab.courses.add(crs)


        for g in lg:
            if g.code not in group_codes:
                lab.groups.remove(g)
        for code in group_codes:
            g = Group.get(code=code)
            if g not in lg:
                for c in lc:
                    if g not in c.groups:
                        missing = True
                    else:
                        missing = False
                        break
                if missing:
                    flash('Группа ' + g.code + " не записана на один из курсов где используется лабораторная работа!",
                          "warning")
                    return render_template('teacher/lab-item.html', lab=lab, lg=lg, lc=lc, courses=courses,
                                           groups=groups, teacher=teacher)
                else:
                    lab.groups.add(g)

        flash('Данные успешно обновлены!', 'success')

    return render_template('teacher/lab-item.html', lab=lab, lg=lg, lc=lc, courses=courses, groups=groups, teacher=teacher)


@app.route('/teacher-<id>/course-<cid>/lab-<lid>/delete', methods=['GET', 'POST'])
def lab_delete(id, cid, lid):
    if current_user.id != int(id):
        return redirect(url_for("login"))
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
    if teacher.id != current_user.id:
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

    return render_template('teacher/lab-add-to-course.html', labs=labs, teacher=teacher)

@app.route('/teacher-<id>/group<code>/course-<cid>/labs', methods=['GET', 'POST'])
def group_labs_list(id, cid, code):
    group_list = True
    if not authorized():
        return redirect(url_for('login'))
    teacher = User.get(id=id)
    if teacher.id != current_user.id:
        return redirect(url_for('login'))

    group = Group.get(code=code)
    course = Course.get(id=cid)

    labs = select(g.labs for g in Group if g.code == code)

    out = []
    s = ''
    sc = ''
    for lab in labs:
        out.append((lab.id, lab.title, sc, s))
        s = ''

    return render_template('teacher/labs.html',group_list=group_list,group=group, labs=out, teacher=teacher, course=course)


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
                if i == '#' or v == '#':
                    continue
                else:
                    if i.split(',')[1] == v.split(',')[1]:
                        equalvars.add(i)
                        equalvars.add(v)
        if len(equalvars) != 0:
            flash('Один и тот же вариант выдан нескольким студентам!', 'warning')
            return render_template('teacher/variant-dist.html', lab=lab, group=group, course=course, students=studvars,
                                   vars=vars, teacher=teacher)

        for item in variants:
            if item != '#':
                item = item.split(',')
                stud = Student.get(id=item[0])
                var = Variant.get(number=item[1], lab=lab)
                if var not in stud.variants:
                    var.student = stud
        flash("Данные успешно обновлены!", "success")


    return render_template('teacher/variant-dist.html',lab=lab, group=group, course=course, students=studvars, vars=vars, teacher=teacher)


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

    return render_template('teacher/variants.html', lab=lab, variants=variants, teacher=teacher, course=course)


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
                return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)
        if Variant.get(number=number, lab=lab):
            flash('Вариант с введённым номером уже существует!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)
        if number == '':
            flash('Не задан номер варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)
        if title == '':
            flash('Не указано название варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)
        if description == '':
            flash('Не указано описания варианта!', 'warning')
            return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)

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

    return render_template('teacher/variant-creation.html', lab=lab, data=data, teacher=teacher)


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

    return render_template('teacher/variant-item.html', teacher=teacher, lab=lab, var=var)


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

    return render_template('teacher/tests.html',cid=cid, teacher=teacher, lab=lab, var=var)


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

    return render_template('teacher/test-creation.html', teacher=teacher, lab=lab, var=var)

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

    return render_template('teacher/test-item.html', teacher=teacher, lab=lab, var=var, test=test)


@app.route('/teacher-<tid>/course-<cid>/lab-<lid>/variant-<vid>/test-<tsid>/delete', methods=['GET', 'POST'])
def test_delete(tid, cid, lid, vid, tsid):
    if current_user.id != int(tid):
        return redirect(url_for("login"))
    test = Test.get(id=tsid)
    test.delete()

    return redirect(url_for('test_list', tid=tid, cid=cid, lid=lid, vid=vid))


@app.route('/group_create/', methods=['GET', 'POST'])
def group_create():
    if not authorized() and not isinstance(current_user, Admin):
        return redirect(url_for('login'))

    form = request.form
    if request.method == 'POST' and 'groupList' in request.files:
        filename = group_lists.save(request.files['groupList'])
        group_code = form.get("groupCodeInput")

        if group_code == '':
            flash("Укажите название группы!", "warning")
            return render_template("admin/group-create.html", teacher=current_user)

        if Group.get(code=group_code) is None:
            pass
        else:
            flash("Группа с таким номером уже существует!", "danger")
            return render_template("admin/group-create.html", teacher=current_user)

        try:
            with open(filename) as obj:
                lst = csv_reader(obj)
        except IOError:
            flash("Ошибка чтения файла!", "danger")
            return render_template("admin/group-create.html", teacher=current_user)
        except KeyError:
            flash("Неверная структура файла!", "danger")
            return render_template("admin/group-create.html", teacher=current_user)

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

    return render_template("admin/group-create.html", teacher=current_user)


@app.route('/teacher-<tid>/groups', methods=['GET', 'POST'] )
def group_list(tid):
    if not authorized() and not isinstance(current_user, Teacher):
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
            cs.append((course.title, course.id))
        cs = sorted(cs)
        out.append((group.id, group.code, cs))
        cs = []

    out = sorted(out)

    return render_template('teacher/groups.html', teacher=teacher, groups=out)


@app.route('/group-<gid>/students', methods=['GET', 'POST'])
def student_list(gid):
    if not authorized() and not (isinstance(current_user, Admin) or isinstance(current_user, Teacher)):
        return redirect(url_for('login'))

    group = Group.get(id=gid)
    students = group.students

    students = sorted(students, key=lambda stud: stud.surname + stud.name)

    return render_template('teacher/students.html', teacher=current_user, group=group, students=students)


@app.route('/admin/student-<sid>/edit', methods=['GET', 'POST'])
def student_edit(sid):
    if not authorized() and not isinstance(current_user, Admin):
        return redirect(url_for('login'))

    student = Student.get(id=sid)

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

    return render_template('admin/student-item.html', teacher=current_user, student=student, groups=groups)



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def login():
    if authorized():
        if Teacher.get(id=current_user.id):
            return redirect(url_for('course_list', id=current_user.id))
        if Student.get(id=current_user.id):
            return redirect(url_for('student'))
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
    if not authorized() and not isinstance(current_user, Admin):
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


@app.route('/student')
def student():
    return render_template('student/index.html')
