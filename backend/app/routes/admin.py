from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CooperationRequest, CooperationStatus, Resource, ReviewStatus, TeacherPost, User
from ..rbac import require_roles
from ..utils import now_utc


bp = Blueprint("admin", __name__)


@bp.post("/users/<int:user_id>/set-password")
@require_roles(["admin"])
def set_user_password(user_id: int):
    from ..utils import hash_password

    data = request.get_json(force=True)
    password = data.get("password") or ""
    if not password:
        return jsonify({"message": "参数不完整"}), 400
    u = User.query.get(user_id)
    if not u:
        return jsonify({"message": "用户不存在"}), 404
    u.password_hash = hash_password(password)
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/cooperations/<int:req_id>/release")
@require_roles(["admin"])
def release_cooperation(req_id: int):
    req = CooperationRequest.query.get(req_id)
    if not req:
        return jsonify({"message": "不存在"}), 404
    req.teacher_status = CooperationStatus.rejected.value
    req.student_status = CooperationStatus.rejected.value
    req.final_status = CooperationStatus.rejected.value
    req.updated_at = now_utc()
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/stats")
@require_roles(["admin"])
def stats():
    return jsonify(
        {
            "users": User.query.count(),
            "teacher_posts": TeacherPost.query.count(),
            "resources": Resource.query.count(),
        }
    )


@bp.get("/users")
@require_roles(["admin"])
def list_users():
    role = (request.args.get("role") or "").strip()
    q = User.query
    if role in {"student", "teacher", "admin"}:
        q = q.filter_by(role=role)
    users = q.order_by(User.created_at.desc()).all()
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat(),
                    "email": u.email,
                    "phone": u.phone,
                }
                for u in users
            ]
        }
    )


@bp.post("/users/batch-create")
@require_roles(["admin"])
def batch_create_users():
    from ..utils import hash_password, now_utc

    data = request.get_json(force=True)
    entries = data.get("users") or []
    created = []
    for e in entries:
        username = (e.get("username") or "").strip()
        password = e.get("password") or "123456"
        role = e.get("role") or "student"
        display_name = (e.get("display_name") or username).strip()
        if not username or role not in {"student", "teacher", "admin"}:
            continue
        if User.query.filter_by(username=username).first():
            continue
        u = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            display_name=display_name,
            is_active=True,
            created_at=now_utc(),
        )
        db.session.add(u)
        created.append({"username": username, "role": role})
    db.session.commit()
    return jsonify({"created": created})


@bp.get("/cooperations")
@require_roles(["admin"])
def cooperation_overview():
    reqs = CooperationRequest.query.order_by(CooperationRequest.created_at.desc()).limit(500).all()
    items = []
    for r in reqs:
        teacher = User.query.get(r.teacher_user_id)
        student = User.query.get(r.student_user_id)
        post = TeacherPost.query.get(r.post_id) if r.post_id else None
        items.append(
            {
                "id": r.id,
                "teacher": {"id": teacher.id, "display_name": teacher.display_name} if teacher else None,
                "student": {"id": student.id, "display_name": student.display_name} if student else None,
                "post": {"id": post.id, "title": post.title} if post else None,
                "teacher_status": r.teacher_status,
                "student_status": r.student_status,
                "final_status": r.final_status,
                "created_at": r.created_at.isoformat(),
            }
        )
    summary = {
        "total": len(reqs),
        "confirmed": len([r for r in reqs if r.final_status == CooperationStatus.confirmed.value]),
        "rejected": len([r for r in reqs if r.final_status == CooperationStatus.rejected.value]),
        "pending": len([r for r in reqs if r.final_status == CooperationStatus.pending.value]),
    }
    return jsonify({"items": items, "summary": summary})


@bp.get("/projects")
@require_roles(["admin"])
def list_projects():
    posts = TeacherPost.query.order_by(TeacherPost.created_at.desc()).all()
    items = []
    for p in posts:
        teacher = User.query.get(p.teacher_user_id)
        reqs = CooperationRequest.query.filter_by(post_id=p.id).all()
        selected_students = []
        for r in reqs:
            stu = User.query.get(r.student_user_id)
            selected_students.append(
                {
                    "id": r.id,
                    "student": {
                        "id": stu.id,
                        "display_name": stu.display_name,
                        "username": stu.username,
                    }
                    if stu
                    else None,
                    "teacher_status": r.teacher_status,
                    "student_status": r.student_status,
                    "final_status": r.final_status,
                }
            )
        items.append(
            {
                "id": p.id,
                "post_type": p.post_type,
                "title": p.title,
                "content": p.content,
                "tech_stack": [],
                "tags": [],
                "recruit_count": p.recruit_count,
                "duration": p.duration,
                "outcome": p.outcome,
                "contact": p.contact,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "teacher": {
                    "id": teacher.id,
                    "display_name": teacher.display_name,
                    "username": teacher.username,
                }
                if teacher
                else None,
                "created_at": p.created_at.isoformat(),
                "selected_students": selected_students,
            }
        )
    return jsonify({"items": items})
