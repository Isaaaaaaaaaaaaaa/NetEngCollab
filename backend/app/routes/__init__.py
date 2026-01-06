from flask import Flask, jsonify


def register_routes(app: Flask):
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .cooperation import bp as cooperation_bp
    from .forum import bp as forum_bp
    from .match import bp as match_bp
    from .messages import bp as messages_bp
    from .notifications import bp as notifications_bp
    from .posts import bp as posts_bp
    from .progress import bp as progress_bp
    from .resources import bp as resources_bp
    from .role_tags import bp as role_tags_bp
    from .teamup import bp as teamup_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(posts_bp, url_prefix="/api")
    app.register_blueprint(resources_bp, url_prefix="/api")
    app.register_blueprint(progress_bp, url_prefix="/api")
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(match_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(cooperation_bp, url_prefix="/api")
    app.register_blueprint(forum_bp, url_prefix="/api")
    app.register_blueprint(teamup_bp, url_prefix="/api")
    app.register_blueprint(role_tags_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})
