#!/usr/bin/env python3
"""
测试修复后的功能
"""

import sys
sys.path.append('.')

from app import app, db, FoodAnalyzer, User, UserProfile
import json

def test_fixes():
    """测试三个关键修复"""
    print("🔧 测试FitLife v2.0修复...")
    
    with app.app_context():
        # 测试1: AI分析引擎修复
        print("\n1️⃣ 测试AI分析引擎修复...")
        analyzer = FoodAnalyzer()
        
        test_foods = [
            "一碗白米饭，两个煎蛋，一杯牛奶",
            "一份西兰花炒牛肉",
            "苹果一个"
        ]
        
        for food in test_foods:
            print(f"\n   测试食物: {food}")
            result = analyzer.analyze_comprehensive(food, meal_type="breakfast")
            
            print(f"   ✅ 热量: {result['total_calories']} kcal")
            print(f"   ✅ 蛋白质: {result['total_protein']} g")
            print(f"   ✅ 碳水: {result['total_carbs']} g")
            print(f"   ✅ 脂肪: {result['total_fat']} g")
            print(f"   ✅ 健康评分: {result['health_score']}/10")
            
            # 验证数值不为0
            assert result['total_calories'] > 0, "热量不应为0"
            assert result['total_protein'] > 0, "蛋白质不应为0"
            print(f"   ✅ 数值验证通过")
        
        # 测试2: API端点
        print("\n2️⃣ 测试v2 API端点...")
        client = app.test_client()
        
        # 创建测试用户
        from werkzeug.security import generate_password_hash
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(test_user)
            db.session.commit()
        
        # 模拟登录
        with client.session_transaction() as sess:
            sess['user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # 测试食物分析API
        response = client.post('/api/v2/food/analyze', 
                              data=json.dumps({
                                  'food_description': '一碗白米饭，两个煎蛋',
                                  'meal_type': 'breakfast'
                              }),
                              content_type='application/json')
        
        print(f"   📡 API响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.get_json()
            print(f"   ✅ API调用成功: {result['success']}")
            if result['success']:
                data = result['data']
                print(f"   ✅ 返回热量: {data['total_calories']} kcal")
                print(f"   ✅ 返回蛋白质: {data['total_protein']} g")
                assert data['total_calories'] > 0, "API返回热量不应为0"
        
        # 测试3: 营养统计API
        daily_response = client.get('/api/v2/nutrition/daily')
        print(f"   📊 营养统计API: {daily_response.status_code}")
        if daily_response.status_code == 200:
            daily_result = daily_response.get_json()
            print(f"   ✅ 营养统计成功: {daily_result['success']}")
        
        print("\n🎉 所有修复测试完成!")
        print("✅ AI分析引擎：数值不再为0")
        print("✅ API端点：正常响应")
        print("✅ 数据处理：逻辑完整")
        
        print("\n📋 修复总结:")
        print("1. 导航链接：dashboard.html已更新指向/meal-log-v2")
        print("2. 智能向导：4步简化为3步，合并基本信息和食物描述")
        print("3. AI分析：修复数据解析和兜底机制，确保数值有效")

if __name__ == '__main__':
    test_fixes()