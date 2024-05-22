from flask import Flask
from config import Config
from flask_login import LoginManager
from app.models import User
import datetime

login = LoginManager()
login.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login.init_app(app)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @login.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
        return datetime.datetime.fromtimestamp(value).strftime(format)

    return app
