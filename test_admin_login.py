#!/usr/bin/env python3
"""
测试管理员登录功能
"""
import requests
import json

def test_admin_login():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试管理员登录功能")
    print("="*50)
    
    # 创建会话
    session = requests.Session()
    
    # 1. 获取登录页面
    print("1. 获取登录页面...")
    login_page = session.get(f"{base_url}/admin/login")
    print(f"   状态码: {login_page.status_code}")
    
    if login_page.status_code != 200:
        print("❌ 无法访问登录页面")
        return
    
    # 2. 尝试登录
    print("2. 尝试管理员登录...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(
        f"{base_url}/admin/login",
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   登录响应状态码: {response.status_code}")
    print(f"   响应头: {dict(response.headers)}")
    
    if response.status_code == 302:
        redirect_url = response.headers.get('Location', '')
        print(f"   重定向到: {redirect_url}")
        
        if '/admin' in redirect_url:
            print("✅ 登录成功！")
            
            # 3. 访问管理页面
            print("3. 访问管理员页面...")
            admin_page = session.get(f"{base_url}/admin")
            print(f"   管理页面状态码: {admin_page.status_code}")
            
            if admin_page.status_code == 200:
                print("✅ 成功访问管理员页面！")
                if "管理" in admin_page.text or "dashboard" in admin_page.text.lower():
                    print("✅ 管理员权限验证通过！")
                else:
                    print("⚠️ 页面内容可能不正确")
            else:
                print("❌ 无法访问管理员页面")
        else:
            print("❌ 登录失败，重定向位置不正确")
    else:
        print("❌ 登录失败")
        print(f"   响应内容: {response.text[:200]}...")

    # 4. 测试健康检查
    print("4. 测试系统健康状态...")
    health = session.get(f"{base_url}/health")
    if health.status_code == 200:
        health_data = health.json()
        print(f"   系统状态: {health_data.get('status', 'unknown')}")
        print(f"   版本: {health_data.get('version', 'unknown')}")
        print("✅ 系统健康检查正常")
    else:
        print("❌ 系统健康检查失败")

if __name__ == "__main__":
    test_admin_login()