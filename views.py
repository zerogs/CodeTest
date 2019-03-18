from app import app
from flask import render_template, request, redirect, url_for
from flask_login import current_user, login_user
from models import db, User
from datetime import datetime
from forms import LoginForm



def authorized():
    if not current_user:
        return False

    try:
        return current_user.is_authenticated()
    except:
        return current_user.is_authenticated


@app.route('/')
@app.route('/index')
def index():
    if authorized():
        return redirect(url_for('index'))

    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        login = form.username.data
        password = form.password.data
        user = User.get(login=login)
        correct = user.check_password(password)
        if correct:
            login_user(user, remember=True, force=True)
            user.last_login = datetime.now()
            return redirect(url_for('index'))

    return render_template('index.html', form=form, title="Login")
