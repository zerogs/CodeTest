from datetime import datetime
from pony.orm import *


db = Database()


class Lab(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    groups = Set('Group')
    teacher = Required('Teacher')
    course = Required('Course')
    variants = Set('Variant')


class Variant(db.Entity):
    id = PrimaryKey(int)
    number = Required(int)
    description = Required(LongStr)
    lab = Required(Lab)
    student = Required('Student')
    tests = Set('Test')
    attempts = Set('Attempt')


class Test(db.Entity):
    id = PrimaryKey(int)
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


class Student(User):
    variants = Set(Variant)
    group = Required('Group')


class Teacher(User):
    labs = Set(Lab)
    courses = Set('Course')


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
    students = Set(Student)
    courses = Set('Course')
    labs = Set(Lab)


class Course(db.Entity):
    id = PrimaryKey(int, auto=True)
    groups = Set(Group)
    labs = Set(Lab)
    teacher = Required(Teacher)
