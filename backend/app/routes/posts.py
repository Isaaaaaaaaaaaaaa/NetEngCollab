import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models import (
    Comment,
    CooperationRequest,
    CooperationStatus,
    File,
    ForumTopic,
    Reaction,
    Resource,
    ReviewStatus,
    Role,
    StudentProfile,
    TeacherProfile,
    TeacherPost,
    TeamupPost,
    User,
    Visibility,
)
from ..utils import ensure_list_str, json_dumps, json_loads, now_utc
from ..services import push_notification


bp = Blueprint("posts", __name__)


def _notify_project_status_change(post, old_status, new_status):
    """项目状态变更时通知相关学生"""
    status_text = {
        "recruiting": "招募中",
        "in_progress": "进行中",
        "completed": "已完成",
        "closed": "已关闭"
    }
    
    # 获取所有申请过该项目的学生（包括待处理和已确认的）
    requests = CooperationRequest.query.filter_by(post_id=post.id).all()
    student_ids = set(r.student_user_id for r in requests if r.student_user_id)
    
    # 获取收藏过该项目的学生
    favorites = Reaction.query.filter_by(
        target_type="teacher_post",
        target_id=post.id,
        reaction_type="favorite"
    ).all()
    for fav in favorites:
        user = User.query.get(fav.user_id)
        if user and user.role == Role.student.value:
            student_ids.add(fav.user_id)
    
    if not student_ids:
        return
    
    # 发送通知
    title = f"项目状态更新：{post.title}"
    summary = f"项目状态从「{status_text.get(old_status, old_status or '未设置')}」变更为「{status_text.get(new_status, new_status)}」"
    
    for student_id in student_ids:
        push_notification(
            user_id=student_id,
            notif_type="project_update",
            title=title,
            payload={"summary": summary, "post_id": post.id}
        )


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
    joined_only = (request.args.get("joined_only") or "").strip() in {"1", "true", "yes"}
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", 20))
    if page_size <= 0 or page_size > 100:
        page_size = 20

    post_type = request.args.get("post_type")
    project_status = request.args.get("project_status")  # 新增：项目状态筛选
    teacher_user_id = request.args.get("teacher_user_id")
    keyword = (request.args.get("keyword") or "").strip()
    tag = (request.args.get("tag") or "").strip()
    tech = (request.args.get("tech") or "").strip()

    if post_type:
        q = q.filter_by(post_type=post_type)
    if project_status:  # 新增：按项目状态筛选
        q = q.filter_by(project_status=project_status)
    if teacher_user_id and str(teacher_user_id).isdigit():
        q = q.filter_by(teacher_user_id=int(teacher_user_id))
    if keyword:
        q = q.filter(TeacherPost.title.contains(keyword) | TeacherPost.content.contains(keyword))

    viewer_id = None
    if like_only or favorite_only or joined_only:
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

    if joined_only:
        reqs = (
            CooperationRequest.query.filter_by(
                student_user_id=viewer_id,
                final_status=CooperationStatus.confirmed.value,
            )
            .order_by(CooperationRequest.created_at.desc())
            .all()
        )
        joined_ids = [int(r.post_id) for r in reqs if r.post_id]
        if not joined_ids:
            return jsonify({"items": [], "total": 0, "page": page, "page_size": page_size})
        q = q.filter(TeacherPost.id.in_(joined_ids))

    if like_only or favorite_only:
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

    def project_level_from_tags(tags_list):
        tags_text = " ".join([str(x) for x in (tags_list or []) if x])
        if "国家级" in tags_text:
            return "国家级"
        if "省级" in tags_text:
            return "省级"
        if "校级" in tags_text:
            return "校级"
        if "企业" in tags_text:
            return "企业合作"
        if "核心期刊" in tags_text:
            return "核心期刊"
        return "普通"

    def get_confirmed_count(post_id: int) -> int:
        """获取项目已确认的学生数量"""
        return CooperationRequest.query.filter_by(
            post_id=post_id,
            final_status=CooperationStatus.confirmed.value
        ).count()

    def success_rate_for_teacher(teacher_id: int):
        confirmed = CooperationRequest.query.filter_by(
            teacher_user_id=teacher_id,
            final_status=CooperationStatus.confirmed.value,
        ).count()
        rejected = CooperationRequest.query.filter_by(
            teacher_user_id=teacher_id,
            final_status=CooperationStatus.rejected.value,
        ).count()
        decided = confirmed + rejected
        if decided <= 0:
            return None, confirmed
        return confirmed / decided, confirmed

    teacher_cache = {}

    def teacher_info(teacher_id: int):
        if teacher_id in teacher_cache:
            return teacher_cache[teacher_id]
        teacher = User.query.get(teacher_id)
        if not teacher:
            teacher_cache[teacher_id] = None
            return None
        p = TeacherProfile.query.get(teacher_id)
        rate, confirmed = success_rate_for_teacher(teacher_id)
        published_posts = TeacherPost.query.filter_by(teacher_user_id=teacher_id).count()
        recent_reqs = (
            CooperationRequest.query.filter_by(
                teacher_user_id=teacher_id,
                final_status=CooperationStatus.confirmed.value,
            )
            .order_by(CooperationRequest.created_at.desc())
            .limit(3)
            .all()
        )
        recent_titles = []
        for r in recent_reqs:
            if not r.post_id:
                continue
            post = TeacherPost.query.get(int(r.post_id))
            if post and post.title:
                recent_titles.append(post.title)

        info = {
            "id": teacher.id,
            "display_name": teacher.display_name,
            "title": (p.title if p else None),
            "organization": (p.organization if p else None),
            "research_tags": json_loads(p.research_tags_json, []) if p else [],
            "stats": {
                "published_posts": published_posts,
                "confirmed_projects": confirmed,
                "success_rate": rate,
            },
            "recent_achievements": recent_titles,
        }
        teacher_cache[teacher_id] = info
        return info

    items = []
    for p in posts:
        if viewer_role != Role.admin.value and p.review_status != ReviewStatus.approved.value:
            continue
        if not _can_view_visibility(p.visibility, viewer_role):
            continue
        tags = json_loads(p.tags_json, [])
        techs = json_loads(p.tech_stack_json, [])
        required_roles = json_loads(p.required_roles_json, []) if hasattr(p, 'required_roles_json') and p.required_roles_json else []
        if tag and tag not in tags:
            continue
        if tech and tech not in techs:
            continue
        tinfo = teacher_info(p.teacher_user_id)
        items.append(
            {
                "id": p.id,
                "post_type": p.post_type,
                "project_level": project_level_from_tags(tags),
                "title": p.title,
                "content": p.content,
                "detailed_info": p.detailed_info,  # 新增：详细信息字段
                "tech_stack": techs,
                "tags": tags,
                "required_roles": required_roles,  # 新增：招募角色标签
                "recruit_count": p.recruit_count,
                "confirmed_count": get_confirmed_count(p.id),  # 新增：已确认学生数量
                "duration": p.duration,
                "outcome": p.outcome,
                "contact": p.contact,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "attachment_file_id": p.attachment_file_id,
                "teacher": tinfo,
                "project_status": p.project_status,  # 新增：项目状态
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
    from .role_tags import validate_role_tags
    
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403

    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    post_type = (data.get("post_type") or "project").strip()

    if not title or not content:
        return jsonify({"message": "标题/内容不能为空"}), 400

    # 验证 detailed_info 字段长度（最大10000字符）
    detailed_info = data.get("detailed_info") or ""
    if len(detailed_info) > 10000:
        return jsonify({"message": "详细信息不能超过10000字符"}), 400

    # 验证招募角色标签
    is_valid, error_msg, required_roles = validate_role_tags(data.get("required_roles"))
    if not is_valid:
        return jsonify({"message": error_msg}), 400

    post = TeacherPost(
        teacher_user_id=user.id,
        post_type=post_type,
        title=title,
        content=content,
        detailed_info=detailed_info,  # 新增：详细信息字段
        tech_stack_json=json_dumps(ensure_list_str(data.get("tech_stack"))),
        tags_json=json_dumps(ensure_list_str(data.get("tags"))),
        required_roles_json=json_dumps(required_roles),  # 新增：招募角色标签
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
    from .role_tags import validate_role_tags
    
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

    # 验证 detailed_info 字段长度（最大10000字符）
    if "detailed_info" in data:
        detailed_info = data.get("detailed_info") or ""
        if len(detailed_info) > 10000:
            return jsonify({"message": "详细信息不能超过10000字符"}), 400
        post.detailed_info = detailed_info

    # 记录旧状态用于通知
    old_status = post.project_status

    # 更新项目状态
    if "project_status" in data:
        project_status = (data.get("project_status") or "").strip()
        if project_status in ("recruiting", "in_progress", "completed", "closed"):
            post.project_status = project_status

    # 更新招募角色标签
    if "required_roles" in data:
        is_valid, error_msg, required_roles = validate_role_tags(data.get("required_roles"))
        if not is_valid:
            return jsonify({"message": error_msg}), 400
        post.required_roles_json = json_dumps(required_roles)

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

    # 项目状态变更通知
    new_status = post.project_status
    if old_status != new_status and new_status:
        _notify_project_status_change(post, old_status, new_status)

    return jsonify({"ok": True})


@bp.get("/students")
def list_students():
    viewer_role = _viewer_role()
    direction = (request.args.get("direction") or "").strip()
    major = (request.args.get("major") or "").strip()
    grade = (request.args.get("grade") or "").strip()
    skill = (request.args.get("skill") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()
    project_id = request.args.get("project_id")  # 新增：项目筛选参数

    # 如果指定了 project_id，筛选已申请或匹配该项目的学生
    if project_id and str(project_id).isdigit():
        project_id = int(project_id)
        # 查询该项目的所有合作请求
        cooperation_requests = CooperationRequest.query.filter_by(post_id=project_id).all()
        student_ids = [req.student_user_id for req in cooperation_requests if req.student_user_id]
        
        if not student_ids:
            # 如果该项目没有任何申请，返回空列表
            return jsonify({"items": []})
        
        # 只查询申请了该项目的学生
        rows = (
            db.session.query(User, StudentProfile)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .filter(User.is_active == True)
            .filter(User.role == Role.student.value)
            .filter(User.id.in_(student_ids))
            .order_by(User.id.asc())
            .limit(2000)
            .all()
        )
        
        # 构建学生ID到合作请求的映射，用于后续排序
        student_to_request = {req.student_user_id: req for req in cooperation_requests if req.student_user_id}
    else:
        # 没有指定项目，查询所有学生
        rows = (
            db.session.query(User, StudentProfile)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .filter(User.is_active == True)
            .filter(User.role == Role.student.value)
            .order_by(User.id.asc())
            .limit(2000)
            .all()
        )
        student_to_request = {}
    items = []
    for user, p in rows:
        visibility = p.visibility if p else Visibility.public.value
        if not _can_view_visibility(visibility, viewer_role):
            continue

        skills = json_loads(p.skills_json, []) if p else []
        interests = json_loads(p.interests_json, []) if p else []
        experiences = json_loads(p.experiences_json or "[]", []) if p else []
        project_links = json_loads(p.project_links_json, []) if p else []
        resume_file = None
        if p and p.resume_file_id:
            f = File.query.get(int(p.resume_file_id))
            if f:
                resume_file = {"id": f.id, "original_name": f.original_name, "size_bytes": f.size_bytes}

        if direction and p and (p.direction or "") != direction:
            continue
        if major and major not in (((p.major or "") if p else "")):
            continue
        if grade and ((p.grade or "") if p else "") != grade:
            continue
        if skill:
            names = [s.get("name") for s in skills if isinstance(s, dict) and s.get("name")]
            if skill not in names:
                continue
        if keyword:
            text = " ".join(
                [
                    user.display_name or "",
                    (p.major or "") if p else "",
                    (p.grade or "") if p else "",
                    (p.class_name or "") if p else "",
                    (p.direction or "") if p else "",
                    json.dumps(skills, ensure_ascii=False),
                    json.dumps(interests, ensure_ascii=False),
                ]
            )
            if keyword not in text:
                continue

        def skill_weight(level_text: str) -> float:
            t = (level_text or "").strip()
            if "精通" in t or "熟练" in t:
                return 5.0
            if "掌握" in t or "较熟练" in t:
                return 4.0
            if "了解" in t or "入门" in t:
                return 2.5
            return 3.0

        skill_points = 0.0
        for s in skills:
            if not isinstance(s, dict):
                continue
            skill_points += skill_weight(str(s.get("level") or ""))
        skill_points = min(skill_points, 35.0)

        exp_points = min(len(experiences) * 7.0, 28.0)

        weekly_hours = (p.weekly_hours if p else None) or 0
        time_points = min(max(float(weekly_hours), 0.0), 20.0) / 20.0 * 10.0

        link_points = min(len(project_links) * 2.0, 6.0)

        score = int(min(100.0, round(20.0 + skill_points + exp_points + time_points + link_points)))
        if score >= 85:
            score_level = "A"
        elif score >= 70:
            score_level = "B"
        elif score >= 55:
            score_level = "C"
        else:
            score_level = "D"

        items.append(
            {
                "user": {
                    "id": user.id,
                    "display_name": user.display_name,
                },
                "skill_score": score,
                "skill_score_level": score_level,
                "major": (p.major if p else None),
                "grade": (p.grade if p else None),
                "class_name": (p.class_name if p else None),
                "direction": (p.direction if p else None),
                "skills": skills,
                "interests": interests,
                "project_links": project_links,
                "experiences": experiences,
                "resume_file": resume_file,
                "weekly_hours": (p.weekly_hours if p else None),
                "prefer_local": (p.prefer_local if p else False),
                "accept_cross": (p.accept_cross if p else True),
                "visibility": visibility,
                "updated_at": p.updated_at.isoformat() if p and p.updated_at else None,
            }
        )
    
    # 如果指定了项目，按匹配分数和申请时间排序
    if project_id and student_to_request:
        # 按匹配分数降序，然后按申请时间升序（早申请的在前）
        items.sort(key=lambda x: (
            -x["skill_score"],  # 匹配分数降序
            student_to_request.get(x["user"]["id"]).created_at if student_to_request.get(x["user"]["id"]) else datetime.max
        ))
    
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
    resume_file = None
    if p.resume_file_id:
        f = File.query.get(int(p.resume_file_id))
        if f:
            resume_file = {"id": f.id, "original_name": f.original_name, "size_bytes": f.size_bytes}
    return jsonify(
        {
            "major": p.major,
            "grade": p.grade,
            "class_name": p.class_name,
            "direction": p.direction,
            "skills": json_loads(p.skills_json, []),
            "project_links": json_loads(p.project_links_json, []),
            "interests": json_loads(p.interests_json, []),
            "experiences": json_loads(p.experiences_json or "[]", []),
            "resume_file": resume_file,
            "resume_file_id": p.resume_file_id,
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

    p.major = (data.get("major") or None)
    p.grade = (data.get("grade") or None)
    p.class_name = (data.get("class_name") or None)
    p.direction = (data.get("direction") or None)
    p.skills_json = json_dumps(data.get("skills") or [])
    p.project_links_json = json_dumps(data.get("project_links") or [])
    p.interests_json = json_dumps(ensure_list_str(data.get("interests")))
    p.experiences_json = json_dumps(data.get("experiences") or [])
    if "resume_file_id" in data:
        p.resume_file_id = int(data.get("resume_file_id")) if data.get("resume_file_id") else None
    p.weekly_hours = data.get("weekly_hours")
    p.prefer_local = bool(data.get("prefer_local"))
    p.accept_cross = bool(data.get("accept_cross", True))
    p.visibility = data.get("visibility") or Visibility.public.value
    p.updated_at = now_utc()
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/teacher-profile")
@jwt_required()
def get_my_teacher_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403
    p = TeacherProfile.query.get(user.id)
    if not p:
        return jsonify({"title": None, "organization": None, "bio": None, "research_tags": []})
    return jsonify(
        {
            "title": p.title,
            "organization": p.organization,
            "bio": p.bio,
            "research_tags": json_loads(p.research_tags_json, []) or [],
        }
    )


@bp.put("/teacher-profile")
@jwt_required()
def upsert_my_teacher_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403
    data = request.get_json(force=True)
    p = TeacherProfile.query.get(user.id)
    if not p:
        p = TeacherProfile(user_id=user.id, updated_at=now_utc())
        db.session.add(p)
    p.title = (data.get("title") or None)
    p.organization = (data.get("organization") or None)
    p.bio = (data.get("bio") or None)
    p.research_tags_json = json_dumps(ensure_list_str(data.get("research_tags")))
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

    target_author_id = None
    if target_type == "teacher_post":
        post = TeacherPost.query.get(int(target_id))
        if post:
            target_author_id = post.teacher_user_id
    elif target_type == "resource":
        res = Resource.query.get(int(target_id))
        if res:
            target_author_id = res.uploader_user_id
    elif target_type == "forum_topic":
        topic = ForumTopic.query.get(int(target_id))
        if topic:
            target_author_id = topic.author_user_id
    elif target_type == "teamup_post":
        post = TeamupPost.query.get(int(target_id))
        if post:
            target_author_id = post.author_user_id

    if parent_id:
        parent = Comment.query.get(parent_id)
        if parent and parent.author_user_id != user.id:
            summary = f"{user.display_name} 回复了你：{content[:60]}"
            push_notification(
                user_id=parent.author_user_id,
                notif_type="comment_reply",
                title="评论有新的回复",
                payload={"target_type": target_type, "target_id": int(target_id), "summary": summary},
            )
    elif target_author_id and target_author_id != user.id:
        summary = f"{user.display_name} 评论了你的内容：{content[:60]}"
        push_notification(
            user_id=target_author_id,
            notif_type="comment_new",
            title="内容收到新的评论",
            payload={"target_type": target_type, "target_id": int(target_id), "summary": summary},
        )

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


@bp.get("/teachers/<int:teacher_id>/profile")
@jwt_required(optional=True)
def get_teacher_profile(teacher_id):
    """
    获取教师完整信息
    Requirements: 1.1, 1.2
    """
    # 获取教师用户信息
    teacher = User.query.filter_by(id=teacher_id, role=Role.teacher.value).first()
    if not teacher:
        return jsonify({"message": "教师不存在"}), 404
    
    # 获取教师画像
    profile = TeacherProfile.query.filter_by(user_id=teacher_id).first()
    
    # 解析研究标签
    research_tags = []
    if profile and profile.research_tags_json:
        research_tags = json_loads(profile.research_tags_json, [])
    
    # 统计教师的项目数据
    total_projects = TeacherPost.query.filter_by(teacher_user_id=teacher_id).count()
    
    # 统计已确认的合作项目数
    confirmed_projects = (
        db.session.query(CooperationRequest)
        .filter(
            CooperationRequest.teacher_user_id == teacher_id,
            CooperationRequest.final_status == CooperationStatus.confirmed.value
        )
        .count()
    )
    
    # 计算组队成功率
    total_requests = (
        db.session.query(CooperationRequest)
        .filter(CooperationRequest.teacher_user_id == teacher_id)
        .count()
    )
    success_rate = confirmed_projects / total_requests if total_requests > 0 else None
    
    # 获取最近的成就（从最近的项目中提取）
    recent_achievements = []
    recent_posts = (
        TeacherPost.query
        .filter_by(teacher_user_id=teacher_id)
        .order_by(TeacherPost.created_at.desc())
        .limit(3)
        .all()
    )
    for post in recent_posts:
        if post.outcome:
            recent_achievements.append(post.outcome)
    
    return jsonify({
        "id": teacher.id,
        "display_name": teacher.display_name,
        "username": teacher.username,
        "email": teacher.email,
        "phone": teacher.phone,
        "title": profile.title if profile else None,
        "organization": profile.organization if profile else None,
        "bio": profile.bio if profile else None,
        "research_tags": research_tags,
        "auto_reply": profile.auto_reply if profile else None,
        "stats": {
            "total_projects": total_projects,
            "confirmed_projects": confirmed_projects,
            "success_rate": success_rate
        },
        "recent_achievements": recent_achievements
    })


@bp.get("/students/<int:student_id>/summary")
@jwt_required()
def get_student_summary(student_id):
    """
    获取学生画像摘要信息（用于悬浮预览）
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 只有教师和管理员可以查看学生摘要
    if user.role not in [Role.teacher.value, Role.admin.value]:
        return jsonify({"message": "无权限"}), 403
    
    # 获取学生用户信息
    student = User.query.filter_by(id=student_id, role=Role.student.value).first()
    if not student:
        return jsonify({"message": "学生不存在"}), 404
    
    # 获取学生画像
    profile = StudentProfile.query.filter_by(user_id=student_id).first()
    
    # 解析技能、兴趣、经历
    skills = json_loads(profile.skills_json, []) if profile else []
    interests = json_loads(profile.interests_json, []) if profile else []
    experiences = json_loads(profile.experiences_json or "[]", []) if profile else []
    
    # 计算技能评分
    def skill_weight(level_text: str) -> float:
        t = (level_text or "").strip()
        if "精通" in t or "熟练" in t:
            return 5.0
        if "掌握" in t or "较熟练" in t:
            return 4.0
        if "了解" in t or "入门" in t:
            return 2.5
        return 3.0
    
    skill_points = 0.0
    for s in skills:
        if isinstance(s, dict):
            skill_points += skill_weight(str(s.get("level") or ""))
    skill_points = min(skill_points, 35.0)
    
    exp_points = min(len(experiences) * 7.0, 28.0)
    weekly_hours = (profile.weekly_hours if profile else None) or 0
    time_points = min(max(float(weekly_hours), 0.0), 20.0) / 20.0 * 10.0
    
    skill_score = int(min(100.0, round(20.0 + skill_points + exp_points + time_points)))
    
    # 获取最近经历（最多2个）
    recent_experiences = []
    for exp in experiences[:2]:
        if isinstance(exp, dict):
            recent_experiences.append({
                "title": exp.get("title", ""),
                "type": exp.get("type", "")
            })
    
    # 获取简历文件ID
    resume_file_id = profile.resume_file_id if profile else None
    
    return jsonify({
        "id": student.id,
        "display_name": student.display_name,
        "grade": profile.grade if profile else None,
        "major": profile.major if profile else None,
        "skills": skills,
        "skill_score": skill_score,
        "weekly_hours": weekly_hours,
        "interests": interests,
        "experiences_count": len(experiences),
        "recent_experiences": recent_experiences,
        "resume_file_id": resume_file_id
    })
