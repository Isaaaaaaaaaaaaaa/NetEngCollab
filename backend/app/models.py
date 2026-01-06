import enum
from datetime import datetime

from .extensions import db


class Role(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class Visibility(str, enum.Enum):
    public = "public"
    teacher_only = "teacher_only"
    student_only = "student_only"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CooperationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    confirmed = "confirmed"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, index=True)

    display_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(32), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    major = db.Column(db.String(128), nullable=True)
    grade = db.Column(db.String(32), nullable=True)
    class_name = db.Column(db.String(64), nullable=True)
    direction = db.Column(db.String(128), nullable=True)
    skills_json = db.Column(db.Text, nullable=False, default="[]")
    project_links_json = db.Column(db.Text, nullable=False, default="[]")
    interests_json = db.Column(db.Text, nullable=False, default="[]")
    experiences_json = db.Column(db.Text, nullable=False, default="[]")
    weekly_hours = db.Column(db.Integer, nullable=True)
    prefer_local = db.Column(db.Boolean, default=False, nullable=False)
    accept_cross = db.Column(db.Boolean, default=True, nullable=False)
    resume_file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)
    visibility = db.Column(db.String(16), default=Visibility.public.value, nullable=False)
    auto_reply = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TeacherProfile(db.Model):
    __tablename__ = "teacher_profiles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    title = db.Column(db.String(64), nullable=True)
    organization = db.Column(db.String(128), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    research_tags_json = db.Column(db.Text, nullable=False, default="[]")
    auto_reply = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    storage_name = db.Column(db.String(255), nullable=False, unique=True)
    content_type = db.Column(db.String(128), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TeacherPost(db.Model):
    __tablename__ = "teacher_posts"

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_type = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    detailed_info = db.Column(db.Text, nullable=True)  # 新增：项目详细信息字段
    tech_stack_json = db.Column(db.Text, nullable=False, default="[]")
    tags_json = db.Column(db.Text, nullable=False, default="[]")
    recruit_count = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.String(64), nullable=True)
    outcome = db.Column(db.String(128), nullable=True)
    contact = db.Column(db.String(128), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    attachment_file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)
    visibility = db.Column(db.String(16), default=Visibility.public.value, nullable=False)
    review_status = db.Column(db.String(16), default=ReviewStatus.pending.value, nullable=False, index=True)
    project_status = db.Column(db.String(32), default="recruiting", nullable=False, index=True)  # 新增：项目状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    target_type = db.Column(db.String(32), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=False, index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Reaction(db.Model):
    __tablename__ = "reactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    target_type = db.Column(db.String(32), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=False, index=True)
    reaction_type = db.Column(db.String(16), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "target_type", "target_id", "reaction_type", name="uq_reaction"
        ),
    )


class CooperationRequest(db.Model):
    __tablename__ = "cooperation_requests"

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("teacher_posts.id"), nullable=True, index=True)
    initiated_by = db.Column(db.String(16), nullable=False)
    teacher_status = db.Column(db.String(16), default=CooperationStatus.pending.value, nullable=False)
    student_status = db.Column(db.String(16), default=CooperationStatus.pending.value, nullable=False)
    final_status = db.Column(db.String(16), default=CooperationStatus.pending.value, nullable=False, index=True)
    student_role = db.Column(db.String(64), nullable=True)  # 新增：学生在项目中的角色
    custom_status = db.Column(db.String(64), nullable=True)  # 新增：自定义状态标签
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class CooperationProject(db.Model):
    __tablename__ = "cooperation_projects"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("cooperation_requests.id"), nullable=False, unique=True)
    title = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Milestone(db.Model):
    __tablename__ = "milestones"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("cooperation_projects.id"), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="todo")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ProgressUpdate(db.Model):
    __tablename__ = "progress_updates"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("cooperation_projects.id"), nullable=False, index=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    attachment_file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    uploader_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    resource_type = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(64), nullable=True, index=True)
    tags_json = db.Column(db.Text, nullable=False, default="[]")
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    review_status = db.Column(db.String(16), default=ReviewStatus.pending.value, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ForumTopic(db.Model):
    __tablename__ = "forum_topics"

    id = db.Column(db.Integer, primary_key=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(64), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags_json = db.Column(db.Text, nullable=False, default="[]")
    review_status = db.Column(db.String(16), default=ReviewStatus.approved.value, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ForumReply(db.Model):
    __tablename__ = "forum_replies"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("forum_topics.id"), nullable=False, index=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TeamupPost(db.Model):
    __tablename__ = "teamup_posts"

    id = db.Column(db.Integer, primary_key=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_kind = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    needed_roles_json = db.Column(db.Text, nullable=False, default="[]")
    tags_json = db.Column(db.Text, nullable=False, default="[]")
    review_status = db.Column(db.String(16), default=ReviewStatus.approved.value, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("teacher_user_id", "student_user_id", name="uq_conversation_pair"),
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    notif_type = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    payload_json = db.Column(db.Text, nullable=False, default="{}")
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
