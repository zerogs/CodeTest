from app import app
from flask import render_template, request
from forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    form = LoginForm(request.form)
    return render_template("index.html",form=form ,title="Авторизация")

db = 'eee'