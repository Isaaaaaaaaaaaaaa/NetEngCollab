"""
属性测试：增强功能的数据库字段约束和业务逻辑验证
Feature: enhanced-profile-and-project-management
"""

import pytest
from hypothesis import given, strategies as st, settings
from app import create_app
from app.extensions import db
from app.models import TeacherPost, CooperationRequest, User, TeacherProfile
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="function")
def app():
    """创建测试应用"""
    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """创建测试客户端"""
    return app.test_client()


def test_teacher_post_project_status_default(app):
    """测试 TeacherPost 的 project_status 默认值为 'recruiting'"""
    with app.app_context():
        teacher = User(
            username="test_teacher",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="Test Project",
            content="Test content"
        )
        db.session.add(post)
        db.session.commit()
        
        assert post.project_status == "recruiting"


def test_cooperation_request_student_info_fields(app):
    """测试 CooperationRequest 的 student_role 和 custom_status 字段"""
    with app.app_context():
        teacher = User(
            username="test_teacher",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        student = User(
            username="test_student",
            password_hash=generate_password_hash("password"),
            role="student",
            display_name="Test Student",
            is_active=True
        )
        db.session.add(teacher)
        db.session.add(student)
        db.session.commit()
        
        # 创建项目
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="Test Project",
            content="Test content"
        )
        db.session.add(post)
        db.session.commit()
        
        # 创建合作请求
        request = CooperationRequest(
            teacher_user_id=teacher.id,
            student_user_id=student.id,
            post_id=post.id,
            initiated_by="student",
            student_role="前端开发",
            custom_status="进行中"
        )
        db.session.add(request)
        db.session.commit()
        
        # 验证字段
        saved_request = db.session.query(CooperationRequest).filter_by(id=request.id).first()
        assert saved_request.student_role == "前端开发"
        assert saved_request.custom_status == "进行中"


# Feature: enhanced-profile-and-project-management, Property 12: Detailed information length validation
@given(
    detailed_info=st.text(min_size=0, max_size=10000, alphabet=st.characters(blacklist_categories=('Cs',)))
)
@settings(max_examples=20, deadline=None)
def test_property_12_detailed_info_length_valid(app, detailed_info):
    """
    Property 12: Detailed information length validation
    For any project detailed information content with length <= 10000 characters,
    the system should accept and store it successfully.
    Validates: Requirements 5.2
    """
    with app.app_context():
        teacher = User(
            username=f"teacher_{hash(detailed_info) % 10000}",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="Test Project",
            content="Test content",
            detailed_info=detailed_info,
            project_status="recruiting"
        )
        db.session.add(post)
        db.session.commit()
        
        # 验证数据已保存
        saved_post = db.session.query(TeacherPost).filter_by(id=post.id).first()
        assert saved_post is not None
        assert saved_post.detailed_info == detailed_info
        assert len(saved_post.detailed_info or "") <= 10000


def test_detailed_info_over_limit(app):
    """
    测试超过10000字符的详细信息
    数据库层面可以存储，但应用层应该拒绝
    """
    with app.app_context():
        teacher = User(
            username="test_teacher_long",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        # 创建超过10000字符的文本
        long_text = "a" * 10001
        
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="Test Project",
            content="Test content",
            detailed_info=long_text,
            project_status="recruiting"
        )
        db.session.add(post)
        db.session.commit()
        
        # 验证数据确实被存储了（数据库层面）
        saved_post = db.session.query(TeacherPost).filter_by(id=post.id).first()
        assert saved_post is not None
        # 但长度超过了限制
        assert len(saved_post.detailed_info) > 10000



def test_teacher_profile_api(app):
    """
    测试教师信息API接口
    Property 1: Teacher modal completeness
    Validates: Requirements 1.1, 1.2, 1.3
    """
    with app.app_context():
        # 创建教师用户
        teacher = User(
            username="api_test_teacher",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="API Test Teacher",
            email="teacher@test.com",
            phone="1234567890",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        # 创建教师画像
        profile = TeacherProfile(
            user_id=teacher.id,
            title="教授",
            organization="计算机学院",
            bio="专注于人工智能研究",
            research_tags_json='["机器学习", "深度学习"]',
            auto_reply="工作日24小时内回复"
        )
        db.session.add(profile)
        db.session.commit()
        
        # 创建一些项目
        post1 = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="AI项目",
            content="测试内容",
            outcome="发表论文1篇"
        )
        post2 = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="innovation",
            title="大创项目",
            content="测试内容"
        )
        db.session.add(post1)
        db.session.add(post2)
        db.session.commit()
    
    # 测试API
    client = app.test_client()
    response = client.get(f'/api/teachers/{teacher.id}/profile')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # 验证所有必需字段都存在
    assert data['id'] == teacher.id
    assert data['display_name'] == "API Test Teacher"
    assert data['email'] == "teacher@test.com"
    assert data['phone'] == "1234567890"
    assert data['title'] == "教授"
    assert data['organization'] == "计算机学院"
    assert data['bio'] == "专注于人工智能研究"
    assert data['research_tags'] == ["机器学习", "深度学习"]
    assert data['auto_reply'] == "工作日24小时内回复"
    
    # 验证统计数据
    assert 'stats' in data
    assert data['stats']['total_projects'] == 2
    assert data['stats']['confirmed_projects'] == 0
    
    # 验证最近成就
    assert 'recent_achievements' in data
    assert "发表论文1篇" in data['recent_achievements']


def test_teacher_profile_not_found(app):
    """测试教师不存在的情况"""
    client = app.test_client()
    response = client.get('/api/teachers/99999/profile')
    
    assert response.status_code == 404
    data = response.get_json()
    assert '教师不存在' in data['message']



def test_project_detailed_info_api(app):
    """
    测试项目详细信息API
    Property 13: Project detail modal completeness
    Validates: Requirements 5.3, 5.4
    """
    with app.app_context():
        # 创建教师
        teacher = User(
            username="project_test_teacher",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Project Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        # 创建项目（包含详细信息）
        detailed_info = "这是一个详细的项目描述，包含了项目的背景、目标、技术要求等信息。" * 50  # 约2500字符
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="测试项目",
            content="项目简介",
            detailed_info=detailed_info,
            tech_stack_json='["Python", "Flask"]',
            tags_json='["AI", "机器学习"]',
            recruit_count=3,
            duration="6个月",
            project_status="recruiting"
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
    
    # 测试GET接口
    client = app.test_client()
    response = client.get('/api/teacher-posts')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # 找到我们创建的项目
    project = None
    for item in data['items']:
        if item['id'] == post_id:
            project = item
            break
    
    assert project is not None
    assert project['title'] == "测试项目"
    assert project['content'] == "项目简介"
    assert project['detailed_info'] == detailed_info
    assert project['tech_stack'] == ["Python", "Flask"]
    assert project['tags'] == ["AI", "机器学习"]
    assert project['recruit_count'] == 3
    assert project['duration'] == "6个月"
    assert project['project_status'] == "recruiting"


def test_project_detailed_info_length_validation(app):
    """
    测试项目详细信息长度验证
    验证超过10000字符的详细信息会被拒绝
    """
    with app.app_context():
        # 创建教师
        teacher = User(
            username="validation_test_teacher",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Validation Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        # 获取JWT token
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(teacher.id))
    
    # 测试创建项目时的长度验证
    client = app.test_client()
    
    # 测试超长的详细信息（超过10000字符）
    long_detailed_info = "a" * 10001
    response = client.post(
        '/api/teacher-posts',
        json={
            "title": "测试项目",
            "content": "项目简介",
            "detailed_info": long_detailed_info,
            "post_type": "project"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert "详细信息不能超过10000字符" in data['message']
    
    # 测试正常长度的详细信息（10000字符以内）
    normal_detailed_info = "a" * 10000
    response = client.post(
        '/api/teacher-posts',
        json={
            "title": "测试项目2",
            "content": "项目简介2",
            "detailed_info": normal_detailed_info,
            "post_type": "project"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data



# Feature: enhanced-profile-and-project-management, Property 3: Project-based student filtering
@given(
    num_students=st.integers(min_value=1, max_value=10),
    num_projects=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[pytest.HealthCheck.function_scoped_fixture])
def test_property_3_project_based_student_filtering(app, num_students, num_projects):
    """
    Property 3: Project-based student filtering
    For any project and set of students, when a teacher selects that project,
    the displayed student list should contain only students who have applied to
    or been matched with that specific project, sorted by matching score or application time.
    Validates: Requirements 2.2, 2.3
    """
    with app.app_context():
        # 创建教师
        teacher = User(
            username=f"teacher_prop3_{num_students}_{num_projects}",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        # 创建多个项目
        projects = []
        for i in range(num_projects):
            post = TeacherPost(
                teacher_user_id=teacher.id,
                post_type="project",
                title=f"Project {i}",
                content=f"Content {i}",
                project_status="recruiting"
            )
            db.session.add(post)
            projects.append(post)
        db.session.commit()
        
        # 创建多个学生
        students = []
        for i in range(num_students):
            student = User(
                username=f"student_prop3_{num_students}_{num_projects}_{i}",
                password_hash=generate_password_hash("password"),
                role="student",
                display_name=f"Student {i}",
                is_active=True
            )
            db.session.add(student)
            students.append(student)
        db.session.commit()
        
        # 为每个项目创建一些合作请求（随机分配学生）
        import random
        random.seed(num_students * 100 + num_projects)
        
        project_to_students = {}
        for project in projects:
            # 每个项目随机选择一些学生申请
            num_applicants = random.randint(1, min(num_students, 5))
            applicants = random.sample(students, num_applicants)
            project_to_students[project.id] = set()
            
            for student in applicants:
                req = CooperationRequest(
                    teacher_user_id=teacher.id,
                    student_user_id=student.id,
                    post_id=project.id,
                    initiated_by="student",
                    final_status="pending"
                )
                db.session.add(req)
                project_to_students[project.id].add(student.id)
        db.session.commit()
        
        # 测试每个项目的筛选
        client = app.test_client()
        for project in projects:
            response = client.get(f'/api/students?project_id={project.id}')
            assert response.status_code == 200
            
            data = response.get_json()
            returned_student_ids = {item['user']['id'] for item in data['items']}
            expected_student_ids = project_to_students[project.id]
            
            # 验证返回的学生列表只包含申请了该项目的学生
            assert returned_student_ids == expected_student_ids, \
                f"Project {project.id}: Expected {expected_student_ids}, got {returned_student_ids}"
            
            # 验证排序：按匹配分数降序
            if len(data['items']) > 1:
                scores = [item['skill_score'] for item in data['items']]
                # 检查分数是否按降序排列（允许相同分数）
                for i in range(len(scores) - 1):
                    assert scores[i] >= scores[i + 1], \
                        f"Scores not sorted correctly: {scores}"


def test_project_filtering_no_applicants(app):
    """
    测试没有申请者的项目筛选
    当项目没有任何申请时，应该返回空列表
    """
    with app.app_context():
        # 创建教师和项目
        teacher = User(
            username="teacher_no_applicants",
            password_hash=generate_password_hash("password"),
            role="teacher",
            display_name="Test Teacher",
            is_active=True
        )
        db.session.add(teacher)
        db.session.commit()
        
        post = TeacherPost(
            teacher_user_id=teacher.id,
            post_type="project",
            title="Empty Project",
            content="No applicants",
            project_status="recruiting"
        )
        db.session.add(post)
        db.session.commit()
        
        # 创建一些学生但不申请该项目
        for i in range(3):
            student = User(
                username=f"student_no_app_{i}",
                password_hash=generate_password_hash("password"),
                role="student",
                display_name=f"Student {i}",
                is_active=True
            )
            db.session.add(student)
        db.session.commit()
    
    # 测试筛选
    client = app.test_client()
    response = client.get(f'/api/students?project_id={post.id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 0


def test_project_filtering_all_students(app):
    """
    测试不指定项目时返回所有学生
    """
    with app.app_context():
        # 创建多个学生
        num_students = 5
        for i in range(num_students):
            student = User(
                username=f"student_all_{i}",
                password_hash=generate_password_hash("password"),
                role="student",
                display_name=f"Student {i}",
                is_active=True
            )
            db.session.add(student)
        db.session.commit()
    
    # 测试不带 project_id 参数
    client = app.test_client()
    response = client.get('/api/students')
    
    assert response.status_code == 200
    data = response.get_json()
    # 应该返回所有学生（至少包含我们创建的5个）
    assert len(data['items']) >= num_students
