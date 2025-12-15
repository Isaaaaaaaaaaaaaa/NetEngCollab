from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Role, StudentProfile, TeacherProfile, User
from ..utils import hash_password, now_utc, verify_password


bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role")
    display_name = (data.get("display_name") or username).strip()
    email = (data.get("email") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None

    if not username or not password or role not in {r.value for r in Role}:
        return jsonify({"message": "参数不完整"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "账号已存在"}), 409

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        display_name=display_name,
        email=email,
        phone=phone,
        is_active=True,
        created_at=now_utc(),
    )
    db.session.add(user)
    db.session.flush()

    if role == Role.student.value:
        db.session.add(StudentProfile(user_id=user.id, updated_at=now_utc()))
    if role == Role.teacher.value:
        db.session.add(TeacherProfile(user_id=user.id, updated_at=now_utc()))

    db.session.commit()
    return jsonify({"id": user.id, "is_active": user.is_active})


@bp.post("/login")
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role")

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"message": "账号或密码错误"}), 401
    if role and role != user.role:
        return jsonify({"message": "角色不匹配"}), 401
    if not user.is_active:
        return jsonify({"message": "账号未启用/待审核"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify(
        {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name,
            },
        }
    )


@bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
        }
    )
