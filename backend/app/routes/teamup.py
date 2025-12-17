from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Comment, Reaction, Role, TeamupPost, User
from ..utils import ensure_list_str, json_dumps, json_loads, now_utc


bp = Blueprint("teamup", __name__)


@bp.get("/teamup")
def list_teamup():
    keyword = (request.args.get("keyword") or "").strip()
    tag = (request.args.get("tag") or "").strip()
    like_only = (request.args.get("like_only") or "").strip() in {"1", "true", "yes"}
    favorite_only = (request.args.get("favorite_only") or "").strip() in {"1", "true", "yes"}
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20
    q = TeamupPost.query
    if keyword:
        q = q.filter(TeamupPost.title.contains(keyword) | TeamupPost.content.contains(keyword))
    if tag:
        q = q.filter(TeamupPost.tags_json.contains(tag))

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
                target_type="teamup_post",
                reaction_type=reaction_type,
            ).all()
        ]
        if not ids:
            return jsonify({"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(TeamupPost.id.in_(ids))

    total = q.count()
    items = []
    for p in (
        q.order_by(TeamupPost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    ):
        u = User.query.get(p.author_user_id)
        items.append(
            {
                "id": p.id,
                "post_kind": p.post_kind,
                "title": p.title,
                "content": p.content,
                "needed_roles": json_loads(p.needed_roles_json, []),
                "tags": json_loads(p.tags_json, []),
                "author": {"id": u.id, "display_name": u.display_name, "role": u.role} if u else None,
                "created_at": p.created_at.isoformat(),
            }
        )
    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})


@bp.post("/teamup")
@jwt_required()
def create_teamup():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"message": "参数不完整"}), 400
    p = TeamupPost(
        author_user_id=user.id,
        post_kind=(data.get("post_kind") or "竞赛").strip(),
        title=title,
        content=content,
        needed_roles_json=json_dumps(ensure_list_str(data.get("needed_roles"))),
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        created_at=now_utc(),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id})


@bp.put("/teamup/<int:post_id>")
@jwt_required()
def update_teamup(post_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p = TeamupPost.query.get(post_id)
    if not p:
        return jsonify({"message": "不存在"}), 404
    if user.role != Role.admin.value and p.author_user_id != user.id:
        return jsonify({"message": "无权限"}), 403

    data = request.get_json(force=True)
    title = (data.get("title") or p.title or "").strip()
    content = (data.get("content") or p.content or "").strip()
    if not title or not content:
        return jsonify({"message": "标题/内容不能为空"}), 400
    p.title = title
    p.content = content
    if "post_kind" in data and (data.get("post_kind") or "").strip():
        p.post_kind = (data.get("post_kind") or p.post_kind).strip()
    if "needed_roles" in data:
        p.needed_roles_json = json_dumps(ensure_list_str(data.get("needed_roles")))
    if "tags" in data:
        p.tags_json = json_dumps(ensure_list_str(data.get("tags")))
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/teamup/<int:post_id>")
@jwt_required()
def delete_teamup(post_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    p = TeamupPost.query.get(post_id)
    if not p:
        return jsonify({"message": "不存在"}), 404
    if user.role != Role.admin.value and p.author_user_id != user.id:
        return jsonify({"message": "无权限"}), 403

    Reaction.query.filter_by(target_type="teamup_post", target_id=p.id).delete(synchronize_session=False)
    Comment.query.filter_by(target_type="teamup_post", target_id=p.id).delete(synchronize_session=False)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})
