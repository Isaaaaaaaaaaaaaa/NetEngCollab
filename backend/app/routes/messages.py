from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Conversation, Message, Role, User
from ..utils import now_utc


bp = Blueprint("messages", __name__)


def _ensure_pair(teacher_user_id: int, student_user_id: int) -> Conversation:
    c = Conversation.query.filter_by(teacher_user_id=teacher_user_id, student_user_id=student_user_id).first()
    if c:
        return c
    c = Conversation(teacher_user_id=teacher_user_id, student_user_id=student_user_id, created_at=now_utc())
    db.session.add(c)
    db.session.commit()
    return c


@bp.get("/conversations")
@jwt_required()
def list_conversations():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    if user.role == Role.teacher.value:
        convs = Conversation.query.filter_by(teacher_user_id=user.id).order_by(Conversation.created_at.desc()).all()
    elif user.role == Role.student.value:
        convs = Conversation.query.filter_by(student_user_id=user.id).order_by(Conversation.created_at.desc()).all()
    else:
        convs = []
    items = []
    for c in convs:
        other_id = c.student_user_id if user.role == Role.teacher.value else c.teacher_user_id
        other = User.query.get(other_id)
        unread = Message.query.filter_by(conversation_id=c.id, is_read=False).filter(Message.sender_user_id != user.id).count()
        items.append(
            {
                "id": c.id,
                "other": {"id": other.id, "display_name": other.display_name, "role": other.role} if other else None,
                "unread": unread,
            }
        )
    return jsonify({"items": items})


@bp.get("/conversations/<int:conversation_id>/messages")
@jwt_required()
def list_messages(conversation_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    c = Conversation.query.get(conversation_id)
    if not c or user.id not in {c.teacher_user_id, c.student_user_id}:
        return jsonify({"message": "无权限"}), 403
    msgs = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).limit(500).all()
    for m in msgs:
        if m.sender_user_id != user.id:
            m.is_read = True
    db.session.commit()
    return jsonify(
        {
            "items": [
                {
                    "id": m.id,
                    "sender_user_id": m.sender_user_id,
                    "content": m.content,
                    "file_id": m.file_id,
                    "is_read": m.is_read,
                    "created_at": m.created_at.isoformat(),
                }
                for m in msgs
            ]
        }
    )


@bp.post("/messages/send")
@jwt_required()
def send_message():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    teacher_user_id = data.get("teacher_user_id")
    student_user_id = data.get("student_user_id")
    content = (data.get("content") or "").strip() or None
    file_id = data.get("file_id")
    if not teacher_user_id or not student_user_id or (not content and not file_id):
        return jsonify({"message": "参数不完整"}), 400

    if user.id not in {int(teacher_user_id), int(student_user_id)}:
        return jsonify({"message": "无权限"}), 403

    c = _ensure_pair(int(teacher_user_id), int(student_user_id))
    m = Message(
        conversation_id=c.id,
        sender_user_id=user.id,
        content=content,
        file_id=int(file_id) if file_id else None,
        is_read=False,
        created_at=now_utc(),
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({"id": m.id})

