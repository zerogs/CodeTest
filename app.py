from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from pony.flask import Pony
from config import config
from models import db
from flask_uploads import configure_uploads, UploadSet, DATA, SCRIPTS, patch_request_class
app = Flask(__name__)
app.config.update(config)
csrf = CSRFProtect(app)
csrf.init_app(app)
Pony(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
patch_request_class(app)
group_lists = UploadSet("data", DATA)
programs = UploadSet("programs", SCRIPTS)
configure_uploads(app, group_lists)
configure_uploads(app, programs)

@login_manager.user_loader
def load_user(user_id):
    return db.User.get(id=user_id)
