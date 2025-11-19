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
# 允许跨域请求，并配置允许携带cookies
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5000"}})
# JWT密钥（实际项目请使用复杂密钥）
app.config['SECRET_KEY'] = 'your-secret-key'

# ========== 数据库配置代码 ==========
from flask_sqlalchemy import SQLAlchemy

# 使用SQLite文件数据库，数据持久化保存
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baoyan_helper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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
            print("❌ 未登录访问受限页面，跳转到登录页")
            return redirect('/login.html')
        
        # 验证用户是否仍然存在于数据库中
        current_user = User.query.filter_by(id=user_id, role=user_role).first()
        if not current_user:
            print("❌ session用户信息无效，清除session并跳转登录")
            session.clear()
            return redirect('/login.html')
        
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
                # 对于页面请求，重定向到登录页
                return redirect('/login.html')
        
        # 验证用户是否仍然存在于数据库中
        current_user = User.query.filter_by(id=user_id, role=user_role).first()
        if not current_user:
            if request.path.startswith('/api/'):
                return jsonify({"code": 401, "message": "用户信息无效，请重新登录"}), 401
            else:
                session.clear()
                return redirect('/login.html')
        
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
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))


# 教师资料模型
class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    department = db.Column(db.String(100))
    title = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))


# 申请材料模型
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'honor', 'sci', 'social', 'other'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    attachments = db.Column(db.Text)  # 附件路径，逗号分隔
    award_level = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')
    apply_time = db.Column(db.DateTime, default=datetime.now)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_time = db.Column(db.DateTime)
    review_remark = db.Column(db.Text)


# ---------------------- 前端页面路由配置 ----------------------
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
@app.route('/login.html', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/student-login.html', methods=['GET'])
def student_login_page():
    return render_template('login.html')

@app.route('/teacher-login.html', methods=['GET'])
def teacher_login_page():
    return render_template('login.html')





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
        return redirect('/login.html')
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
        return redirect('/login.html')
    
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
        return redirect('/login.html')
    return render_template('student-notifications.html')


@app.route('/student-security.html', methods=['GET'])
@page_auth_required
def student_security(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/login.html')
    return render_template('student-security.html')


@app.route('/student-transcript.html', methods=['GET'])
@page_auth_required
def student_transcript(current_user):
    if current_user.role != 'student':
        from flask import session
        session.clear()
        return redirect('/login.html')
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
        print('❌ Session中无登录信息，跳转到登录页')
        return redirect('/login.html')
    
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
    if current_user.role != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可访问"}), 403

    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"code": 404, "message": "学生信息不存在"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "id": profile.id,
            "name": current_user.name,
            "gender": profile.gender,
            "major": profile.major,
            "grade": profile.grade,
            "phone": profile.phone,
            "email": profile.email
        }
    })


# 提交申请接口
@app.route('/api/students/applications/<string:app_type>', methods=['POST'])
@token_required
def submit_application(current_user, app_type):
    if current_user.role != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可提交"}), 403

    valid_types = ['honor', 'sci', 'social', 'other']
    if app_type not in valid_types:
        return jsonify({"code": 400, "message": f"申请类型错误，支持：{valid_types}"}), 400

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    attachments = data.get('attachments', [])

    if not title or not description:
        return jsonify({"code": 400, "message": "标题和描述不能为空"}), 400

    # OCR识别奖项级别
    award_level = '未明确'
    for attachment in attachments:
        if attachment.endswith(('.jpg', '.jpeg', '.png')) and os.path.exists(attachment):
            text = get_text_from_image(attachment)
            award_level = extract_award_level(text)
            break

    # 保存到数据库
    new_application = Application(
        student_id=current_user.id,
        type=app_type,
        title=title,
        description=description,
        attachments=','.join(attachments),
        award_level=award_level,
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
    if status_filter:
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
            "award_level": app.award_level
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


# 获取教师个人信息接口
@app.route('/api/teachers/profile', methods=['GET'])
@token_required
def get_teacher_profile(current_user):
    if current_user.role != 'teacher':
        return jsonify({"code": 403, "message": "权限不足，仅教师可访问"}), 403

    profile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"code": 404, "message": "教师信息不存在"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "id": profile.id,
            "name": current_user.name,
            "department": profile.department,
            "title": profile.title,
            "phone": profile.phone,
            "email": profile.email
        }
    })


# ---------------------- 后端接口配置结束 ----------------------

# ========== 数据库初始化 ==========
with app.app_context():
    try:
        db.create_all()  # 创建所有表
        print("✅ 数据库表创建成功")
        
        # 打印当前所有用户，用于调试
        all_users = User.query.all()
        print(f"📊 当前数据库中共有 {len(all_users)} 个用户")
        for user in all_users:
            print(f"   - 用户: {user.username}, 角色: {user.role}, 姓名: {user.name}")

        # 添加默认学生
        if not User.query.filter_by(username='student001').first():
            student = User(username='student001', password='123456', name='张三', role='student')
            db.session.add(student)
            db.session.commit()
            print("✅ 默认学生账号创建成功: student001/123456")
            
            # 学生资料
            student_profile = StudentProfile(
                user_id=student.id,
                gender='male',
                major='计算机科学与技术',
                grade='2022',
                phone='13800138000',
                email='zhangsan@example.com'
            )
            db.session.add(student_profile)
        else:
            print("ℹ️  默认学生账号已存在")

        # 添加新学生账号 student002
        if not User.query.filter_by(username='student002').first():
            student002 = User(username='student002', password='111111', name='李四', role='student')
            db.session.add(student002)
            db.session.commit()
            print("✅ 新学生账号创建成功: student002/111111")
            
            # 学生资料
            student002_profile = StudentProfile(
                user_id=student002.id,
                gender='female',
                major='软件工程',
                grade='2023',
                phone='13900139001',
                email='lisi@example.com'
            )
            db.session.add(student002_profile)
        else:
            print("ℹ️  student002 账号已存在")

        # 添加默认教师
        if not User.query.filter_by(username='teacher001').first():
            teacher = User(username='teacher001', password='654321', name='李老师', role='teacher')
            db.session.add(teacher)
            db.session.commit()
            print("✅ 默认教师账号创建成功: teacher001/654321")
            
            # 教师资料
            teacher_profile = TeacherProfile(
                user_id=teacher.id,
                department='计算机学院',
                title='副教授',
                phone='13900139000',
                email='li_teacher@example.com'
            )
            db.session.add(teacher_profile)
        else:
            print("ℹ️  默认教师账号已存在")

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