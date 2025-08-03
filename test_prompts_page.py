#!/usr/bin/env python3
"""
测试管理后台prompts页面
"""
import requests
from bs4 import BeautifulSoup

def test_prompts_page():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试管理后台Prompts页面")
    print("="*50)
    
    try:
        # 测试prompts页面
        print("1. 访问Prompts管理页面...")
        response = requests.get(f"{base_url}/admin/prompts")
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 页面访问成功！")
            
            # 检查页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查关键元素
            title = soup.find('title')
            if title and 'FitLife' in title.text:
                print("✅ 页面标题正确")
            
            # 检查是否有中文内容显示正常
            if 'Prompt 管理' in response.text:
                print("✅ 中文内容显示正常")
            
            if 'AI Prompt 模板' in response.text:
                print("✅ 主要功能区域显示正常")
            
            if '运动分析模板' in response.text and '饮食分析模板' in response.text:
                print("✅ 模板分类显示正常")
            
            # 检查表格
            if '模板名称' in response.text and '类型' in response.text:
                print("✅ 数据表格显示正常")
            
            # 检查JavaScript是否正常
            if 'promptsData' in response.text:
                print("✅ JavaScript代码加载正常")
            
            print("\n📊 页面统计:")
            print(f"   页面大小: {len(response.text)} 字符")
            print(f"   编码: {response.encoding}")
            
        else:
            print(f"❌ 页面访问失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    # 测试其他管理页面
    test_pages = [
        ('/admin', '管理员仪表盘'),
        ('/admin/users', '用户管理'),
        ('/admin/settings', '系统设置')
    ]
    
    print("\n2. 测试其他管理页面...")
    for url, name in test_pages:
        try:
            response = requests.get(f"{base_url}{url}")
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {name}: {response.status_code}")
        except:
            print(f"   ❌ {name}: 访问失败")

if __name__ == "__main__":
    test_prompts_page()