import os

from flask import Flask
from sqlalchemy import text

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
        _ensure_schema()

    return app


def _ensure_schema():
    engine = db.engine
    dialect = engine.dialect.name

    def _exec(stmt, params=None):
        with engine.begin() as conn:
            return conn.execute(text(stmt), params or {})

    def has_column_sqlite(table: str, column: str) -> bool:
        rows = _exec(f"PRAGMA table_info({table})").mappings().all()
        return any(r.get("name") == column for r in rows)

    def has_column_mysql(table: str, column: str) -> bool:
        rows = _exec(
            """
            SELECT 1
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            LIMIT 1
            """,
            {"table": table, "column": column},
        ).all()
        return bool(rows)

    def ensure_comments_parent_comment_id():
        table = "comments"
        column = "parent_comment_id"

        if dialect == "sqlite":
            if has_column_sqlite(table, column):
                return
            _exec(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER")
            return

        if dialect in {"mysql", "mariadb"}:
            if has_column_mysql(table, column):
                return
            _exec(f"ALTER TABLE {table} ADD COLUMN {column} INT NULL")
            return

    def ensure_student_profiles_experiences_json():
        table = "student_profiles"
        column = "experiences_json"

        if dialect == "sqlite":
            if has_column_sqlite(table, column):
                return
            _exec(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
            return

        if dialect in {"mysql", "mariadb"}:
            if has_column_mysql(table, column):
                return
            _exec(f"ALTER TABLE {table} ADD COLUMN {column} TEXT NULL")
            return

    def ensure_student_profiles_basic_info():
        table = "student_profiles"

        def ensure_column(col: str, sqlite_type: str, mysql_type: str):
            if dialect == "sqlite":
                if has_column_sqlite(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {sqlite_type}")
                return

            if dialect in {"mysql", "mariadb"}:
                if has_column_mysql(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {mysql_type} NULL")
                return

        ensure_column("major", "TEXT", "VARCHAR(128)")
        ensure_column("grade", "TEXT", "VARCHAR(32)")
        ensure_column("class_name", "TEXT", "VARCHAR(64)")

    def ensure_student_profiles_resume_and_auto_reply():
        table = "student_profiles"

        def ensure_column(col: str, sqlite_type: str, mysql_type: str):
            if dialect == "sqlite":
                if has_column_sqlite(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {sqlite_type}")
                return

            if dialect in {"mysql", "mariadb"}:
                if has_column_mysql(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {mysql_type} NULL")
                return

        ensure_column("resume_file_id", "INTEGER", "INT")
        ensure_column("auto_reply", "TEXT", "VARCHAR(255)")

    def ensure_teacher_profiles_auto_reply_and_basic():
        table = "teacher_profiles"

        def ensure_column(col: str, sqlite_type: str, mysql_type: str):
            if dialect == "sqlite":
                if has_column_sqlite(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {sqlite_type}")
                return

            if dialect in {"mysql", "mariadb"}:
                if has_column_mysql(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {mysql_type} NULL")
                return

        ensure_column("title", "TEXT", "VARCHAR(64)")
        ensure_column("organization", "TEXT", "VARCHAR(128)")
        ensure_column("bio", "TEXT", "TEXT")
        ensure_column("research_tags_json", "TEXT", "TEXT")
        ensure_column("auto_reply", "TEXT", "VARCHAR(255)")

    def ensure_users_force_password_change():
        table = "users"

        def ensure_column(col: str, sqlite_type: str, mysql_type: str):
            if dialect == "sqlite":
                if has_column_sqlite(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {sqlite_type}")
                return

            if dialect in {"mysql", "mariadb"}:
                if has_column_mysql(table, col):
                    return
                _exec(f"ALTER TABLE {table} ADD COLUMN {col} {mysql_type} NOT NULL DEFAULT 0")
                return

        ensure_column("must_change_password", "INTEGER", "TINYINT(1)")

    try:
        ensure_comments_parent_comment_id()
    except Exception:
        pass

    try:
        ensure_student_profiles_experiences_json()
    except Exception:
        pass

    try:
        ensure_student_profiles_basic_info()
    except Exception:
        pass

    try:
        ensure_student_profiles_resume_and_auto_reply()
    except Exception:
        pass

    try:
        ensure_teacher_profiles_auto_reply_and_basic()
    except Exception:
        pass

    try:
        ensure_users_force_password_change()
    except Exception:
        pass
