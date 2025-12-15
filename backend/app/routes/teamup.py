from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import TeamupPost, User
from ..utils import ensure_list_str, json_dumps, json_loads, now_utc


bp = Blueprint("teamup", __name__)


@bp.get("/teamup")
def list_teamup():
    keyword = (request.args.get("keyword") or "").strip()
    q = TeamupPost.query
    if keyword:
        q = q.filter(TeamupPost.title.contains(keyword) | TeamupPost.content.contains(keyword))
    items = []
    for p in q.order_by(TeamupPost.created_at.desc()).limit(200).all():
        u = User.query.get(p.author_user_id)
        items.append(
            {
                "id": p.id,
                "post_kind": p.post_kind,
                "title": p.title,
                "content": p.content,
                "needed_roles": json_loads(p.needed_roles_json, []),
                "tags": json_loads(p.tags_json, []),
                "author": {"id": u.id, "display_name": u.display_name} if u else None,
                "created_at": p.created_at.isoformat(),
            }
        )
    return jsonify({"items": items})


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

