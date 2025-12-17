网工师生协作平台（Vue + Flask + MySQL）部署文档

本项目目录：
- `backend/`：Flask API（RBAC + 业务模块）
- `frontend/`：Vue3 前端（按角色分工作台）

由于当前环境未内置 `node`/`npm`/`docker`，仓库内提供的是可直接在你们电脑上按步骤启动的完整代码与部署说明。

---

## 1. 环境准备

### 1.1 后端环境

- Python：推荐 3.9+
- MySQL：推荐 8.0+

### 1.2 前端环境

- Node.js：推荐 18+（自带 npm）

---

## 2. 数据库安装与初始化（MySQL）

1）安装并启动 MySQL

2）创建数据库与用户（示例）

```sql
CREATE DATABASE collab_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'collab'@'localhost' IDENTIFIED BY 'collab123';
GRANT ALL PRIVILEGES ON collab_platform.* TO 'collab'@'localhost';
FLUSH PRIVILEGES;
```

3）准备后端环境变量

在项目根目录创建 `.env`（或在 shell 导出环境变量），示例：

```bash
DATABASE_URL="mysql+pymysql://collab:collab123@127.0.0.1:3306/collab_platform?charset=utf8mb4"
JWT_SECRET_KEY="change-me"
SECRET_KEY="change-me"
CORS_ORIGINS="http://localhost:5173"
```

注意：如果你使用 MySQL，需要额外安装驱动：

```bash
pip install pymysql
```

---

## 3. 后端启动（Flask）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/seed.py
python3 run_dev.py
```

健康检查：
- `http://127.0.0.1:5000/api/health`

---

## 4. 前端启动（Vue3 + Vite）

```bash
cd frontend
npm install
npm run dev
```

前端默认端口：
- `http://localhost:5173`

前端开发环境已配置代理：`/api -> http://localhost:5000`（见 `frontend/vite.config.ts`）。

---

## 5. 测试账号（seed 数据）

执行 `backend/scripts/seed.py` 后，会清空并重建数据库，并写入一批测试账号：

- 管理员：`admin / admin123`
- 教师示例：`1010001 / tea123456`（更多教师账号可在人员概览中查看）
- 学生示例：`221002501 / stu123456`（更多学生账号可在人员概览中查看）

用户名规范：
- 学生账号：**用户名为学号**（如 `221002501`）；
- 教师账号：**用户名为工号**（如 `1010001`）。

登录页需要选择角色（学生/教师/管理员），角色必须与账号一致。

---

## 6. 关键功能自测清单

### 6.1 学生端

- 登录(如果首次登陆且密码为管理员批量创建账号时的秘密，需要先修改密码) -> 学生工作台
- 完善“我的画像”（专业、年级、班级、技能、兴趣、可投入时间、可见性）
- 在“项目与匹配”中浏览教师发布项目（科研/大创/竞赛），支持按类型/教师以及“我点赞/我收藏/我加入”等维度筛选
- 发起合作申请（项目申请），查看自己的申请/邀请状态
- 在“合作项目进展”页面查看已确认合作项目的里程碑和进度更新，并提交个人进展
- 使用私信进行一对一沟通（支持附件与自动回复），通过顶部“消息”查看匹配进度、评论和新私信提醒
- 浏览资源库并上传资源（上传后在资源库立即可见，可编辑/删除自己的资源）
- 在讨论区发帖与回复，在组队互助区发布组队需求，并可编辑/删除自己发布的内容

### 6.2 教师端

- 登录 -> 教师工作台
- 在“项目与竞赛管理”中：
  - 通过“发布新项目”弹窗发布科研项目 / 大创项目 / 学科竞赛；
  - 左侧侧边栏选择项目，右侧查看项目详情与“选择该项目的学生”列表；
  - 对学生发起的申请点击“同意”后，直接达成双选并生成合作项目。
- 在“学生画像与匹配”中：按**专业、年级、技能和关键字**筛选学生，查看系统计算的技能评分，选择自己的项目并发送合作邀请（仅对尚未有合作流程记录的“学生+项目”组合可重复邀请）。
- 在“合作项目”中：为已确认合作的项目配置里程碑并记录进度更新，查看学生提交的进展。
- 使用“私信”与学生沟通（支持附件与自动回复），通过顶部“消息”查看匹配进度、评论和新私信提醒。

### 6.3 管理员端

- 登录 -> 管理员控制台
- 总览：查看平台用户数、教师发布项目数、资源数等汇总数据，以及近 14 天项目发布数和私信沟通量、热门研究方向与内容治理说明。
- 人员概览：
  - 按角色（学生/教师/管理员）筛选账号；
  - 支持按学号/工号或姓名搜索；
  - 左侧侧边栏选择人员，右侧查看详细信息：
    - 学生：可查看其画像摘要（专业、年级、班级、技能、兴趣、项目经历等）；
    - 教师：可查看其发布项目数量与已确认合作数量。
  - 支持创建账号、批量创建账号、重置密码。
- 项目概览：
-   - 左侧项目列表支持分页、按类型（科研/大创/竞赛）筛选和按项目名称搜索；
-   - 右侧查看项目详细信息，包括发布教师、招募信息以及选择该项目的所有学生及状态（已确认/已拒绝/待处理等）；
-   - 管理员可对某条合作请求执行“重置选择”，允许老师和学生重新发起双选。
- 内容治理与消息：管理员可在资源库/讨论区/组队互助中删除违规内容，并通过“私信 + 消息提醒”向相关师生发出提醒。

---

## 7. 答辩/提交用数据库导出

### 7.1 mysqldump

```bash
mysqldump -u collab -p collab_platform > collab_platform.sql
```

### 7.2 表结构 describe

```sql
USE collab_platform;
SHOW TABLES;
DESCRIBE users;
DESCRIBE teacher_posts;
DESCRIBE student_profiles;
```

将 `DESCRIBE <表名>` 的结果整理进 word 文档即可。
