from flask import Flask
import os
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-secret-key'

@app.route('/')
def index():
    return '''
    <h1>🏥 FitLife 真实Flask测试</h1>
    <p>✅ 真实Flask应用正常工作</p>
    <ul>
        <li><a href="/debug">调试信息</a></li>
        <li><a href="/test">测试页面</a></li>
    </ul>
    '''

@app.route('/debug')
def debug():
    import sys
    return f'''
    <h1>🔧 真实Flask调试信息</h1>
    <p>Python版本: {sys.version}</p>
    <p>Flask版本: 正常导入</p>
    <p>工作目录: {os.getcwd()}</p>
    '''

@app.route('/test')
def test():
    return '''
    <h1>🧪 真实Flask测试页面</h1>
    <p>这是真正的Flask路由</p>
    '''

# Vercel需要的app变量
if __name__ == '__main__':
    app.run(debug=True)