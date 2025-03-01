from app import create_app

application = create_app()
app = application  # For Gunicorn

if __name__ == "__main__":
    application.run() 