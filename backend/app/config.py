import os

from dotenv import load_dotenv


def load_config(app):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(repo_root, ".env"))
    load_dotenv(os.path.join(repo_root, "backend", ".env"))
    load_dotenv()

    env = os.getenv("FLASK_ENV", "development")

    app.config["ENV"] = env
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = f"sqlite:///{os.path.join(app.instance_path, 'app.sqlite3')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "7200"))

    app.config["CORS_ORIGINS"] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    storage_dir = os.getenv("STORAGE_DIR")
    if not storage_dir:
        storage_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
    app.config["STORAGE_DIR"] = os.path.abspath(storage_dir)
    os.makedirs(app.config["STORAGE_DIR"], exist_ok=True)
