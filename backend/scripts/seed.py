import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    CooperationProject,
    CooperationRequest,
    CooperationStatus,
    ReviewStatus,
    Role,
    StudentProfile,
    TeacherPost,
    TeacherProfile,
    User,
)
from app.utils import hash_password, json_dumps, now_utc


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        def ensure_user(username: str, role: str, password: str, display_name: str, is_active: bool):
            existing = User.query.filter_by(username=username).first()
            if existing:
                return existing
            u = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                display_name=display_name,
                is_active=is_active,
                created_at=now_utc(),
            )
            db.session.add(u)
            db.session.flush()
            if role == Role.student.value:
                db.session.add(
                    StudentProfile(
                        user_id=u.id,
                        direction="网络安全",
                        skills_json=json_dumps(
                            [
                                {"name": "Python", "level": "熟练"},
                                {"name": "Vue", "level": "了解"},
                                {"name": "渗透测试", "level": "了解"},
                            ]
                        ),
                        interests_json=json_dumps(["网络安全", "AI", "CTF"]),
                        weekly_hours=12,
                        accept_cross=True,
                        prefer_local=False,
                        updated_at=now_utc(),
                    )
                )
            if role == Role.teacher.value:
                db.session.add(TeacherProfile(user_id=u.id, title="讲师", organization="网络工程系", updated_at=now_utc()))
            db.session.commit()
            return u

        admin = ensure_user("admin", Role.admin.value, "admin123", "管理员", True)
        teacher1 = ensure_user("teacher1", Role.teacher.value, "teacher123", "李老师", True)
        teacher2 = ensure_user("teacher2", Role.teacher.value, "teacher123", "张老师", True)
        student1 = ensure_user("student1", Role.student.value, "student123", "王同学", True)
        student2 = ensure_user("student2", Role.student.value, "student123", "赵同学", True)
        student3 = ensure_user("student3", Role.student.value, "student123", "陈同学", True)
        student4 = ensure_user("student4", Role.student.value, "student123", "刘同学", True)

        if not TeacherPost.query.first():
            p1 = TeacherPost(
                teacher_user_id=teacher1.id,
                post_type="project",
                title="网络安全入侵检测科研项目",
                content="基于深度学习的网络入侵检测系统研究。",
                tech_stack_json=json_dumps(["Python", "PyTorch", "网络安全"]),
                tags_json=json_dumps(["入侵检测", "深度学习"]),
                recruit_count=3,
                duration="1 学期",
                outcome="论文+竞赛",
                contact="teacher1@example.com",
                visibility="public",
                review_status=ReviewStatus.approved.value,
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            db.session.add(p1)

            p2 = TeacherPost(
                teacher_user_id=teacher2.id,
                post_type="competition",
                title="蓝桥杯程序设计竞赛集训队",
                content="选拔有算法基础的同学，进行蓝桥杯方向的集训。",
                tech_stack_json=json_dumps(["C++", "算法", "数据结构"]),
                tags_json=json_dumps(["竞赛", "蓝桥杯"]),
                recruit_count=5,
                duration="3 个月",
                outcome="省赛一等奖冲刺",
                contact="teacher2@example.com",
                visibility="public",
                review_status=ReviewStatus.approved.value,
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            db.session.add(p2)
            db.session.flush()

            req1 = CooperationRequest(
                teacher_user_id=teacher1.id,
                student_user_id=student1.id,
                post_id=p1.id,
                initiated_by=Role.student.value,
                teacher_status=CooperationStatus.accepted.value,
                student_status=CooperationStatus.accepted.value,
                final_status=CooperationStatus.confirmed.value,
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            db.session.add(req1)
            db.session.flush()
            db.session.add(CooperationProject(request_id=req1.id, title=p1.title, created_at=now_utc()))

            req2 = CooperationRequest(
                teacher_user_id=teacher2.id,
                student_user_id=student2.id,
                post_id=p2.id,
                initiated_by=Role.student.value,
                teacher_status=CooperationStatus.pending.value,
                student_status=CooperationStatus.pending.value,
                final_status=CooperationStatus.pending.value,
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            db.session.add(req2)

        db.session.commit()


if __name__ == "__main__":
    run()
