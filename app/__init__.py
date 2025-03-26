from flask import Flask
from flask_mail import Mail
from app.config import Config
from app.utils.database import get_user_role
from flask_talisman import Talisman

mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Add security headers
    Talisman(app, 
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", 'code.jquery.com', 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'stackpath.bootstrapcdn.com', 'fonts.googleapis.com', 'cdnjs.cloudflare.com', 'use.fontawesome.com'],
            'font-src': ["'self'", 'fonts.gstatic.com', 'use.fontawesome.com', 'cdnjs.cloudflare.com'],
            'img-src': ["'self'", 'data:', 'https:'],
            'connect-src': ["'self'", 'https:'],
        },
        force_https=False  # Desabilita HTTPS forçado para desenvolvimento local
    )

    mail.init_app(app)

    from app.routes import admin, auth, main, quiz
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(quiz.bp)

    # Registrando funções globais para os templates
    app.jinja_env.globals.update(get_user_role=get_user_role)

    return app

# Create an application instance for Gunicorn
app = create_app()
