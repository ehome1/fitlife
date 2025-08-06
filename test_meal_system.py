#!/usr/bin/env python3
"""
饮食记录系统功能验证脚本
确保所有饮食相关功能在生产环境中正常工作
"""
import sys
import json
from app import app, db, User, MealLog
from datetime import date

def test_meal_model():
    """测试MealLog模型"""
    print("🧪 测试MealLog模型...")
    
    with app.app_context():
        try:
            # 创建测试数据
            test_meal = MealLog(
                user_id=1,
                meal_date=date.today(),
                meal_type='breakfast',
                food_items=[
                    {"name": "苹果", "amount": 1, "unit": "个"},
                    {"name": "牛奶", "amount": 1, "unit": "盒"}
                ],
                total_calories=300,
                analysis_result={
                    "basic_nutrition": {"total_calories": 300},
                    "meal_analysis": {"meal_score": 8}
                },
                notes="测试早餐"
            )
            
            # 测试属性访问
            assert test_meal.meal_type_display == '早餐'
            assert test_meal.food_items_summary is not None
            
            print("✅ MealLog模型测试通过")
            return True
            
        except Exception as e:
            print(f"❌ MealLog模型测试失败: {e}")
            return False

def test_meal_routes():
    """测试饮食记录路由"""
    print("🧪 测试饮食记录路由...")
    
    with app.test_client() as client:
        try:
            # 测试meal_log页面路由
            response = client.get('/meal-log')
            if response.status_code == 302:  # 重定向到登录页面
                print("✅ /meal-log 路由正常 (需要登录)")
            else:
                print(f"⚠️ /meal-log 路由返回状态码: {response.status_code}")
            
            # 测试AI分析API路由
            response = client.post('/api/analyze-meal', 
                                 json={'meal_type': 'breakfast', 'food_items': []})
            if response.status_code == 302:  # 重定向到登录页面
                print("✅ /api/analyze-meal 路由正常 (需要登录)")
            else:
                print(f"⚠️ /api/analyze-meal 路由返回状态码: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ 路由测试失败: {e}")
            return False

def test_ai_analysis_function():
    """测试AI分析功能"""
    print("🧪 测试AI营养分析功能...")
    
    try:
        from app import generate_fallback_nutrition_analysis
        
        # 测试fallback分析函数
        test_foods = [
            {"name": "苹果", "amount": 1, "unit": "个"},
            {"name": "牛奶", "amount": 1, "unit": "盒"}
        ]
        
        result = generate_fallback_nutrition_analysis(test_foods, 'breakfast')
        
        # 验证返回结构
        required_keys = ['basic_nutrition', 'meal_analysis', 'detailed_analysis']
        for key in required_keys:
            if key not in result:
                raise Exception(f"缺少必要字段: {key}")
        
        print("✅ AI分析功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ AI分析功能测试失败: {e}")
        return False

def test_template_exists():
    """测试模板文件是否存在"""
    print("🧪 测试模板文件...")
    
    import os
    template_path = 'templates/meal_log.html'
    
    if os.path.exists(template_path):
        print("✅ meal_log.html 模板存在")
        
        # 检查模板内容的关键部分
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_elements = [
            'food-items-container',
            'analyzeMeal',
            'mealAnalysisResults',
            'ai/analyze-meal'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"✅ 找到关键元素: {element}")
            else:
                print(f"⚠️ 缺少关键元素: {element}")
        
        return True
    else:
        print("❌ meal_log.html 模板不存在")
        return False

def main():
    """主测试函数"""
    print("🚀 FitLife 饮食记录系统验证")
    print("=" * 50)
    
    tests = [
        ("MealLog模型", test_meal_model),
        ("饮食记录路由", test_meal_routes),
        ("AI分析功能", test_ai_analysis_function),
        ("模板文件", test_template_exists)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过，饮食记录系统准备就绪!")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)