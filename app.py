from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import jwt
import datetime
from functools import wraps

# 初始化Flask应用
app = Flask(__name__)
# 允许跨域请求（解决前后端分离时的跨域问题）
CORS(app)
# 用于JWT令牌加密的密钥（实际项目需使用复杂密钥）
app.config['SECRET_KEY'] = 'your-secret-key'

# ---------------------- 前端页面路由配置 ----------------------
# 根路径路由：访问http://127.0.0.1:5000/时，渲染templates/index.html
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# 登录页面路由
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# 学生登录页面
@app.route('/student-login', methods=['GET'])
def student_login_page():
    return render_template('login.html', role='student')

# 教师登录页面
@app.route('/teacher-login', methods=['GET'])
def teacher_login_page():
    return render_template('login.html', role='teacher')

# 密码找回页面（已存在，确认路由正确）
@app.route('/reset-password.html', methods=['GET'])  # 与前端<a href="reset-password.html">对应
def reset_password():
    return render_template('reset-password.html')

# 帮助页面路由
@app.route('/help.html', methods=['GET'])
def help_page():
    return render_template('help.html')

# 荣誉称号主页面路由
@app.route('/honor-title', methods=['GET'])
def honor_title():
    return render_template('honor-title.html')

# 荣誉称号申请页面路由
@app.route('/honor-title-application', methods=['GET'])
def honor_title_application():
    return render_template('honor-title-application.html')

# 荣誉称号未通过页面路由
@app.route('/honor-title-failed', methods=['GET'])
def honor_title_failed():
    return render_template('honor-title-failed.html')

# 荣誉称号通过页面路由
@app.route('/honor-title-passed', methods=['GET'])
def honor_title_passed():
    return render_template('honor-title-passed.html')

# 荣誉称号待审核页面路由
@app.route('/honor-title-pending', methods=['GET'])
def honor_title_pending():
    return render_template('honor-title-pending.html')

# 荣誉称号已通过列表页面路由
@app.route('/honor-titles-passed', methods=['GET'])
def honor_titles_passed():
    return render_template('honor-titles-passed.html')

# 申请记录页面路由
@app.route('/application-records', methods=['GET'])
def application_records():
    return render_template('application-records.html')

# 数据管理页面路由
@app.route('/data-management', methods=['GET'])
def data_management():
    return render_template('data-management.html')

# 新申请页面路由
@app.route('/new-application.html', methods=['GET'])
def new_application():
    return render_template('new-application.html')

# 其他加分已通过页面路由
@app.route('/other-additions-passed', methods=['GET'])
def other_additions_passed():
    return render_template('other-additions-passed.html')

# 其他加分申请页面路由
@app.route('/other-application', methods=['GET'])
def other_application():
    return render_template('other-application.html')

# 其他加分记录主页面路由
@app.route('/other-records', methods=['GET'])
def other_records():
    return render_template('other-records.html')

# 其他加分未通过页面路由
@app.route('/other-records-failed', methods=['GET'])
def other_records_failed():
    return render_template('other-records-failed.html')

# 其他加分已通过页面路由
@app.route('/other-records-passed', methods=['GET'])
def other_records_passed():
    return render_template('other-records-passed.html')

# 其他加分待审核页面路由
@app.route('/other-records-pending', methods=['GET'])
def other_records_pending():
    return render_template('other-records-pending.html')

# 项目详情页面路由
@app.route('/project-detail', methods=['GET'])
def project_detail():
    return render_template('project-detail.html')



# 科研竞赛主页面路由
@app.route('/scientific-competition', methods=['GET'])
def scientific_competition():
    return render_template('scientific-competition.html')

# 科研竞赛申请页面路由
@app.route('/scientific-competition-application.html', methods=['GET'])
def scientific_competition_application():
    return render_template('scientific-competition-application.html')

# 科研竞赛未通过页面路由
@app.route('/scientific-competition-failed', methods=['GET'])
def scientific_competition_failed():
    return render_template('scientific-competition-failed.html')

# 科研竞赛已通过页面路由
@app.route('/scientific-competition-passed', methods=['GET'])
def scientific_competition_passed():
    return render_template('scientific-competition-passed.html')

# 科研竞赛待审核页面路由
@app.route('/scientific-competition-pending', methods=['GET'])
def scientific_competition_pending():
    return render_template('scientific-competition-pending.html')

# 社会工作主页面路由
@app.route('/social-work', methods=['GET'])
def social_work():
    return render_template('social-work.html')

# 社会工作申请页面路由
@app.route('/social-work-application', methods=['GET'])
def social_work_application():
    return render_template('social-work-application.html')

# 社会工作未通过页面路由
@app.route('/social-work-failed', methods=['GET'])
def social_work_failed():
    return render_template('social-work-failed.html')

# 社会工作已通过页面路由
@app.route('/social-work-passed', methods=['GET'])
def social_work_passed():
    return render_template('social-work-passed.html')

# 社会工作待审核页面路由
@app.route('/social-work-pending', methods=['GET'])
def social_work_pending():
    return render_template('social-work-pending.html')

# 学生仪表盘页面路由
@app.route('/student-dashboard.html', methods=['GET'])
def student_dashboard_page():
    return render_template('student-dashboard.html')

# 学生列表页面路由
@app.route('/student-list', methods=['GET'])
def student_list():
    return render_template('student-list.html')

# 学生通知页面路由
@app.route('/student-notifications', methods=['GET'])
def student_notifications():
    return render_template('student-notifications.html')

# 学生个人资料页面路由
@app.route('/student-profile.html', methods=['GET'])
def student_profile():
    return render_template('student-profile.html')

# 学生记录页面路由
@app.route('/student-records', methods=['GET'])
def student_records():
    return render_template('student-records.html')

# 学生安全设置页面路由
@app.route('/student-security', methods=['GET'])
def student_security():
    return render_template('student-security.html')

# 学生成绩单页面路由
@app.route('/student-transcript', methods=['GET'])
def student_transcript():
    return render_template('student-transcript.html')

# 提交指南页面路由
@app.route('/submission-guide', methods=['GET'])
def submission_guide():
    return render_template('submission-guide.html')

# 教师公告记录页面路由
@app.route('/teacher-announcement-records', methods=['GET'])
def teacher_announcement_records():
    return render_template('teacher-announcement-records.html')

# 教师仪表盘页面路由
@app.route('/teacher-dashboard.html', methods=['GET'])
def teacher_dashboard():
    return render_template('teacher-dashboard.html')

# 教师通知页面路由
@app.route('/teacher-notifications', methods=['GET'])
def teacher_notifications():
    return render_template('teacher-notifications.html')

# 教师个人资料页面路由
@app.route('/teacher-profile', methods=['GET'])
def teacher_profile():
    return render_template('teacher-profile.html')

# 教师发布公告页面路由
@app.route('/teacher-publish-announcement', methods=['GET'])
def teacher_publish_announcement():
    return render_template('teacher-publish-announcement.html')

# 教师审核分类页面路由
@app.route('/teacher-review-category', methods=['GET'])
def teacher_review_category():
    return render_template('teacher-review-category.html')

# 教师审核详情页面路由
@app.route('/teacher-review-detail', methods=['GET'])
def teacher_review_detail():
    return render_template('teacher-review-detail.html')

# 教师审核管理页面路由
@app.route('/teacher-review-management', methods=['GET'])
def teacher_review_management():
    return render_template('teacher-review-management.html')

# 教师安全设置页面路由
@app.route('/teacher-security', methods=['GET'])
def teacher_security():
    return render_template('teacher-security.html')

# 成绩单分类页面路由
@app.route('/transcript-category', methods=['GET'])
def transcript_category():
    return render_template('transcript-category.html')

# 成绩单详情页面路由
@app.route('/transcript-detail', methods=['GET'])
def transcript_detail():
    return render_template('transcript-detail.html')
# ---------------------- 前端页面路由配置结束 ----------------------

# ---------------------- 模拟数据库与工具函数 ----------------------
# 模拟用户数据
users = {
    "student001": {
        "id": 1,
        "username": "student001",
        "password": "123456",
        "name": "张三",
        "role": "student"
    },
    "teacher001": {
        "id": 2,
        "username": "teacher001",
        "password": "654321",
        "name": "李老师",
        "role": "teacher"
    }
}

# 模拟学生信息数据
student_profiles = {
    1: {
        "id": 1,
        "name": "张三",
        "gender": "male",
        "major": "计算机科学与技术",
        "grade": "2022",
        "phone": "13800138000",
        "email": "zhangsan@example.com"
    }
}

# 模拟申请记录数据
applications = []
application_id = 1  # 申请记录自增ID

# 生成JWT令牌的工具函数
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

# 令牌验证装饰器（保护需要登录的接口）
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
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = payload.get('sub')
            try:
                current_user_id = int(current_user_id)
            except (TypeError, ValueError):
                pass
            current_user = next((u for u in users.values() if u['id'] == current_user_id), None)
            if not current_user:
                return jsonify({"code": 401, "message": "令牌无效，用户不存在"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"code": 401, "message": "令牌已过期，请重新登录"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 401, "message": "无效的令牌"}), 401

        return f(current_user, *args, **kwargs)
    return decorated
# ---------------------- 模拟数据库与工具函数结束 ----------------------

# ---------------------- 后端接口配置 ----------------------
# 登录接口：POST /api/auth/login
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"code":400, "message":"请求体必须为 JSON"}), 400
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400

    user = users.get(username)
    if not user:
        return jsonify({"code": 401, "message": "用户名不存在"}), 401
    if user['password'] != password:
        return jsonify({"code": 401, "message": "密码错误"}), 401

    token = generate_token(user['id'])

    return jsonify({
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "name": user['name'],
                "role": user['role']
            }
        }
    })

# 获取学生个人信息接口：GET /api/students/profile（需要令牌验证）
@app.route('/api/students/profile', methods=['GET'])
@token_required
def get_student_profile(current_user):
    if current_user['role'] != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可访问"}), 403

    profile = student_profiles.get(current_user['id'])
    if not profile:
        return jsonify({"code": 404, "message": "学生信息不存在"}), 404

    return jsonify({
        "code": 200,
        "data": profile
    })

# 提交申请接口：POST /api/students/applications/{type}（需要令牌验证）
@app.route('/api/students/applications/<string:type>', methods=['POST'])
@token_required
def submit_application(current_user, app_type):
    if current_user['role'] != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可提交"}), 403

    valid_types = ['honor', 'sci', 'social', 'other']
    if type not in valid_types:
        return jsonify({"code": 400, "message": f"申请类型错误，支持：{valid_types}"}), 400

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    attachments = data.get('attachments', [])
    extra = data.get('extra', {})

    if not title or not description:
        return jsonify({"code": 400, "message": "标题和描述不能为空"}), 400

    global application_id
    new_application = {
        "id": application_id,
        "student_id": current_user['id'],
        "student_name": current_user['name'],
        "type": type,
        "title": title,
        "description": description,
        "attachments": attachments,
        "extra": extra,
        "status": "pending",
        "apply_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reviewer": None,
        "review_time": None
    }
    applications.append(new_application)
    application_id += 1

    return jsonify({
        "code": 200,
        "message": "申请提交成功",
        "data": {"applicationId": new_application['id']}
    })

# 获取学生申请记录接口：GET /api/students/applications（需要令牌验证）
@app.route('/api/students/applications', methods=['GET'])
@token_required
def get_application_records(current_user):
    if current_user['role'] != 'student':
        return jsonify({"code": 403, "message": "权限不足，仅学生可查看"}), 403

    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
    except ValueError:
        return jsonify({"code": 400, "message": "分页参数必须为整数"}), 400
    size = int(request.args.get('size', 10))

    user_applications = [app for app in applications if app['student_id'] == current_user['id']]

    if type_filter:
        user_applications = [app for app in user_applications if app['type'] == type_filter]

    if status_filter:
        user_applications = [app for app in user_applications if app['status'] == status_filter]

    total = len(user_applications)
    start = (page - 1) * size
    end = start + size
    paginated = user_applications[start:end]

    return jsonify({
        "code": 200,
        "data": {
            "total": total,
            "list": paginated,
            "page": page,
            "size": size
        }
    })
# ---------------------- 后端接口配置结束 ----------------------

# 启动Flask服务（开发环境启用调试模式）
if __name__ == '__main__':
    app.run(debug=True)