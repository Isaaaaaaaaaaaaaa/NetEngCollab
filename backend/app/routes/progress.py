from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CooperationProject, CooperationRequest, Milestone, ProgressUpdate, Role, User
from ..utils import now_utc


bp = Blueprint("progress", __name__)


def _project_and_request(project_id: int):
    p = CooperationProject.query.get(project_id)
    if not p:
        return None, None
    r = CooperationRequest.query.get(p.request_id)
    return p, r


def _ensure_member(user: User, r: CooperationRequest) -> bool:
    return user.id in {r.teacher_user_id, r.student_user_id} or user.role == Role.admin.value


@bp.get("/projects/<int:project_id>/milestones")
@jwt_required()
def list_milestones(project_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p, r = _project_and_request(project_id)
    if not p or not r or not _ensure_member(user, r):
        return jsonify({"message": "无权限"}), 403
    ms = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.created_at.asc()).all()
    now = now_utc()
    return jsonify(
        {
            "items": [
                {
                    "id": m.id,
                    "title": m.title,
                    "due_date": m.due_date.isoformat() if m.due_date else None,
                    "status": m.status,
                    "is_near_due": bool(
                        m.due_date
                        and m.status != "done"
                        and m.due_date >= now
                        and m.due_date - now <= timedelta(days=3)
                    ),
                }
                for m in ms
            ]
        }
    )


@bp.post("/projects/<int:project_id>/milestones")
@jwt_required()
def add_milestone(project_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p, r = _project_and_request(project_id)
    if not p or not r or not _ensure_member(user, r):
        return jsonify({"message": "无权限"}), 403
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"message": "参数不完整"}), 400
    due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    m = Milestone(project_id=project_id, title=title, due_date=due_date, status=(data.get("status") or "todo"), created_at=now_utc())
    db.session.add(m)
    db.session.commit()
    return jsonify({"id": m.id})


@bp.put("/projects/<int:project_id>/milestones/<int:milestone_id>")
@jwt_required()
def update_milestone(project_id: int, milestone_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p, r = _project_and_request(project_id)
    if not p or not r or not _ensure_member(user, r):
        return jsonify({"message": "无权限"}), 403
    m = Milestone.query.get(milestone_id)
    if not m or m.project_id != project_id:
        return jsonify({"message": "不存在"}), 404
    data = request.get_json(force=True)
    if data.get("title") is not None:
        m.title = (data.get("title") or "").strip()
    if data.get("due_date") is not None:
        m.due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    if data.get("status") is not None:
        m.status = (data.get("status") or "todo").strip()
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/projects/<int:project_id>/updates")
@jwt_required()
def list_updates(project_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p, r = _project_and_request(project_id)
    if not p or not r or not _ensure_member(user, r):
        return jsonify({"message": "无权限"}), 403
    ups = ProgressUpdate.query.filter_by(project_id=project_id).order_by(ProgressUpdate.created_at.desc()).limit(200).all()
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "author_user_id": u.author_user_id,
                    "content": u.content,
                    "attachment_file_id": u.attachment_file_id,
                    "created_at": u.created_at.isoformat(),
                }
                for u in ups
            ]
        }
    )


@bp.post("/projects/<int:project_id>/updates")
@jwt_required()
def add_update(project_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p, r = _project_and_request(project_id)
    if not p or not r or not _ensure_member(user, r):
        return jsonify({"message": "无权限"}), 403
    data = request.get_json(force=True)
    content = (data.get("content") or "").strip()
    attachment_file_id = data.get("attachment_file_id")
    if not content and not attachment_file_id:
        return jsonify({"message": "参数不完整"}), 400
    u = ProgressUpdate(
        project_id=project_id,
        author_user_id=user.id,
        content=content,
        attachment_file_id=int(attachment_file_id) if attachment_file_id else None,
        created_at=now_utc(),
    )
    db.session.add(u)
    db.session.commit()
    return jsonify({"id": u.id})
