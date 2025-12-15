from app import create_app
from app.extensions import db
from app.models import Role, User
from app.utils import hash_password, now_utc


def setup_app():
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
    return app


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_basic_student_teacher_post_and_apply_flow():
    app = setup_app()
    client = app.test_client()

    resp = client.post(
        "/api/auth/register",
        json={
            "username": "t1",
            "password": "123456",
            "role": Role.teacher.value,
            "display_name": "李老师",
        },
    )
    assert resp.status_code == 200
    teacher_id = resp.get_json()["id"]

    resp = client.post(
        "/api/auth/register",
        json={
            "username": "s1",
            "password": "123456",
            "role": Role.student.value,
            "display_name": "王同学",
        },
    )
    assert resp.status_code == 200
    student_id = resp.get_json()["id"]

    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123", "role": Role.admin.value},
    )
    assert resp.status_code == 200
    admin_token = resp.get_json()["access_token"]

    resp = client.post(
        "/api/auth/login",
        json={"username": "t1", "password": "123456", "role": Role.teacher.value},
    )
    assert resp.status_code == 200
    teacher_token = resp.get_json()["access_token"]

    resp = client.post(
        "/api/teacher-posts",
        json={
            "title": "网络安全科研项目",
            "content": "研究入侵检测",
            "post_type": "project",
            "tech_stack": ["Python", "深度学习"],
            "tags": ["网络安全"],
        },
        headers=auth_headers(teacher_token),
    )
    assert resp.status_code == 200
    post_id = resp.get_json()["id"]

    resp = client.post(
        "/api/auth/login",
        json={"username": "s1", "password": "123456", "role": Role.student.value},
    )
    assert resp.status_code == 200
    student_token = resp.get_json()["access_token"]

    resp = client.get("/api/teacher-posts", headers=auth_headers(student_token))
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert any(i["id"] == post_id for i in items)

    resp = client.post(
        "/api/cooperation/request",
        json={"post_id": post_id, "student_user_id": student_id},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 200
    req_id = resp.get_json()["id"]

    resp = client.post(
        "/api/cooperation/requests/%d/respond" % req_id,
        json={"action": "accept"},
        headers=auth_headers(teacher_token),
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/cooperation/requests/%d/respond" % req_id,
        json={"action": "accept"},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["final_status"] == "confirmed"

    resp = client.get("/api/cooperation/projects", headers=auth_headers(student_token))
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) == 1
