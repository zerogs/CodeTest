from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from pony.flask import Pony
from config import config
from models import db
from flask_uploads import configure_uploads, UploadSet, DATA, SCRIPTS, patch_request_class
from test_daemon import daemon_start

app = Flask(__name__)
app.config.update(config)
csrf = CSRFProtect(app)
csrf.init_app(app)
Pony(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
patch_request_class(app)
ALLOWED_EXTENSIONS = set(['py', 'cpp', 'c'])
group_lists = UploadSet("data", DATA)
configure_uploads(app, group_lists)
daemon_start()

@login_manager.user_loader
def load_user(user_id):
    return db.User.get(id=user_id)
