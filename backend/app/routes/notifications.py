import json

from flask import Blueprint, jsonify
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
    ns = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify(
        {
            "items": [
                {
                    "id": n.id,
                    "notif_type": n.notif_type,
                    "title": n.title,
                    "payload": json.loads(n.payload_json or "{}"),
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in ns
            ]
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

