from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from ocr_utils import get_text_from_image, extract_award_level
import os
import jwt
import datetime
from functools import wraps

# 初始化Flask应用
app = Flask(__name__)
# 允许跨域请求
CORS(app)
# JWT密钥（实际项目请使用复杂密钥）
app.config['SECRET_KEY'] = 'your-secret-key'

# ========== 数据库配置代码 ==========
from flask_sqlalchemy import SQLAlchemy
import pymysql

pymysql.install_as_MySQLdb()

# 数据库连接配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:24640@localhost:3306/student_award_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' 或 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

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
    apply_time = db.Column(db.DateTime, default=datetime.datetime.now)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_time = db.Column(db.DateTime)
    review_remark = db.Column(db.Text)


# ---------------------- 前端页面路由配置 ----------------------
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/login.html', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/student-login.html', methods=['GET'])
def student_login_page():
    return render_template('login.html', role='student')


@app.route('/teacher-login.html', methods=['GET'])
def teacher_login_page():
    return render_template('login.html', role='teacher')


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
def new_application():
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
def student_dashboard_page():
    return render_template('student-dashboard.html')


@app.route('/student-list.html', methods=['GET'])
def student_list():
    return render_template('student-list.html')


@app.route('/student-notifications.html', methods=['GET'])
def student_notifications():
    return render_template('student-notifications.html')


@app.route('/student-profile.html', methods=['GET'])
def student_profile():
    return render_template('student-profile.html')


@app.route('/student-records.html', methods=['GET'])
def student_records():
    return render_template('student-records.html')


@app.route('/student-security.html', methods=['GET'])
def student_security():
    return render_template('student-security.html')


@app.route('/student-transcript.html', methods=['GET'])
def student_transcript():
    return render_template('student-transcript.html')


@app.route('/submission-guide.html', methods=['GET'])
def submission_guide():
    return render_template('submission-guide.html')


@app.route('/teacher-announcement-records.html', methods=['GET'])
def teacher_announcement_records():
    return render_template('teacher-announcement-records.html')


@app.route('/teacher-dashboard.html', methods=['GET'])
def teacher_dashboard():
    return render_template('teacher-dashboard.html')


@app.route('/teacher-notifications.html', methods=['GET'])
def teacher_notifications():
    return render_template('teacher-notifications.html')


@app.route('/teacher-profile.html', methods=['GET'])
def teacher_profile():
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
def teacher_security():
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

# ---------------------- 工具函数 ----------------------
# 生成JWT令牌
def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


# 令牌验证装饰器（核心修复部分）
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({"code": 401, "message": "未提供令牌，请先登录"}), 401

        try:
            # 解码令牌获取用户ID
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = payload.get('sub')

            # 严格验证用户ID格式并查询数据库
            try:
                current_user_id = int(current_user_id)  # 确保ID是整数
                current_user = User.query.filter_by(id=current_user_id).first()  # 数据库查询
                if not current_user:
                    return jsonify({"code": 401, "message": "令牌无效，用户不存在"}), 401
            except (TypeError, ValueError):
                return jsonify({"code": 401, "message": "令牌格式错误"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"code": 401, "message": "令牌已过期，请重新登录"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 401, "message": "无效的令牌"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# ---------------------- 工具函数结束 ----------------------

# ---------------------- 后端接口配置 ----------------------
# 登录接口（验证数据库中的账号和角色）
@app.route('/api/login', methods=['POST'])
def login():
    # 获取前端提交的账号、密码、角色
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # 1. 验证参数是否完整
    if not all([username, password, role]):
        return jsonify({"success": False, "message": "请输入用户名、密码和角色"})

    # 2. 查询数据库：是否存在该用户名且角色匹配的用户
    # 关键：必须同时匹配用户名和角色（防止学生用教师账号登录）
    user = User.query.filter_by(username=username, role=role).first()

    # 3. 验证用户是否存在
    if not user:
        return jsonify({"success": False, "message": "用户名不存在或角色不匹配"})

    # 4. 验证密码是否正确（与数据库中存储的密码比对）
    if user.password != password:
        return jsonify({"success": False, "message": "密码错误"})

    # 5. 所有验证通过，允许登录
    return jsonify({
        "success": True,
        "message": "登录成功",
        "role": role  # 返回角色用于前端跳转
    })



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
    db.create_all()  # 创建所有表

    # 添加默认学生
    if not User.query.filter_by(username='student001').first():
        student = User(username='student001', password='123456', name='张三', role='student')
        db.session.add(student)
        db.session.commit()
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

    # 添加默认教师
    if not User.query.filter_by(username='teacher001').first():
        teacher = User(username='teacher001', password='654321', name='李老师', role='teacher')
        db.session.add(teacher)
        db.session.commit()
        # 教师资料
        teacher_profile = TeacherProfile(
            user_id=teacher.id,
            department='计算机学院',
            title='副教授',
            phone='13900139000',
            email='li_teacher@example.com'
        )
        db.session.add(teacher_profile)

    db.session.commit()
# ==================================

# 启动服务
if __name__ == '__main__':
    app.run(debug=True)