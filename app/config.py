import os

class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['internal_db_url']
    
    # Configurações do Flask-Mail
    MAIL_SERVER = "smtp.seu_servidor.com"
    MAIL_PORT = 587
    MAIL_USERNAME = os.environ['MAIL_USERNAME']
    MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # Configurações de upload
    ALLOWED_EXTENSIONS = {"csv"}
