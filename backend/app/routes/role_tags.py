"""
角色标签API
提供预设角色标签和自定义角色标签管理功能
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import User


bp = Blueprint("role_tags", __name__)


# 预设角色标签列表
PRESET_ROLE_TAGS = [
    "前端开发",
    "后端开发",
    "全栈开发",
    "UI/UX设计",
    "产品经理",
    "项目管理",
    "数据分析",
    "算法工程",
    "测试工程",
    "运维部署",
    "文档撰写",
    "市场调研",
    "硬件开发",
    "嵌入式开发",
    "机器学习",
    "深度学习",
    "计算机视觉",
    "自然语言处理",
    "其他"
]

# 存储自定义标签（简单实现，实际可以存数据库）
_custom_tags = set()


@bp.get("/role-tags")
def list_role_tags():
    """
    获取角色标签列表
    返回预设标签和用户自定义标签
    """
    # 合并预设标签和自定义标签
    all_tags = list(PRESET_ROLE_TAGS) + sorted(list(_custom_tags - set(PRESET_ROLE_TAGS)))
    
    return jsonify({
        "preset_tags": PRESET_ROLE_TAGS,
        "custom_tags": sorted(list(_custom_tags - set(PRESET_ROLE_TAGS))),
        "all_tags": all_tags
    })


@bp.post("/role-tags")
@jwt_required()
def add_custom_tag():
    """
    添加自定义角色标签
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    data = request.get_json(force=True)
    tag_name = (data.get("tag_name") or "").strip()
    
    # 验证标签名称
    if not tag_name:
        return jsonify({"message": "标签名称不能为空"}), 400
    
    if len(tag_name) > 32:
        return jsonify({"message": "角色标签不能超过32个字符"}), 400
    
    # 检查是否已存在
    if tag_name in PRESET_ROLE_TAGS or tag_name in _custom_tags:
        return jsonify({
            "success": True,
            "message": "标签已存在",
            "tag_name": tag_name,
            "is_new": False
        })
    
    # 添加自定义标签
    _custom_tags.add(tag_name)
    
    return jsonify({
        "success": True,
        "message": "标签添加成功",
        "tag_name": tag_name,
        "is_new": True
    })


def validate_role_tags(tags):
    """
    验证角色标签列表
    返回 (is_valid, error_message, cleaned_tags)
    """
    if tags is None:
        return True, None, []
    
    if not isinstance(tags, list):
        return False, "角色标签格式无效", None
    
    cleaned_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            return False, "角色标签格式无效", None
        
        tag = tag.strip()
        if not tag:
            continue
        
        if len(tag) > 32:
            return False, f"角色标签「{tag[:10]}...」超过32个字符", None
        
        cleaned_tags.append(tag)
        
        # 如果是新标签，自动添加到自定义标签列表
        if tag not in PRESET_ROLE_TAGS:
            _custom_tags.add(tag)
    
    return True, None, cleaned_tags
