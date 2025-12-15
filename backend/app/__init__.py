import os

from flask import Flask

from .config import load_config
from .extensions import cors, db, jwt
from .routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)
    load_config(app)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS")}})

    register_routes(app)

    with app.app_context():
        db.create_all()

    return app
