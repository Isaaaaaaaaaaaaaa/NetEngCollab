import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models import (
    Comment,
    Reaction,
    ReviewStatus,
    Role,
    StudentProfile,
    TeacherPost,
    User,
    Visibility,
)
from ..utils import ensure_list_str, json_dumps, json_loads, now_utc


bp = Blueprint("posts", __name__)


def _viewer_role():
    if not request.headers.get("Authorization"):
        return None
    try:
        from flask_jwt_extended import verify_jwt_in_request

        verify_jwt_in_request(optional=True)
        user = User.query.get(int(get_jwt_identity()))
        return user.role if user else None
    except Exception:
        return None


def _can_view_visibility(visibility, viewer_role):
    if visibility == Visibility.public.value:
        return True
    if visibility == Visibility.teacher_only.value:
        return viewer_role == Role.teacher.value or viewer_role == Role.admin.value
    if visibility == Visibility.student_only.value:
        return viewer_role == Role.student.value or viewer_role == Role.admin.value
    return False


@bp.get("/teacher-posts")
def list_teacher_posts():
    viewer_role = _viewer_role()
    q = TeacherPost.query

    like_only = (request.args.get("like_only") or "").strip() in {"1", "true", "yes"}
    favorite_only = (request.args.get("favorite_only") or "").strip() in {"1", "true", "yes"}
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20

    post_type = request.args.get("post_type")
    keyword = (request.args.get("keyword") or "").strip()
    tag = (request.args.get("tag") or "").strip()
    tech = (request.args.get("tech") or "").strip()

    if post_type:
        q = q.filter_by(post_type=post_type)
    if keyword:
        q = q.filter(TeacherPost.title.contains(keyword) | TeacherPost.content.contains(keyword))

    if like_only or favorite_only:
        if not request.headers.get("Authorization"):
            return jsonify({"message": "未登录"}), 401
        try:
            from flask_jwt_extended import verify_jwt_in_request

            verify_jwt_in_request(optional=True)
            viewer_id = int(get_jwt_identity()) if get_jwt_identity() else None
        except Exception:
            viewer_id = None
        if not viewer_id:
            return jsonify({"message": "未登录"}), 401

        reaction_type = "like" if like_only else "favorite"
        ids = [
            r.target_id
            for r in Reaction.query.filter_by(
                user_id=viewer_id,
                target_type="teacher_post",
                reaction_type=reaction_type,
            ).all()
        ]
        if not ids:
            return jsonify({"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(TeacherPost.id.in_(ids))

    posts = q.order_by(TeacherPost.created_at.desc()).limit(2000).all()

    items = []
    for p in posts:
        if viewer_role != Role.admin.value and p.review_status != ReviewStatus.approved.value:
            continue
        if not _can_view_visibility(p.visibility, viewer_role):
            continue
        tags = json_loads(p.tags_json, [])
        techs = json_loads(p.tech_stack_json, [])
        if tag and tag not in tags:
            continue
        if tech and tech not in techs:
            continue
        teacher = User.query.get(p.teacher_user_id)
        items.append(
            {
                "id": p.id,
                "post_type": p.post_type,
                "title": p.title,
                "content": p.content,
                "tech_stack": techs,
                "tags": tags,
                "recruit_count": p.recruit_count,
                "duration": p.duration,
                "outcome": p.outcome,
                "contact": p.contact,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "attachment_file_id": p.attachment_file_id,
                "teacher": {
                    "id": teacher.id,
                    "display_name": teacher.display_name,
                }
                if teacher
                else None,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
        )

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return jsonify({"items": items[start:end], "total": total, "page": page, "page_size": page_size})


@bp.post("/teacher-posts")
@jwt_required()
def create_teacher_post():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403

    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    post_type = (data.get("post_type") or "project").strip()

    if not title or not content:
        return jsonify({"message": "标题/内容不能为空"}), 400

    post = TeacherPost(
        teacher_user_id=user.id,
        post_type=post_type,
        title=title,
        content=content,
        tech_stack_json=json_dumps(ensure_list_str(data.get("tech_stack"))),
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        recruit_count=data.get("recruit_count"),
        duration=(data.get("duration") or None),
        outcome=(data.get("outcome") or None),
        contact=(data.get("contact") or None),
        deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
        attachment_file_id=int(data.get("attachment_file_id")) if data.get("attachment_file_id") else None,
        visibility=data.get("visibility") or Visibility.public.value,
        review_status=ReviewStatus.approved.value,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"id": post.id})


@bp.put("/teacher-posts/<int:post_id>")
@jwt_required()
def update_teacher_post(post_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403

    post = TeacherPost.query.get(post_id)
    if not post or post.teacher_user_id != user.id:
        return jsonify({"message": "不存在"}), 404

    data = request.get_json(force=True)
    title = (data.get("title") or post.title or "").strip()
    content = (data.get("content") or post.content or "").strip()
    if not title or not content:
        return jsonify({"message": "标题/内容不能为空"}), 400

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
    if "deadline" in data:
        post.deadline = datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None
    if "attachment_file_id" in data:
        post.attachment_file_id = int(data.get("attachment_file_id")) if data.get("attachment_file_id") else None
    post.updated_at = now_utc()
    post.review_status = ReviewStatus.approved.value
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/students")
def list_students():
    viewer_role = _viewer_role()
    q = StudentProfile.query
    direction = (request.args.get("direction") or "").strip()
    skill = (request.args.get("skill") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()

    profiles = q.limit(500).all()
    items = []
    for p in profiles:
        if not _can_view_visibility(p.visibility, viewer_role):
            continue
        user = User.query.get(p.user_id)
        if not user or not user.is_active or user.role != Role.student.value:
            continue

        skills = json_loads(p.skills_json, [])
        interests = json_loads(p.interests_json, [])
        if direction and (p.direction or "") != direction:
            continue
        if skill and skill not in [s.get("name") for s in skills if isinstance(s, dict)]:
            continue
        if keyword:
            text = " ".join(
                [
                    user.display_name or "",
                    p.direction or "",
                    json.dumps(skills, ensure_ascii=False),
                    json.dumps(interests, ensure_ascii=False),
                ]
            )
            if keyword not in text:
                continue

        items.append(
            {
                "user": {
                    "id": user.id,
                    "display_name": user.display_name,
                },
                "direction": p.direction,
                "skills": skills,
                "interests": interests,
                "weekly_hours": p.weekly_hours,
                "prefer_local": p.prefer_local,
                "accept_cross": p.accept_cross,
                "visibility": p.visibility,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
        )
    return jsonify({"items": items})


@bp.get("/student-profile")
@jwt_required()
def get_my_student_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.student.value:
        return jsonify({"message": "无权限"}), 403
    p = StudentProfile.query.get(user.id)
    if not p:
        return jsonify({"message": "未创建"}), 404
    return jsonify(
        {
            "direction": p.direction,
            "skills": json_loads(p.skills_json, []),
            "project_links": json_loads(p.project_links_json, []),
            "interests": json_loads(p.interests_json, []),
            "weekly_hours": p.weekly_hours,
            "prefer_local": p.prefer_local,
            "accept_cross": p.accept_cross,
            "visibility": p.visibility,
        }
    )


@bp.put("/student-profile")
@jwt_required()
def upsert_my_student_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.student.value:
        return jsonify({"message": "无权限"}), 403
    data = request.get_json(force=True)
    p = StudentProfile.query.get(user.id)
    if not p:
        p = StudentProfile(user_id=user.id)
        db.session.add(p)

    p.direction = (data.get("direction") or None)
    p.skills_json = json_dumps(data.get("skills") or [])
    p.project_links_json = json_dumps(data.get("project_links") or [])
    p.interests_json = json_dumps(ensure_list_str(data.get("interests")))
    p.weekly_hours = data.get("weekly_hours")
    p.prefer_local = bool(data.get("prefer_local"))
    p.accept_cross = bool(data.get("accept_cross", True))
    p.visibility = data.get("visibility") or Visibility.public.value
    p.updated_at = now_utc()
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/comments")
@jwt_required()
def add_comment():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    target_type = (data.get("target_type") or "").strip()
    target_id = data.get("target_id")
    content = (data.get("content") or "").strip()
    parent_comment_id = data.get("parent_comment_id")
    if not target_type or not target_id or not content:
        return jsonify({"message": "参数不完整"}), 400

    parent_id = int(parent_comment_id) if parent_comment_id else None
    if parent_id:
        parent = Comment.query.get(parent_id)
        if not parent or parent.target_type != target_type or parent.target_id != int(target_id):
            return jsonify({"message": "父评论不存在"}), 400

    c = Comment(
        author_user_id=user.id,
        target_type=target_type,
        target_id=int(target_id),
        parent_comment_id=parent_id,
        content=content,
        created_at=now_utc(),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id})


@bp.get("/comments")
def list_comments():
    target_type = (request.args.get("target_type") or "").strip()
    target_id = request.args.get("target_id")
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20
    if not target_type or not target_id:
        return jsonify({"message": "参数不完整"}), 400

    q = Comment.query.filter_by(target_type=target_type, target_id=int(target_id))
    total = q.count()
    comments = (
        q.order_by(Comment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = []
    for c in comments:
        u = User.query.get(c.author_user_id)
        items.append(
            {
                "id": c.id,
                "author": {"id": u.id, "display_name": u.display_name} if u else None,
                "parent_comment_id": c.parent_comment_id,
                "content": c.content,
                "created_at": c.created_at.isoformat(),
            }
        )
    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})


@bp.get("/interactions/summary")
def interactions_summary():
    target_type = (request.args.get("target_type") or "").strip()
    target_id = request.args.get("target_id")
    if not target_type or not target_id:
        return jsonify({"message": "参数不完整"}), 400

    viewer_id = None
    if request.headers.get("Authorization"):
        try:
            from flask_jwt_extended import verify_jwt_in_request

            verify_jwt_in_request(optional=True)
            viewer_id = int(get_jwt_identity()) if get_jwt_identity() else None
        except Exception:
            viewer_id = None

    tid = int(target_id)
    likes = (
        db.session.query(func.count(Reaction.id))
        .filter_by(target_type=target_type, target_id=tid, reaction_type="like")
        .scalar()
        or 0
    )
    favorites = (
        db.session.query(func.count(Reaction.id))
        .filter_by(target_type=target_type, target_id=tid, reaction_type="favorite")
        .scalar()
        or 0
    )
    comments = (
        db.session.query(func.count(Comment.id))
        .filter_by(target_type=target_type, target_id=tid)
        .scalar()
        or 0
    )

    liked = False
    favorited = False
    if viewer_id:
        liked = (
            Reaction.query.filter_by(
                user_id=viewer_id,
                target_type=target_type,
                target_id=tid,
                reaction_type="like",
            ).first()
            is not None
        )
        favorited = (
            Reaction.query.filter_by(
                user_id=viewer_id,
                target_type=target_type,
                target_id=tid,
                reaction_type="favorite",
            ).first()
            is not None
        )
    return jsonify(
        {
            "target_type": target_type,
            "target_id": tid,
            "likes": likes,
            "favorites": favorites,
            "comments": comments,
            "liked": liked,
            "favorited": favorited,
        }
    )


@bp.post("/interactions/batch-summary")
@jwt_required(optional=True)
def interactions_batch_summary():
    data = request.get_json(force=True)
    target_type = (data.get("target_type") or "").strip()
    target_ids = data.get("target_ids") or []
    if not target_type or not isinstance(target_ids, list) or not target_ids:
        return jsonify({"message": "参数不完整"}), 400

    ids = [int(x) for x in target_ids if str(x).isdigit()]
    if not ids:
        return jsonify({"message": "参数不完整"}), 400

    viewer_id = None
    if get_jwt_identity():
        viewer_id = int(get_jwt_identity())

    like_rows = (
        db.session.query(Reaction.target_id, func.count(Reaction.id))
        .filter(
            Reaction.target_type == target_type,
            Reaction.reaction_type == "like",
            Reaction.target_id.in_(ids),
        )
        .group_by(Reaction.target_id)
        .all()
    )
    fav_rows = (
        db.session.query(Reaction.target_id, func.count(Reaction.id))
        .filter(
            Reaction.target_type == target_type,
            Reaction.reaction_type == "favorite",
            Reaction.target_id.in_(ids),
        )
        .group_by(Reaction.target_id)
        .all()
    )
    comment_rows = (
        db.session.query(Comment.target_id, func.count(Comment.id))
        .filter(Comment.target_type == target_type, Comment.target_id.in_(ids))
        .group_by(Comment.target_id)
        .all()
    )

    likes_map = {int(tid): int(cnt) for tid, cnt in like_rows}
    fav_map = {int(tid): int(cnt) for tid, cnt in fav_rows}
    com_map = {int(tid): int(cnt) for tid, cnt in comment_rows}

    liked_set = set()
    favorited_set = set()
    if viewer_id:
        liked_set = {
            int(r.target_id)
            for r in Reaction.query.filter(
                Reaction.user_id == viewer_id,
                Reaction.target_type == target_type,
                Reaction.reaction_type == "like",
                Reaction.target_id.in_(ids),
            ).all()
        }
        favorited_set = {
            int(r.target_id)
            for r in Reaction.query.filter(
                Reaction.user_id == viewer_id,
                Reaction.target_type == target_type,
                Reaction.reaction_type == "favorite",
                Reaction.target_id.in_(ids),
            ).all()
        }

    result = {}
    for tid in ids:
        result[str(tid)] = {
            "likes": likes_map.get(tid, 0),
            "favorites": fav_map.get(tid, 0),
            "comments": com_map.get(tid, 0),
            "liked": tid in liked_set,
            "favorited": tid in favorited_set,
        }
    return jsonify({"target_type": target_type, "items": result})


@bp.post("/reactions/toggle")
@jwt_required()
def toggle_reaction():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    target_type = (data.get("target_type") or "").strip()
    target_id = data.get("target_id")
    reaction_type = (data.get("reaction_type") or "").strip()
    if not target_type or not target_id or reaction_type not in {"like", "favorite"}:
        return jsonify({"message": "参数不完整"}), 400

    existing = Reaction.query.filter_by(
        user_id=user.id,
        target_type=target_type,
        target_id=int(target_id),
        reaction_type=reaction_type,
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"active": False})

    r = Reaction(
        user_id=user.id,
        target_type=target_type,
        target_id=int(target_id),
        reaction_type=reaction_type,
        created_at=now_utc(),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"active": True})


@bp.get("/reactions")
@jwt_required()
def list_reactions():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    target_type = (request.args.get("target_type") or "").strip()
    reaction_type = (request.args.get("reaction_type") or "").strip()
    if not target_type or reaction_type not in {"like", "favorite"}:
        return jsonify({"message": "参数不完整"}), 400

    rows = Reaction.query.filter_by(
        user_id=user.id,
        target_type=target_type,
        reaction_type=reaction_type,
    ).order_by(Reaction.created_at.desc()).all()
    return jsonify({"items": [{"target_id": r.target_id} for r in rows]})
