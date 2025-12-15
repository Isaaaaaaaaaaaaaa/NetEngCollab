import os

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import File, Reaction, Resource, ReviewStatus, Role, User
from ..utils import ensure_list_str, json_dumps, json_loads, new_storage_name, now_utc, storage_path


bp = Blueprint("resources", __name__)


@bp.post("/files")
@jwt_required()
def upload_file():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    if "file" not in request.files:
        return jsonify({"message": "缺少文件"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"message": "文件名为空"}), 400

    storage_name = new_storage_name(f.filename)
    path = storage_path(storage_name)
    f.save(path)
    size_bytes = os.path.getsize(path)

    record = File(
        owner_user_id=user.id,
        original_name=f.filename,
        storage_name=storage_name,
        content_type=f.mimetype,
        size_bytes=size_bytes,
        created_at=now_utc(),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"file_id": record.id, "original_name": record.original_name})


@bp.get("/files/<int:file_id>")
@jwt_required()
def download_file(file_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    record = File.query.get(file_id)
    if not record:
        return jsonify({"message": "文件不存在"}), 404
    return send_file(storage_path(record.storage_name), as_attachment=True, download_name=record.original_name)


@bp.post("/resources")
@jwt_required()
def create_resource():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    file_id = data.get("file_id")
    if not title or not file_id:
        return jsonify({"message": "参数不完整"}), 400

    review_status = ReviewStatus.approved.value

    r = Resource(
        uploader_user_id=user.id,
        resource_type=(data.get("resource_type") or "doc").strip(),
        title=title,
        description=(data.get("description") or None),
        category=(data.get("category") or None),
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        file_id=int(file_id),
        review_status=review_status,
        created_at=now_utc(),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id, "review_status": r.review_status})


@bp.get("/resources")
def list_resources():
    q = Resource.query.filter_by(review_status=ReviewStatus.approved.value)
    category = (request.args.get("category") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()
    like_only = (request.args.get("like_only") or "").strip() in {"1", "true", "yes"}
    favorite_only = (request.args.get("favorite_only") or "").strip() in {"1", "true", "yes"}
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20
    if category:
        q = q.filter_by(category=category)
    if keyword:
        q = q.filter(Resource.title.contains(keyword) | Resource.description.contains(keyword))

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
                target_type="resource",
                reaction_type=reaction_type,
            ).all()
        ]
        if not ids:
            return jsonify({"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(Resource.id.in_(ids))

    total = q.count()
    items = []
    for r in (
        q.order_by(Resource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    ):
        u = User.query.get(r.uploader_user_id)
        file_record = File.query.get(r.file_id)
        items.append(
            {
                "id": r.id,
                "resource_type": r.resource_type,
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "tags": json_loads(r.tags_json, []),
                "file": {
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "size_bytes": file_record.size_bytes,
                }
                if file_record
                else None,
                "uploader": {"id": u.id, "display_name": u.display_name} if u else None,
                "created_at": r.created_at.isoformat(),
            }
        )
    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})
