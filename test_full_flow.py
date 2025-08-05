#!/usr/bin/env python3
"""
完整测试用户登录+运动分析的流程
"""
import requests
import json
import re

class FitnessAppTester:
    def __init__(self, base_url='http://127.0.0.1:5001'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_complete_flow(self):
        """测试完整流程"""
        print("🚀 开始完整流程测试...")
        
        # 1. 检查健康状态（跳过，直接测试核心功能）
        # if not self.check_health():
        #     return False
            
        # 2. 注册或登录用户
        if not self.login_user():
            return False
            
        # 3. 测试运动分析API
        if not self.test_exercise_analysis():
            return False
            
        print("✅ 完整流程测试成功!")
        return True
    
    def check_health(self):
        """检查应用健康状态"""
        try:
            print("🏥 检查应用健康状态...")
            response = self.session.get(f'{self.base_url}/health')
            if response.status_code == 200:
                print("✅ 应用健康状态正常")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查错误: {e}")
            return False
    
    def register_user(self):
        """注册测试用户"""
        try:
            print("📝 注册测试用户...")
            
            # 获取注册页面
            register_page = self.session.get(f'{self.base_url}/register')
            if register_page.status_code != 200:
                print(f"❌ 无法访问注册页面: {register_page.status_code}")
                return False
            
            # 注册用户
            register_data = {
                'username': 'test_user',
                'email': 'test@example.com',
                'password': 'test123456',
                'confirm_password': 'test123456'
            }
            
            response = self.session.post(f'{self.base_url}/register', data=register_data)
            
            if response.status_code == 200 or 'login' in response.url:
                print("✅ 用户注册成功")
                return True
            else:
                print(f"❌ 用户注册失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 注册过程错误: {e}")
            return False
    
    def login_user(self):
        """登录用户"""
        try:
            print("🔐 尝试登录...")
            
            # 先尝试注册（如果用户不存在）
            self.register_user()
            
            # 获取登录页面
            login_page = self.session.get(f'{self.base_url}/login')
            if login_page.status_code != 200:
                print(f"❌ 无法访问登录页面: {login_page.status_code}")
                return False
            
            # 登录
            login_data = {
                'username': 'test_user',
                'password': 'test123456'
            }
            
            response = self.session.post(f'{self.base_url}/login', data=login_data)
            
            # 检查是否登录成功（重定向到仪表盘或其他页面）
            if response.status_code == 200 and ('dashboard' in response.url or 'index' in response.url):
                print("✅ 用户登录成功")
                return True
            elif response.status_code == 302:  # 重定向
                print("✅ 用户登录成功（重定向）")
                return True
            else:
                print(f"❌ 用户登录失败: {response.status_code}")
                print(f"响应URL: {response.url}")
                return False
                
        except Exception as e:
            print(f"❌ 登录过程错误: {e}")
            return False
    
    def test_exercise_analysis(self):
        """测试运动分析API"""
        try:
            print("🏃 测试运动分析API...")
            
            test_data = {
                "exercise_type": "running",
                "exercise_name": "晨跑",
                "duration": 30
            }
            
            response = self.session.post(
                f'{self.base_url}/api/analyze-exercise',
                json=test_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            print(f"📊 API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        print("✅ 运动分析API测试成功!")
                        analysis_data = result.get('data', {})
                        print(f"🔥 消耗卡路里: {analysis_data.get('calories_burned', 'N/A')}")
                        print(f"💪 运动强度: {analysis_data.get('intensity_level', 'N/A')}")
                        print(f"⭐ 健身得分: {analysis_data.get('fitness_score', 'N/A')}")
                        return True
                    else:
                        print(f"❌ API返回错误: {result.get('error', '未知错误')}")
                        return False
                except json.JSONDecodeError:
                    print("❌ API响应不是有效的JSON")
                    print(f"响应内容: {response.text[:200]}...")
                    return False
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ 运动分析测试错误: {e}")
            return False

if __name__ == "__main__":
    tester = FitnessAppTester()
    success = tester.test_complete_flow()
    exit(0 if success else 1)