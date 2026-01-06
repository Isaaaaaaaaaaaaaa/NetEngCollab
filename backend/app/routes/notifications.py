import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Notification, User


bp = Blueprint("notifications", __name__)


@bp.get("/notifications")
@jwt_required()
def list_notifications():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 30))
    if page_size <= 0 or page_size > 100:
        page_size = 30

    q = Notification.query.filter_by(user_id=user.id)
    total = q.count()
    ns = (
        q.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": n.id,
                    "notif_type": n.notif_type,
                    "title": n.title,
                    "payload": json.loads(n.payload_json or "{}"),
                    "payload_json": n.payload_json or "{}",
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in ns
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": total > page * page_size,
        }
    )


@bp.post("/notifications/<int:notif_id>/read")
@jwt_required()
def mark_read(notif_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    n = Notification.query.get(notif_id)
    if not n or n.user_id != user.id:
        return jsonify({"message": "不存在"}), 404
    n.is_read = True
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/notifications/read-all")
@jwt_required()
def mark_all_read():
    """标记所有通知为已读"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/notifications/unread-count")
@jwt_required()
def get_unread_count():
    """获取未读通知数量"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"count": count})
