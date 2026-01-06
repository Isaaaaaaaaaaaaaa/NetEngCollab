from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CooperationProject, CooperationRequest, Milestone, ProgressUpdate, Role, TeacherPost, User
from ..utils import now_utc
from ..services import push_notification


bp = Blueprint("progress", __name__)


def _notify_milestone_change(post_id: int, milestone_title: str, action: str):
    """通知项目参与者里程碑变更"""
    post = TeacherPost.query.get(post_id)
    if not post:
        return
    
    # 获取所有已确认的合作请求
    confirmed_requests = CooperationRequest.query.filter_by(
        post_id=post_id,
        final_status="confirmed"
    ).all()
    
    student_ids = set(r.student_user_id for r in confirmed_requests if r.student_user_id)
    
    if action == "created":
        title = "新里程碑已添加"
        summary = f"项目《{post.title}》添加了新里程碑：{milestone_title}"
        notif_type = "milestone_new"
    elif action == "completed":
        title = "里程碑已完成"
        summary = f"项目《{post.title}》的里程碑「{milestone_title}」已完成"
        notif_type = "milestone_done"
    else:
        return
    
    for student_id in student_ids:
        try:
            push_notification(
                user_id=student_id,
                notif_type=notif_type,
                title=title,
                payload={"summary": summary, "post_id": post_id}
            )
        except Exception as e:
            print(f"发送里程碑通知失败: {e}")


def _project_and_request(project_id: int):
    p = CooperationProject.query.get(project_id)
    if not p:
        return None, None
    r = CooperationRequest.query.get(p.request_id)
    return p, r


def _ensure_member(user: User, r: CooperationRequest) -> bool:
    return user.id in {r.teacher_user_id, r.student_user_id} or user.role == Role.admin.value


def _get_projects_by_post_id(post_id: int):
    """获取某个post下所有已确认的合作项目"""
    reqs = CooperationRequest.query.filter_by(
        post_id=post_id,
        final_status="confirmed"
    ).all()
    project_ids = []
    for r in reqs:
        p = CooperationProject.query.filter_by(request_id=r.id).first()
        if p:
            project_ids.append(p.id)
    return project_ids


@bp.get("/posts/<int:post_id>/milestones")
@jwt_required()
def list_milestones_by_post(post_id: int):
    """按post_id获取所有相关项目的里程碑"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 获取该post下所有项目的ID
    project_ids = _get_projects_by_post_id(post_id)
    if not project_ids:
        return jsonify({"items": []})
    
    # 获取所有相关的里程碑
    ms = Milestone.query.filter(Milestone.project_id.in_(project_ids)).order_by(Milestone.created_at.asc()).all()
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


@bp.post("/posts/<int:post_id>/milestones")
@jwt_required()
def add_milestone_by_post(post_id: int):
    """为post下的第一个项目添加里程碑"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 获取该post下的第一个项目
    project_ids = _get_projects_by_post_id(post_id)
    if not project_ids:
        return jsonify({"message": "无可用项目"}), 404
    
    project_id = project_ids[0]  # 使用第一个项目
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"message": "参数不完整"}), 400
    due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    m = Milestone(project_id=project_id, title=title, due_date=due_date, status=(data.get("status") or "todo"), created_at=now_utc())
    db.session.add(m)
    db.session.commit()
    
    # 通知项目参与者
    _notify_milestone_change(post_id, title, "created")
    
    return jsonify({"id": m.id})


@bp.put("/posts/<int:post_id>/milestones/<int:milestone_id>")
@jwt_required()
def update_milestone_by_post(post_id: int, milestone_id: int):
    """更新里程碑"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    m = Milestone.query.get(milestone_id)
    if not m:
        return jsonify({"message": "不存在"}), 404
    
    data = request.get_json(force=True)
    old_status = m.status
    
    if data.get("title") is not None:
        m.title = (data.get("title") or "").strip()
    if data.get("due_date") is not None:
        m.due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    if data.get("status") is not None:
        m.status = (data.get("status") or "todo").strip()
    db.session.commit()
    
    # 如果状态变为完成，发送通知
    if old_status != "done" and m.status == "done":
        _notify_milestone_change(post_id, m.title, "completed")
    
    return jsonify({"ok": True})


@bp.get("/posts/<int:post_id>/updates")
@jwt_required()
def list_updates_by_post(post_id: int):
    """按post_id获取所有相关项目的进度更新"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 获取该post下所有项目的ID
    project_ids = _get_projects_by_post_id(post_id)
    if not project_ids:
        return jsonify({"items": []})
    
    # 获取所有相关的进度更新
    ups = ProgressUpdate.query.filter(ProgressUpdate.project_id.in_(project_ids)).order_by(ProgressUpdate.created_at.desc()).limit(200).all()
    
    # 获取所有作者信息
    author_ids = list(set(u.author_user_id for u in ups))
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "author_user_id": u.author_user_id,
                    "author_name": authors[u.author_user_id].display_name if u.author_user_id in authors else "未知",
                    "content": u.content,
                    "attachment_file_id": u.attachment_file_id,
                    "created_at": u.created_at.isoformat(),
                }
                for u in ups
            ]
        }
    )


@bp.post("/posts/<int:post_id>/updates")
@jwt_required()
def add_update_by_post(post_id: int):
    """为post下的第一个项目添加进度更新"""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 获取该post下的第一个项目
    project_ids = _get_projects_by_post_id(post_id)
    if not project_ids:
        return jsonify({"message": "无可用项目"}), 404
    
    project_id = project_ids[0]  # 使用第一个项目
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
