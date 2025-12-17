from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Conversation, File, Message, Role, StudentProfile, TeacherProfile, User
from ..utils import now_utc
from ..services import push_notification


bp = Blueprint("messages", __name__)


@bp.get("/messages/auto-reply")
@jwt_required()
def get_auto_reply():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    if user.role == Role.student.value:
        p = StudentProfile.query.get(user.id)
        return jsonify({"auto_reply": (p.auto_reply if p else None)})
    if user.role == Role.teacher.value:
        p = TeacherProfile.query.get(user.id)
        return jsonify({"auto_reply": (p.auto_reply if p else None)})
    return jsonify({"auto_reply": None})


@bp.put("/messages/auto-reply")
@jwt_required()
def set_auto_reply():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    auto_reply = (data.get("auto_reply") or "").strip() or None
    if user.role == Role.student.value:
        p = StudentProfile.query.get(user.id)
        if not p:
            p = StudentProfile(user_id=user.id, updated_at=now_utc())
            db.session.add(p)
        p.auto_reply = auto_reply
        p.updated_at = now_utc()
        db.session.commit()
        return jsonify({"ok": True})
    if user.role == Role.teacher.value:
        p = TeacherProfile.query.get(user.id)
        if not p:
            p = TeacherProfile(user_id=user.id, updated_at=now_utc())
            db.session.add(p)
        p.auto_reply = auto_reply
        p.updated_at = now_utc()
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"message": "无权限"}), 403


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
    elif user.role == Role.admin.value:
        convs = (
            Conversation.query.filter(or_(Conversation.teacher_user_id == user.id, Conversation.student_user_id == user.id))
            .order_by(Conversation.created_at.desc())
            .all()
        )
    else:
        convs = []
    items = []
    for c in convs:
        other_id = c.student_user_id if c.teacher_user_id == user.id else c.teacher_user_id
        other = User.query.get(other_id)
        unread = Message.query.filter_by(conversation_id=c.id, is_read=False).filter(Message.sender_user_id != user.id).count()
        last = Message.query.filter_by(conversation_id=c.id).order_by(Message.created_at.desc()).first()
        items.append(
            {
                "id": c.id,
                "teacher_user_id": c.teacher_user_id,
                "student_user_id": c.student_user_id,
                "other": {"id": other.id, "display_name": other.display_name, "role": other.role} if other else None,
                "unread": unread,
                "last_message": last.content if last and last.content else ("[文件]" if last and last.file_id else None),
                "last_at": last.created_at.isoformat() if last else c.created_at.isoformat(),
            }
        )
    items.sort(key=lambda x: x.get("last_at") or "", reverse=True)
    return jsonify({"items": items})


@bp.post("/conversations/start")
@jwt_required()
def start_conversation():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    if user.role != Role.admin.value:
        return jsonify({"message": "无权限"}), 403
    data = request.get_json(force=True)
    target_user_id = data.get("user_id")
    if not target_user_id or not str(target_user_id).isdigit():
        return jsonify({"message": "参数不完整"}), 400
    target = User.query.get(int(target_user_id))
    if not target or not target.is_active:
        return jsonify({"message": "用户不存在"}), 404

    if target.role == Role.student.value:
        teacher_user_id = user.id
        student_user_id = target.id
    else:
        teacher_user_id = target.id
        student_user_id = user.id

    c = _ensure_pair(int(teacher_user_id), int(student_user_id))
    return jsonify({"id": c.id})


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
    items = []
    for m in msgs:
        f = File.query.get(m.file_id) if m.file_id else None
        items.append(
            {
                "id": m.id,
                "sender_user_id": m.sender_user_id,
                "content": m.content,
                "file_id": m.file_id,
                "file": {
                    "id": f.id,
                    "original_name": f.original_name,
                    "size_bytes": f.size_bytes,
                }
                if f
                else None,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat(),
            }
        )
    return jsonify({"items": items})


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
    now = now_utc()
    m = Message(
        conversation_id=c.id,
        sender_user_id=user.id,
        content=content,
        file_id=int(file_id) if file_id else None,
        is_read=False,
        created_at=now,
    )
    db.session.add(m)
    db.session.commit()

    other_id = int(student_user_id) if user.id == int(teacher_user_id) else int(teacher_user_id)

    summary = f"来自 {user.display_name} 的私信"
    if content:
        summary = f"{summary}：{content[:60]}"
    elif file_id:
        f = File.query.get(int(file_id))
        name = f.original_name if f and f.original_name else "文件"
        summary = f"{summary}：[{name}]"
    push_notification(
        user_id=other_id,
        notif_type="message_new",
        title="收到新的私信",
        payload={"conversation_id": c.id, "from_user_id": user.id, "summary": summary},
    )
    auto_reply_text = None
    if other_id == int(student_user_id):
        p = StudentProfile.query.get(other_id)
        auto_reply_text = (p.auto_reply or "").strip() if p else ""
    else:
        p = TeacherProfile.query.get(other_id)
        auto_reply_text = (p.auto_reply or "").strip() if p else ""

    if auto_reply_text:
        last_from_other = (
            Message.query.filter_by(conversation_id=c.id, sender_user_id=other_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        if (not last_from_other) or (now - last_from_other.created_at > timedelta(hours=12)):
            auto_reply_content = auto_reply_text
            if not auto_reply_content.startswith("【自动回复】"):
                auto_reply_content = f"【自动回复】{auto_reply_content}"
            db.session.add(
                Message(
                    conversation_id=c.id,
                    sender_user_id=other_id,
                    content=auto_reply_content,
                    file_id=None,
                    is_read=False,
                    created_at=now_utc(),
                )
            )
            db.session.commit()
    return jsonify({"id": m.id})
