#!/usr/bin/env python3
"""
测试新的饮食记录仪表板界面
"""
import requests
import json

def test_dashboard_interface():
    base_url = "http://127.0.0.1:5001"
    
    print("🧪 测试新的饮食记录仪表板界面")
    print("=" * 50)
    
    try:
        # 测试主页访问
        print("1. 测试主页访问...")
        response = requests.get(f"{base_url}/")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 主页访问成功")
            
            # 检查是否包含新的仪表板相关内容
            if 'FitLife' in response.text:
                print("✅ 页面标题正确")
            
            # 测试饮食记录页面（需要先登录）
            print("\n2. 测试饮食记录页面（未登录状态）...")
            meal_response = requests.get(f"{base_url}/meal_log")
            print(f"   状态码: {meal_response.status_code}")
            
            if meal_response.status_code == 302:
                print("✅ 正确重定向到登录页面")
            elif meal_response.status_code == 200:
                if 'dashboard-header' in meal_response.text:
                    print("✅ 新仪表板界面元素存在")
                if 'nutrition-overview-item' in meal_response.text:
                    print("✅ 营养概览组件存在")
                if 'nutritionTrendChart' in meal_response.text:
                    print("✅ 趋势图表组件存在")
                if 'Chart.js' in meal_response.text:
                    print("✅ Chart.js库已加载")
            
            # 测试新的API端点
            print("\n3. 测试新的API端点（未登录状态）...")
            
            # 测试营养趋势API
            trends_response = requests.get(f"{base_url}/api/nutrition-trends?range=week")
            print(f"   营养趋势API状态码: {trends_response.status_code}")
            
            # 测试今日营养API
            daily_response = requests.get(f"{base_url}/api/daily-nutrition")
            print(f"   今日营养API状态码: {daily_response.status_code}")
            
            if trends_response.status_code == 302 and daily_response.status_code == 302:
                print("✅ API正确要求身份验证")
            
        else:
            print(f"❌ 主页访问失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    
    # 显示访问链接
    print("\n🔗 访问链接:")
    print(f"   主页: {base_url}/")
    print(f"   饮食记录: {base_url}/meal_log")
    print(f"   用户注册: {base_url}/register")
    print(f"   用户登录: {base_url}/login")
    print(f"   管理后台: {base_url}/admin")

if __name__ == "__main__":
    test_dashboard_interface()