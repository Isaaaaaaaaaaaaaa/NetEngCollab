import json
from typing import Dict, List, Tuple

from .models import CooperationRequest, CooperationStatus, Notification, ReviewStatus, Role, StudentProfile, TeacherPost, User
from .utils import json_dumps, json_loads, now_utc
from .extensions import db


def has_blocking_pending_selection(user_id: int) -> bool:
    reqs = CooperationRequest.query.filter(
        (CooperationRequest.teacher_user_id == user_id) | (CooperationRequest.student_user_id == user_id)
    ).filter(CooperationRequest.final_status == CooperationStatus.pending.value)

    for r in reqs.all():
        if r.teacher_user_id == user_id and r.teacher_status == CooperationStatus.accepted.value:
            return True
        if r.student_user_id == user_id and r.student_status == CooperationStatus.accepted.value:
            return True
    return False


def similarity_score(a: List[str], b: List[str]) -> float:
    sa = {x.strip().lower() for x in a if str(x).strip()}
    sb = {x.strip().lower() for x in b if str(x).strip()}
    if not sa and not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    if not union:
        return 0.0
    return len(inter) / len(union)


def recommend_teacher_posts_for_student(student_user_id: int, limit: int = 10):
    profile = StudentProfile.query.get(student_user_id)
    if not profile:
        return []
    interests = json_loads(profile.interests_json, [])
    skills = json_loads(profile.skills_json, [])
    skill_names = [s.get("name") for s in skills if isinstance(s, dict) and s.get("name")]
    base = interests + skill_names

    posts = TeacherPost.query.filter_by(review_status=ReviewStatus.approved.value).order_by(TeacherPost.created_at.desc()).limit(300).all()
    scored: List[Tuple[float, TeacherPost]] = []
    for p in posts:
        tags = json_loads(p.tags_json, [])
        tech = json_loads(p.tech_stack_json, [])
        score = max(similarity_score(base, tags), similarity_score(base, tech))
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    return [{"id": p.id, "title": p.title, "post_type": p.post_type, "score": round(s, 4)} for s, p in scored[:limit]]


def recommend_students_for_teacher(teacher_user_id: int, limit: int = 10):
    posts = TeacherPost.query.filter_by(teacher_user_id=teacher_user_id, review_status=ReviewStatus.approved.value).order_by(TeacherPost.created_at.desc()).limit(50).all()
    desired: List[str] = []
    for p in posts:
        desired.extend(json_loads(p.tags_json, []))
        desired.extend(json_loads(p.tech_stack_json, []))
    desired = [x for x in desired if str(x).strip()]
    profiles = StudentProfile.query.limit(500).all()
    scored: List[Tuple[float, StudentProfile, User]] = []
    for sp in profiles:
        user = User.query.get(sp.user_id)
        if not user or not user.is_active or user.role != Role.student.value:
            continue
        interests = json_loads(sp.interests_json, [])
        skills = json_loads(sp.skills_json, [])
        skill_names = [s.get("name") for s in skills if isinstance(s, dict) and s.get("name")]
        score = max(similarity_score(desired, interests), similarity_score(desired, skill_names))
        if score > 0:
            scored.append((score, sp, user))
    scored.sort(key=lambda x: (-x[0], -x[1].user_id))
    return [
        {"user_id": sp.user_id, "display_name": user.display_name, "score": round(s, 4)}
        for s, sp, user in scored[:limit]
    ]


def push_notification(user_id: int, notif_type: str, title: str, payload: Dict):
    n = Notification(
        user_id=user_id,
        notif_type=notif_type,
        title=title,
        payload_json=json_dumps(payload),
        is_read=False,
        created_at=now_utc(),
    )
    db.session.add(n)
    db.session.commit()
    return n



def check_and_start_project(post_id: int):
    """
    检查项目是否达到招募人数，如果达到则自动启动项目
    - 更新项目状态为 "in_progress"
    - 创建默认里程碑（注意：里程碑需要cooperation_project_id）
    - 发送通知给教师和所有已确认的学生
    """
    from datetime import timedelta
    
    # 获取项目
    post = TeacherPost.query.get(post_id)
    if not post:
        return False
    
    # 如果项目已经不是招募中状态，不处理
    if post.project_status != "recruiting":
        return False
    
    # 如果没有设置招募人数，不自动启动
    if not post.recruit_count or post.recruit_count <= 0:
        return False
    
    # 统计已确认的学生数量
    confirmed_count = CooperationRequest.query.filter_by(
        post_id=post_id,
        final_status=CooperationStatus.confirmed.value
    ).count()
    
    # 如果人数未达到要求，不启动
    if confirmed_count < post.recruit_count:
        return False
    
    # 更新项目状态为进行中
    post.project_status = "in_progress"
    post.updated_at = now_utc()
    
    # 注意：里程碑功能需要cooperation_project，这里先跳过里程碑创建
    # 因为Milestone模型使用的是project_id（指向cooperation_projects表）
    # 而不是post_id（指向teacher_posts表）
    # 如果需要里程碑功能，需要先创建或找到对应的cooperation_project
    
    # 发送通知给教师
    try:
        teacher = User.query.get(post.teacher_user_id)
        if teacher:
            push_notification(
                user_id=teacher.id,
                notif_type="project_started",
                title="项目已自动启动",
                payload={
                    "post_id": post_id,
                    "post_title": post.title,
                    "summary": f"项目《{post.title}》已达到招募人数（{confirmed_count}/{post.recruit_count}），自动进入进行中状态"
                }
            )
    except Exception as e:
        print(f"发送教师通知失败: {e}")
    
    # 发送通知给所有已确认的学生
    try:
        confirmed_requests = CooperationRequest.query.filter_by(
            post_id=post_id,
            final_status=CooperationStatus.confirmed.value
        ).all()
        
        for req in confirmed_requests:
            student = User.query.get(req.student_user_id)
            if student:
                push_notification(
                    user_id=student.id,
                    notif_type="project_started",
                    title="项目已正式启动",
                    payload={
                        "post_id": post_id,
                        "post_title": post.title,
                        "summary": f"您参与的项目《{post.title}》已正式启动，请查看项目详情"
                    }
                )
    except Exception as e:
        print(f"发送学生通知失败: {e}")
    
    # 通知待处理申请的学生项目已满员
    try:
        pending_requests = CooperationRequest.query.filter_by(
            post_id=post_id,
            final_status=CooperationStatus.pending.value
        ).all()
        
        for req in pending_requests:
            student = User.query.get(req.student_user_id)
            if student:
                push_notification(
                    user_id=student.id,
                    notif_type="project_full",
                    title="项目已满员",
                    payload={
                        "post_id": post_id,
                        "post_title": post.title,
                        "summary": f"您申请的项目《{post.title}》已达到招募人数上限，暂停接受新申请"
                    }
                )
    except Exception as e:
        print(f"发送满员通知失败: {e}")
    
    db.session.commit()
    return True
