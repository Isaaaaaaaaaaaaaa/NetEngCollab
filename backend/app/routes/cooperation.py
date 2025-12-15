from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CooperationProject, CooperationRequest, CooperationStatus, Role, TeacherPost, User
from ..utils import now_utc
from ..services import push_notification


bp = Blueprint("cooperation", __name__)


def _finalize_if_ready(req: CooperationRequest):
    if req.teacher_status == CooperationStatus.accepted.value and req.student_status == CooperationStatus.accepted.value:
        req.final_status = CooperationStatus.confirmed.value
        existing = CooperationProject.query.filter_by(request_id=req.id).first()
        if not existing:
            title = "合作项目"
            if req.post_id:
                post = TeacherPost.query.get(req.post_id)
                if post:
                    title = post.title
            db.session.add(CooperationProject(request_id=req.id, title=title, created_at=now_utc()))
    if req.teacher_status == CooperationStatus.rejected.value or req.student_status == CooperationStatus.rejected.value:
        req.final_status = CooperationStatus.rejected.value


@bp.post("/cooperation/request")
@jwt_required()
def create_request():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)

    post_id = data.get("post_id")
    teacher_user_id = data.get("teacher_user_id")
    student_user_id = data.get("student_user_id")

    if post_id:
        post = TeacherPost.query.get(int(post_id))
        if not post:
            return jsonify({"message": "项目不存在"}), 404
        teacher_user_id = post.teacher_user_id

    if not teacher_user_id or not student_user_id:
        return jsonify({"message": "参数不完整"}), 400

    teacher_user_id = int(teacher_user_id)
    student_user_id = int(student_user_id)
    if user.role == Role.student.value and user.id != student_user_id:
        return jsonify({"message": "无权限"}), 403
    if user.role == Role.teacher.value and user.id != teacher_user_id:
        return jsonify({"message": "无权限"}), 403

    existing = CooperationRequest.query.filter_by(
        teacher_user_id=teacher_user_id, student_user_id=student_user_id, post_id=int(post_id) if post_id else None
    ).first()
    if existing:
        return jsonify({"id": existing.id})

    initiated_by = user.role
    teacher_status = CooperationStatus.pending.value
    student_status = CooperationStatus.pending.value
    if initiated_by == Role.teacher.value:
        teacher_status = CooperationStatus.accepted.value
    elif initiated_by == Role.student.value:
        student_status = CooperationStatus.accepted.value

    req = CooperationRequest(
        teacher_user_id=teacher_user_id,
        student_user_id=student_user_id,
        post_id=int(post_id) if post_id else None,
        initiated_by=initiated_by,
        teacher_status=teacher_status,
        student_status=student_status,
        final_status=CooperationStatus.pending.value,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.session.add(req)
    db.session.flush()

    teacher = User.query.get(teacher_user_id)
    student = User.query.get(student_user_id)
    if teacher and student:
        post = TeacherPost.query.get(int(post_id)) if post_id else None
        if initiated_by == Role.student.value:
            title = f"{student.display_name} 申请加入项目"
            summary = f"项目：{post.title}" if post else "有新的合作申请"
            target_user_id = teacher.id
        else:
            title = f"{teacher.display_name} 发出合作邀请"
            summary = f"项目：{post.title}" if post else "有新的合作邀请"
            target_user_id = student.id
        push_notification(
            user_id=target_user_id,
            notif_type="cooperation_request",
            title=title,
            payload={"summary": summary},
        )

    db.session.commit()

    return jsonify({"id": req.id})


@bp.get("/cooperation/requests")
@jwt_required()
def list_requests():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401

    post_id_filter = request.args.get("post_id")

    if user.role == Role.teacher.value:
        reqs = CooperationRequest.query.filter_by(teacher_user_id=user.id)
    elif user.role == Role.student.value:
        reqs = CooperationRequest.query.filter_by(student_user_id=user.id)
    else:
        reqs = CooperationRequest.query.filter_by(teacher_user_id=-1)

    if post_id_filter:
        reqs = reqs.filter_by(post_id=int(post_id_filter))

    reqs = reqs.order_by(CooperationRequest.created_at.desc()).all()

    items = []
    for r in reqs:
        teacher = User.query.get(r.teacher_user_id)
        student = User.query.get(r.student_user_id)
        post = TeacherPost.query.get(r.post_id) if r.post_id else None
        items.append(
            {
                "id": r.id,
                "teacher": {"id": teacher.id, "display_name": teacher.display_name} if teacher else None,
                "student": {"id": student.id, "display_name": student.display_name} if student else None,
                "post": {"id": post.id, "title": post.title} if post else None,
                "initiated_by": r.initiated_by,
                "teacher_status": r.teacher_status,
                "student_status": r.student_status,
                "final_status": r.final_status,
                "created_at": r.created_at.isoformat(),
            }
        )
    return jsonify({"items": items})


@bp.post("/cooperation/requests/<int:req_id>/respond")
@jwt_required()
def respond(req_id: int):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    data = request.get_json(force=True)
    action = data.get("action")
    if action not in {"accept", "reject"}:
        return jsonify({"message": "参数不完整"}), 400
    req = CooperationRequest.query.get(req_id)
    if not req:
        return jsonify({"message": "不存在"}), 404
    if user.id == req.teacher_user_id:
        req.teacher_status = CooperationStatus.accepted.value if action == "accept" else CooperationStatus.rejected.value
        if action == "accept" and req.initiated_by == Role.student.value:
            req.student_status = CooperationStatus.accepted.value
    elif user.id == req.student_user_id:
        req.student_status = CooperationStatus.accepted.value if action == "accept" else CooperationStatus.rejected.value
    else:
        return jsonify({"message": "无权限"}), 403

    req.updated_at = now_utc()
    _finalize_if_ready(req)
    db.session.commit()

    teacher = User.query.get(req.teacher_user_id)
    student = User.query.get(req.student_user_id)
    post = TeacherPost.query.get(req.post_id) if req.post_id else None
    target_user = None
    if user.id == req.teacher_user_id and student:
        target_user = student
    elif user.id == req.student_user_id and teacher:
        target_user = teacher
    if target_user:
        title = "合作申请已处理"
        status_text = {
            CooperationStatus.accepted.value: "已接受",
            CooperationStatus.rejected.value: "已拒绝",
        }
        summary = status_text.get(
            req.final_status if req.final_status != CooperationStatus.pending.value else (req.teacher_status or req.student_status),
            "状态已更新",
        )
        if post:
            summary = f"项目：{post.title}（{summary}）"
        push_notification(
            user_id=target_user.id,
            notif_type="cooperation_respond",
            title=title,
            payload={"summary": summary},
        )

    return jsonify({"final_status": req.final_status})


@bp.get("/cooperation/projects")
@jwt_required()
def list_projects():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    reqs = CooperationRequest.query.filter_by(final_status=CooperationStatus.confirmed.value)
    if user.role == Role.teacher.value:
        reqs = reqs.filter_by(teacher_user_id=user.id)
    elif user.role == Role.student.value:
        reqs = reqs.filter_by(student_user_id=user.id)
    else:
        reqs = reqs.filter_by(teacher_user_id=-1)
    reqs = reqs.all()
    items = []
    for r in reqs:
        p = CooperationProject.query.filter_by(request_id=r.id).first()
        if p:
            items.append({"id": p.id, "title": p.title, "request_id": r.id})
    return jsonify({"items": items})
