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

执行 `backend/scripts/seed.py` 后，会写入以下账号：

- 管理员：`admin / admin123`
- 教师：`teacher1 / teacher123`，`teacher2 / teacher123`
- 学生：`student1 / student123`，`student2 / student123`，`student3 / student123`，`student4 / student123`

登录页需要选择角色（学生/教师/管理员），角色必须与账号一致。

---

## 6. 关键功能自测清单

### 6.1 学生端

- 登录 -> 学生工作台
- 完善“我的画像”（技能、兴趣、可投入时间、可见性）
- 浏览教师发布项目（科研/大创/竞赛），收藏
- 发起合作申请（项目申请）
- 私信沟通
- 浏览资源库并上传资源（提交后等待管理员审核通过）
- 话题讨论区发帖
- 组队互助区发布需求

### 6.2 教师端

- 登录 -> 教师工作台
- 在“项目与竞赛管理”中：
  - 通过“发布新项目”弹窗发布科研项目 / 大创项目 / 学科竞赛
  - 左侧侧边栏选择项目，右侧查看项目详情与“选择该项目的学生”列表
  - 对学生发起的申请点击“同意”后，直接达成双选并生成合作项目
- 在“学生画像与匹配”中：按方向/技能筛选学生，选择自己的项目并发送合作邀请
- 在“合作项目”中：为已确认合作的项目配置里程碑并记录进度更新
- 使用“私信”与学生沟通

### 6.3 管理员端

- 登录 -> 管理员控制台
- 总览：查看平台用户数、项目数、资源数等汇总数据
- 人员概览：
  - 按角色（学生/教师/管理员）筛选账号
  - 左侧侧边栏选择人员，右侧查看详细信息
  - 支持创建账号、重置密码
- 项目概览：
  - 左侧查看所有项目列表，右侧查看项目详细信息
  - 包含发布教师、招募信息、以及选择该项目的所有学生及状态（已确认/已拒绝/待处理等）

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
