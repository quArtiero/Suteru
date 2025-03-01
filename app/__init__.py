from flask import Flask
from flask_mail import Mail
from app.config import Config
from app.utils.database import get_user_role

mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    mail.init_app(app)

    from app.routes import admin, auth, main, quiz
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(quiz.bp)

    # Registrando funções globais para os templates
    app.jinja_env.globals.update(get_user_role=get_user_role)

    return app
