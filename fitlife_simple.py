from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'temp-secret-key')

# 数据库配置
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///fitlife.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化SQLAlchemy但不自动创建表
db = SQLAlchemy()
db.init_app(app)

@app.route('/')
def index():
    return render_template_string('''
    <h1>🏥 FitLife 简化版</h1>
    <p>✅ 应用正常启动</p>
    <ul>
        <li><a href="/debug">调试信息</a></li>
        <li><a href="/health">健康检查</a></li>
    </ul>
    ''')

@app.route('/debug')
def debug():
    import sys
    db_status = "已连接" if database_url else "使用SQLite"
    return render_template_string('''
    <h1>🔧 调试信息</h1>
    <p>Python版本: {{ python_version }}</p>
    <p>数据库状态: {{ db_status }}</p>
    <p>SECRET_KEY: {{ secret_set }}</p>
    ''', 
    python_version=sys.version,
    db_status=db_status,
    secret_set="已设置" if os.getenv('SECRET_KEY') else "未设置"
    )

@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected' if database_url else 'sqlite'}

if __name__ == '__main__':
    app.run(debug=True)