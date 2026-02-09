from flask import Flask

from .api.routes import api_bp
from .infrastructure.db import init_db


def create_app() -> Flask:
    app = Flask(__name__)

    # Инициализация БД (создание таблиц при первом запуске)
    init_db()

    # Register blueprints
    app.register_blueprint(api_bp)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


    