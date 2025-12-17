from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import ForumReply, ForumTopic, Reaction, Role, User
from ..utils import ensure_list_str, json_dumps, json_loads, now_utc


bp = Blueprint("forum", __name__)


@bp.get("/forum/topics")
def list_topics():
    category = (request.args.get("category") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()
    tag = (request.args.get("tag") or "").strip()
    like_only = (request.args.get("like_only") or "").strip() in {"1", "true", "yes"}
    favorite_only = (request.args.get("favorite_only") or "").strip() in {"1", "true", "yes"}
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20
    q = ForumTopic.query
    if category:
        q = q.filter_by(category=category)
    if keyword:
        q = q.filter(ForumTopic.title.contains(keyword) | ForumTopic.content.contains(keyword))
    if tag:
        q = q.filter(ForumTopic.tags_json.contains(tag))

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
                target_type="forum_topic",
                reaction_type=reaction_type,
            ).all()
        ]
        if not ids:
            return jsonify({"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(ForumTopic.id.in_(ids))

    total = q.count()

    items = []
    for t in (
        q.order_by(ForumTopic.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    ):
        u = User.query.get(t.author_user_id)
        items.append(
            {
                "id": t.id,
                "category": t.category,
                "title": t.title,
                "content": t.content,
                "tags": json_loads(t.tags_json, []),
                "author": {"id": u.id, "display_name": u.display_name, "role": u.role} if u else None,
                "created_at": t.created_at.isoformat(),
            }
        )
    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})


@bp.post("/forum/topics")
@jwt_required()
def create_topic():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    category = (data.get("category") or "综合").strip()
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"message": "参数不完整"}), 400

    t = ForumTopic(
        author_user_id=user.id,
        category=category,
        title=title,
        content=content,
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        created_at=now_utc(),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id})


@bp.get("/forum/topics/<int:topic_id>/replies")
def list_replies(topic_id: int):
    replies = ForumReply.query.filter_by(topic_id=topic_id).order_by(ForumReply.created_at.asc()).all()
    items = []
    for r in replies:
        u = User.query.get(r.author_user_id)
        items.append(
            {
                "id": r.id,
                "content": r.content,
                "author": {"id": u.id, "display_name": u.display_name} if u else None,
                "created_at": r.created_at.isoformat(),
            }
        )
    return jsonify({"items": items})


@bp.post("/forum/topics/<int:topic_id>/replies")
@jwt_required()
def add_reply(topic_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"message": "内容不能为空"}), 400
    if not ForumTopic.query.get(topic_id):
        return jsonify({"message": "话题不存在"}), 404
    r = ForumReply(topic_id=topic_id, author_user_id=user.id, content=content, created_at=now_utc())
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id})
