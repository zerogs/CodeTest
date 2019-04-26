from datetime import datetime
from pony.orm import *
from werkzeug.security import generate_password_hash, check_password_hash

db = Database()


class Lab(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    groups = Set('Group')
    teacher = Required('Teacher')
    courses = Set('Course')
    variants = Set('Variant')


class Variant(db.Entity):
    id = PrimaryKey(int, auto=True)
    number = Required(int)
    title = Required(str)
    description = Required(LongStr)
    lab = Required(Lab)
    student = Optional('Student')
    tests = Set('Test')
    attempts = Set('Attempt')


class Test(db.Entity):
    id = PrimaryKey(int, auto=True)
    input = Required(str)
    output = Required(str)
    variant = Required(Variant)


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    surname = Required(str)
    name = Required(str)
    patronymic = Required(str)
    login = Optional(str)
    password = Optional(str)
    email = Optional(str)
    password_resets = Set('PasswordReset')
    reg_code = Required(str)
    activated = Required(bool)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @staticmethod
    def generate_password(password):
        return generate_password_hash(password)

    def check_password(self, given_password):
        return check_password_hash(self.password, given_password)


class Student(User):
    variants = Set(Variant)
    group = Required('Group')


class Teacher(User):
    labs = Set(Lab)
    courses = Set('Course')
    faculty = Optional(str)
    department = Optional(str)


class Attempt(db.Entity):
    id = PrimaryKey(int, auto=True)
    variant = Required(Variant)
    dt = Required(datetime)
    result = Optional(str)
    source = Optional(str)
    language = Optional(str)


class PasswordReset(db.Entity):
    id = PrimaryKey(int, auto=True)
    dt = Required(datetime)
    user = Required(User)
    email = Optional(str)
    approve = Optional(bool)


class Group(db.Entity):
    id = PrimaryKey(int, auto=True)
    code = Required(str)
    students = Set(Student)
    courses = Set('Course')
    labs = Set(Lab)


class Course(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    groups = Set(Group)
    labs = Set(Lab)
    teacher = Required(Teacher)


class Admin(User):
    is_admin = Required(bool)
