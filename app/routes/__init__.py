from app.routes.admin import bp as admin_bp
from app.routes.auth import bp as auth_bp
from app.routes.main import bp as main_bp
from app.routes.quiz import bp as quiz_bp

__all__ = ['admin_bp', 'auth_bp', 'main_bp', 'quiz_bp']
