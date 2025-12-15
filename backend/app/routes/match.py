from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Role, User
from ..services import recommend_students_for_teacher, recommend_teacher_posts_for_student


bp = Blueprint("match", __name__)


@bp.get("/match/top")
@jwt_required()
def top_match():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    limit = int(request.args.get("limit") or 10)
    limit = max(1, min(50, limit))

    if user.role == Role.student.value:
        items = recommend_teacher_posts_for_student(user.id, limit=limit)
        return jsonify({"items": items, "kind": "teacher_posts"})
    if user.role == Role.teacher.value:
        items = recommend_students_for_teacher(user.id, limit=limit)
        return jsonify({"items": items, "kind": "students"})
    return jsonify({"items": [], "kind": "none"})

