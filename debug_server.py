#!/usr/bin/env python3
"""
调试服务器 - 简化版本用于测试
"""
import os
from flask import Flask, render_template, jsonify
from flask_login import current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-key'

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'FitLife Debug Server Running',
        'config': {
            'debug': app.config.get('DEBUG', False),
            'secret_key_set': bool(app.config.get('SECRET_KEY')),
        }
    })

@app.route('/debug')
def debug():
    return """
    <h1>🔧 FitLife Debug</h1>
    <h2>环境检查:</h2>
    <ul>
        <li>Flask版本: 正常</li>
        <li>模板引擎: Jinja2</li>
        <li>应用状态: 运行中</li>
    </ul>
    <h2>测试链接:</h2>
    <ul>
        <li><a href="/test-template">测试模板渲染</a></li>
        <li><a href="/test-profile">测试Profile页面</a></li>
        <li><a href="/test-settings">测试Settings页面</a></li>
    </ul>
    """

@app.route('/test-template')
def test_template():
    try:
        # 创建简单的模拟用户数据
        class MockUser:
            username = 'testuser'
            email = 'test@example.com'
            created_at = __import__('datetime').datetime.now()
            
            class MockProfile:
                height = 170
                weight = 65
                age = 25
                gender = '男'
            
            profile = MockProfile()
            meal_logs = []
            exercise_logs = []
            goals = []
        
        mock_user = MockUser()
        
        # 简单的模板测试
        template_content = """
        <html>
        <head><title>测试模板</title></head>
        <body>
            <h1>模板渲染测试</h1>
            <p>用户名: {{ user.username }}</p>
            <p>邮箱: {{ user.email }}</p>
            {% if user.profile %}
            <p>身高: {{ user.profile.height }} cm</p>
            <p>体重: {{ user.profile.weight }} kg</p>
            {% endif %}
        </body>
        </html>
        """
        
        from flask import render_template_string
        return render_template_string(template_content, user=mock_user)
        
    except Exception as e:
        return f"<h1>模板测试失败</h1><p>错误: {str(e)}</p>"

@app.route('/test-profile')
def test_profile():
    try:
        # 直接读取并返回模板文件内容，不渲染
        with open('templates/profile.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return f"<h1>Profile模板文件读取成功</h1><p>文件大小: {len(content)} 字符</p><pre>{content[:500]}...</pre>"
    except Exception as e:
        return f"<h1>Profile模板读取失败</h1><p>错误: {str(e)}</p>"

@app.route('/test-settings')
def test_settings():
    try:
        # 直接读取并返回模板文件内容，不渲染
        with open('templates/settings.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return f"<h1>Settings模板文件读取成功</h1><p>文件大小: {len(content)} 字符</p><pre>{content[:500]}...</pre>"
    except Exception as e:
        return f"<h1>Settings模板读取失败</h1><p>错误: {str(e)}</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5002)