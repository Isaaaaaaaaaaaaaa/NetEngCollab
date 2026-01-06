from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CooperationProject, CooperationRequest, CooperationStatus, Role, TeacherPost, User
from ..utils import now_utc
from ..services import push_notification, check_and_start_project


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
        
        # 检查项目是否可以申请
        # 1. 检查项目状态
        if post.project_status and post.project_status != "recruiting":
            return jsonify({"message": "该项目不在招募中"}), 400
        
        # 2. 检查截止时间
        if post.deadline and post.deadline < now_utc():
            return jsonify({"message": "该项目已过报名截止时间"}), 400
        
        # 3. 检查是否已满员
        if post.recruit_count:
            confirmed_count = CooperationRequest.query.filter_by(
                post_id=int(post_id),
                final_status=CooperationStatus.confirmed.value
            ).count()
            if confirmed_count >= post.recruit_count:
                return jsonify({"message": "该项目已达到招募人数上限"}), 400

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
                "student_role": r.student_role,
                "custom_status": r.custom_status,
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
    
    # 如果是教师同意申请，检查是否已达到招募人数上限
    if user.id == req.teacher_user_id and action == "accept" and req.post_id:
        post = TeacherPost.query.get(req.post_id)
        if post and post.recruit_count:
            # 统计已确认的学生数量
            confirmed_count = CooperationRequest.query.filter_by(
                post_id=req.post_id,
                final_status=CooperationStatus.confirmed.value
            ).count()
            if confirmed_count >= post.recruit_count:
                return jsonify({"message": "该项目已达到招募人数上限"}), 400
    
    if user.id == req.teacher_user_id:
        req.teacher_status = CooperationStatus.accepted.value if action == "accept" else CooperationStatus.rejected.value
        if action == "accept" and req.initiated_by == Role.student.value:
            req.student_status = CooperationStatus.accepted.value
    elif user.id == req.student_user_id:
        req.student_status = CooperationStatus.accepted.value if action == "accept" else CooperationStatus.rejected.value
    else:
        return jsonify({"message": "无权限"}), 403

    before_final = req.final_status
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
            CooperationStatus.confirmed.value: "已确认",
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

    if before_final != CooperationStatus.confirmed.value and req.final_status == CooperationStatus.confirmed.value:
        if teacher:
            push_notification(
                user_id=teacher.id,
                notif_type="cooperation_confirmed",
                title="合作已确认",
                payload={"summary": f"项目：{post.title}" if post else "合作已确认"},
            )
        if student:
            push_notification(
                user_id=student.id,
                notif_type="cooperation_confirmed",
                title="合作已确认",
                payload={"summary": f"项目：{post.title}" if post else "合作已确认"},
            )
        
        # 检查并自动启动项目（如果达到招募人数）
        if req.post_id:
            try:
                check_and_start_project(req.post_id)
            except Exception as e:
                print(f"自动启动项目失败: {e}")

    return jsonify({"final_status": req.final_status})


@bp.get("/cooperation/projects")
@jwt_required()
def list_projects():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 获取所有确认的合作请求
    reqs = CooperationRequest.query.filter_by(final_status=CooperationStatus.confirmed.value)
    if user.role == Role.teacher.value:
        reqs = reqs.filter_by(teacher_user_id=user.id)
    elif user.role == Role.student.value:
        reqs = reqs.filter_by(student_user_id=user.id)
    else:
        reqs = reqs.filter_by(teacher_user_id=-1)
    reqs = reqs.all()
    
    # 按post_id分组，避免重复显示同一个项目
    projects_dict = {}
    for r in reqs:
        if not r.post_id:
            continue
        
        # 如果这个项目还没有记录，创建新条目
        if r.post_id not in projects_dict:
            post = TeacherPost.query.get(r.post_id)
            if post:
                projects_dict[r.post_id] = {
                    "post_id": r.post_id,
                    "title": post.title,
                    "project_status": post.project_status,
                    "students": [],
                    "request_ids": [],
                    "my_request_id": None,  # 当前用户的请求ID
                    "my_student_role": None,
                    "my_custom_status": None
                }
        
        # 添加学生信息到项目
        if r.post_id in projects_dict:
            student = User.query.get(r.student_user_id)
            if student:
                projects_dict[r.post_id]["students"].append({
                    "id": student.id,
                    "display_name": student.display_name,
                    "student_role": r.student_role,
                    "custom_status": r.custom_status
                })
                projects_dict[r.post_id]["request_ids"].append(r.id)
                
                # 如果是当前学生的请求，记录下来
                if user.role == Role.student.value and r.student_user_id == user.id:
                    projects_dict[r.post_id]["my_request_id"] = r.id
                    projects_dict[r.post_id]["my_student_role"] = r.student_role
                    projects_dict[r.post_id]["my_custom_status"] = r.custom_status
    
    # 转换为列表并添加ID（使用post_id作为唯一标识）
    items = []
    for post_id, project_data in projects_dict.items():
        item = {
            "id": post_id,  # 使用post_id作为项目ID
            "title": project_data["title"],
            "project_status": project_data["project_status"],
            "students": project_data["students"],
            "student_count": len(project_data["students"]),
            "request_ids": project_data["request_ids"]
        }
        # 为学生添加自己的请求信息
        if user.role == Role.student.value:
            item["my_request_id"] = project_data["my_request_id"]
            item["my_student_role"] = project_data["my_student_role"]
            item["my_custom_status"] = project_data["my_custom_status"]
        items.append(item)
    
    return jsonify({"items": items})



@bp.put("/cooperation/requests/<int:req_id>/student-info")
@jwt_required()
def update_student_info(req_id: int):
    """
    更新合作请求中的学生信息（角色和状态）
    教师可以编辑所有学生的信息
    学生只能编辑自己的信息
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 查找合作请求
    req = CooperationRequest.query.get(req_id)
    if not req:
        return jsonify({"message": "合作请求不存在"}), 404
    
    # 验证权限
    if user.role == Role.teacher.value:
        # 教师只能编辑自己项目的学生信息
        if req.teacher_user_id != user.id:
            return jsonify({"message": "无权编辑该学生信息"}), 403
    elif user.role == Role.student.value:
        # 学生只能编辑自己的信息，且必须是已确认的合作
        if req.student_user_id != user.id:
            return jsonify({"message": "无权编辑该信息"}), 403
        if req.final_status != CooperationStatus.confirmed.value:
            return jsonify({"message": "只有已确认的合作才能更新状态"}), 400
    else:
        return jsonify({"message": "无权限"}), 403
    
    # 获取请求数据
    data = request.get_json(force=True)
    student_role = data.get("student_role")
    custom_status = data.get("custom_status")
    
    # 输入验证
    if student_role is not None:
        student_role = str(student_role).strip()
        if len(student_role) > 64:
            return jsonify({"message": "学生角色不能超过64个字符"}), 400
        req.student_role = student_role if student_role else None
    
    if custom_status is not None:
        custom_status = str(custom_status).strip()
        if len(custom_status) > 64:
            return jsonify({"message": "自定义状态不能超过64个字符"}), 400
        req.custom_status = custom_status if custom_status else None
    
    req.updated_at = now_utc()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "信息更新成功",
        "data": {
            "id": req.id,
            "student_role": req.student_role,
            "custom_status": req.custom_status
        }
    })


@bp.get("/cooperation/my-request/<int:post_id>")
@jwt_required()
def get_my_request_for_project(post_id: int):
    """
    获取当前学生在指定项目中的合作请求信息
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    if user.role != Role.student.value:
        return jsonify({"message": "只有学生可以访问此接口"}), 403
    
    req = CooperationRequest.query.filter_by(
        student_user_id=user.id,
        post_id=post_id
    ).first()
    
    if not req:
        return jsonify({"message": "未找到合作请求"}), 404
    
    return jsonify({
        "id": req.id,
        "post_id": req.post_id,
        "student_role": req.student_role,
        "custom_status": req.custom_status,
        "final_status": req.final_status,
        "teacher_status": req.teacher_status,
        "student_status": req.student_status
    })



@bp.delete("/cooperation/requests/<int:req_id>")
@jwt_required()
def delete_cooperation_request(req_id: int):
    """
    删除合作请求（取消学生与项目的关联）
    教师可以删除自己项目的合作请求
    学生可以删除自己的合作请求
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    req = CooperationRequest.query.get(req_id)
    if not req:
        return jsonify({"message": "合作请求不存在"}), 404
    
    # 验证权限
    if user.role == Role.teacher.value:
        if req.teacher_user_id != user.id:
            return jsonify({"message": "无权删除该合作请求"}), 403
    elif user.role == Role.student.value:
        if req.student_user_id != user.id:
            return jsonify({"message": "无权删除该合作请求"}), 403
    else:
        return jsonify({"message": "无权限"}), 403
    
    # 删除关联的合作项目
    proj = CooperationProject.query.filter_by(request_id=req.id).first()
    if proj:
        db.session.delete(proj)
    
    # 获取相关信息用于通知
    student = User.query.get(req.student_user_id)
    teacher = User.query.get(req.teacher_user_id)
    post = TeacherPost.query.get(req.post_id) if req.post_id else None
    
    # 删除合作请求
    db.session.delete(req)
    db.session.commit()
    
    # 发送通知给对方
    if user.role == Role.teacher.value and student:
        push_notification(
            user_id=student.id,
            notif_type="cooperation_cancelled",
            title="合作已取消",
            payload={"summary": f"教师 {teacher.display_name if teacher else '未知'} 取消了您在项目「{post.title if post else '未知项目'}」中的合作关系"},
        )
    elif user.role == Role.student.value and teacher:
        push_notification(
            user_id=teacher.id,
            notif_type="cooperation_cancelled",
            title="学生退出项目",
            payload={"summary": f"学生 {student.display_name if student else '未知'} 退出了项目「{post.title if post else '未知项目'}」"},
        )
    
    return jsonify({
        "success": True,
        "message": "合作关系已取消"
    })


@bp.get("/cooperation/requests/grouped-by-project")
@jwt_required()
def get_grouped_requests():
    """
    按项目聚合申请列表
    只有教师可以访问
    返回按项目分组的申请，包含每个项目的待处理申请数量
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"message": "未登录"}), 401
    
    # 只有教师可以访问
    if user.role != Role.teacher.value:
        return jsonify({"message": "无权限"}), 403
    
    # 查询该教师的所有合作请求
    requests = CooperationRequest.query.filter_by(
        teacher_user_id=user.id
    ).order_by(CooperationRequest.created_at.desc()).all()
    
    # 按项目分组
    project_groups = {}
    for req in requests:
        post_id = req.post_id
        if not post_id:
            continue
        
        if post_id not in project_groups:
            post = TeacherPost.query.get(post_id)
            if not post:
                continue
            
            project_groups[post_id] = {
                "project": {
                    "id": post.id,
                    "title": post.title,
                    "project_status": post.project_status
                },
                "applications": [],
                "pending_count": 0
            }
        
        # 添加申请到对应项目组
        student = User.query.get(req.student_user_id)
        application = {
            "id": req.id,
            "student": {
                "id": student.id,
                "display_name": student.display_name
            } if student else None,
            "created_at": req.created_at.isoformat(),
            "final_status": req.final_status,
            "teacher_status": req.teacher_status,
            "student_status": req.student_status,
            "student_role": req.student_role,
            "custom_status": req.custom_status
        }
        
        project_groups[post_id]["applications"].append(application)
        
        # 统计待处理数量
        if req.final_status == CooperationStatus.pending.value:
            project_groups[post_id]["pending_count"] += 1
    
    # 转换为列表格式
    groups = list(project_groups.values())
    
    # 按待处理数量降序排序（待处理多的在前）
    groups.sort(key=lambda x: (-x["pending_count"], x["project"]["id"]))
    
    return jsonify({"groups": groups})
