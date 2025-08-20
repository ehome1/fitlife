"""
紧急修复版本 - Vercel部署入口
回滚到最基本的稳定版本
"""
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'

try:
    # 尝试导入基础Flask应用
    from flask import Flask, render_template, request, redirect, url_for, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, current_user
    from datetime import datetime, timezone
    
    # 创建基础应用
    app = Flask(__name__)
    
    # 基础配置
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'emergency-secret-key'),
        'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', 'sqlite:///emergency.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': False,
        'TESTING': False
    })
    
    # 初始化数据库
    db = SQLAlchemy(app)
    
    # 基础用户模型
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 基础路由
    @app.route('/')
    def index():
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FitLife - 健身饮食管理</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 100px 0; }
                .feature-card { transition: transform 0.3s; }
                .feature-card:hover { transform: translateY(-5px); }
            </style>
        </head>
        <body>
            <div class="hero text-center">
                <div class="container">
                    <h1 class="display-4 mb-4">🏃‍♂️ FitLife</h1>
                    <p class="lead">智能健身饮食管理平台</p>
                    <p class="mb-4">系统正在恢复中，核心功能暂时可用</p>
                    <div class="mt-4">
                        <a href="/register" class="btn btn-light btn-lg me-3">立即注册</a>
                        <a href="/login" class="btn btn-outline-light btn-lg">用户登录</a>
                    </div>
                </div>
            </div>
            
            <div class="container py-5">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <h3>🍽️ 饮食记录</h3>
                                <p>记录每日饮食，分析营养成分</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <h3>💪 运动追踪</h3>
                                <p>追踪运动数据，制定健身计划</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <h3>📊 数据分析</h3>
                                <p>AI智能分析，个性化建议</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <footer class="bg-light text-center py-4">
                <div class="container">
                    <p class="text-muted mb-0">© 2024 FitLife - 系统维护中，感谢您的耐心等待</p>
                </div>
            </footer>
        </body>
        </html>
        """)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "emergency_mode",
            "message": "系统正在恢复中",
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route('/login')
    def login():
        return render_template_string("""
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h2>🔐 用户登录</h2>
            <p>系统维护中，登录功能暂时不可用</p>
            <p>预计恢复时间：30分钟内</p>
            <a href="/" style="color: #007bff;">返回首页</a>
        </div>
        """)
    
    @app.route('/register')
    def register():
        return render_template_string("""
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h2>📝 用户注册</h2>
            <p>系统维护中，注册功能暂时不可用</p>
            <p>预计恢复时间：30分钟内</p>
            <a href="/" style="color: #007bff;">返回首页</a>
        </div>
        """)
    
    @app.route('/api/<path:path>')
    def api_maintenance(path):
        return jsonify({
            "error": "系统维护中",
            "message": "API功能暂时不可用",
            "path": path
        }), 503
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return render_template_string("""
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h1>404 - 页面未找到</h1>
            <p>请求的页面不存在或系统维护中</p>
            <a href="/" style="color: #007bff;">返回首页</a>
        </div>
        """), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return render_template_string("""
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h1>500 - 服务器错误</h1>
            <p>系统正在维护中，请稍后重试</p>
            <a href="/" style="color: #007bff;">返回首页</a>
        </div>
        """), 500
    
    # 导入render_template_string函数
    from flask import render_template_string
    
    logger.info("✅ 紧急模式应用启动成功")

except Exception as e:
    logger.error(f"❌ 紧急模式启动失败: {e}")
    
    # 最后的备选方案 - 纯静态应用
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def emergency_static():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FitLife - 系统维护中</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .status { background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏃‍♂️ FitLife</h1>
                <h2>🔧 系统维护中</h2>
                <div class="status">
                    <p><strong>我们正在进行系统升级</strong></p>
                    <p>新功能包括：扩展营养分析、热量计算优化、每日励志名言等</p>
                    <p>预计恢复时间：<strong>30-60分钟</strong></p>
                </div>
                <p>感谢您的耐心等待，升级完成后将带来更好的体验！</p>
                <a href="javascript:location.reload()" class="btn">刷新页面</a>
            </div>
        </body>
        </html>
        """
    
    @app.route('/health')
    def emergency_health():
        return jsonify({"status": "critical_error", "error": str(e)})

# 确保Vercel可以访问app变量
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)