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
        profile.auto_reply = "你好，我会在 24 小时内回复消息。"
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
        t_profile.auto_reply = "工作日 24 小时内回复。"
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
      ("project", "网络安全入侵检测科研项目", "基于深度学习的网络入侵检测系统研究。", ["Python", "PyTorch", "网络安全"], ["入侵检测", "深度学习"], "本项目旨在构建一个基于深度学习的网络入侵检测系统。\n\n研究背景：随着网络攻击手段日益复杂，传统的基于规则的入侵检测系统已难以应对新型威胁。\n\n技术要求：\n- 熟悉Python编程\n- 了解PyTorch深度学习框架\n- 对网络安全有基本认识\n\n工作内容：\n1. 收集和预处理网络流量数据\n2. 设计并训练深度学习模型\n3. 评估模型性能并优化\n\n预期成果：发表一篇会议论文或期刊论文"),
      ("project", "校园流量异常行为分析", "分析校园网流量并识别异常行为。", ["Python", "Pandas"], ["流量分析", "可视化"], "本项目专注于校园网络流量的异常行为检测与分析。\n\n项目目标：通过数据分析技术识别校园网中的异常流量模式，为网络安全管理提供支持。\n\n技能要求：\n- Python数据分析能力\n- 熟悉Pandas、NumPy等数据处理库\n- 具备数据可视化经验\n\n主要任务：\n1. 采集校园网流量日志\n2. 数据清洗与特征提取\n3. 异常检测算法实现\n4. 可视化展示分析结果"),
      ("innovation", "智能实验室值班系统", "面向实验室的智能值班与门禁管理。", ["Vue", "Node.js"], ["全栈开发", "实验室管理"], "开发一个智能化的实验室值班管理系统，提升实验室管理效率。\n\n系统功能：\n- 值班人员排班管理\n- 门禁记录与统计\n- 实验室使用情况监控\n- 移动端消息推送\n\n技术栈：\n- 前端：Vue3 + Element Plus\n- 后端：Node.js + Express\n- 数据库：MySQL\n\n适合对全栈开发感兴趣的同学参与。"),
      ("innovation", "毕业设计题目管理平台", "统一管理与分配毕业设计题目。", ["Django", "MySQL"], ["信息系统", "管理平台"], "构建一个毕业设计题目管理平台，实现题目发布、学生选题、过程管理等功能。\n\n核心功能：\n- 教师发布毕业设计题目\n- 学生在线选题\n- 选题审核流程\n- 进度跟踪与管理\n\n技术方案：\n- 后端框架：Django\n- 数据库：MySQL\n- 前端：Bootstrap + jQuery\n\n项目周期约一学期，适合有一定Web开发基础的同学。"),
      ("competition", "蓝桥杯程序设计竞赛集训队", "选拔有算法基础的同学，进行蓝桥杯方向的集训。", ["C++", "算法", "数据结构"], ["竞赛", "蓝桥杯"], "组建蓝桥杯程序设计竞赛集训队，系统训练算法与数据结构。\n\n集训内容：\n- 基础算法：排序、搜索、贪心\n- 数据结构：树、图、并查集\n- 动态规划专题\n- 历年真题讲解与模拟\n\n集训安排：\n- 每周2-3次集中训练\n- 定期模拟测试\n- 赛前冲刺辅导\n\n要求：\n- 熟练掌握C++或Java\n- 有一定算法基础\n- 能保证训练时间投入"),
      ("competition", "互联网+ 创新创业备赛", "指导学生完成互联网+ 项目路演与材料准备。", ["产品设计", "BP"], ["互联网+", "创新创业"], "指导学生参加互联网+创新创业大赛，从项目策划到路演全程辅导。\n\n辅导内容：\n- 项目选题与市场调研\n- 商业计划书撰写\n- 产品原型设计\n- 路演PPT制作与演讲训练\n- 答辩技巧指导\n\n适合人群：\n- 对创业感兴趣的同学\n- 有创新项目想法\n- 具备团队协作能力\n\n往期成绩：指导团队获省赛金奖2项、银奖3项"),
      ("project", "Web 安全漏洞自动化扫描", "开发轻量级 Web 漏洞扫描工具。", ["Go", "HTTP"], ["Web安全", "扫描器"], "开发一个轻量级的Web安全漏洞扫描工具，用于教学演示。\n\n项目特色：\n- 使用Go语言开发，性能优异\n- 支持常见Web漏洞检测（SQL注入、XSS等）\n- 可扩展的插件架构\n\n技术要点：\n- HTTP协议深入理解\n- Web安全漏洞原理\n- 并发编程\n\n适合对Web安全和Go语言感兴趣的同学。"),
      ("project", "CTF 靶场平台搭建", "搭建校内 CTF 靶场环境。", ["Docker", "Linux"], ["CTF", "靶场"], "搭建一个校内CTF（夺旗赛）训练平台，为网络安全课程提供实践环境。\n\n建设内容：\n- 基于Docker的题目容器化部署\n- 自动化评分系统\n- 题目管理后台\n- 排行榜与统计功能\n\n技术栈：\n- 容器化：Docker + Docker Compose\n- 系统：Linux服务器管理\n- 开发：Python/Node.js\n\n适合对系统运维和网络安全感兴趣的同学。"),
      ("innovation", "课程学习行为分析", "基于学习日志分析学生学习行为。", ["Python", "数据分析"], ["学习分析"], "通过数据分析技术研究学生的在线学习行为模式。\n\n研究内容：\n- 学习日志数据采集\n- 学习行为特征提取\n- 学习效果预测模型\n- 个性化学习建议\n\n技术方法：\n- 数据分析：Pandas、NumPy\n- 机器学习：Scikit-learn\n- 可视化：Matplotlib、Seaborn\n\n适合对教育数据挖掘感兴趣的同学。"),
      ("project", "校园网日志可视化看板", "构建网络日志看板，用于教学展示。", ["ECharts", "Vue"], ["可视化", "网络日志"], "开发一个实时的校园网络日志可视化看板系统。\n\n功能设计：\n- 实时流量监控\n- 访问统计分析\n- 异常告警展示\n- 多维度数据钻取\n\n技术实现：\n- 前端：Vue3 + ECharts\n- 数据处理：Python\n- 实时通信：WebSocket\n\n项目成果可用于网络安全课程的教学演示。"),
      ("competition", "数学建模竞赛训练营", "组织数学建模培训与模拟比赛。", ["Python", "Matlab"], ["数学建模"], "组建数学建模竞赛训练营，系统培训建模方法与编程技能。\n\n训练内容：\n- 数学建模基础理论\n- 常用算法：优化、预测、评价\n- Python/Matlab编程实践\n- 论文写作规范\n- 历年赛题分析\n\n训练形式：\n- 每周专题讲座\n- 小组讨论与实践\n- 模拟赛训练\n\n往期成绩：国赛一等奖1项、二等奖3项"),
      ("project", "物联网安全监测系统", "面向实验室物联网设备的安全监测。", ["MQTT", "Python"], ["物联网", "安全"], "开发一个物联网设备安全监测系统，保障实验室IoT设备安全。\n\n系统功能：\n- 设备接入管理\n- 通信流量监控\n- 异常行为检测\n- 安全事件告警\n\n技术架构：\n- 通信协议：MQTT\n- 后端：Python + Flask\n- 数据存储：InfluxDB\n- 前端展示：Vue\n\n适合对物联网安全感兴趣的同学参与。"),
      ("innovation", "实验室资产管理小程序", "用于登记与盘点实验室资产。", ["小程序", "数据库"], ["资产管理"], "开发一个实验室资产管理小程序，实现资产的数字化管理。\n\n核心功能：\n- 资产信息录入与查询\n- 二维码标签生成\n- 资产借用归还管理\n- 盘点统计报表\n\n技术选型：\n- 小程序：微信小程序\n- 后端：Node.js\n- 数据库：MongoDB\n\n项目实用性强，完成后可在实验室实际使用。"),
      ("project", "云服务器成本可视化", "分析课程所用云服务器成本构成。", ["FinOps", "可视化"], ["云计算"], "构建云服务器成本分析与可视化系统，优化资源使用。\n\n分析内容：\n- 云资源使用统计\n- 成本构成分析\n- 优化建议生成\n- 预算预警\n\n技术方案：\n- 数据采集：云平台API\n- 数据分析：Python\n- 可视化：ECharts/Grafana\n\n适合对云计算和成本优化感兴趣的同学。"),
      ("competition", "网络攻防赛备赛", "组织省赛网络攻防方向训练。", ["渗透测试", "Linux"], ["攻防", "竞赛"], "组建网络攻防竞赛集训队，备战省级网络安全竞赛。\n\n训练方向：\n- Web渗透测试\n- 系统提权技术\n- 流量分析\n- 应急响应\n- 攻防对抗实战\n\n训练安排：\n- 每周3次集中训练\n- 靶场实战演练\n- 模拟攻防对抗\n- 赛前集训冲刺\n\n要求：\n- 熟悉Linux系统\n- 有网络安全基础\n- 能投入充足时间训练\n\n往期成绩：省赛一等奖2项、二等奖4项"),
    ]

    # 设置固定的招募人数，确保测试数据合理
    # 第一个项目招募4人，确保张伟能申请进来
    recruit_counts = [4, 4, 4, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]  # 15个项目的招募人数
    # 设置截止时间：前12个项目正常，后3个项目已截止（用于测试）
    deadline_offsets = [30, 45, 30, 45, 30, 45, 30, 45, 30, 45, 30, 45, -10, -5, -15]  # 负数表示已过期
    
    for idx, spec in enumerate(post_specs):
      post_type, title, content, techs, tags, detailed_info = spec
      teacher = teachers[idx % len(teachers)]
      deadline_offset = deadline_offsets[idx % len(deadline_offsets)]
      p = TeacherPost(
        teacher_user_id=teacher.id,
        post_type=post_type,
        title=title,
        content=content,
        detailed_info=detailed_info,  # 添加详细信息
        tech_stack_json=json_dumps(techs),
        tags_json=json_dumps(tags),
        recruit_count=recruit_counts[idx % len(recruit_counts)],  # 使用固定的招募人数
        duration=random.choice(["1 学期", "3 个月", "半年"]),
        outcome=random.choice(["论文", "竞赛获奖", "课程项目"]),
        contact=f"{teacher.username}@example.com",
        deadline=now_utc() + timedelta(days=deadline_offset),  # 使用预设的截止时间
        visibility=Visibility.public.value,
        review_status=ReviewStatus.approved.value,
        project_status="recruiting",  # 设置初始状态为招募中
        created_at=now_utc(),
        updated_at=now_utc(),
      )
      db.session.add(p)
      db.session.flush()
      posts.append(p)

    db.session.commit()

    requests = []
    student_roles = ["前端开发", "后端开发", "算法研究", "数据分析", "测试", "文档撰写", "UI设计", "项目管理"]
    custom_statuses = ["进展顺利", "需要帮助", "已完成阶段任务", "待分配任务", "学习中"]
    
    # 定义明确的状态组合，确保状态逻辑正确
    status_combinations = [
      # (final_status, teacher_status, student_status, description)
      (CooperationStatus.pending.value, CooperationStatus.pending.value, CooperationStatus.accepted.value, "学生已申请，待教师确认"),
      (CooperationStatus.confirmed.value, CooperationStatus.accepted.value, CooperationStatus.accepted.value, "双方已确认"),
      (CooperationStatus.rejected.value, CooperationStatus.rejected.value, CooperationStatus.accepted.value, "教师已拒绝"),
      (CooperationStatus.confirmed.value, CooperationStatus.accepted.value, CooperationStatus.accepted.value, "双方已确认"),
      (CooperationStatus.pending.value, CooperationStatus.pending.value, CooperationStatus.accepted.value, "学生已申请，待教师确认"),
      (CooperationStatus.confirmed.value, CooperationStatus.accepted.value, CooperationStatus.accepted.value, "双方已确认"),
      (CooperationStatus.pending.value, CooperationStatus.accepted.value, CooperationStatus.pending.value, "教师已邀请，待学生确认"),
      (CooperationStatus.confirmed.value, CooperationStatus.accepted.value, CooperationStatus.accepted.value, "双方已确认"),
    ]
    
    for i, stu in enumerate(students[:8]):
      post = posts[i % len(posts)]
      final_status, teacher_status, student_status, _ = status_combinations[i]
      
      # 为已确认的合作请求添加角色和状态
      student_role = None
      custom_status = None
      if final_status == CooperationStatus.confirmed.value:
        student_role = random.choice(student_roles)
        custom_status = random.choice(custom_statuses)
      
      req = CooperationRequest(
        teacher_user_id=post.teacher_user_id,
        student_user_id=stu.id,
        post_id=post.id,
        initiated_by=Role.student.value,
        teacher_status=teacher_status,
        student_status=student_status,
        final_status=final_status,
        student_role=student_role,
        custom_status=custom_status,
        created_at=now_utc(),
        updated_at=now_utc(),
      )
      db.session.add(req)
      db.session.flush()
      if final_status == CooperationStatus.confirmed.value:
        proj = CooperationProject(request_id=req.id, title=post.title, created_at=now_utc())
        db.session.add(proj)
        requests.append((req, proj))
      else:
        requests.append((req, None))

    db.session.commit()

    # 添加更多合作请求，包括一些已满员并自动启动的项目
    # 为前3个项目添加足够的确认学生，使其自动启动（但不超过recruit_count - 1，留一个位置给pending的申请）
    for post_idx in range(3):
      post = posts[post_idx]
      # 计算已有的确认学生数量
      existing_confirmed = sum(1 for r in requests if r[0].post_id == post.id and r[0].final_status == CooperationStatus.confirmed.value)
      # 计算已有的pending学生数量
      existing_pending = sum(1 for r in requests if r[0].post_id == post.id and r[0].final_status == CooperationStatus.pending.value)
      
      # 确保这些项目有足够的确认学生，但要留位置给pending的申请
      # 如果有pending申请，最多填到 recruit_count - 1
      max_confirmed = post.recruit_count - existing_pending if existing_pending > 0 else post.recruit_count
      confirmed_count = existing_confirmed
      for stu_idx in range(len(students)):
        if confirmed_count >= max_confirmed:
          break
        stu = students[stu_idx]
        # 检查是否已经有请求
        existing = any(r[0].student_user_id == stu.id and r[0].post_id == post.id for r in requests)
        if not existing:
          req = CooperationRequest(
            teacher_user_id=post.teacher_user_id,
            student_user_id=stu.id,
            post_id=post.id,
            initiated_by=Role.student.value,
            teacher_status=CooperationStatus.accepted.value,
            student_status=CooperationStatus.accepted.value,
            final_status=CooperationStatus.confirmed.value,
            student_role=random.choice(student_roles),
            custom_status=random.choice(custom_statuses),
            created_at=now_utc(),
            updated_at=now_utc(),
          )
          db.session.add(req)
          db.session.flush()
          proj = CooperationProject(request_id=req.id, title=post.title, created_at=now_utc())
          db.session.add(proj)
          requests.append((req, proj))
          confirmed_count += 1
      
      # 如果达到招募人数（不包括pending的），更新项目状态为进行中
      if confirmed_count >= post.recruit_count:
        post.project_status = "in_progress"
        db.session.add(post)

    db.session.commit()

    # 按 post_id 创建里程碑和进度更新，避免重复
    # 收集每个 post 对应的第一个 project 和相关学生
    post_projects = {}  # post_id -> (first_project, student_ids)
    for req, proj in requests:
      if not proj:
        continue
      post_id = req.post_id
      if post_id not in post_projects:
        post_projects[post_id] = (proj, [req.student_user_id])
      else:
        post_projects[post_id][1].append(req.student_user_id)
    
    # 为每个 post 创建里程碑（只创建一次）
    for post_id, (proj, student_ids) in post_projects.items():
      for j in range(3):
        due = now_utc() + timedelta(days=7 * (j + 1))
        m = Milestone(project_id=proj.id, title=f"阶段 {j + 1}", due_date=due, status="todo", created_at=now_utc())
        db.session.add(m)
      # 为每个学生创建进度更新
      for stu_id in student_ids[:2]:  # 只为前2个学生创建进度更新
        for j in range(2):
          u = ProgressUpdate(project_id=proj.id, author_user_id=stu_id, content=f"第 {j + 1} 次周报：完成既定任务。", created_at=now_utc())
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

    if students and demo_files:
      profile0 = StudentProfile.query.filter_by(user_id=students[0].id).first()
      if profile0:
        profile0.resume_file_id = demo_files[0].id
        db.session.add(profile0)
        db.session.commit()

    for stu in students[:3]:
      n = Notification(
        user_id=stu.id,
        notif_type="system",
        title="欢迎使用平台",
        payload_json=json_dumps({"summary": "这是用于测试的系统通知。"}),
        is_read=False,
        created_at=now_utc(),
      )
      db.session.add(n)
    db.session.commit()


if __name__ == "__main__":
  run()
