from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Notification, Role, User
from ..services import push_notification, recommend_students_for_teacher, recommend_teacher_posts_for_student


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


@bp.post("/match/check")
@jwt_required()
def check_match_updates():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401

    limit = int(request.args.get("limit") or 5)
    limit = max(1, min(10, limit))

    kind = "none"
    ids = []
    summary = None
    if user.role == Role.student.value:
        kind = "teacher_posts"
        items = recommend_teacher_posts_for_student(user.id, limit=limit)
        ids = [int(x.get("id")) for x in items if x.get("id")]
        names = [str(x.get("title")) for x in items[:3] if x.get("title")]
        summary = "为你更新了项目推荐" + ("：" + "、".join(names) if names else "")
    elif user.role == Role.teacher.value:
        kind = "students"
        items = recommend_students_for_teacher(user.id, limit=limit)
        ids = [int(x.get("user_id")) for x in items if x.get("user_id")]
        names = [str(x.get("display_name")) for x in items[:3] if x.get("display_name")]
        summary = "为你更新了学生推荐" + ("：" + "、".join(names) if names else "")
    else:
        return jsonify({"ok": True, "kind": "none"})

    if not ids:
        return jsonify({"ok": True, "kind": kind})

    last = (
        Notification.query.filter_by(user_id=user.id, notif_type="match_refresh")
        .order_by(Notification.created_at.desc())
        .first()
    )
    last_ids = []
    if last and last.payload_json:
        try:
            import json

            payload = json.loads(last.payload_json)
            last_ids = payload.get("ids") or []
        except Exception:
            last_ids = []

    if list(last_ids) == list(ids):
        return jsonify({"ok": True, "kind": kind})

    push_notification(
        user_id=user.id,
        notif_type="match_refresh",
        title="匹配推荐已更新",
        payload={"kind": kind, "ids": ids, "summary": summary},
    )
    return jsonify({"ok": True, "kind": kind})
