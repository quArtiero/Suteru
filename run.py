from app import create_app

app = create_app()

if __name__ == '__main__':
    # Usar configurações de debug apenas em desenvolvimento
    debug_mode = app.config.get('DEBUG', False)
    app.run(debug=debug_mode, port=5001)
