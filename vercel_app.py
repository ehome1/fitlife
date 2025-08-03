"""
Vercel部署入口文件 - 简化版本
"""
try:
    from app import app
    # Vercel需要这个变量
    application = app
except Exception as e:
    # 如果导入失败，创建一个最基本的Flask应用
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def emergency():
        return f"Emergency mode: {str(e)}"