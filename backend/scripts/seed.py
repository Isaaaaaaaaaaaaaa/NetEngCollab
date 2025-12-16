import os
import random
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    Comment,
    CooperationProject,
    CooperationRequest,
    CooperationStatus,
    File,
    ForumReply,
    ForumTopic,
    Message,
    Milestone,
    Notification,
    ProgressUpdate,
    Reaction,
    Resource,
    ReviewStatus,
    Role,
    StudentProfile,
    TeacherPost,
    TeacherProfile,
    TeamupPost,
    User,
    Visibility,
)
from app.utils import hash_password, json_dumps, now_utc, new_storage_name, storage_path


def run():
  app = create_app()
  with app.app_context():
    db.drop_all()
    db.create_all()

    random.seed(42)

    def make_user(username: str, role: str, password: str, display_name: str, *, active: bool = True) -> User:
      u = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        display_name=display_name,
        is_active=active,
        created_at=now_utc(),
      )
      db.session.add(u)
      db.session.flush()
      if role == Role.student.value:
        profile = StudentProfile(
          user_id=u.id,
          major="网络工程",
          grade=random.choice(["大一", "大二", "大三", "大四"]),
          class_name=f"网工 {random.randint(1, 4)} 班",
          direction="网络安全",
          skills_json=json_dumps(
            [
              {"name": "Python", "level": random.choice(["熟练", "了解"])},
              {"name": "Vue", "level": "了解"},
              {"name": "渗透测试", "level": "了解"},
            ]
          ),
          project_links_json=json_dumps([f"https://github.com/demo/student-{u.username}"]),
          interests_json=json_dumps(["网络安全", "AI", "CTF"]),
          experiences_json=json_dumps(
            [
              {
                "type": "科研",
                "title": "校园网络流量分析",
                "content": "负责日志采集与可视化。",
                "outcome": "实验报告",
                "time": "2024.03-2024.07",
              }
            ]
          ),
          weekly_hours=random.choice([8, 10, 12, 14]),
          prefer_local=False,
          accept_cross=True,
          visibility=Visibility.public.value,
          updated_at=now_utc(),
        )
        db.session.add(profile)
      if role == Role.teacher.value:
        t_profile = TeacherProfile(
          user_id=u.id,
          title=random.choice(["讲师", "副教授"]),
          organization="网络工程系",
          bio="长期从事网络安全与系统开发相关教学与科研。",
          research_tags_json=json_dumps(["网络安全", "竞赛指导", "大创项目"]),
          updated_at=now_utc(),
        )
        db.session.add(t_profile)
      db.session.commit()
      return u

    admin = make_user("admin", Role.admin.value, "admin123", "系统管理员")

    student_names = ["张伟", "李静", "王磊", "赵婷", "陈浩", "刘芳", "杨杰", "黄蕾", "周敏", "徐晨", "郭强"]
    teacher_names = ["王志成", "李雪", "陈远", "刘洋", "赵琳", "周鹏", "黄杰", "徐宁", "唐敏", "沈哲", "马青"]

    students = []
    for i, name in enumerate(student_names, start=1):
      username = f"22{1002500 + i:03d}"
      students.append(make_user(username, Role.student.value, "stu123456", name))

    teachers = []
    for i, name in enumerate(teacher_names, start=1):
      username = f"10{10000 + i:03d}"
      teachers.append(make_user(username, Role.teacher.value, "tea123456", name))

    demo_files = []
    for i in range(5):
      storage_name = new_storage_name(f"demo{i + 1}.pdf")
      open(storage_path(storage_name), "wb").write(b"demo")
      f = File(
        owner_user_id=admin.id,
        original_name=f"demo{i + 1}.pdf",
        storage_name=storage_name,
        content_type="application/pdf",
        size_bytes=4,
        created_at=now_utc(),
      )
      db.session.add(f)
      db.session.flush()
      demo_files.append(f)

    posts = []
    post_specs = [
      ("project", "网络安全入侵检测科研项目", "基于深度学习的网络入侵检测系统研究。", ["Python", "PyTorch", "网络安全"], ["入侵检测", "深度学习"]),
      ("project", "校园流量异常行为分析", "分析校园网流量并识别异常行为。", ["Python", "Pandas"], ["流量分析", "可视化"]),
      ("innovation", "智能实验室值班系统", "面向实验室的智能值班与门禁管理。", ["Vue", "Node.js"], ["全栈开发", "实验室管理"]),
      ("innovation", "毕业设计题目管理平台", "统一管理与分配毕业设计题目。", ["Django", "MySQL"], ["信息系统", "管理平台"]),
      ("competition", "蓝桥杯程序设计竞赛集训队", "选拔有算法基础的同学，进行蓝桥杯方向的集训。", ["C++", "算法", "数据结构"], ["竞赛", "蓝桥杯"]),
      ("competition", "互联网+ 创新创业备赛", "指导学生完成互联网+ 项目路演与材料准备。", ["产品设计", "BP"], ["互联网+", "创新创业"]),
      ("project", "Web 安全漏洞自动化扫描", "开发轻量级 Web 漏洞扫描工具。", ["Go", "HTTP"], ["Web安全", "扫描器"]),
      ("project", "CTF 靶场平台搭建", "搭建校内 CTF 靶场环境。", ["Docker", "Linux"], ["CTF", "靶场"]),
      ("innovation", "课程学习行为分析", "基于学习日志分析学生学习行为。", ["Python", "数据分析"], ["学习分析"]),
      ("project", "校园网日志可视化看板", "构建网络日志看板，用于教学展示。", ["ECharts", "Vue"], ["可视化", "网络日志"]),
      ("competition", "数学建模竞赛训练营", "组织数学建模培训与模拟比赛。", ["Python", "Matlab"], ["数学建模"]),
      ("project", "物联网安全监测系统", "面向实验室物联网设备的安全监测。", ["MQTT", "Python"], ["物联网", "安全"]),
      ("innovation", "实验室资产管理小程序", "用于登记与盘点实验室资产。", ["小程序", "数据库"], ["资产管理"]),
      ("project", "云服务器成本可视化", "分析课程所用云服务器成本构成。", ["FinOps", "可视化"], ["云计算"]),
      ("competition", "网络攻防赛备赛", "组织省赛网络攻防方向训练。", ["渗透测试", "Linux"], ["攻防", "竞赛"]),
    ]

    for idx, spec in enumerate(post_specs):
      post_type, title, content, techs, tags = spec
      teacher = teachers[idx % len(teachers)]
      p = TeacherPost(
        teacher_user_id=teacher.id,
        post_type=post_type,
        title=title,
        content=content,
        tech_stack_json=json_dumps(techs),
        tags_json=json_dumps(tags),
        recruit_count=random.randint(2, 6),
        duration=random.choice(["1 学期", "3 个月", "半年"]),
        outcome=random.choice(["论文", "竞赛获奖", "课程项目"]),
        contact=f"{teacher.username}@example.com",
        deadline=now_utc() + timedelta(days=random.randint(15, 60)),
        visibility=Visibility.public.value,
        review_status=ReviewStatus.approved.value,
        created_at=now_utc(),
        updated_at=now_utc(),
      )
      db.session.add(p)
      db.session.flush()
      posts.append(p)

    db.session.commit()

    requests = []
    for i, stu in enumerate(students[:8]):
      post = posts[i % len(posts)]
      status = random.choice(
        [
          CooperationStatus.pending.value,
          CooperationStatus.accepted.value,
          CooperationStatus.rejected.value,
          CooperationStatus.confirmed.value,
        ]
      )
      teacher_status = CooperationStatus.accepted.value if status == CooperationStatus.confirmed.value else CooperationStatus.pending.value
      student_status = CooperationStatus.accepted.value if status in {CooperationStatus.accepted.value, CooperationStatus.confirmed.value} else CooperationStatus.pending.value
      req = CooperationRequest(
        teacher_user_id=post.teacher_user_id,
        student_user_id=stu.id,
        post_id=post.id,
        initiated_by=Role.student.value,
        teacher_status=teacher_status,
        student_status=student_status,
        final_status=status,
        created_at=now_utc(),
        updated_at=now_utc(),
      )
      db.session.add(req)
      db.session.flush()
      if status == CooperationStatus.confirmed.value:
        proj = CooperationProject(request_id=req.id, title=post.title, created_at=now_utc())
        db.session.add(proj)
        requests.append((req, proj))
      else:
        requests.append((req, None))

    db.session.commit()

    for req, proj in requests:
      if not proj:
        continue
      for j in range(3):
        due = now_utc() + timedelta(days=7 * (j + 1))
        m = Milestone(project_id=proj.id, title=f"阶段 {j + 1}", due_date=due, status="todo", created_at=now_utc())
        db.session.add(m)
      for j in range(2):
        u = ProgressUpdate(project_id=proj.id, author_user_id=req.student_user_id, content=f"第 {j + 1} 次周报：完成既定任务。", created_at=now_utc())
        db.session.add(u)

    db.session.commit()

    for f in demo_files:
      r = Resource(
        uploader_user_id=students[0].id,
        resource_type=random.choice(["paper", "dataset", "slides", "project"]),
        title=f"示例资源 {f.id}",
        description="用于平台展示的测试资源。",
        category="通用",
        tags_json=json_dumps(["示例", "测试"]),
        file_id=f.id,
        review_status=ReviewStatus.approved.value,
        created_at=now_utc(),
      )
      db.session.add(r)

    db.session.commit()

    t1 = ForumTopic(
      author_user_id=students[0].id,
      category="网络安全讨论区",
      title="如何入门渗透测试",
      content="请问各位学长，渗透测试建议从哪些方向开始？",
      tags_json=json_dumps(["渗透测试", "入门"]),
      review_status=ReviewStatus.approved.value,
      created_at=now_utc(),
    )
    db.session.add(t1)
    db.session.flush()
    r1 = ForumReply(topic_id=t1.id, author_user_id=teachers[0].id, content="可以先从 Web 安全基础开始学习。", created_at=now_utc())
    db.session.add(r1)

    tp = TeamupPost(
      author_user_id=students[1].id,
      post_kind="竞赛组队",
      title="招募算法同学，一起备战蓝桥杯",
      content="目前已有 2 名队员，缺 1 名算法方向同学。",
      needed_roles_json=json_dumps(["算法", "后端"]),
      tags_json=json_dumps(["蓝桥杯", "组队"]),
      review_status=ReviewStatus.approved.value,
      created_at=now_utc(),
    )
    db.session.add(tp)

    db.session.commit()

    for p in posts[:5]:
      c = Comment(
        author_user_id=students[0].id,
        target_type="teacher_post",
        target_id=p.id,
        content="这个项目很有意思，期待参与。",
        created_at=now_utc(),
      )
      db.session.add(c)
    db.session.commit()

    for i in range(6):
      r = Reaction(
        user_id=students[i % len(students)].id,
        target_type="teacher_post",
        target_id=posts[i].id,
        reaction_type=random.choice(["like", "favorite"]),
        created_at=now_utc(),
      )
      db.session.add(r)
    db.session.commit()

    conv = None
    if students and teachers:
      from app.models import Conversation

      conv = Conversation(teacher_user_id=teachers[0].id, student_user_id=students[0].id, created_at=now_utc())
      db.session.add(conv)
      db.session.flush()
      for i in range(3):
        msg = Message(
          conversation_id=conv.id,
          sender_user_id=students[0].id if i % 2 == 0 else teachers[0].id,
          content=f"测试消息 {i + 1}",
          created_at=now_utc(),
        )
        db.session.add(msg)
      db.session.commit()

    for stu in students[:3]:
      n = Notification(
        user_id=stu.id,
        notif_type="system",
        title="欢迎使用平台",
        payload_json=json_dumps({"message": "这是用于测试的系统通知。"}),
        is_read=False,
        created_at=now_utc(),
      )
      db.session.add(n)
    db.session.commit()


if __name__ == "__main__":
  run()

