from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from pony.flask import Pony
from config import config
from models import db

app = Flask(__name__)
app.config.update(config)
csrf = CSRFProtect(app)
Pony(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.User.get(id=user_id)
