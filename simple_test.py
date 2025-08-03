"""
最简单的Vercel测试应用
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <h1>🎉 FitLife 测试成功!</h1>
    <p>✅ Vercel Python运行时正常</p>
    <p>✅ Flask应用可以启动</p>
    <p>现在开始诊断主应用问题...</p>
    <ul>
        <li><a href="/test">基础测试</a></li>
        <li><a href="/env">环境变量检查</a></li>
    </ul>
    """

@app.route('/test')
def test():
    return {"status": "ok", "message": "Basic Flask app working"}

@app.route('/env')
def env_check():
    import os
    return {
        "VERCEL": os.getenv('VERCEL', 'Not set'),
        "GEMINI_API_KEY": "Set" if os.getenv('GEMINI_API_KEY') else "Not set",
        "DATABASE_URL": "Set" if os.getenv('DATABASE_URL') else "Not set",
        "SECRET_KEY": "Set" if os.getenv('SECRET_KEY') else "Not set"
    }

if __name__ == '__main__':
    app.run(debug=True)