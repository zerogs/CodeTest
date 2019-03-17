from flask import Flask
from flask_login import LoginManager
from pony.flask import Pony

app = Flask(__name__)

Pony(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

