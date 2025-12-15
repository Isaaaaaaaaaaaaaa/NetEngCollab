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


@bp.get("/pending-users")
@require_roles(["admin"])
def pending_users():
    users = User.query.filter_by(is_active=False).order_by(User.created_at.desc()).all()
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "role": u.role,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users
            ]
        }
    )


@bp.get("/pending-teacher-posts")
@require_roles(["admin"])
def pending_teacher_posts():
    posts = (
        TeacherPost.query.filter_by(review_status=ReviewStatus.pending.value)
        .order_by(TeacherPost.created_at.desc())
        .all()
    )
    items = []
    for p in posts:
        teacher = User.query.get(p.teacher_user_id)
        items.append(
            {
                "id": p.id,
                "post_type": p.post_type,
                "title": p.title,
                "content": p.content,
                "created_at": p.created_at.isoformat(),
                "teacher": {
                    "id": teacher.id,
                    "display_name": teacher.display_name,
                }
                if teacher
                else None,
            }
        )
    return jsonify({"items": items})


@bp.get("/pending-resources")
@require_roles(["admin"])
def pending_resources():
    resources = (
        Resource.query.filter_by(review_status=ReviewStatus.pending.value)
        .order_by(Resource.created_at.desc())
        .all()
    )
    items = []
    for r in resources:
        uploader = User.query.get(r.uploader_user_id)
        items.append(
            {
                "id": r.id,
                "title": r.title,
                "resource_type": r.resource_type,
                "created_at": r.created_at.isoformat(),
                "uploader": {
                    "id": uploader.id,
                    "display_name": uploader.display_name,
                }
                if uploader
                else None,
            }
        )
    return jsonify({"items": items})


@bp.get("/users")
@require_roles(["admin"])
def list_users():
    role = (request.args.get("role") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20
    q = User.query
    if role in {"student", "teacher", "admin"}:
        q = q.filter_by(role=role)
    total = q.count()
    users = (
        q.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
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
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
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
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20

    q = TeacherPost.query
    total = q.count()
    posts = (
        q.order_by(TeacherPost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
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
    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})


@bp.post("/projects")
@require_roles(["admin"])
def admin_create_project():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    teacher_user_id = data.get("teacher_user_id")
    post_type = (data.get("post_type") or "project").strip()
    if not title or not content or not teacher_user_id:
        return jsonify({"message": "参数不完整"}), 400
    teacher = User.query.get(int(teacher_user_id))
    if not teacher or teacher.role != "teacher":
        return jsonify({"message": "教师不存在"}), 400
    from ..utils import ensure_list_str, json_dumps, now_utc

    post = TeacherPost(
        teacher_user_id=teacher.id,
        post_type=post_type,
        title=title,
        content=content,
        tech_stack_json=json_dumps(ensure_list_str(data.get("tech_stack"))),
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        recruit_count=data.get("recruit_count"),
        duration=(data.get("duration") or None),
        outcome=(data.get("outcome") or None),
        contact=(data.get("contact") or None),
        deadline=None,
        visibility="public",
        review_status=ReviewStatus.approved.value,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"id": post.id})


@bp.put("/projects/<int:post_id>")
@require_roles(["admin"])
def admin_update_project(post_id: int):
    data = request.get_json(force=True)
    post = TeacherPost.query.get(post_id)
    if not post:
        return jsonify({"message": "不存在"}), 404
    title = (data.get("title") or post.title or "").strip()
    content = (data.get("content") or post.content or "").strip()
    if not title or not content:
        return jsonify({"message": "标题/内容不能为空"}), 400
    from ..utils import ensure_list_str, json_dumps, now_utc

    post.title = title
    post.content = content
    if "post_type" in data and (data.get("post_type") or "").strip():
        post.post_type = (data.get("post_type") or post.post_type).strip()
    if "tech_stack" in data:
        post.tech_stack_json = json_dumps(ensure_list_str(data.get("tech_stack")))
    if "tags" in data:
        post.tags_json = json_dumps(ensure_list_str(data.get("tags")))
    if "recruit_count" in data:
        post.recruit_count = data.get("recruit_count")
    if "duration" in data:
        post.duration = (data.get("duration") or None)
    if "outcome" in data:
        post.outcome = (data.get("outcome") or None)
    if "contact" in data:
        post.contact = (data.get("contact") or None)
    post.updated_at = now_utc()
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/projects/<int:post_id>")
@require_roles(["admin"])
def admin_delete_project(post_id: int):
    post = TeacherPost.query.get(post_id)
    if not post:
        return jsonify({"message": "不存在"}), 404
    db.session.delete(post)
    db.session.commit()
    return jsonify({"ok": True})
