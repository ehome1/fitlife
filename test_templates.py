#!/usr/bin/env python3
"""
测试模板渲染
"""
import sys
sys.path.append('.')

from app import app, User, UserProfile
from flask import render_template

def test_templates():
    """测试模板渲染"""
    print("🔧 测试模板渲染...")
    
    with app.app_context():
        try:
            # 测试基础模板
            print("\n1️⃣ 测试基础模板...")
            base_html = render_template('base.html')
            print("✅ base.html 渲染成功")
            
            # 测试登录页面
            print("\n2️⃣ 测试登录页面...")
            login_html = render_template('login.html')
            print("✅ login.html 渲染成功")
            
            # 测试注册页面
            print("\n3️⃣ 测试注册页面...")
            register_html = render_template('register.html')
            print("✅ register.html 渲染成功")
            
            # 创建测试用户来测试需要认证的页面
            from werkzeug.security import generate_password_hash
            from flask_login import login_user
            
            # 查找或创建测试用户
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash=generate_password_hash('testpass123')
                )
                # 创建用户资料
                profile = UserProfile(
                    user=test_user,
                    height=175.0,
                    weight=70.0,
                    age=25,
                    gender='男'
                )
                from app import db
                db.session.add(test_user)
                db.session.add(profile)
                db.session.commit()
            
            # 模拟用户登录状态
            print("\n4️⃣ 测试profile页面...")
            
            # 使用Flask test client来模拟登录状态
            from flask import Flask
            test_app = Flask(__name__)
            test_app.config.update(SECRET_KEY='test-key')
            
            from app import login_manager
            login_manager.init_app(test_app)
            
            with test_app.test_request_context():
                # 直接渲染模板，不依赖current_user
                profile_html = app.jinja_env.get_template('profile.html').render(current_user=test_user)
                print("✅ profile.html 渲染成功")
                
                print("\n5️⃣ 测试settings页面...")
                settings_html = app.jinja_env.get_template('settings.html').render(current_user=test_user)
                print("✅ settings.html 渲染成功")
            
            print("\n🎉 所有模板测试完成!")
            
        except Exception as e:
            print(f"❌ 模板渲染错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = test_templates()
    sys.exit(0 if success else 1)