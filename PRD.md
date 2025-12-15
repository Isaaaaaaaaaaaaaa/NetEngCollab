网工师生协作平台（两人完成版）项目文档

---

## 1. 项目概述

本项目实现“网络工程专业师生协作平台”，目标是让教师发布科研/大创/竞赛信息，学生发布技能与意愿信息，双方双向选择并通过站内沟通确认合作；同时提供资源共享、进度管理、成果沉淀、讨论区与组队互助等扩展功能。

技术架构：
- 前端：Vue3 + TypeScript + Pinia + Vue Router + Element Plus
  - 三套角色工作台（学生 / 教师 / 管理员），统一白色简约风格布局
  - 使用 Element Plus 的 `el-layout`、`el-card`、`el-table`、`el-form`、`el-timeline` 等组件实现仪表盘和业务界面
- 后端：Flask + SQLAlchemy + Flask-JWT-Extended（基于 RBAC 的权限控制）
  - Blueprints 按模块拆分（auth、posts、resources、messages、cooperation、forum、teamup、match、progress、notifications、admin）
- 数据库：MySQL（通过 `DATABASE_URL` 配置，可切换 SQLite 方便开发）

---

## 2. 两人分工（按角色与模块拆分，前后端都参与）

### 成员 A：学生端负责人（同时负责后端学生相关模块）

- 前端：
  - 学生登录流程与学生工作台页面
  - “我的画像”页面（技能、兴趣、可投入时间、可见范围）
  - 教师项目浏览、收藏、申请加入
  - 资源库浏览与上传入口
  - 讨论区、组队互助页面
  - 私信页面（会话与消息）

- 后端：
  - 学生画像 `GET/PUT /api/student-profile`
  - 教师项目列表 `GET /api/teacher-posts` 的筛选能力
  - 评论/点赞/收藏 `POST /api/comments`、`POST /api/reactions/toggle`
  - 智能匹配 `GET /api/match/top`（学生侧推荐项目）
  - 资源库 `POST/GET /api/resources`、文件上传下载 `/api/files`
  - 讨论区与组队互助 ` /api/forum/*`、`/api/teamup`

### 成员 B：教师端 + 管理员端负责人（同时负责后端审核/合作模块）

- 前端：
  - 教师工作台：项目发布、学生匹配、合作项目进度
  - 管理员控制台：账号审核、内容审核、统计数据
  - 教师处理合作请求、里程碑与进度更新 UI

- 后端：
  - RBAC 与登录鉴权 `/api/auth/login`、`/api/auth/me`
  - 教师发布 `POST /api/teacher-posts`（提交后管理员审核）
  - 合作流程：申请/邀请、接受/拒绝、确认后生成合作项目
    - `POST /api/cooperation/request`
    - `POST /api/cooperation/requests/<id>/respond`
    - `GET /api/cooperation/projects`
  - 进度管理（里程碑/更新）：
    - `GET/POST /api/projects/<id>/milestones`
    - `GET/POST /api/projects/<id>/updates`
  - 管理员审核接口：
    - 账号审核：`/api/admin/pending-users`、`/api/admin/users/<id>/set-active`
    - 项目审核：`/api/admin/pending-teacher-posts`、`/api/admin/teacher-posts/<id>/review`
    - 资源审核：`/api/admin/pending-resources`、`/api/admin/resources/<id>/review`
    - 统计：`/api/admin/stats`

---

## 3. 功能实现说明（对应指导书模块）

### 3.1 信息发布模块

- 教师发布通道：教师发布科研/大创/竞赛信息（统一为 teacher_posts 表，区分 post_type）
- 学生发布通道：学生完善技能画像与合作意愿（student_profiles 表）
- 评论/点赞/收藏：comments + reactions（支持 like / favorite）

### 3.2 信息检索与匹配模块

- 多维筛选：关键字、标签、技术栈筛选项目；关键字/技能筛选学生
- 智能匹配推荐（选作实现）：`/api/match/top` 使用标签集合相似度（Jaccard）推荐 TOP10
- 匹配提醒（选作实现）：提供 `notifications` 表与 `/api/notifications` 接口，前端轮询展示提醒面板

### 3.3 双向沟通与合作确认模块

- 站内私信：会话 `conversations` + 消息 `messages`，支持未读数
- 合作申请/邀请：cooperation_requests 记录双向选择状态
- 确认与备案：当师生双方均 accept 时 final_status 变为 confirmed，并生成 cooperation_projects 作为合作备案记录

### 3.4 资源共享模块（扩展功能）

- 资源库：resources + files，支持上传、下载、标签筛选
- 审核：学生/教师上传资源默认 pending，管理员审核通过后展示

### 3.5 进度管理与成果展示模块（扩展功能）

- 合作项目：confirmed 后自动生成 project
- 里程碑：milestones
- 进度更新：progress_updates（可挂载附件）

### 3.6 互动交流模块（扩展功能）

- 话题讨论区：forum_topics + forum_replies
- 组队互助区：teamup_posts

### 3.7 数据统计与分析模块（扩展功能）

- 管理员统计：`/api/admin/stats`（用户数/发布数/资源数）

此外新增：
- 管理员合作情况总览：`/api/admin/cooperations` 返回所有师生互选记录及汇总（总数 / 已确认 / 已拒绝 / 待处理）

---

## 5. 数据库设计概述

本项目采用关系型数据库（MySQL），核心表及关系如下（仅列出重点字段）：

1. `users`
   - `id`（PK）、`username`、`password_hash`、`role`（student/teacher/admin）、`display_name`、`email`、`phone`、`is_active`、`created_at`
   - 不同角色的公共账号信息，RBAC 的基础

2. `student_profiles`
   - `user_id`（PK, FK->users.id）、`direction`、`skills_json`、`project_links_json`、`interests_json`、`weekly_hours`、`prefer_local`、`accept_cross`、`visibility`、`updated_at`
   - 用 JSON 存储技能和兴趣标签，方便前端展示与匹配

3. `teacher_profiles`
   - `user_id`（PK, FK->users.id）、`title`、`organization`、`bio`、`research_tags_json`、`updated_at`
   - 教师画像（职称、单位、研究方向标签）

4. `teacher_posts`
   - `id`（PK）、`teacher_user_id`（FK->users.id）、`post_type`（project/innovation/competition）、`title`、`content`、`tech_stack_json`、`tags_json`、`recruit_count`、`duration`、`outcome`、`contact`、`deadline`、`visibility`、`review_status`、`created_at`、`updated_at`
   - 老师发布的科研项目 / 大创 / 竞赛信息

5. `cooperation_requests`
   - `id`（PK）、`teacher_user_id`、`student_user_id`、`post_id`（FK->teacher_posts.id）、`initiated_by`（student/teacher）、`teacher_status`、`student_status`、`final_status`、`created_at`、`updated_at`
   - 记录每一条合作申请/邀请，以及双方状态；`final_status=confirmed` 时表示已双向确认

6. `cooperation_projects`
   - `id`（PK）、`request_id`（FK->cooperation_requests.id）、`title`、`created_at`
   - 对应每一条已确认合作关系的“合作项目”实体，用于进度管理

7. `milestones`
   - `id`（PK）、`project_id`（FK->cooperation_projects.id）、`title`、`due_date`、`status`（todo/doing/done）、`created_at`
   - 项目的里程碑节点

8. `progress_updates`
   - `id`（PK）、`project_id`（FK->cooperation_projects.id）、`author_user_id`、`content`、`attachment_file_id`、`created_at`
   - 项目进度更新记录

9. `files` & `resources`
   - `files`：`id`、`owner_user_id`、`original_name`、`storage_name`、`content_type`、`size_bytes`、`created_at`
   - `resources`：`id`、`uploader_user_id`、`resource_type`、`title`、`description`、`category`、`tags_json`、`file_id`、`review_status`、`created_at`
   - 用于科研/竞赛资源库与文件存储

10. 讨论与组队相关表
    - `forum_topics` / `forum_replies`：话题讨论区
    - `teamup_posts`：组队互助区需求信息

11. 私信与通知
    - `conversations` / `messages`：老师和学生一对一站内私信（支持未读状态）
    - `notifications`：系统通知（合作申请、审核结果等），由后端通过 `push_notification` 统一写入

整体上，`users` 作为中心表，扩展学生/教师画像、发布信息、合作请求等多张业务表。通过外键保持数据一致性，并在序列化时返回给前端使用。

---

## 6. 前后端设计概述

### 6.1 后端模块划分（Flask + Blueprints）

- `app/routes/auth.py`
  - 账号注册（区分角色）、登录、获取当前用户信息 `/api/auth/register` `/api/auth/login` `/api/auth/me`

- `app/routes/posts.py`
  - 教师发布/修改项目信息：`POST /api/teacher-posts`、`PUT /api/teacher-posts/<id>`
  - 项目列表查询：`GET /api/teacher-posts` 支持按关键字、类型、标签、技术栈筛选
  - 学生画像查询/更新：`GET/PUT /api/student-profile`

- `app/routes/cooperation.py`
  - 创建合作申请/邀请：`POST /api/cooperation/request`
  - 查询当前用户相关的合作请求：`GET /api/cooperation/requests`（支持按 `post_id` 过滤）
  - 双方响应（接受/拒绝）：`POST /api/cooperation/requests/<id>/respond`
  - 合作项目列表：`GET /api/cooperation/projects`
  - 在处理请求时结合 `services.push_notification` 推送系统通知

- `app/routes/messages.py`
  - 会话列表、消息列表、发送消息：`GET /api/conversations`、`GET /api/conversations/<id>/messages`、`POST /api/messages/send`

- `app/routes/resources.py`
  - 文件上传/下载：`POST/GET /api/files`
  - 资源上传/列表：`POST/GET /api/resources`

- 其他模块：
  - `forum.py`（讨论区）、`teamup.py`（组队互助）、`match.py`（智能匹配）、`progress.py`（里程碑与进度管理）、`notifications.py`（系统通知）、`admin.py`（管理员功能，如账号审核、内容审核、统计与合作总览）。

### 6.2 前端路由与页面设计（Vue3 + Element Plus）

- 路由按角色拆分：
  - 学生端：`/student/dashboard`、`/student/projects`、`/student/profile`、`/student/resources`、`/student/forum`、`/student/teamup`、`/student/messages`
  - 教师端：`/teacher/dashboard`、`/teacher/posts`、`/teacher/students`、`/teacher/projects`、`/teacher/resources`、`/teacher/forum`、`/teacher/teamup`、`/teacher/messages`
  - 管理员端：`/admin/dashboard`、`/admin/users`、`/admin/content`

- 学生端：
  - 总览页：三个统计卡片 + 匹配项目时间线 + 合作项目表格 + 技能画像摘要 + 资源/动态卡片
  - 项目与匹配：表格展示项目列表，右侧智能匹配推荐；新增“我的申请状态”列，基于 `/api/cooperation/requests` 显示每个项目对当前学生的申请状态（未申请/待处理/已确认/已拒绝等）
  - 我的画像：双栏表单 + tag 组件维护技能画像和项目链接
  - 资源库、讨论区、组队互助、私信：统一使用 Element Plus 表格/表单/时间线等组件，呈现资源列表、话题列表、组队需求和类聊天界面

- 教师端：
  - 总览页：已发布项目/进行中合作/推荐学生/待处理请求四个指标卡片 + 最近项目时间线 + 合作项目表 + 合作请求与推荐学生列表
  - 项目与竞赛：左侧表格查看项目列表，右侧表单发布新项目，并新增“编辑”按钮 + 弹窗，调用 `PUT /api/teacher-posts/<id>` 修改项目信息
  - 学生匹配：左侧表格浏览学生画像，右侧详情卡片展示选中学生的技能与合作偏好，并提供“发出合作邀请”和“发私信”按钮
  - 合作项目：左侧选择项目，中间查看/添加里程碑，右侧查看与登记进度更新

- 管理员端：
  - 总览：统计卡片 + 三类待办事项列表 + “师生合作情况”区块，调用 `/api/admin/cooperations` 展示师生互选记录和汇总统计
  - 账号审核：表格显示待审核账号，提供“通过/禁用”操作，调用 `/api/admin/users/<id>/set-active`
  - 内容审核：表格展示待审核项目和资源，管理员可分别进行“通过/拒绝”操作

---

## 4. 测试与联调

### 4.1 后端自动化测试

后端已提供 pytest 测试：

```bash
cd backend
python3 -m pytest -q
```

覆盖：健康检查、管理员登录、教师注册待审核->管理员启用->发布项目->管理员审核->学生申请->双方确认->生成合作项目。

### 4.2 前后端联调

联调方式：
- 后端运行在 `http://localhost:5000`
- 前端运行在 `http://localhost:5173`
- `frontend/vite.config.ts` 已配置 `/api` 代理到后端

建议联调路径（答辩演示同路径）：
- 管理员登录 -> 审核教师账号
- 教师登录 -> 发布项目（待审核）
- 管理员审核项目
- 学生登录 -> 浏览项目 -> 申请加入
- 教师登录 -> 接受申请 -> 学生确认 -> 生成合作项目
- 教师在“合作项目”配置里程碑并更新进度
- 学生/教师私信沟通
- 上传资源 -> 管理员审核 -> 全平台可下载
