from app import create_app


def create_client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health_ok():
    client = create_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_login_seed_accounts():
    from app.extensions import db
    from app.models import Role, User
    from app.utils import hash_password, now_utc

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role=Role.admin.value,
            display_name="管理员",
            is_active=True,
            created_at=now_utc(),
        )
        db.session.add(admin)
        db.session.commit()

        client = app.test_client()
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123", "role": Role.admin.value},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == Role.admin.value
        assert data["access_token"]

