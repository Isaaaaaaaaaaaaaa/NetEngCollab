import json
from typing import Dict, List, Tuple

from .models import (
    CooperationRequest,
    CooperationStatus,
    Notification,
    ReviewStatus,
    Role,
    StudentProfile,
    TeacherPost,
    User,
)
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
