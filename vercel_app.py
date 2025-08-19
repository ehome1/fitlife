"""
Vercel部署入口文件 - 优化的Serverless部署
"""
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 设置环境变量确保生产模式
    os.environ['FLASK_ENV'] = 'production'
    
    from app import app as flask_app
    
    # 确保生产环境配置
    flask_app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY=os.getenv('SECRET_KEY', 'fallback-secret-key')
    )
    
    # Vercel需要名为'app'的变量
    app = flask_app
    logger.info("✅ Flask应用加载成功")
    
except Exception as e:
    logger.error(f"❌ Flask应用加载失败: {e}")
    # 创建紧急模式应用
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def emergency():
        return f"""
        <h1>FitLife 应用启动中...</h1>
        <p>系统正在初始化，请稍后刷新页面。</p>
        <p>错误信息: {str(e)}</p>
        <a href="javascript:location.reload()">刷新页面</a>
        """
    
    @app.route('/health')
    def health():
        return jsonify({"status": "emergency", "error": str(e)})
    
    @app.route('/api/<path:path>')
    def api_emergency(path):
        return jsonify({"error": "服务初始化中", "message": str(e)}), 503