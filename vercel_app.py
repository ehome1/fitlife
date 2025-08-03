"""
Vercel部署入口文件 - 符合Vercel规范
"""
try:
    from app import app as flask_app
    # Vercel需要名为'app'的变量
    app = flask_app
except Exception as e:
    # 如果导入失败，创建一个最基本的Flask应用
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def emergency():
        return f"Emergency mode: Import error - {str(e)}"
    
    @app.route('/health')
    def health():
        return {"status": "emergency", "error": str(e)}