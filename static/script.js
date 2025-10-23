// 保研助手 - JavaScript 交互功能
class BaoYanHelper {
    constructor() {
        this.currentPage = 'home';
        this.modal = null;
        this.notification = null;
        this.loginUserType = null; // 存储登录用户类型
        this.currentUser = null; // 存储当前登录用户信息
        // 从localStorage中恢复用户类型状态，如果没有则默认为false
        const savedUserType = localStorage.getItem('userType');
        this.isTeacher = savedUserType === 'teacher';
        this.init();
    }
    
    // 防抖函数 - 用于优化高频触发的事件
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupNavigation();
        this.setupModals();
        this.setupNotifications();
        this.setupFAQ();
        this.setupFormValidation();
    }

    // 设置事件监听器
    setupEventListeners() {
        // 导航栏切换
        const navbarToggle = document.querySelector('.navbar__toggle');
        const navbarList = document.querySelector('.navbar__list');

        if (navbarToggle && navbarList) {
            navbarToggle.addEventListener('click', () => {
                navbarList.classList.toggle('navbar__list--active');
            });
        }

        // 导航链接
        const navLinks = document.querySelectorAll('.navbar__link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page) {
                    this.navigateToPage(page);
                }
            });
        });

        // 直接为登录按钮添加事件监听器，提高性能
        const studentLoginBtn = document.querySelector('.homepage__btn--student');
        const teacherLoginBtn = document.querySelector('.homepage__btn--teacher');

        if (studentLoginBtn) {
            studentLoginBtn.addEventListener('click', () => {
                this.showLoginModal('student');
            });
        }

        if (teacherLoginBtn) {
            teacherLoginBtn.addEventListener('click', () => {
                this.showLoginModal('teacher');
            });
        }

        // 其他按钮使用选择器分组添加事件监听器
        const actionButtons = document.querySelectorAll('[data-action]:not(.homepage__btn--student):not(.homepage__btn--teacher)');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                if (action) {
                    this.handleAction(action, e.currentTarget);
                }
            });
        });

        // 为状态按钮添加事件监听器
        const statusButtons = document.querySelectorAll('[data-status]');
        statusButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const status = e.currentTarget.dataset.status;
                if (status) {
                    this.handleStatusClick(status);
                }
            });
        });

        // 为记录项添加事件监听器
        const recordItems = document.querySelectorAll('.record-item');
        recordItems.forEach((item, index) => {
            // 添加data-record-id属性，用于识别具体的记录项
            if (!item.dataset.recordId) {
                item.dataset.recordId = index + 1;
            }
            item.addEventListener('click', (e) => {
                // 获取记录名称和类型
                const recordName = item.querySelector('.record-name')?.textContent || '';
                const recordId = item.dataset.recordId;

                if (recordName && recordId) {
                    this.handleRecordItemClick(recordId, recordName);
                }
            });
        });

        // 键盘导航
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        // 窗口大小变化 - 添加防抖处理
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 100));
    }

    // 初始化组件
    initializeComponents() {
        this.modal = document.getElementById('modal');
        this.notification = document.getElementById('notification');

        // 初始化工具提示
        this.initializeTooltips();

        // 初始化懒加载
        this.initializeLazyLoading();
    }

    // 设置导航
    setupNavigation() {
        // 从URL获取当前页面
        const hash = window.location.hash.substring(1);
        if (hash && this.isValidPage(hash)) {
            this.navigateToPage(hash);
        }
    }

    // 页面导航
    navigateToPage(pageName) {
        // 隐藏所有页面
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.classList.remove('page--active');
        });

        // 显示目标页面
        const targetPage = document.getElementById(pageName);
        if (targetPage) {
            targetPage.classList.add('page--active');
            this.currentPage = pageName;

            // 更新导航状态
            this.updateNavigationState(pageName);

            // 更新URL
            window.history.pushState({}, '', `#${pageName}`);

            // 滚动到顶部
            window.scrollTo(0, 0);

            // 触发页面加载事件
            this.onPageLoad(pageName);
        }
    }

    // 更新导航状态
    updateNavigationState(activePage) {
        const navLinks = document.querySelectorAll('.navbar__link');
        navLinks.forEach(link => {
            link.classList.remove('navbar__link--active');
            if (link.dataset.page === activePage) {
                link.classList.add('navbar__link--active');
            }
        });
    }

    // 页面加载事件
    onPageLoad(pageName) {
        // 根据页面执行特定逻辑
        switch (pageName) {
            case 'student':
                this.loadStudentData();
                break;
            case 'teacher':
                this.loadTeacherData();
                break;
            case 'help':
                this.loadHelpContent();
                break;
        }
    }

    // 处理按钮动作
    handleAction(action, element) {
        // 确保每次操作都更新用户类型状态
        const savedUserType = localStorage.getItem('userType');
        this.isTeacher = savedUserType === 'teacher';

        // 在控制台记录当前状态，便于调试
        console.log('当前动作:', action);
        console.log('用户类型状态 - isTeacher:', this.isTeacher);
        console.log('用户类型状态 - localStorage:', savedUserType);
        console.log('当前页面URL:', window.location.href);

        switch (action) {
            case 'student-login':
                this.showLoginModal('student');
                break;
            case 'teacher-login':
                this.showLoginModal('teacher');
                break;
            case 'edit-profile':
                this.showEditProfileModal();
                break;
            case 'new-application':
            case 'apply':
                console.log('执行'+action+'动作，即将跳转到new-application.html');
                // 直接使用绝对路径确保跳转正确
                window.location.href = 'new-application.html';
                break;
            case 'upload-transcript':
                this.showUploadModal();
                break;
            case 'view-all':
                this.showAllApplications();
                break;
            case 'export-list':
                this.exportStudentList();
                break;
            case 'new-announcement':
                this.showAnnouncementModal();
                break;
            case 'export-data':
                this.exportData();
                break;
            case 'generate-report':
                this.generateReport();
                break;
            case 'modal-cancel':
                this.closeModal();
                break;
            case 'modal-confirm':
                // 检查当前是否是登录模态框
                const modalTitleEl = document.querySelector('#modal .modal__title');
                const modalTitle = modalTitleEl?.textContent;

                console.log('模态框标题:', modalTitle);

                if (modalTitle === '学生端登录' || modalTitle === '教师端登录') {
                    console.log('识别为登录模态框，调用handleLoginSubmit');
                    this.handleLoginSubmit();
                } else {
                    this.confirmModal();
                }
                break;
            case 'logout':
                this.logout();
                break;
            case 'apply':
                this.showNewApplicationModal();
                break;
            case 'records':
                this.showAllApplications();
                break;
            case 'transcript':
                // 导航到显示四个分类按钮的中间页面
                console.log('点击成绩单按钮，导航到分类选择页面');
                window.location.href = 'transcript-category.html';
                break;
            case 'guide':
                console.log('点击规范指南按钮，导航到规范指南页面');
                window.location.href = 'submission-guide.html';
                break;
            case 'profile':
                // 根据用户类型导航到相应的个人信息页面
                console.log('Profile action triggered');
                console.log('isTeacher value:', window.baoyanHelper ? window.baoyanHelper.isTeacher : 'undefined');
                console.log('LocalStorage userType:', localStorage.getItem('userType'));
                console.log('Current URL:', window.location.href);

                // 三重检查机制确保正确导航：
                // 1. 检查当前URL是否包含教师面板标识
                const isOnTeacherPage = window.location.href.includes('teacher-dashboard.html');
                // 2. 检查localStorage中的用户类型
                const userType = localStorage.getItem('userType');

                // 如果在教师面板页面或明确是教师用户，导航到教师个人信息
                if (isOnTeacherPage || userType === 'teacher' || (window.baoyanHelper && window.baoyanHelper.isTeacher)) {
                    console.log('教师用户确认，导航到teacher-profile.html');
                    window.location.href = 'teacher-profile.html';
                } else {
                    console.log('学生用户确认，导航到student-profile.html');
                    window.location.href = 'student-profile.html';
                }
                break;
            case 'back':
                // 返回按钮处理
                console.log('返回按钮点击');
                window.location.href = 'student-records.html';
                break;
            case 'back-to-dashboard':
                // 申报记录页面的返回按钮，导航到学生仪表盘
                console.log('申报记录页面返回按钮点击');
                window.location.href = 'student-dashboard.html';
                break;
            case 'scientific-competition':
                // 科研竞赛申报记录
                console.log('查看科研竞赛申报记录');
                this.showNotification('正在加载科研竞赛申报记录...', 'info');
                window.location.href = 'scientific-competition.html';
                break;
            case 'honor-title':
                // 荣誉称号申报记录
                console.log('查看荣誉称号申报记录');
                this.showNotification('正在加载荣誉称号申报记录...', 'info');
                window.location.href = 'honor-title.html';
                break;
            case 'social-work':
                // 社会工作申报记录
                console.log('查看社会工作申报记录');
                this.showNotification('正在加载社会工作申报记录...', 'info');
                window.location.href = 'social-work.html';
                break;
            case 'other-records':
                // 其他申报记录
                console.log('查看其他申报记录');
                this.showNotification('正在加载其他申报记录...', 'info');
                window.location.href = 'other-records.html';
                break;
            case 'security':
                // 根据用户类型导航到相应的账号安全页面
                console.log('Security action triggered');
                console.log('isTeacher value:', window.baoyanHelper ? window.baoyanHelper.isTeacher : 'undefined');
                console.log('LocalStorage userType:', localStorage.getItem('userType'));
                console.log('Current URL:', window.location.href);

                // 三重检查机制确保正确导航：
                // 1. 检查当前URL是否包含教师面板标识
                const isOnTeacherPageForSecurity = window.location.href.includes('teacher-dashboard.html');
                // 2. 检查localStorage中的用户类型
                const userTypeForSecurity = localStorage.getItem('userType');

                // 如果在教师面板页面或明确是教师用户，导航到教师账号安全
                if (isOnTeacherPageForSecurity || userTypeForSecurity === 'teacher' || (window.baoyanHelper && window.baoyanHelper.isTeacher)) {
                    console.log('教师用户确认，导航到teacher-security.html');
                    window.location.href = 'teacher-security.html';
                } else {
                    console.log('学生用户确认，导航到student-security.html');
                    window.location.href = 'student-security.html';
                }
                break;
            case 'notifications':
                // 根据用户类型导航到相应的通知页面
                console.log('Notifications action triggered');
                console.log('isTeacher value:', window.baoyanHelper ? window.baoyanHelper.isTeacher : 'undefined');
                console.log('LocalStorage userType:', localStorage.getItem('userType'));
                console.log('Current URL:', window.location.href);

                // 三重检查机制确保正确导航：
                // 1. 检查当前URL是否包含教师面板标识
                const isOnTeacherPageForNotifications = window.location.href.includes('teacher-dashboard.html');
                // 2. 检查localStorage中的用户类型
                const userTypeForNotifications = localStorage.getItem('userType');

                // 如果在教师面板页面或明确是教师用户，导航到教师通知页面
                if (isOnTeacherPageForNotifications || userTypeForNotifications === 'teacher' || (window.baoyanHelper && window.baoyanHelper.isTeacher)) {
                    console.log('教师用户确认，导航到teacher-notifications.html');
                    window.location.href = 'teacher-notifications.html';
                } else {
                    console.log('学生用户确认，导航到student-notifications.html');
                    window.location.href = 'student-notifications.html';
                }
                break;
            case 'confirm-password-change':
                // 确认修改手机
                this.confirmPhoneChange();
                break;
            case 'confirm-email-change':
                // 确认修改邮箱
                this.confirmEmailChange();
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    // 处理状态按钮点击
    handleStatusClick(status) {
        console.log('状态按钮点击:', status);

        // 获取当前页面的基本名称，用于确定要导航到哪个状态详情页面
        const currentPath = window.location.pathname;
        let basePage = '';

        // 根据当前页面确定基础页面名称
        if (currentPath.includes('scientific-competition')) {
            basePage = 'scientific-competition';
        } else if (currentPath.includes('honor-title')) {
            basePage = 'honor-title';
        } else if (currentPath.includes('social-work')) {
            basePage = 'social-work';
        } else if (currentPath.includes('other-records')) {
            basePage = 'other-records';
        }

        // 如果无法确定基础页面，则不进行跳转
        if (!basePage) {
            console.log('无法确定基础页面，不进行跳转');
            return;
        }

        // 构建目标页面URL
        let targetPage = '';
        if (status === 'passed') {
            targetPage = `${basePage}-passed.html`;
        } else if (status === 'rejected') {
            targetPage = `${basePage}-failed.html`;
        } else if (status === 'pending') {
            targetPage = `${basePage}-pending.html`;
        }

        // 如果状态无效，则不进行跳转
        if (!targetPage) {
            console.log('无效的状态值，不进行跳转');
            return;
        }

        // 显示通知并跳转到目标页面
        this.showNotification(`正在加载${this.getStatusText(status)}的记录...`, 'info');
        window.location.href = targetPage;
    }

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            'passed': '已通过',
            'rejected': '未通过',
            'pending': '审核中'
        };
        return statusMap[status] || status;
    }

    // 处理记录项点击
    handleRecordItemClick(recordId, recordName) {
        console.log('记录项点击:', recordId, recordName);

        // 获取当前页面的基本名称，用于确定记录类型
        const currentPath = window.location.pathname;
        let recordType = '';

        // 根据当前页面确定记录类型
        if (currentPath.includes('scientific-competition')) {
            recordType = '科研竞赛';
        } else if (currentPath.includes('honor-title')) {
            recordType = '荣誉称号';
        } else if (currentPath.includes('social-work')) {
            recordType = '社会工作';
        } else if (currentPath.includes('other-records')) {
            recordType = '其他记录';
        }

        // 确定记录状态
        let recordStatus = 'pending'; // 默认状态
        if (currentPath.includes('passed')) {
            recordStatus = 'passed';
        } else if (currentPath.includes('failed')) {
            recordStatus = 'rejected';
        } else if (currentPath.includes('pending')) {
            recordStatus = 'pending';
        }

        // 显示通知并跳转到项目详情页面
        this.showNotification(`正在加载${recordName}的详情...`, 'info');

        // 使用URL参数传递记录信息
        setTimeout(() => {
            window.location.href = `project-detail.html?id=${recordId}&name=${encodeURIComponent(recordName)}&type=${encodeURIComponent(recordType)}&status=${recordStatus}`;
        }, 500);
    }

    // 处理退出登录
    logout() {
        // 清除可能的用户信息存储
        // 实际应用中可能需要清除localStorage或cookie中的token
        this.showNotification('已成功退出登录');

        // 延迟跳转到首页
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);
    }

    // 设置模态框
    setupModals() {
        if (!this.modal) return;

        // 关闭按钮
        const closeBtn = this.modal.querySelector('.modal__close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }

        // 点击遮罩关闭
        const overlay = this.modal.querySelector('.modal__overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeModal());
        }
    }

    // 显示模态框 - 优化性能
    showModal(title, content, actions = []) {
        if (!this.modal) return;

        // 预先设置内容，避免在显示时进行大量DOM操作
        const titleEl = this.modal.querySelector('.modal__title');
        const bodyEl = this.modal.querySelector('.modal__body');
        const footerEl = this.modal.querySelector('.modal__footer');

        if (titleEl) titleEl.textContent = title;
        if (bodyEl) bodyEl.innerHTML = content;

        // 更新按钮
        if (footerEl && actions.length > 0) {
            footerEl.innerHTML = actions.map(action =>
                `<button class="btn ${action.class || 'btn--secondary'}" data-action="${action.action}">${action.text}</button>`
            ).join('');
        }

        // 使用requestAnimationFrame优化重绘性能
        requestAnimationFrame(() => {
            this.modal.classList.add('modal--active');
            document.body.style.overflow = 'hidden';

            // 延迟焦点管理，确保模态框完全显示
            setTimeout(() => {
                const firstFocusable = this.modal.querySelector('button, input, textarea, select');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }, 50);
        });
    }

    // 关闭模态框
    closeModal() {
        if (!this.modal) return;

        this.modal.classList.remove('modal--active');
        document.body.style.overflow = '';
    }

    // 确认模态框
    confirmModal() {
        // 这里可以添加确认逻辑
        this.showNotification('操作已确认', 'success');
        this.closeModal();
    }

    // 显示登录模态框
    showLoginModal(type) {
        this.loginUserType = type; // 存储登录用户类型
        const title = type === 'student' ? '学生端登录' : '教师端登录';
        const content = `
            <form class="login-form" id="login-form">
                <div class="form-group">
                    <label for="username">用户名/学号</label>
                    <input type="text" id="username" name="username" required placeholder="请输入用户名或学号">
                </div>
                <div class="form-group">
                    <label for="password">密码</label>
                    <input type="password" id="password" name="password" required placeholder="请输入密码">
                </div>
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="remember">
                        <span>记住我</span>
                    </label>
                </div>
                <div class="form-group">
                    <a href="reset-password.html" class="forgot-password">忘记密码？</a>
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '登录', action: 'modal-confirm', class: 'btn--primary' }
        ];

        this.showModal(title, content, actions);

        // 添加表单提交事件阻止
        setTimeout(() => {
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    console.log('表单默认提交被阻止');
                });
            }

            // 添加额外的事件监听器确保登录按钮能正确触发
            const confirmButton = document.querySelector('#modal [data-action="modal-confirm"]');
            if (confirmButton) {
                // 移除可能存在的旧监听器
                const newConfirmButton = confirmButton.cloneNode(true);
                confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);

                // 添加新监听器
                newConfirmButton.addEventListener('click', () => {
                    console.log('登录按钮直接点击事件触发');
                    this.handleLoginSubmit();
                });
            }
        }, 100);
    }

    // 处理登录表单提交
    handleLoginSubmit() {
        // 添加调试信息
        console.log('handleLoginSubmit方法被调用');

        // 获取表单元素
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const rememberCheckbox = document.querySelector('input[name="remember"]');

        // 检查元素是否存在
        if (!usernameInput || !passwordInput || !rememberCheckbox) {
            console.error('无法找到表单元素');
            this.showNotification('系统错误，请刷新页面重试', 'error');
            return;
        }

        // 获取输入值
        const username = usernameInput.value;
        const password = passwordInput.value;
        const remember = rememberCheckbox.checked;

        console.log('表单数据:', { username, password, remember });

        // 简单验证
        if (!username || !password) {
            this.showNotification('请填写完整的登录信息', 'error');
            return;
        }

        // 实现默认密码验证：任意账号+密码123456可登录
        if (password !== '123456') {
            this.showNotification('错误', 'error');
            return;
        }

        // 模拟登录API调用
        this.login(username, password, this.loginUserType).then(() => {
            // 设置用户类型标志
            this.isTeacher = this.loginUserType === 'teacher';

            // 保存用户类型到localStorage，以便页面刷新后仍能保持状态
            localStorage.setItem('userType', this.loginUserType);

            // 显示登录成功提示
            this.showNotification('登录成功，正在跳转...');

            // 根据用户类型跳转到相应的首页
            setTimeout(() => {
                if (this.loginUserType === 'teacher') {
                    window.location.href = 'teacher-dashboard.html';
                } else {
                    window.location.href = 'student-dashboard.html';
                }
            }, 1500);
        }).catch(error => {
            this.showNotification('登录失败，请重试', 'error');
        });
    }

    // 显示编辑资料模态框
    showEditProfileModal() {
        const content = `
            <form class="profile-form">
                <div class="form-group">
                    <label for="name">姓名</label>
                    <input type="text" id="name" name="name" value="张三" required>
                </div>
                <div class="form-group">
                    <label for="studentId">学号</label>
                    <input type="text" id="studentId" name="studentId" value="2021001001" required>
                </div>
                <div class="form-group">
                    <label for="major">专业</label>
                    <input type="text" id="major" name="major" value="计算机科学与技术" required>
                </div>
                <div class="form-group">
                    <label for="email">邮箱</label>
                    <input type="email" id="email" name="email" value="zhangsan@example.com" required>
                </div>
                <div class="form-group">
                    <label for="phone">电话</label>
                    <input type="tel" id="phone" name="phone" value="13800138000">
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '保存', action: 'modal-confirm', class: 'btn--primary' }
        ];

        this.showModal('编辑个人信息', content, actions);
    }

    // 显示新申请模态框
    showNewApplicationModal() {
        const content = `
            <form class="application-form">
                <div class="form-group">
                    <label for="applicationType">申请类型</label>
                    <select id="applicationType" name="applicationType" required>
                        <option value="">请选择申请类型</option>
                        <option value="research">科研竞赛</option>
                        <option value="social">社会工作</option>
                        <option value="honor">荣誉称号</option>
                        <option value="other">其他</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="applicationTitle">申请标题</label>
                    <input type="text" id="applicationTitle" name="applicationTitle" required>
                </div>
                <div class="form-group">
                    <label for="applicationDescription">申请描述</label>
                    <textarea id="applicationDescription" name="applicationDescription" rows="4" required></textarea>
                </div>
                <div class="form-group">
                    <label for="applicationFiles">相关文件</label>
                    <input type="file" id="applicationFiles" name="applicationFiles" multiple accept=".pdf,.doc,.docx,.jpg,.png">
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '提交申请', action: 'modal-confirm', class: 'btn--primary' }
        ];

        this.showModal('新建申请', content, actions);
    }

    // 显示上传模态框
    showUploadModal() {
        const content = `
            <form class="upload-form">
                <div class="form-group">
                    <label for="transcriptType">成绩单类型</label>
                    <select id="transcriptType" name="transcriptType" required>
                        <option value="">请选择类型</option>
                        <option value="semester">学期成绩单</option>
                        <option value="year">年度成绩单</option>
                        <option value="total">总成绩单</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="transcriptFile">选择文件</label>
                    <input type="file" id="transcriptFile" name="transcriptFile" accept=".pdf,.jpg,.png" required>
                </div>
                <div class="form-group">
                    <label for="transcriptNote">备注</label>
                    <textarea id="transcriptNote" name="transcriptNote" rows="3" placeholder="可选备注信息"></textarea>
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '上传', action: 'modal-confirm', class: 'btn--primary' }
        ];

        this.showModal('上传成绩单', content, actions);
    }

    // 显示成绩单模态框
    showTranscriptModal() {
        const content = `
            <div class="transcript-viewer">
                <div class="transcript-header">
                    <h3>我的成绩单</h3>
                    <p>总成绩点: <span class="gpa-highlight">3.85</span></p>
                </div>
                <div class="transcript-content">
                    <div class="semester-section">
                        <h4>2023-2024学年 第一学期</h4>
                        <table class="transcript-table">
                            <thead>
                                <tr>
                                    <th>课程名称</th>
                                    <th>学分</th>
                                    <th>成绩</th>
                                    <th>绩点</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>高等数学</td>
                                    <td>5</td>
                                    <td>92</td>
                                    <td>4.0</td>
                                </tr>
                                <tr>
                                    <td>线性代数</td>
                                    <td>4</td>
                                    <td>88</td>
                                    <td>3.7</td>
                                </tr>
                                <tr>
                                    <td>计算机基础</td>
                                    <td>3</td>
                                    <td>95</td>
                                    <td>4.0</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <!-- 更多学期可以在这里添加 -->
                </div>
                <div class="transcript-actions">
                    <button class="btn btn--secondary" data-action="upload-transcript">上传新成绩单</button>
                </div>
            </div>
        `;

        const actions = [
            { text: '关闭', action: 'modal-cancel', class: 'btn--secondary' }
        ];

        this.showModal('我的成绩单', content, actions);
    }

    // 显示规范指南模态框
    showGuideModal() {
        const content = `
            <div class="guide-content">
                <h3>保研申请规范指南</h3>
                <div class="guide-section">
                    <h4>申请流程</h4>
                    <ol>
                        <li>准备申请材料，包括成绩单、获奖证书等</li>
                        <li>在系统中填写申请信息</li>
                        <li>上传相关证明材料</li>
                        <li>提交申请并等待审核</li>
                    </ol>
                </div>
                <div class="guide-section">
                    <h4>材料要求</h4>
                    <ul>
                        <li>所有材料必须为原件扫描件</li>
                        <li>文件格式支持PDF、JPG、PNG</li>
                        <li>单个文件大小不超过10MB</li>
                    </ul>
                </div>
                <div class="guide-section">
                    <h4>常见问题</h4>
                    <div class="faq-item">
                        <strong>Q: 申请截止日期是什么时候？</strong>
                        <p>A: 每学期末的前两周为申请截止日期，请关注系统通知。</p>
                    </div>
                    <div class="faq-item">
                        <strong>Q: 如何查询申请进度？</strong>
                        <p>A: 在"申报记录"中可以查看所有申请的当前状态。</p>
                    </div>
                </div>
            </div>
        `;

        const actions = [
            { text: '关闭', action: 'modal-cancel', class: 'btn--secondary' }
        ];

        this.showModal('规范指南', content, actions);
    }



    // 显示修改密码模态框
    showPasswordChangeModal() {
        const title = '修改密码';
        const content = `
            <form id="password-form">
                <div class="form-group">
                    <label for="current-password">当前密码</label>
                    <input type="password" id="current-password" name="currentPassword" required placeholder="请输入当前密码">
                </div>
                <div class="form-group">
                    <label for="new-password">新密码</label>
                    <input type="password" id="new-password" name="newPassword" required placeholder="请输入新密码">
                </div>
                <div class="form-group">
                    <label for="confirm-password">确认新密码</label>
                    <input type="password" id="confirm-password" name="confirmPassword" required placeholder="请再次输入新密码">
                </div>
                <div class="password-tips">
                    <p>密码要求：</p>
                    <ul>
                        <li>长度至少8位</li>
                        <li>包含字母和数字</li>
                        <li>建议包含特殊字符</li>
                    </ul>
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '确认修改', action: 'confirm-password-change', class: 'btn--primary' }
        ];

        this.showModal(title, content, actions);
    }

    // 显示修改手机号模态框
    showPhoneChangeModal() {
        const title = '修改手机号';
        const content = `
            <form id="phone-form">
                <div class="form-group">
                    <label for="current-phone">当前手机号</label>
                    <input type="tel" id="current-phone" name="currentPhone" required placeholder="请输入当前手机号">
                </div>
                <div class="form-group">
                    <label for="new-phone">新手机号</label>
                    <input type="tel" id="new-phone" name="newPhone" required placeholder="请输入新手机号">
                </div>
                <div class="form-group">
                    <label for="verification-code">验证码</label>
                    <div class="verification-input">
                        <input type="text" id="verification-code" name="verificationCode" required placeholder="请输入验证码">
                        <button type="button" id="send-code-btn" class="btn btn--secondary small">发送验证码</button>
                    </div>
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '确认修改', action: 'confirm-phone-change', class: 'btn--primary' }
        ];

        this.showModal(title, content, actions);

        // 添加发送验证码按钮事件监听
        setTimeout(() => {
            const sendCodeBtn = document.getElementById('send-code-btn');
            if (sendCodeBtn) {
                sendCodeBtn.addEventListener('click', () => {
                    this.sendVerificationCode('phone');
                });
            }
        }, 100);
    }

    // 显示修改邮箱模态框
    showEmailChangeModal() {
        const title = '修改邮箱';
        const content = `
            <form id="email-form">
                <div class="form-group">
                    <label for="current-email">当前邮箱</label>
                    <input type="email" id="current-email" name="currentEmail" required placeholder="请输入当前邮箱">
                </div>
                <div class="form-group">
                    <label for="new-email">新邮箱</label>
                    <input type="email" id="new-email" name="newEmail" required placeholder="请输入新邮箱">
                </div>
                <div class="form-group">
                    <label for="email-verification-code">验证码</label>
                    <div class="verification-input">
                        <input type="text" id="email-verification-code" name="emailVerificationCode" required placeholder="请输入验证码">
                        <button type="button" id="send-email-code-btn" class="btn btn--secondary small">发送验证码</button>
                    </div>
                </div>
            </form>
        `;

        const actions = [
            { text: '取消', action: 'modal-cancel', class: 'btn--secondary' },
            { text: '确认修改', action: 'confirm-email-change', class: 'btn--primary' }
        ];

        this.showModal(title, content, actions);

        // 添加发送验证码按钮事件监听
        setTimeout(() => {
            const sendEmailCodeBtn = document.getElementById('send-email-code-btn');
            if (sendEmailCodeBtn) {
                sendEmailCodeBtn.addEventListener('click', () => {
                    this.sendVerificationCode('email');
                });
            }
        }, 100);
    }

    // 显示通知列表
    showNotificationsList() {
        const title = '消息通知';
        // 模拟通知数据
        const notifications = [
            {
                id: 1,
                title: '申请状态更新',
                message: '您的保研申请已通过初审，请准备面试。',
                time: '2023-05-15 14:30',
                read: false
            },
            {
                id: 2,
                title: '系统公告',
                message: '系统将于本周日进行维护，请提前做好准备。',
                time: '2023-05-10 09:15',
                read: true
            },
            {
                id: 3,
                title: '导师回复',
                message: '李教授已查看您的申请材料，请保持联系。',
                time: '2023-05-08 16:45',
                read: true
            }
        ];

        const content = `
            <div class="notifications-list">
                ${notifications.map(notification => `
                    <div class="notification-item ${!notification.read ? 'unread' : ''}">
                        <div class="notification-header">
                            <h4>${notification.title}</h4>
                            <span class="notification-time">${notification.time}</span>
                        </div>
                        <p class="notification-message">${notification.message}</p>
                    </div>
                `).join('')}
            </div>
        `;

        const actions = [
            { text: '关闭', action: 'modal-cancel', class: 'btn--secondary' }
        ];

        this.showModal(title, content, actions);
    }

    // 发送验证码
    sendVerificationCode(type) {
        // 模拟发送验证码
        const sendBtn = type === 'phone' ? document.getElementById('send-code-btn') : document.getElementById('send-email-code-btn');
        if (sendBtn) {
            let countdown = 60;
            sendBtn.disabled = true;
            sendBtn.textContent = `${countdown}秒后重新发送`;

            const timer = setInterval(() => {
                countdown--;
                sendBtn.textContent = `${countdown}秒后重新发送`;

                if (countdown <= 0) {
                    clearInterval(timer);
                    sendBtn.disabled = false;
                    sendBtn.textContent = '发送验证码';
                }
            }, 1000);
        }

        this.showNotification('验证码已发送，请查收', 'info');
    }

    // 确认修改密码
    confirmPasswordChange() {
        // 获取表单数据
        const currentPassword = document.getElementById('current-password')?.value;
        const newPassword = document.getElementById('new-password')?.value;
        const confirmPassword = document.getElementById('confirm-password')?.value;

        // 表单验证
        if (!currentPassword || !newPassword || !confirmPassword) {
            this.showNotification('请填写所有密码字段', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showNotification('两次输入的新密码不一致', 'error');
            return;
        }

        if (newPassword.length < 8 || !/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/.test(newPassword)) {
            this.showNotification('新密码必须至少8位，包含字母和数字', 'error');
            return;
        }

        // 模拟API请求
        setTimeout(() => {
            this.showNotification('密码修改成功');
            this.closeModal();
        }, 1500);
    }

    // 确认修改手机号
    confirmPhoneChange() {
        // 获取表单数据
        const currentPhone = document.getElementById('current-phone')?.value;
        const newPhone = document.getElementById('new-phone')?.value;
        const verificationCode = document.getElementById('verification-code')?.value;

        // 表单验证
        if (!currentPhone || !newPhone || !verificationCode) {
            this.showNotification('请填写所有字段', 'error');
            return;
        }

        if (!/^1[3-9]\d{9}$/.test(newPhone)) {
            this.showNotification('请输入有效的手机号码', 'error');
            return;
        }

        if (currentPhone === newPhone) {
            this.showNotification('新手机号不能与当前手机号相同', 'error');
            return;
        }

        // 模拟API请求
        setTimeout(() => {
            this.showNotification('手机号修改成功');
            this.closeModal();
        }, 1500);
    }

    // 确认修改邮箱
    confirmEmailChange() {
        // 获取表单数据
        const currentEmail = document.getElementById('current-email')?.value;
        const newEmail = document.getElementById('new-email')?.value;
        const verificationCode = document.getElementById('email-verification-code')?.value;

        // 表单验证
        if (!currentEmail || !newEmail || !verificationCode) {
            this.showNotification('请填写所有字段', 'error');
            return;
        }

        // 简单的邮箱格式验证
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
        if (!emailRegex.test(newEmail)) {
            this.showNotification('请输入有效的电子邮箱', 'error');
            return;
        }

        if (currentEmail === newEmail) {
            this.showNotification('新邮箱不能与当前邮箱相同', 'error');
            return;
        }

        // 模拟API请求
        setTimeout(() => {
            this.showNotification('邮箱修改成功');
            this.closeModal();
        }, 1500);
    }

    // 验证页面名称
    isValidPage(pageName) {
        const validPages = ['home', 'student', 'teacher', 'help'];
        return validPages.includes(pageName);
    }

    // 工具方法：防抖
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 工具方法：节流
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // 初始化工具提示
    initializeTooltips() {
        // 这里可以初始化工具提示功能
    }

    // 初始化懒加载
    initializeLazyLoading() {
        // 这里可以初始化图片懒加载功能
    }

    // 处理键盘导航
    handleKeyboardNavigation(e) {
        // 这里可以实现键盘导航功能
    }

    // 处理窗口大小变化
    handleResize() {
        // 这里可以实现响应式调整逻辑
    }

    // 加载学生数据
    loadStudentData() {
        // 这里可以加载学生相关数据
    }

    // 加载教师数据
    loadTeacherData() {
        // 这里可以加载教师相关数据
    }

    // 设置通知系统
    setupNotifications() {
        // 这里可以设置通知系统
    }

    // 显示通知
    showNotification(message, type = 'success') {
        // 确保通知元素存在
        if (!this.notification) {
            this.notification = document.getElementById('notification');
        }

        if (!this.notification) {
            console.log(`Notification (${type}): ${message}`);
            return;
        }

        // 设置通知消息
        const messageElement = this.notification.querySelector('.notification__message');
        const iconElement = this.notification.querySelector('.notification__icon');

        if (messageElement) {
            messageElement.textContent = message;
        }

        // 根据通知类型设置图标和样式
        if (iconElement) {
            switch (type) {
                case 'success':
                    iconElement.textContent = '✓';
                    iconElement.style.color = 'var(--color-success)';
                    break;
                case 'error':
                    iconElement.textContent = '✗';
                    iconElement.style.color = 'var(--color-error)';
                    break;
                case 'warning':
                    iconElement.textContent = '⚠';
                    iconElement.style.color = 'var(--color-warning)';
                    break;
                case 'info':
                default:
                    iconElement.textContent = 'ℹ';
                    iconElement.style.color = 'var(--color-info)';
                    break;
            }
        }

        // 显示通知
        this.notification.style.display = 'flex';
        setTimeout(() => {
            this.notification.classList.add('notification--active');
        }, 10);

        // 设置自动关闭
        setTimeout(() => {
            this.notification.classList.remove('notification--active');
            setTimeout(() => {
                this.notification.style.display = 'none';
            }, 300);
        }, 3000);
    }

    // 显示通知列表
    showNotificationsList() {
        window.location.href = 'student-notifications.html';
    }

    // 设置FAQ功能
    setupFAQ() {
        // 这里可以设置FAQ功能
    }

    // 设置表单验证
    setupFormValidation() {
        // 这里可以设置表单验证功能
    }

    // API请求处理
    async apiRequest(endpoint, method = 'GET', data = null) {
        try {
            const url = endpoint;
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            // 模拟API响应
            return new Promise((resolve) => {
                setTimeout(() => {
                    if (endpoint === '/auth/login' && method === 'POST') {
                        // 模拟登录成功
                        resolve({
                            success: true,
                            token: 'mock-jwt-token',
                            user: {
                                id: data.username,
                                name: data.username === 'admin' ? '管理员' : data.username,
                                role: data.userType
                            }
                        });
                    } else if (endpoint === '/user/student' && method === 'GET') {
                        return {
                            id: 'S1001',
                            name: '张三',
                            grade: '2021',
                            department: '计算机科学与技术学院',
                            gender: '男',
                            nationality: '汉族',
                            political: '共青团员',
                            idNumber: '3501XXXXXXXXXXXX1234',
                            phone: '138XXXX1234',
                            email: 'zhangsan@example.com',
                            avatar: '张'
                        };
                    } else if (endpoint === '/user/teacher' && method === 'GET') {
                        return {
                            id: 'T1001',
                            name: '李四',
                            department: '计算机学院',
                            position: '副教授',
                            avatar: '李'
                        };
                    }

                    // 对于其他请求返回成功
                    resolve({ success: true });
                }, 500);
            });
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    // 获取用户数据
    async fetchUserData(userType) {
        try {
            const endpoint = userType === 'student' ? '/user/student' : '/user/teacher';
            const userData = await this.apiRequest(endpoint);
            return userData;
        } catch (error) {
            console.error('Failed to fetch user data:', error);
            throw error;
        }
    }

    // 登录API
    async login(username, password, userType) {
        try {
            const data = {
                username: username,
                password: password,
                userType: userType
            };

            const result = await this.apiRequest('/auth/login', 'POST', data);

            // 存储认证token
            if (result.token) {
                localStorage.setItem('authToken', result.token);
            }

            return result;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    // 获取学生列表
    async getStudentList() {
        try {
            return await this.apiRequest('/students', 'GET');
        } catch (error) {
            console.error('Failed to get student list:', error);
            throw error;
        }
    }

    // 提交申请
    async submitApplication(applicationData) {
        try {
            return await this.apiRequest('/applications', 'POST', applicationData);
        } catch (error) {
            console.error('Failed to submit application:', error);
            throw error;
        }
    }

    // 发布公告
    async publishAnnouncement(announcementData) {
        try {
            return await this.apiRequest('/announcements', 'POST', announcementData);
        } catch (error) {
            console.error('Failed to publish announcement:', error);
            throw error;
        }
    }

    // 加载帮助内容
    loadHelpContent() {
        // 模拟内容加载
        console.log('Loading help content...');
    }

    // 显示所有申请
    showAllApplications() {
        window.location.href = 'student-records.html';
    }

    // 导出学生列表
    exportStudentList() {
        this.showNotification('正在导出学生列表...', 'info');
        // 模拟导出
        setTimeout(() => {
            this.showNotification('学生列表导出成功', 'success');
        }, 2000);
    }

    // 导出数据
    exportData() {
        this.showNotification('正在导出数据...', 'info');
        // 模拟导出
        setTimeout(() => {
            this.showNotification('数据导出成功', 'success');
        }, 2000);
    }

    // 生成报告
    generateReport() {
        this.showNotification('正在生成报告...', 'info');
        // 模拟生成
        setTimeout(() => {
            this.showNotification('报告生成成功', 'success');
        }, 3000);
    }

}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，初始化BaoYanHelper');
    window.baoyanHelper = new BaoYanHelper();

    // 添加全局点击事件监听器来处理所有带data-action属性的元素点击
    document.addEventListener('click', (e) => {
        const actionElement = e.target.closest('[data-action]');
        if (actionElement) {
            const action = actionElement.getAttribute('data-action');
            console.log('检测到data-action点击事件:', action);
            window.baoyanHelper.handleAction(action, actionElement);
        }
    });

    // 额外为new-application按钮直接绑定事件，作为备用方案
    const newApplicationBtn = document.querySelector('[data-action="new-application"]');
    if (newApplicationBtn) {
        console.log('找到new-application按钮，添加直接事件绑定');
        newApplicationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            console.log('new-application按钮直接点击事件触发');
            window.location.href = 'new-application.html';
        });
    }
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BaoYanHelper;
}
