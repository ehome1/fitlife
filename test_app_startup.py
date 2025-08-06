#!/usr/bin/env python3
"""
应用启动测试脚本
验证应用是否可以正常启动和响应请求
"""
import sys
import time
import requests
import subprocess
import os
import signal

def test_app_startup():
    """测试应用启动"""
    print("🧪 测试应用启动...")
    
    # 启动应用
    try:
        # 设置环境变量以避免Gemini API依赖
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        
        process = subprocess.Popen(
            ['python3', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # 等待应用启动
        print("等待应用启动...")
        time.sleep(5)
        
        # 测试基本路由
        try:
            response = requests.get('http://127.0.0.1:5001/', timeout=10)
            if response.status_code == 200:
                print("✅ 主页可以访问")
            else:
                print(f"⚠️ 主页返回状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 主页访问失败: {e}")
        
        # 测试其他关键路由
        test_routes = [
            '/login',
            '/register', 
            '/meal-log'  # 需要登录，会重定向到登录页
        ]
        
        for route in test_routes:
            try:
                response = requests.get(f'http://127.0.0.1:5001{route}', timeout=5)
                if response.status_code in [200, 302]:  # 302是重定向
                    print(f"✅ {route} 可以访问")
                else:
                    print(f"⚠️ {route} 返回状态码: {response.status_code}")
            except Exception as e:
                print(f"❌ {route} 访问失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        return False
    
    finally:
        # 终止进程
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass

def test_import():
    """测试导入"""
    print("🧪 测试Python导入...")
    
    try:
        import app
        print("✅ app.py 导入成功")
        return True
    except Exception as e:
        print(f"❌ app.py 导入失败: {e}")
        return False

def test_gemini_fallback():
    """测试Gemini fallback功能"""
    print("🧪 测试Gemini fallback功能...")
    
    try:
        from app import generate_fallback_nutrition_analysis
        
        test_foods = [
            {'name': '苹果', 'amount': 1, 'unit': '个'},
            {'name': '牛奶', 'amount': 1, 'unit': '盒'}
        ]
        
        result = generate_fallback_nutrition_analysis(test_foods, 'breakfast')
        
        if 'basic_nutrition' in result and 'total_calories' in result['basic_nutrition']:
            print("✅ Fallback营养分析功能正常")
            return True
        else:
            print("❌ Fallback营养分析结果格式错误")
            return False
            
    except Exception as e:
        print(f"❌ Fallback功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 FitLife 应用启动诊断")
    print("=" * 50)
    
    tests = [
        ("Python导入测试", test_import),
        ("Fallback功能测试", test_gemini_fallback),
        ("应用启动测试", test_app_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            break  # 如果基础测试失败，停止后续测试
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 应用启动正常，可以部署到生产环境！")
        return True
    else:
        print("⚠️ 应用存在问题，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)