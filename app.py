from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime, timedelta
from flask_cors import CORS
from ocr_utils import get_text_from_image, extract_award_level
import os
import jwt
from functools import wraps

# 需要安装的依赖包：
# pip install flask flask-cors flask-sqlalchemy pyjwt pillow

# 初始化Flask应用
app = Flask(__name__)
# 允许跨域请求，并配置允许携带cookies（开发环境允许所有来源）
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
# JWT密钥（实际项目请使用复杂密钥）
app.config['SECRET_KEY'] = 'your-secret-key'

# ========== 数据库配置代码 ==========
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

# 使用SQLite文件数据库，数据持久化保存
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baoyan_helper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据库迁移函数
def migrate_database():
    """
    动态检查并更新数据库表结构，添加缺失的列
    这对于从旧版本升级到新版本特别有用，不需要删除现有数据
    """
    print("\n🔄 开始数据库迁移检查...")
    
    try:
        # 获取数据库表的当前结构
        inspector = inspect(db.engine)
        
        # 处理teacher_profile表
        print("📋 检查teacher_profile表结构...")
        columns = inspector.get_columns('teacher_profile')
        column_names = [column['name'] for column in columns]
        
        # 检查需要添加的列
        columns_to_add = []
        if 'gender' not in column_names:
            columns_to_add.append('ALTER TABLE teacher_profile ADD COLUMN gender VARCHAR(10)')
        if 'ethnicity' not in column_names:
            columns_to_add.append('ALTER TABLE teacher_profile ADD COLUMN ethnicity VARCHAR(50)')
        if 'political_status' not in column_names:
            columns_to_add.append('ALTER TABLE teacher_profile ADD COLUMN political_status VARCHAR(50)')
        if 'id_card' not in column_names:
            columns_to_add.append('ALTER TABLE teacher_profile ADD COLUMN id_card VARCHAR(30)')
        
        # 处理student_profile表
        print("📋 检查student_profile表结构...")
        columns = inspector.get_columns('student_profile')
        column_names = [column['name'] for column in columns]
        
        # 检查需要添加的列
        if 'ethnicity' not in column_names:
            columns_to_add.append('ALTER TABLE student_profile ADD COLUMN ethnicity VARCHAR(50)')
        if 'political_status' not in column_names:
            columns_to_add.append('ALTER TABLE student_profile ADD COLUMN political_status VARCHAR(50)')
        if 'id_card' not in column_names:
            columns_to_add.append('ALTER TABLE student_profile ADD COLUMN id_card VARCHAR(30)')
        
        # 处理application表，添加score字段
        print("📋 检查application表结构...")
        columns = inspector.get_columns('application')
        column_names = [column['name'] for column in columns]
        
        # 检查需要添加的列
        if 'score' not in column_names:
            columns_to_add.append('ALTER TABLE application ADD COLUMN score FLOAT')
        
        # 执行添加列的操作
        if columns_to_add:
            print(f"发现需要添加的列: {len(columns_to_add)}")
            with db.engine.connect() as conn:
                for stmt in columns_to_add:
                    print(f"执行SQL: {stmt}")
                    conn.execute(text(stmt))
                conn.commit()
            print("✅ 数据库迁移成功完成!")
        else:
            print("✅ 数据库结构已是最新，无需迁移")
            
    except OperationalError as e:
        print(f"⚠️  数据库迁移时出错: {str(e)}")
        print("这可能是因为数据库文件较旧或不存在。应用将在首次运行时自动创建所需的表结构。")
    except Exception as e:
        print(f"⚠️  数据库迁移时发生未预期的错误: {str(e)}")


# ================== 工具函数和装饰器定义 ==================

# 页面访问认证装饰器（简化版）
def page_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import session
        
        # 检查session中是否有登录信息
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        
        if not user_id or not user_role:
            print("❌ 未登录访问受限页面，跳转到首页")
            return redirect('/')
        
        # 验证用户是否仍然存在于数据库中
        current_user = User.query.filter_by(id=user_id, role=user_role).first()
        if not current_user:
            print("❌ session用户信息无效，清除session并跳转首页")
            session.clear()
            return redirect('/')
        
        return f(current_user, *args, **kwargs)

    return decorated


# 生成JWT令牌
def generate_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


# API访问认证装饰器（用于后端API接口）
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import session, request, jsonify
        
        # 检查session中是否有登录信息
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        
        if not user_id or not user_role:
            # 对于API请求，返回JSON错误响应
            if request.path.startswith('/api/'):
                return jsonify({"code": 401, "message": "未登录，请先登录"}), 401
            else:
                # 对于页面请求，重定向到首页
                return redirect('/')
        
        # 验证用户是否仍然存在于数据库中
        current_user = User.query.filter_by(id=user_id, role=user_role).first()
        if not current_user:
            if request.path.startswith('/api/'):
                return jsonify({"code": 401, "message": "用户信息无效，请重新登录"}), 401
            else:
                session.clear()
                return redirect('/')
        
        return f(current_user, *args, **kwargs)
    
    return decorated


# ================== 工具函数和装饰器定义结束 ==================


# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' 或 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系定义
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False)
    student_applications = db.relationship(
        'Application',
        foreign_keys='Application.student_id',
        backref='student',
        lazy=True
    )
    reviewed_applications = db.relationship(
        'Application',
        foreign_keys='Application.reviewer_id',
        backref='reviewer',
        lazy=True
    )


# 学生资料模型
class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    gender = db.Column(db.String(10))
    major = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    department = db.Column(db.String(100))  # 系别
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    # 个人信息字段
    ethnicity = db.Column(db.String(50))  # 民族
    political_status = db.Column(db.String(50))  # 政治面貌
    id_card = db.Column(db.String(30))  # 身份证号
    # 成绩字段
    total_score = db.Column(db.Float)  # 总成绩
    academic_score = db.Column(db.Float)  # 学业成绩
    research_score = db.Column(db.Float)  # 科研竞赛总分
    social_score = db.Column(db.Float)  # 社会工作总分
    honor_score = db.Column(db.Float)  # 荣誉称号总分
    other_score = db.Column(db.Float)  # 其他加分总分
    
    def __init__(self, user_id=None, gender=None, major=None, grade=None, department=None,
                 phone=None, email=None, ethnicity=None, 
                 political_status=None, id_card=None, total_score=0.0,
                 academic_score=0.0, research_score=0.0, social_score=0.0,
                 honor_score=0.0, other_score=0.0):
        self.user_id = user_id
        self.gender = gender
        self.major = major
        self.grade = grade
        self.department = department
        self.phone = phone
        self.email = email
        self.ethnicity = ethnicity
        self.political_status = political_status
        self.id_card = id_card
        self.total_score = total_score
        self.academic_score = academic_score
        self.research_score = research_score
        self.social_score = social_score
        self.honor_score = honor_score
        self.other_score = other_score


# 教师资料模型
class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    department = db.Column(db.String(100))
    title = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    # 添加个人信息字段
    gender = db.Column(db.String(10))  # 性别
    ethnicity = db.Column(db.String(50))  # 民族
    political_status = db.Column(db.String(50))  # 政治面貌
    id_card = db.Column(db.String(30))  # 身份证号
    
    def __init__(self, user_id, gender=None, ethnicity=None, political_status=None, id_card=None, 
                 department=None, title=None, phone=None, email=None):
        self.user_id = user_id
        self.gender = gender
        self.ethnicity = ethnicity
        self.political_status = political_status
        self.id_card = id_card
        self.department = department
        self.title = title
        self.phone = phone
        self.email = email


# 申请材料模型
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'honor', 'sci', 'social', 'other'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    attachments = db.Column(db.Text)  # 附件路径，逗号分隔
    award_level = db.Column(db.String(20))
    score = db.Column(db.Float)  # 申请分值
    status = db.Column(db.String(20), default='pending')
    apply_time = db.Column(db.DateTime, default=datetime.now)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_time = db.Column(db.DateTime)
    review_remark = db.Column(db.Text)


# 公告模型
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    publish_time = db.Column(db.DateTime, default=datetime.now)
    # 关系定义
    publisher = db.relationship('User', backref='published_announcements')


# 公告读取状态模型
class AnnouncementReadStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_time = db.Column(db.DateTime)
    # 关系定义
    announcement = db.relationship('Announcement', backref='read_statuses')
    student = db.relationship('User', backref='announcement_read_statuses')


# ---------------------- 前端页面路由配置 ----------------------
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
@app.route('/login.html', methods=['GET'])
def login_page():
    """登录页面路由已弃用，直接跳转到首页"""
    return redirect('/')

@app.route('/student-login.html', methods=['GET'])
def student_login_page():
    """学生登录页面路由已弃用，直接跳转到首页"""
    return redirect('/')

@app.route('/teacher-login.html', methods=['GET'])
def teacher_login_page():
    """教师登录页面路由已弃用，直接跳转到首页"""
    return redirect('/')





@app.route('/reset-password.html', methods=['GET'])
def reset_password():
    return render_template('reset-password.html')


@app.route('/help.html', methods=['GET'])
def help_page():
    return render_template('help.html')


@app.route('/honor-title.html', methods=['GET'])
def honor_title():
    return render_template('honor-title.html')


@app.route('/honor-title-application.html', methods=['GET'])
def honor_title_application():
    return render_template('honor-title-application.html')


@app.route('/honor-title-failed.html', methods=['GET'])
def honor_title_failed():
    return render_template('honor-title-failed.html')


@app.route('/honor-title-passed.html', methods=['GET'])
def honor_title_passed():
    return render_template('honor-title-passed.html')


@app.route('/honor-title-pending.html', methods=['GET'])
def honor_title_pending():
    return render_template('honor-title-pending.html')


@app.route('/honor-titles-passed.html', methods=['GET'])
def honor_titles_passed():
    return render_template('honor-titles-passed.html')


@app.route('/application-records.html', methods=['GET'])
def application_records():
    return render_template('application-records.html')


@app.route('/data-management.html', methods=['GET'])
def data_management():
    return render_template('data-management.html')


@app.route('/new-application.html', methods=['GET'])
@page_auth_required
def new_application(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/')
    return render_template('new-application.html')


@app.route('/other-additions-passed.html', methods=['GET'])
def other_additions_passed():
    return render_template('other-additions-passed.html')


@app.route('/other-application.html', methods=['GET'])
def other_application():
    return render_template('other-application.html')


@app.route('/other-records.html', methods=['GET'])
def other_records():
    return render_template('other-records.html')


@app.route('/other-records-failed.html', methods=['GET'])
def other_records_failed():
    return render_template('other-records-failed.html')


@app.route('/other-records-passed.html', methods=['GET'])
def other_records_passed():
    return render_template('other-records-passed.html')


@app.route('/other-records-pending.html', methods=['GET'])
def other_records_pending():
    return render_template('other-records-pending.html')


@app.route('/project-detail.html', methods=['GET'])
def project_detail():
    return render_template('project-detail.html')


# ================== 调试接口 ==================
@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    """调试接口：查看数据库中的所有用户"""
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'password': user.password,  # 仅用于调试，生产环境应删除
                'name': user.name,
                'role': user.role,
                'created_at': user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        print(f"=== 数据库调试信息 ===")
        print(f"数据库中共有 {len(user_list)} 个用户")
        for user_info in user_list:
            print(f"用户: {user_info}")
        print(f"=== 数据库调试信息结束 ===")
        
        return jsonify({
            "code": 200,
            "message": "数据库用户列表",
            "data": {
                "total": len(user_list),
                "users": user_list
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"查询用户失败: {str(e)}"
        }), 500


@app.route('/scientific-competition.html', methods=['GET'])
def scientific_competition():
    return render_template('scientific-competition.html')


@app.route('/scientific-competition-application.html', methods=['GET'])
def scientific_competition_application():
    return render_template('scientific-competition-application.html')


@app.route('/scientific-competition-failed.html', methods=['GET'])
def scientific_competition_failed():
    return render_template('scientific-competition-failed.html')


@app.route('/scientific-competition-passed.html', methods=['GET'])
def scientific_competition_passed():
    return render_template('scientific-competition-passed.html')


@app.route('/scientific-competition-pending.html', methods=['GET'])
def scientific_competition_pending():
    return render_template('scientific-competition-pending.html')


@app.route('/social-work.html', methods=['GET'])
def social_work():
    return render_template('social-work.html')


@app.route('/social-work-application.html', methods=['GET'])
def social_work_application():
    return render_template('social-work-application.html')


@app.route('/social-work-failed.html', methods=['GET'])
def social_work_failed():
    return render_template('social-work-failed.html')


@app.route('/social-work-passed.html', methods=['GET'])
def social_work_passed():
    return render_template('social-work-passed.html')


@app.route('/social-work-pending.html', methods=['GET'])
def social_work_pending():
    return render_template('social-work-pending.html')


@app.route('/student-dashboard.html', methods=['GET'])
@app.route('/student-dashboard', methods=['GET'])
def student_dashboard_page():
    print('🔍 学生仪表板页面访问检查')
    from flask import session
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    user_name = session.get('user_name')
    
    print(f'🔍 Session检查 - user_id: {user_id}, user_role: {user_role}, user_name: {user_name}')
    
    # 只检查是否登录，不强制角色匹配（前端会做角色检查）
    if not user_id or not user_role:
        print('❌ Session中无登录信息，跳转到登录页')
        return redirect('/')
    
    print('✅ Session验证通过，返回学生仪表板')
    return render_template('student-dashboard.html')


@app.route('/student-list.html', methods=['GET'])
def student_list():
    return render_template('student-list.html')


@app.route('/student-notifications.html', methods=['GET'])
@page_auth_required
def student_notifications(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/')
    return render_template('student-notifications.html')


@app.route('/student-security.html', methods=['GET'])
@page_auth_required
def student_security(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/')
    return render_template('student-security.html')


@app.route('/student-transcript.html', methods=['GET'])
@page_auth_required
def student_transcript(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/')
    return render_template('student-transcript.html')


@app.route('/student-records.html', methods=['GET'])
@page_auth_required
def student_records(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('student-records.html')


@app.route('/student-profile.html', methods=['GET'])
@page_auth_required
def student_profile(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('student-profile.html')


@app.route('/submission-guide.html', methods=['GET'])
def submission_guide():
    return render_template('submission-guide.html')


@app.route('/teacher-announcement-records.html', methods=['GET'])
def teacher_announcement_records():
    return render_template('teacher-announcement-records.html')


@app.route('/teacher-dashboard.html', methods=['GET'])
def teacher_dashboard():
    print('🔍 教师仪表板页面访问检查')
    from flask import session
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    user_name = session.get('user_name')
    
    print(f'🔍 Session检查 - user_id: {user_id}, user_role: {user_role}, user_name: {user_name}')
    
    # 只检查是否登录，不强制角色匹配（前端会做角色检查）
    if not user_id or not user_role:
        print('❌ Session中无登录信息，跳转到首页')
        return redirect('/')
    
    print('✅ Session验证通过，返回教师仪表板')
    return render_template('teacher-dashboard.html')


@app.route('/teacher-notifications.html', methods=['GET'])
@page_auth_required
def teacher_notifications(current_user):
    if current_user.role != 'teacher':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('teacher-notifications.html')


@app.route('/teacher-profile.html', methods=['GET'])
@page_auth_required
def teacher_profile(current_user):
    if current_user.role != 'teacher':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('teacher-profile.html')


@app.route('/teacher-publish-announcement.html', methods=['GET'])
def teacher_publish_announcement():
    return render_template('teacher-publish-announcement.html')


@app.route('/teacher-review-category.html', methods=['GET'])
def teacher_review_category():
    return render_template('teacher-review-category.html')


@app.route('/teacher-review-detail.html', methods=['GET'])
def teacher_review_detail():
    return render_template('teacher-review-detail.html')


@app.route('/teacher-review-management.html', methods=['GET'])
def teacher_review_management():
    return render_template('teacher-review-management.html')


@app.route('/teacher-security.html', methods=['GET'])
@page_auth_required
def teacher_security(current_user):
    if current_user.role != 'teacher':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('teacher-security.html')


@app.route('/transcript-category.html', methods=['GET'])
def transcript_category():
    return render_template('transcript-category.html')


@app.route('/transcript-detail.html', methods=['GET'])
def transcript_detail():
    return render_template('transcript-detail.html')


@app.route('/index.html')
def index_html():
    return redirect('/')


# ---------------------- 前端页面路由配置结束 ----------------------

# ================== 用户会话管理接口 ==================

# ---------------------- 后端接口配置 ----------------------

@app.route('/api/auth/login', methods=['POST'])
def login():
    print("\n🔍 === 登录API被调用 ===")
    
    # 获取前端提交的账号、密码、角色
    try:
        data = request.get_json()
        print(f"📦 接收到的数据: {data}")
        
        if data is None:
            print("❌ 接收到的数据为空")
            return jsonify({"code": 400, "message": "请求数据为空"}), 400
            
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        
        print(f"👤 用户名: {username}")
        print(f"🔒 密码: {password}")
        print(f"🎭 角色: {role}")

    except Exception as e:
        print(f"❌ 解析JSON数据失败: {e}")
        return jsonify({"code": 400, "message": "请求数据格式错误"}), 400

    # 1. 验证参数是否完整
    if not all([username, password, role]):
        print("❌ 参数不完整")
        return jsonify({"code": 400, "message": "请输入用户名、密码和角色"})

    # 2. 验证角色值是否有效
    if role not in ['student', 'teacher']:
        print(f"❌ 无效的角色类型: {role}")
        return jsonify({"code": 400, "message": "无效的角色类型"})

    # 3. 查询数据库：是否存在该用户名且角色匹配的用户
    # 关键：必须同时匹配用户名和角色（防止学生用教师账号登录）
    print(f"🔍 正在查询数据库: username={username}, role={role}")
    user = User.query.filter_by(username=username, role=role).first()
    
    if user:
        print(f"✅ 找到用户: {user.name} (ID: {user.id}, 角色: {user.role})")
    else:
        print(f"❌ 用户不存在: username={username}, role={role}")
        # 打印数据库中所有用户用于调试
        all_users = User.query.all()
        print(f"📊 数据库中共有 {len(all_users)} 个用户:")
        for u in all_users:
            print(f"   - {u.username} ({u.role})")
        return jsonify({"code": 401, "message": "用户名或角色错误，请使用正确的账号登录"})

    # 4. 验证密码是否正确（与数据库中存储的密码比对）
    print(f"🔐 验证密码: 数据库密码={user.password}, 输入密码={password}")
    if user.password != password:
        print(f"❌ 密码错误")
        return jsonify({"code": 401, "message": "密码错误，请重新输入"})

    print("✅ 密码验证通过")
    
    # 6. 同时设置session和生成JWT token（双重保障）
    from flask import session
    session['user_id'] = user.id
    session['user_role'] = role
    session['user_name'] = user.name
    session.permanent = True  # 设置session为持久性
    session.modified = True   # 标记session为已修改
    
    print("✅ Session设置完成")
    
    # 修复JWT token编码和datetime弃用警告
    from datetime import timezone
    try:
        token_payload = {
            'sub': str(user.id),
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)  # 24小时过期
        }
        print(f"🔑 生成JWT payload: {token_payload}")
        
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        # 确保token是字符串格式（兼容不同Python版本）
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        print(f"✅ JWT token生成成功: {token[:20] if token else 'None'}...")
        
    except Exception as e:
        print(f"❌ JWT token生成失败: {e}")
        return jsonify({"code": 500, "message": "Token生成失败"}), 500

    # 7. 所有验证通过，允许登录
    print("🎉 登录成功，返回成功响应")
    
    response_data = {
        "code": 200,
        "message": "登录成功",
        "data": {
            "role": role,
            "token": token,
            "user_id": user.id,
            "user_name": user.name
        }
    }
    
    print(f"📤 返回响应: {response_data}")
    
    return jsonify(response_data)


# 兼容旧接口路径
@app.route('/api/login', methods=['POST'])
def login_old():
    # 直接使用新的安全登录逻辑
    return login()


# 获取学生个人信息接口
@app.route('/api/students/profile', methods=['GET'])
@token_required
def get_student_profile(current_user):
    print("\n🔍 === 获取学生个人信息API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'student':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅学生可访问"}), 403
    
    # 查找学生资料，如果不存在则创建
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
    
    # 确保profile对象有所有必要的属性（向后兼容）
    if not hasattr(profile, 'ethnicity'):
        profile.ethnicity = None
    if not hasattr(profile, 'political_status'):
        profile.political_status = None
    if not hasattr(profile, 'id_card'):
        profile.id_card = None
        db.session.commit()
        print(f"✅ 为用户创建了新的学生资料: {current_user.name}")
    
    # 确保profile对象有所有必要的属性（向后兼容）
    if not hasattr(profile, 'ethnicity'):
        profile.ethnicity = None
    if not hasattr(profile, 'political_status'):
        profile.political_status = None
    if not hasattr(profile, 'id_card'):
        profile.id_card = None
    
    # 构建返回数据，使用数据库中的值或合理的默认值
    student_data = {
        "id": current_user.username,  # 学号
        "name": current_user.name,
        "major": profile.major or "未设置",
        "grade": profile.grade or "未设置",
        "department": profile.department or "未设置",  # 从数据库获取系别信息
        "gender": profile.gender or "未设置",
        "nationality": profile.ethnicity or "未设置",  # 从数据库获取民族信息
        "political": profile.political_status or "未设置",  # 从数据库获取政治面貌
        "idNumber": profile.id_card or "未设置",  # 从数据库获取身份证号
        "phone": profile.phone or "未设置",
        "email": profile.email or "未设置"
    }
    
    print(f"✅ 学生个人信息获取成功")
    return jsonify({
        "code": 200,
        "message": "获取成功",
        "data": student_data
    }), 200

# 更新学生个人信息接口
@app.route('/api/students/profile', methods=['PUT'])
@token_required
def update_student_profile(current_user):
    print("\n🔄 === 更新学生个人信息API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'student':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅学生可修改"}), 403

    # 查找学生资料，如果不存在则创建
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
    
    # 获取请求数据
    data = request.get_json()
    print(f"📦 接收到的数据: {data}")
    
    try:
        # 更新学生资料
        if data.get('name'):
            current_user.name = data['name']
        if data.get('major'):
            profile.major = data['major']
        if data.get('grade'):
            profile.grade = data['grade']
        if data.get('department'):
            profile.department = data['department']  # 更新系别
        if data.get('gender'):
            profile.gender = data['gender']
        if data.get('phone'):
            profile.phone = data['phone']
        if data.get('email'):
            profile.email = data['email']
        
        # 新增个人信息字段更新
        if data.get('nationality'):
            profile.ethnicity = data['nationality']  # 更新民族
        if data.get('political'):
            profile.political_status = data['political']  # 更新政治面貌
        if data.get('idNumber'):
            profile.id_card = data['idNumber']  # 更新身份证号
        
        # 提交更新到数据库
        db.session.commit()
        print(f"✅ 学生个人信息更新成功")
        
        return jsonify({
            "code": 200,
            "message": "更新成功",
            "success": True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 更新过程中出错: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"更新失败: {str(e)}",
            "success": False
        }), 500


# 提交申请接口
@app.route('/api/students/applications/<string:app_type>', methods=['POST'])
@token_required
def submit_application(current_user, app_type):
    if current_user.role != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可提交"}), 403

    valid_types = ['honor', 'sci', 'social', 'other']
    if app_type not in valid_types:
        return jsonify({"code": 400, "message": f"申请类型错误，支持：{valid_types}"}), 400

    # 使用form获取文本数据
    title = request.form.get('title')
    description = request.form.get('description')
    score = request.form.get('score')
    
    # 验证必填字段
    if not title or not description:
        return jsonify({"code": 400, "message": "标题和描述不能为空"}), 400
    
    # 对于科研竞赛申请，分数是必填的
    if app_type == 'sci' and (score is None or float(score) <= 0):
        return jsonify({"code": 400, "message": "申请分值必须大于0"}), 400
    
    # 创建上传目录
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', str(current_user.id))
    os.makedirs(upload_folder, exist_ok=True)
    
    # 处理上传的文件
    attachments = []
    files = request.files.getlist('files')
    
    for file in files:
        if file and file.filename:
            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(upload_folder, filename)
            
            # 保存文件
            try:
                file.save(file_path)
                # 保存相对路径（从static目录开始）
                relative_path = os.path.join('static', 'uploads', str(current_user.id), filename)
                attachments.append(relative_path)
                print(f"文件上传成功: {relative_path}")
            except Exception as e:
                print(f"文件保存失败: {str(e)}")
    
    # OCR识别奖项级别
    award_level = '未明确'
    for attachment in attachments:
        full_path = os.path.join(app.root_path, attachment)
        if os.path.exists(full_path) and attachment.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                text = get_text_from_image(full_path)
                award_level = extract_award_level(text)
                break
            except Exception as e:
                print(f"OCR处理出错: {e}")

    # 保存到数据库
    new_application = Application(
        student_id=current_user.id,
        type=app_type,
        title=title,
        description=description,
        attachments=','.join(attachments) if attachments else '',
        award_level=award_level,
        score=float(score) if score is not None else None,
        status="pending"
    )
    db.session.add(new_application)
    db.session.commit()

    return jsonify({
        "code": 200,
        "message": "申请提交成功",
        "data": {"applicationId": new_application.id}
    })


# 用户登出接口
@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出，清除session信息"""
    from flask import session
    session.clear()  # 清除所有session信息
    return jsonify({
        "code": 200,
        "message": "登出成功"
    })


# 获取学生申请记录接口
@app.route('/api/students/applications', methods=['GET'])
@token_required
def get_application_records(current_user):
    if current_user.role != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可查看"}), 403

    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
    except ValueError:
        return jsonify({"code": 400, "message": "分页参数必须为整数"}), 400

    # 数据库查询
    query = Application.query.filter_by(student_id=current_user.id)
    if type_filter:
        query = query.filter_by(type=type_filter)
    if status_filter and status_filter != 'all':  # 只有当status_filter不为空且不等于'all'时才添加过滤
        query = query.filter_by(status=status_filter)

    total = query.count()
    paginated = query.offset((page - 1) * size).limit(size).all()

    # 格式化返回
    result = []
    for app in paginated:
        result.append({
                "id": app.id,
                "student_id": app.student_id,
                "student_name": current_user.name,
                "type": app.type,
                "title": app.title,
                "description": app.description,
                "attachments": app.attachments.split(',') if app.attachments else [],
                "status": app.status,
                "apply_time": app.apply_time.strftime("%Y-%m-%d %H:%M:%S"),
                "reviewer": app.reviewer.name if app.reviewer else None,
                "review_time": app.review_time.strftime("%Y-%m-%d %H:%M:%S") if app.review_time else None,
                "award_level": app.award_level,
                "score": app.score,
                "review_remark": app.review_remark
            })

    return jsonify({
        "code": 200,
        "data": {
            "total": total,
            "list": result,
            "page": page,
            "size": size
        }
    })

# 获取学生分数信息API接口
@app.route('/api/students/score', methods=['GET'])
@token_required
def get_student_score(current_user):
    print(f"\n🔍 === 获取学生分数信息API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'student':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅学生可查看"}), 403
    
    # 查找学生资料
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        print(f"❌ 未找到学生资料，用户ID: {current_user.id}")
        # 返回默认分数
        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": {
                "total_score": 0.0,
                "academic_score": 0.0,
                "research_score": 0.0,
                "social_score": 0.0,
                "honor_score": 0.0,
                "other_score": 0.0,
                "scientific_competition_items": [],
                "social_work_items": [],
                "honor_title_items": [],
                "other_items": []
            }
        }), 200
    
    # 获取分数信息
    score_data = {
        "total_score": profile.total_score or 0.0,
        "academic_score": profile.academic_score or 0.0,
        "research_score": profile.research_score or 0.0,
        "social_score": profile.social_score or 0.0,
        "honor_score": profile.honor_score or 0.0,
        "other_score": profile.other_score or 0.0,
        # 默认的加分项目，实际应用中可以从数据库获取
        "scientific_competition_items": [
            { "name": "全国大学生数学建模竞赛", "date": "2023年3月提交", "score": 3.0 },
            { "name": "校级计算机程序设计大赛", "date": "2023年4月提交", "score": 2.0 }
        ],
        "social_work_items": [
            { "name": "暑期三下乡社会工作活动", "date": "2023年8月提交", "score": 2.0 },
            { "name": "社区志愿者服务（50小时）", "date": "2023年12月提交", "score": 1.0 }
        ],
        "honor_title_items": [
            { "name": "校级优秀学生", "date": "2023年9月提交", "score": 3.0 },
            { "name": "校级优秀学生干部", "date": "2023年9月提交", "score": 2.0 }
        ],
        "other_items": [
            { "name": "英语四级证书", "date": "2022年12月提交", "score": 1.0 },
            { "name": "英语六级证书", "date": "2023年6月提交", "score": 1.0 }
        ]
    }
    
    # 计算总成绩
    total_score = (profile.academic_score or 0.0) + (profile.research_score or 0.0) + \
                 (profile.social_score or 0.0) + (profile.honor_score or 0.0) + \
                 (profile.other_score or 0.0)
    score_data["total_score"] = total_score
    
    print(f"✅ 成功获取学生分数信息")
    return jsonify({"code": 200, "message": "获取成功", "data": score_data}), 200


# 教师审核申请接口
@app.route('/api/teachers/applications/<int:app_id>/review', methods=['POST'])
@token_required
def review_application(current_user, app_id):
    print(f"\n📋 === 教师审核申请API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    print(f"📝 申请ID: {app_id}")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可审核"}), 403
    
    # 获取请求数据
    try:
        data = request.get_json()
        action = data.get('action')
        remark = data.get('remark', '')
    except Exception as e:
        print(f"❌ 解析请求数据失败: {e}")
        return jsonify({"code": 400, "message": "请求数据格式错误"}), 400
    
    # 验证操作类型
    if action not in ['approve', 'reject']:
        print(f"❌ 无效的审核操作: {action}")
        return jsonify({"code": 400, "message": "无效的审核操作，仅支持通过或拒绝"}), 400
    
    # 查找申请
    application = Application.query.get(app_id)
    if not application:
        print(f"❌ 申请不存在，ID: {app_id}")
        return jsonify({"code": 404, "message": "申请不存在"}), 404
    
    if application.status != 'pending':
        print(f"❌ 申请已处理，状态: {application.status}")
        return jsonify({"code": 400, "message": "该申请已处理，无法重复审核"}), 400
    
    # 更新申请状态
    try:
        application.status = 'approved' if action == 'approve' else 'rejected'
        application.reviewer_id = current_user.id
        application.review_time = datetime.now()
        application.review_remark = remark
        
        # 如果审核通过，更新学生分数
        if action == 'approve' and application.score:
            # 获取学生
            student = User.query.get(application.student_id)
            if student:
                # 获取学生资料
                profile = StudentProfile.query.filter_by(user_id=student.id).first()
                if not profile:
                    # 如果学生资料不存在，创建一个
                    profile = StudentProfile(user_id=student.id)
                    db.session.add(profile)
                
                # 根据申请类型更新对应分数
                if application.type == 'sci':
                    profile.research_score = (profile.research_score or 0.0) + application.score
                elif application.type == 'social':
                    profile.social_score = (profile.social_score or 0.0) + application.score
                elif application.type == 'honor':
                    profile.honor_score = (profile.honor_score or 0.0) + application.score
                elif application.type == 'other':
                    profile.other_score = (profile.other_score or 0.0) + application.score
                
                # 重新计算总成绩
                profile.total_score = (profile.academic_score or 0.0) + (profile.research_score or 0.0) + \
                                     (profile.social_score or 0.0) + (profile.honor_score or 0.0) + \
                                     (profile.other_score or 0.0)
                
                print(f"✅ 学生分数已更新，学生ID: {student.id}, 申请分数: {application.score}, 类型: {application.type}")
        
        db.session.commit()
        
        print(f"✅ 申请审核成功，ID: {app_id}, 操作: {action}")
        
        return jsonify({
            "code": 200,
            "message": "审核成功",
            "data": {
                "application_id": app_id,
                "status": application.status,
                "review_time": application.review_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 审核过程中出错: {e}")
        return jsonify({"code": 500, "message": f"审核失败: {str(e)}"}), 500


# 获取单个申请详情接口
@app.route('/api/applications/<int:app_id>', methods=['GET'])
@token_required
def get_application_detail(current_user, app_id):
    print(f"\n🔍 === 获取申请详情API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    print(f"📝 申请ID: {app_id}")
    
    # 查找申请
    application = Application.query.get(app_id)
    if not application:
        print(f"❌ 申请不存在，ID: {app_id}")
        return jsonify({"code": 404, "message": "申请不存在"}), 404
    
    # 权限检查：教师可以查看所有申请，学生只能查看自己的申请
    if current_user.role == 'student' and application.student_id != current_user.id:
        print(f"❌ 学生无权查看其他学生的申请")
        return jsonify({"code": 403, "message": "权限不足，只能查看自己的申请"}), 403
    
    # 获取学生信息
    student = User.query.get(application.student_id)
    reviewer = User.query.get(application.reviewer_id) if application.reviewer_id else None
    
    # 格式化结果
    result = {
        "id": application.id,
        "student_id": application.student_id,
        "student_name": student.name if student else "未知学生",
        "type": application.type,
        "title": application.title,
        "description": application.description,
        "attachments": application.attachments.split(',') if application.attachments else [],
        "status": application.status,
        "apply_time": application.apply_time.strftime("%Y-%m-%d %H:%M:%S"),
        "reviewer": reviewer.name if reviewer else None,
        "reviewer_id": application.reviewer_id,
        "review_time": application.review_time.strftime("%Y-%m-%d %H:%M:%S") if application.review_time else None,
        "review_remark": application.review_remark,
        "award_level": application.award_level,
        "score": application.score
    }
    
    return jsonify({
        "code": 200,
        "data": result
    })


# 获取教师个人信息接口
@app.route('/api/teachers/profile', methods=['GET'])
@token_required
def get_teacher_profile(current_user):
    print("\n🔍 === 获取教师个人信息API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可访问"}), 403
    
    # 查找教师资料，如果不存在则创建
    profile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        # 创建新教师资料并设置默认值
        profile = TeacherProfile(
            user_id=current_user.id,
            gender="男",           # 默认性别
            ethnicity="汉族",       # 默认民族
            political_status="中共党员", # 默认政治面貌
            id_card="3501XXXXXXXXXXXX1234"  # 默认身份证号
        )
        db.session.add(profile)
        db.session.commit()
        print(f"✅ 为新用户创建教师资料并设置默认值: {current_user.name}")
    
    # 确保profile对象有所有必要的属性并设置有意义的默认值
    # 即使属性存在，也要确保它不是None或空字符串
    profile.gender = getattr(profile, 'gender', "") or "男"
    profile.ethnicity = getattr(profile, 'ethnicity', "") or "汉族"
    profile.political_status = getattr(profile, 'political_status', "") or "中共党员"
    profile.id_card = getattr(profile, 'id_card', "") or "3501XXXXXXXXXXXX1234"
    
    # 构建返回数据，使用有意义的默认值
    teacher_data = {
        "id": current_user.username,  # 工号
        "name": current_user.name,
        "department": profile.department or "信息学院",
        "title": profile.title or "副教授",
        "gender": profile.gender or "男",  # 默认性别
        "nationality": profile.ethnicity or "汉族",  # 默认民族
        "political": profile.political_status or "中共党员",  # 默认政治面貌
        "idNumber": profile.id_card or "3501XXXXXXXXXXXX1234",  # 默认身份证号
        "phone": profile.phone or "13912345678",
        "email": profile.email or "lixiuyuan@example.com"
    }
    
    return jsonify({
        "code": 200,
        "message": "获取教师个人信息成功",
        "data": teacher_data
    })


@app.route('/api/teachers/profile', methods=['PUT'])
@token_required
def update_teacher_profile(current_user):
    print("\n🔄 === 更新教师个人信息API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可修改"}), 403
    
    # 查找教师资料，如果不存在则创建
    profile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = TeacherProfile(user_id=current_user.id)
        db.session.add(profile)
    
    # 获取请求数据
    data = request.get_json()
    print(f"📦 接收到的数据: {data}")
    
    try:
        # 更新教师资料
        if data.get('name'):
            current_user.name = data['name']
        if data.get('department'):
            profile.department = data['department']
        if data.get('title'):
            profile.title = data['title']
        if data.get('gender'):
            profile.gender = data['gender']
        if data.get('phone'):
            profile.phone = data['phone']
        if data.get('email'):
            profile.email = data['email']
        
        # 新增个人信息字段更新
        if data.get('nationality'):
            profile.ethnicity = data['nationality']  # 更新民族
        if data.get('political'):
            profile.political_status = data['political']  # 更新政治面貌
        if data.get('idNumber'):
            profile.id_card = data['idNumber']  # 更新身份证号
        
        # 提交更新到数据库
        db.session.commit()
        print(f"✅ 教师个人信息更新成功")
        
        return jsonify({
            "code": 200,
            "message": "更新成功",
            "success": True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 更新过程中出错: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"更新失败: {str(e)}",
            "success": False
        }), 500


@app.route('/api/teachers/applications', methods=['GET'])
@token_required
def get_teacher_applications(current_user):
    print("\n🔍 === 获取教师待审核申请API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可访问"}), 403
    
    # 获取查询参数
    status_filter = request.args.get('status')  # 不设置默认值，以便获取所有状态的数据
    type_filter = request.args.get('type')  # 按申请类型过滤
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))
    
    print(f"📊 查询参数 - 状态过滤: {status_filter}, 类型过滤: {type_filter}")
    
    # 构建查询
    query = Application.query
    
    # 只有当status_filter不为空且不等于'all'时才添加状态过滤
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)
        print(f"🔍 添加状态过滤: status={status_filter}")
    else:
        print(f"🔍 不添加状态过滤，返回所有状态的申请")
        
    # 添加类型过滤条件
    if type_filter:
        query = query.filter_by(type=type_filter)
        print(f"🔍 添加类型过滤: type={type_filter}")
    
    # 获取总数和分页数据
    total = query.count()
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    # 格式化结果
    result = []
    for app in paginated:
        student = User.query.get(app.student_id)
        reviewer = User.query.get(app.reviewer_id) if app.reviewer_id else None
        
        result.append({
            "id": app.id,
            "student_id": app.student_id,
            "student_name": student.name if student else "未知学生",
            "type": app.type,
            "title": app.title,
            "description": app.description,
            "attachments": app.attachments.split(',') if app.attachments else [],
            "status": app.status,
            "apply_time": app.apply_time.strftime("%Y-%m-%d %H:%M:%S"),
            "reviewer": reviewer.name if reviewer else None,
            "reviewer_id": app.reviewer_id,
            "review_time": app.review_time.strftime("%Y-%m-%d %H:%M:%S") if app.review_time else None,
            "review_remark": app.review_remark,
            "award_level": app.award_level,
            "score": app.score
        })
    
    return jsonify({
        "code": 200,
        "data": {
            "total": total,
            "list": result,
            "page": page,
            "size": size
        }
    })


@app.route('/api/teachers/pending-counts', methods=['GET'])
@token_required
def get_pending_counts(current_user):
    """
    获取每个类别的待审核数量
    """
    print("\n🔍 === 获取待审核数量API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可访问"}), 403
    
    # 获取所有待审核的申请
    pending_applications = Application.query.filter_by(status='pending').all()
    
    # 计算每个类别的待审核数量
    counts = {
        'scientific-competition': 0,  # 科研竞赛
        'honor-title': 0,             # 荣誉称号
        'social-work': 0,             # 社会工作
        'other': 0                    # 其他
    }
    
    # 类型映射
    type_map = {
        'sci': 'scientific-competition',
        'honor': 'honor-title',
        'social': 'social-work',
        'other': 'other'
    }
    
    for app in pending_applications:
        if app.type in type_map:
            counts[type_map[app.type]] += 1
    
    return jsonify({"code": 200, "counts": counts})


# ---------------------- 公告相关API ----------------------

@app.route('/api/teachers/announcements', methods=['GET'])
@token_required
def get_teacher_announcements(current_user):
    """
    教师获取自己发布的公告列表API
    """
    print("\n📋 === 教师获取公告列表API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可查看自己的公告"}), 403
    
    try:
        # 获取该教师发布的所有公告，按发布时间倒序
        announcements = Announcement.query.filter_by(publisher_id=current_user.id)\
                                         .order_by(Announcement.publish_time.desc())\
                                         .all()
        
        # 格式化公告数据
        announcements_list = []
        for announcement in announcements:
            announcements_list.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'publish_time': announcement.publish_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        print(f"✅ 获取公告列表成功，共 {len(announcements_list)} 条公告")
        return jsonify({
            "code": 200, 
            "message": "获取公告列表成功",
            "announcements": announcements_list
        }), 200
    except Exception as e:
        print(f"❌ 获取公告列表失败: {e}")
        return jsonify({"code": 500, "message": "获取公告列表失败，请重试"}), 500

@app.route('/api/teachers/announcements', methods=['POST'])
@token_required
def publish_announcement(current_user):
    """
    教师发布公告API
    """
    print("\n📢 === 教师发布公告API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可发布公告"}), 403
    
    # 获取请求数据
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
    except Exception as e:
        print(f"❌ 解析请求数据失败: {e}")
        return jsonify({"code": 400, "message": "请求数据格式错误"}), 400
    
    # 验证必填字段
    if not title or not content:
        print(f"❌ 缺少必填字段，标题: {title}, 内容: {content}")
        return jsonify({"code": 400, "message": "标题和内容不能为空"}), 400
    
    # 创建公告
    try:
        announcement = Announcement(
            title=title,
            content=content,
            publisher_id=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        
        # 为所有学生创建未读状态
        students = User.query.filter_by(role='student').all()
        for student in students:
            read_status = AnnouncementReadStatus(
                announcement_id=announcement.id,
                student_id=student.id,
                is_read=False
            )
            db.session.add(read_status)
        db.session.commit()
        
        print(f"✅ 公告发布成功，ID: {announcement.id}, 标题: {title}")
        return jsonify({"code": 200, "message": "公告发布成功"}), 200
    except Exception as e:
        print(f"❌ 公告发布失败: {e}")
        db.session.rollback()
        return jsonify({"code": 500, "message": "公告发布失败，请重试"}), 500

@app.route('/api/teachers/announcements/<int:announcement_id>', methods=['DELETE'])
@token_required
def delete_announcement(current_user, announcement_id):
    """
    教师删除公告API
    """
    print("\n🗑️ === 教师删除公告API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    print(f"📢 要删除的公告ID: {announcement_id}")
    
    if current_user.role != 'teacher':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅教师可删除公告"}), 403
    
    try:
        # 查找公告
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            print(f"❌ 未找到ID为 {announcement_id} 的公告")
            return jsonify({"code": 404, "message": "公告不存在"}), 404
        
        # 检查是否是该教师发布的公告
        if announcement.publisher_id != current_user.id:
            print(f"❌ 无权删除他人发布的公告")
            return jsonify({"code": 403, "message": "无权删除他人发布的公告"}), 403
        
        # 删除相关的阅读状态记录
        AnnouncementReadStatus.query.filter_by(announcement_id=announcement_id).delete()
        
        # 删除公告
        db.session.delete(announcement)
        db.session.commit()
        
        print(f"✅ 公告删除成功，ID: {announcement_id}")
        return jsonify({"code": 200, "message": "公告删除成功"}), 200
    except Exception as e:
        print(f"❌ 删除公告失败: {e}")
        db.session.rollback()
        return jsonify({"code": 500, "message": "删除公告失败，请重试"}), 500


@app.route('/api/students/announcements', methods=['GET'])
@token_required
def get_student_announcements(current_user):
    """
    学生获取公告列表API
    """
    print("\n📢 === 学生获取公告列表API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    
    if current_user.role != 'student':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅学生可访问"}), 403
    
    try:
        # 获取所有公告
        announcements = Announcement.query.order_by(Announcement.publish_time.desc()).all()
        
        # 获取当前学生的所有公告读取状态
        read_statuses = AnnouncementReadStatus.query.filter_by(student_id=current_user.id).all()
        read_status_map = {status.announcement_id: status for status in read_statuses}
        
        # 构建响应数据
        announcement_list = []
        for announcement in announcements:
            read_status = read_status_map.get(announcement.id)
            is_read = read_status.is_read if read_status else False
            
            announcement_list.append({
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "publisher_name": announcement.publisher.name,
                "publish_time": announcement.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_read": is_read
            })
        
        # 计算未读公告数量
        unread_count = sum(1 for a in announcement_list if not a["is_read"])
        
        print(f"✅ 学生获取公告列表成功，共 {len(announcement_list)} 条公告，{unread_count} 条未读")
        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": {
                "announcements": announcement_list,
                "unread_count": unread_count
            }
        }), 200
    except Exception as e:
        print(f"❌ 获取公告列表失败: {e}")
        return jsonify({"code": 500, "message": "获取公告列表失败，请重试"}), 500


@app.route('/api/students/announcements/<int:announcement_id>/read', methods=['POST'])
@token_required
def mark_announcement_read(current_user, announcement_id):
    """
    学生标记公告已读API
    """
    print("\n📢 === 学生标记公告已读API被调用 ===")
    print(f"👤 当前用户: {current_user.name} (ID: {current_user.id}, 角色: {current_user.role})")
    print(f"📄 公告ID: {announcement_id}")
    
    if current_user.role != 'student':
        print(f"❌ 权限不足，用户角色: {current_user.role}")
        return jsonify({"code": 403, "message": "权限不足，仅学生可访问"}), 403
    
    try:
        # 查找公告读取状态
        read_status = AnnouncementReadStatus.query.filter_by(
            announcement_id=announcement_id,
            student_id=current_user.id
        ).first()
        
        if not read_status:
            print(f"❌ 公告读取状态不存在，公告ID: {announcement_id}, 学生ID: {current_user.id}")
            return jsonify({"code": 404, "message": "公告不存在"}), 404
        
        # 标记为已读
        read_status.is_read = True
        read_status.read_time = datetime.now()
        db.session.commit()
        
        print(f"✅ 公告标记已读成功，公告ID: {announcement_id}")
        return jsonify({"code": 200, "message": "标记成功"}), 200
    except Exception as e:
        print(f"❌ 标记公告已读失败: {e}")
        db.session.rollback()
        return jsonify({"code": 500, "message": "标记失败，请重试"}), 500


# ---------------------- 后端接口配置结束 ----------------------

# ========== 数据库初始化 ==========
with app.app_context():
    try:
        db.create_all()  # 创建所有表
        print("✅ 数据库表创建成功")
        # 执行数据库迁移，添加缺失的列
        migrate_database()
        print("✅ 数据库迁移完成")
        
        # 打印当前所有用户，用于调试
        all_users = User.query.all()
        print(f"📊 当前数据库中共有 {len(all_users)} 个用户")
        for user in all_users:
            print(f"   - 用户: {user.username}, 角色: {user.role}, 姓名: {user.name}")

        # 添加默认教师 - 检查是否已有教师账号，而不是特定的teacher001
        if not User.query.filter_by(role='teacher').first():
            teacher = User(username='2011981001', password='654321', name='李修远', role='teacher')
            db.session.add(teacher)
            db.session.commit()
            print("✅ 默认教师账号创建成功")
            
            # 教师资料
            teacher_profile = TeacherProfile(
                user_id=teacher.id,
                gender='男',
                department='信息学院',
                title='副教授',
                ethnicity='汉族',
                political_status='中共党员',
                id_card='440305198111097916',
                phone='18790032041',
                email='lixiuyuan@example.com'
            )
            db.session.add(teacher_profile)
            db.session.commit()
        else:
            print("ℹ️  已有教师账号存在")

        # 确保学生用户信息与数据库实际信息一致
        # 张景珩 (数据库中的实际信息)
        student1 = User.query.filter_by(username='22920222203906').first()
        if not student1:
            # 如果学生不存在，则创建
            student1 = User(username='22920222203906', password='123456', name='张景珩', role='student')
            db.session.add(student1)
            db.session.commit()
            print("✅ 创建学生账号 张景珩")
        else:
            # 更新学生信息
            student1.name = '张景珩'
            student1.role = 'student'
            student1.password = '123456'
            print("✅ 学生账号 张景珩 信息保持一致")
        
        # 更新或创建张景珩的学生资料
        profile1 = StudentProfile.query.filter_by(user_id=student1.id).first()
        if not profile1:
            profile1 = StudentProfile(
                user_id=student1.id,
                gender='男',
                department='计算机科学与技术系',
                major='计算机科学与技术',
                grade='2022',
                phone='18938270656',
                email='zhangjingheng@example.com',
                ethnicity='汉族',
                political_status='共青团员',
                id_card='110101200404227138',
                total_score=104.5,
                academic_score=85.5,
                research_score=6.5,
                social_score=4.2,
                honor_score=5.8,
                other_score=2.5
            )
            db.session.add(profile1)
            db.session.commit()
            print("✅ 创建学生资料 张景珩")
        else:
            profile1.gender = '男'
            profile1.department = '计算机科学与技术系'
            profile1.major = '计算机科学与技术'
            profile1.grade = '2022'
            profile1.phone = '18938270656'
            profile1.email = 'zhangjingheng@example.com'
            profile1.ethnicity = '汉族'
            profile1.political_status = '共青团员'
            profile1.id_card = '110101200404227138'
            profile1.total_score = 104.5
            profile1.academic_score = 85.5
            profile1.research_score = 6.5
            profile1.social_score = 4.2
            profile1.honor_score = 5.8
            profile1.other_score = 2.5
            print("✅ 学生资料 张景珩 信息保持一致")
        
        # 李书韫 (数据库中的实际信息)
        student2 = User.query.filter_by(username='22920232202189').first()
        if not student2:
            # 如果学生不存在，则创建
            student2 = User(username='22920232202189', password='111111', name='李书韫', role='student')
            db.session.add(student2)
            db.session.commit()
            print("✅ 创建学生账号 李书韫")
        else:
            # 更新学生信息
            student2.name = '李书韫'
            student2.role = 'student'
            student2.password = '111111'
            print("✅ 学生账号 李书韫 信息保持一致")
        
        # 更新或创建李书韫的学生资料
        profile2 = StudentProfile.query.filter_by(user_id=student2.id).first()
        if not profile2:
            profile2 = StudentProfile(
                user_id=student2.id,
                gender='女',
                department='软件工程系',
                major='软件工程',
                grade='2023',
                phone='15196083798',
                email='lishuyun@example.com',
                ethnicity='汉族',
                political_status='共青团员',
                id_card='310104200411011266',
                total_score=92.0,
                academic_score=92.0,
                research_score=0.0,
                social_score=0.0,
                honor_score=0.0,
                other_score=0.0
            )
            db.session.add(profile2)
            db.session.commit()
            print("✅ 创建学生资料 李书韫")
        else:
            profile2.gender = '女'
            profile2.department = '软件工程系'
            profile2.major = '软件工程'
            profile2.grade = '2023'
            profile2.phone = '15196083798'
            profile2.email = 'lishuyun@example.com'
            profile2.ethnicity = '汉族'
            profile2.political_status = '共青团员'
            profile2.id_card = '310104200411011266'
            profile2.total_score = 92.0
            profile2.academic_score = 92.0
            profile2.research_score = 0.0
            profile2.social_score = 0.0
            profile2.honor_score = 0.0
            profile2.other_score = 0.0
            print("✅ 学生资料 李书韫 信息保持一致")
        
        db.session.commit()
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
# ==================================

# 启动服务
if __name__ == '__main__':
    import socket


    # 获取本机IP地址
    def get_local_ip():
        try:
            # 创建一个socket连接来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"获取IP地址失败: {e}")
            return '127.0.0.1'


    # 手动打印访问URL
    local_ip = get_local_ip()
    print("\n========== 保研助手系统启动成功 ==========")
    print(f"本地访问地址: http://127.0.0.1:5000")
    print(f"局域网访问地址: http://{local_ip}:5000")
    print("========================================\n")

    # 启动Flask服务
    app.run(debug=True, host='0.0.0.0', port=5000)