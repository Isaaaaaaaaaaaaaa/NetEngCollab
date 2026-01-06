import os

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required, decode_token

from ..extensions import db
from ..models import Comment, File, Reaction, Resource, ReviewStatus, Role, User
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
def download_file(file_id: int):
    """
    文件下载接口
    支持两种认证方式：
    1. Authorization header (标准JWT认证)
    2. URL query parameter: ?token=<jwt_token> (用于新标签页打开)
    """
    user = None
    
    # 方式1: 尝试从Authorization header获取token
    if request.headers.get("Authorization"):
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(int(user_id))
        except Exception:
            pass
    
    # 方式2: 尝试从URL参数获取token
    if not user:
        token = request.args.get("token")
        if token:
            try:
                decoded = decode_token(token)
                user_id = decoded.get("sub")
                if user_id:
                    user = User.query.get(int(user_id))
            except Exception:
                pass
    
    # 验证用户
    if not user or not user.is_active:
        return jsonify({"message": "未登录或认证已过期"}), 401
    
    # 查找文件
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
    tag = (request.args.get("tag") or "").strip()
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
    if tag:
        q = q.filter(Resource.tags_json.contains(tag))

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


@bp.put("/resources/<int:resource_id>")
@jwt_required()
def update_resource(resource_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    r = Resource.query.get(resource_id)
    if not r:
        return jsonify({"message": "不存在"}), 404
    if user.role != Role.admin.value and r.uploader_user_id != user.id:
        return jsonify({"message": "无权限"}), 403

    data = request.get_json(force=True)
    title = (data.get("title") or r.title or "").strip()
    if not title:
        return jsonify({"message": "标题不能为空"}), 400
    r.title = title
    if "resource_type" in data and (data.get("resource_type") or "").strip():
        r.resource_type = (data.get("resource_type") or r.resource_type).strip()
    if "description" in data:
        r.description = (data.get("description") or None)
    if "category" in data:
        r.category = (data.get("category") or None)
    if "tags" in data:
        r.tags_json = json_dumps(ensure_list_str(data.get("tags")))
    if "file_id" in data and data.get("file_id"):
        r.file_id = int(data.get("file_id"))
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/resources/<int:resource_id>")
@jwt_required()
def delete_resource(resource_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    r = Resource.query.get(resource_id)
    if not r:
        return jsonify({"message": "不存在"}), 404
    if user.role != Role.admin.value and r.uploader_user_id != user.id:
        return jsonify({"message": "无权限"}), 403

    Reaction.query.filter_by(target_type="resource", target_id=r.id).delete(synchronize_session=False)
    Comment.query.filter_by(target_type="resource", target_id=r.id).delete(synchronize_session=False)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})
