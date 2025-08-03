"""
FitLife最小化版本用于调试
"""
from flask import Flask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-secret-key'

@app.route('/')
def index():
    try:
        return """
        <h1>🏥 FitLife 最小化版本</h1>
        <p>✅ Flask应用启动成功</p>
        <p>正在逐步恢复功能...</p>
        <ul>
            <li><a href="/debug">调试信息</a></li>
            <li><a href="/env">环境变量</a></li>
        </ul>
        """
    except Exception as e:
        return f"Index error: {str(e)}", 500

@app.route('/debug')
def debug():
    try:
        import sys
        return f"""
        <h1>🔧 调试信息</h1>
        <p>Python版本: {sys.version}</p>
        <p>Flask版本: 正常导入</p>
        <p>工作目录: {os.getcwd()}</p>
        """
    except Exception as e:
        return f"Debug error: {str(e)}", 500

@app.route('/env')
def env_check():
    try:
        env_vars = {
            "VERCEL": os.getenv('VERCEL', 'Not set'),
            "GEMINI_API_KEY": "Set" if os.getenv('GEMINI_API_KEY') else "Not set",
            "DATABASE_URL": "Set" if os.getenv('DATABASE_URL') else "Not set",
            "SECRET_KEY": "Set" if os.getenv('SECRET_KEY') else "Not set"
        }
        
        html = "<h1>🌍 环境变量检查</h1><ul>"
        for key, value in env_vars.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        
        return html
    except Exception as e:
        return f"Env check error: {str(e)}", 500