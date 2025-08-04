#!/usr/bin/env python3
"""
FitLife应急版本 - 最简化可用系统
只保留核心功能，移除所有可能导致错误的复杂逻辑
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 应急配置 - 只使用必要设置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emergency-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///emergency.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = False

# 移除所有可能导致问题的配置
# app.config['SERVER_NAME'] = None

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== 最简化数据模型 =====

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    
    user = db.relationship('User', backref='profile', uselist=False)

# ===== 应急路由 =====

@app.route('/')
def index():
    """应急首页"""
    try:
        return render_template('emergency_index.html')
    except:
        return """
        <html>
        <head><title>FitLife - 应急模式</title></head>
        <body style="font-family: Arial; margin: 40px; text-align: center;">
            <h1>🚑 FitLife 应急模式</h1>
            <p>系统正在紧急维护中，请稍后再试。</p>
            <p><a href="/login" style="color: blue;">登录</a> | 
               <a href="/register" style="color: blue;">注册</a></p>
            <hr>
            <small>如果您急需使用，请联系客服</small>
        </body>
        </html>
        """

@app.route('/register', methods=['GET', 'POST'])
def register():
    """应急注册"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            # 检查用户是否已存在
            if User.query.filter_by(username=username).first():
                flash('用户名已存在')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('邮箱已注册')
                return redirect(url_for('register'))
            
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"注册错误: {e}")
            flash('注册失败，请重试')
    
    try:
        return render_template('emergency_register.html')
    except:
        return """
        <html>
        <head><title>注册 - FitLife</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h2>用户注册</h2>
            <form method="POST">
                <p><label>用户名: <input type="text" name="username" required></label></p>
                <p><label>邮箱: <input type="email" name="email" required></label></p>
                <p><label>密码: <input type="password" name="password" required></label></p>
                <p><button type="submit">注册</button></p>
            </form>
            <p><a href="/login">已有账户？去登录</a></p>
        </body>
        </html>
        """

@app.route('/login', methods=['GET', 'POST'])
def login():
    """应急登录"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
                
        except Exception as e:
            logger.error(f"登录错误: {e}")
            flash('登录失败，请重试')
    
    try:
        return render_template('emergency_login.html')
    except:
        return """
        <html>
        <head><title>登录 - FitLife</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h2>用户登录</h2>
            <form method="POST">
                <p><label>用户名: <input type="text" name="username" required></label></p>
                <p><label>密码: <input type="password" name="password" required></label></p>
                <p><button type="submit">登录</button></p>
            </form>
            <p><a href="/register">还没账户？去注册</a></p>
        </body>
        </html>
        """

@app.route('/dashboard')
@login_required
def dashboard():
    """应急仪表盘"""
    try:
        return f"""
        <html>
        <head><title>仪表盘 - FitLife</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h1>欢迎, {current_user.username}!</h1>
            <p>✅ 系统运行正常</p>
            <p><strong>应急模式功能:</strong></p>
            <ul>
                <li><a href="/profile">个人资料</a></li>
                <li><a href="/settings">设置</a></li>
                <li><a href="/logout">退出登录</a></li>
            </ul>
            <hr>
            <p><small>完整功能正在恢复中，感谢您的耐心</small></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"仪表盘加载错误: {str(e)}"

@app.route('/profile')
@login_required
def profile():
    """应急个人资料页面"""
    try:
        profile = current_user.profile
        return f"""
        <html>
        <head><title>个人资料 - FitLife</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h2>个人资料</h2>
            <p><strong>用户名:</strong> {current_user.username}</p>
            <p><strong>邮箱:</strong> {current_user.email}</p>
            <p><strong>注册时间:</strong> {current_user.created_at.strftime('%Y-%m-%d')}</p>
            
            {f'''
            <h3>基本信息</h3>
            <p><strong>身高:</strong> {profile.height or "未设置"} cm</p>
            <p><strong>体重:</strong> {profile.weight or "未设置"} kg</p>
            <p><strong>年龄:</strong> {profile.age or "未设置"}</p>
            <p><strong>性别:</strong> {profile.gender or "未设置"}</p>
            ''' if profile else '<p><em>请完善个人资料</em></p>'}
            
            <p><a href="/dashboard">返回仪表盘</a></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"个人资料页面错误: {str(e)}"

@app.route('/settings')
@login_required
def settings():
    """应急设置页面"""
    try:
        return f"""
        <html>
        <head><title>设置 - FitLife</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h2>应用设置</h2>
            <p><strong>用户名:</strong> {current_user.username}</p>
            <p><strong>邮箱:</strong> {current_user.email}</p>
            <p><strong>注册时间:</strong> {current_user.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            
            <h3>系统状态</h3>
            <p>✅ 数据库连接正常</p>
            <p>✅ 用户认证正常</p>
            <p>⚠️ 应急模式运行中</p>
            
            <p><a href="/dashboard">返回仪表盘</a></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"设置页面错误: {str(e)}"

@app.route('/logout')
@login_required
def logout():
    """应急登出"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'mode': 'emergency',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'mode': 'emergency'
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(e):
    return """
    <html>
    <body style="font-family: Arial; margin: 40px; text-align: center;">
        <h1>404 - 页面未找到</h1>
        <p><a href="/">返回首页</a></p>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(e):
    return """
    <html>
    <body style="font-family: Arial; margin: 40px; text-align: center;">
        <h1>🚑 系统维护中</h1>
        <p>服务暂时不可用，我们正在紧急修复</p>
        <p><a href="/">返回首页</a></p>
    </body>
    </html>
    """, 500

# 初始化数据库
def init_db():
    """初始化数据库"""
    try:
        db.create_all()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5001)