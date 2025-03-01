import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    SQLALCHEMY_DATABASE_URI = os.environ.get('internal_db_url', 'sqlite:///dev.db')
    
    # Configurações do Flask-Mail
    MAIL_SERVER = "smtp.seu_servidor.com"
    MAIL_PORT = 587
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # Configurações de upload
    ALLOWED_EXTENSIONS = {"csv"}
