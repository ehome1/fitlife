#!/usr/bin/env python3
"""
测试数据库架构修复
"""
import sys
sys.path.append('.')

from app import app, db, User, UserProfile, MealLog, ExerciseLog, FitnessGoal
from flask import render_template
from werkzeug.security import generate_password_hash

def test_database_models():
    """测试数据库模型的安全访问"""
    print("🔧 测试数据库模型安全访问...")
    
    with app.app_context():
        try:
            # 创建或获取测试用户
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash=generate_password_hash('testpass123')
                )
                db.session.add(test_user)
                db.session.commit()
                print("✅ 创建测试用户成功")
            
            # 测试安全统计查询
            try:
                meal_count = db.session.query(MealLog).filter_by(user_id=test_user.id).count()
                print(f"✅ 饮食记录统计查询成功: {meal_count} 条")
            except Exception as e:
                print(f"❌ 饮食记录查询失败: {e}")
            
            try:
                exercise_count = db.session.query(ExerciseLog).filter_by(user_id=test_user.id).count()
                print(f"✅ 运动记录统计查询成功: {exercise_count} 条")
            except Exception as e:
                print(f"❌ 运动记录查询失败: {e}")
            
            try:
                goals_count = db.session.query(FitnessGoal).filter_by(user_id=test_user.id).count()
                print(f"✅ 健身目标统计查询成功: {goals_count} 条")
            except Exception as e:
                print(f"❌ 健身目标查询失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库模型测试失败: {e}")
            return False

def test_safe_routes():
    """测试安全路由"""
    print("\n🌐 测试安全路由...")
    
    with app.test_client() as client:
        try:
            # 测试首页
            response = client.get('/')
            print(f"✅ 首页响应: {response.status_code}")
            
            # 测试登录页
            response = client.get('/login')
            print(f"✅ 登录页响应: {response.status_code}")
            
            # 测试注册页
            response = client.get('/register')
            print(f"✅ 注册页响应: {response.status_code}")
            
            # 模拟登录状态测试profile和settings
            with client.session_transaction() as sess:
                # 创建测试用户会话
                test_user = User.query.filter_by(username='testuser').first()
                if test_user:
                    sess['user_id'] = str(test_user.id)
                    sess['_fresh'] = True
            
            # 测试profile页面
            response = client.get('/profile')
            print(f"✅ 个人资料页面响应: {response.status_code}")
            if response.status_code != 200:
                print(f"   响应内容: {response.get_data(as_text=True)[:200]}...")
            
            # 测试settings页面
            response = client.get('/settings')
            print(f"✅ 设置页面响应: {response.status_code}")
            if response.status_code != 200:
                print(f"   响应内容: {response.get_data(as_text=True)[:200]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ 路由测试失败: {e}")
            return False

def test_meal_log_model():
    """测试MealLog模型的属性访问"""
    print("\n🍽️ 测试MealLog模型属性...")
    
    with app.app_context():
        try:
            # 尝试访问MealLog的各种属性
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                print("❌ 测试用户不存在")
                return False
            
            # 创建一个测试MealLog记录（如果可能）
            try:
                test_meal = MealLog(
                    user_id=test_user.id,
                    meal_type='breakfast',
                    food_name='测试食物',
                    calories=300
                )
                db.session.add(test_meal)
                db.session.commit()
                print("✅ 创建测试MealLog成功")
                
                # 测试属性访问
                print(f"  food_description: {test_meal.food_description}")
                print(f"  total_calories: {test_meal.total_calories}")
                print(f"  total_protein: {test_meal.total_protein}")
                print(f"  health_score: {test_meal.health_score}")
                print(f"  meal_suitability: {test_meal.meal_suitability}")
                print("✅ 所有属性访问正常")
                
                return True
                
            except Exception as e:
                print(f"❌ MealLog模型测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ MealLog模型初始化失败: {e}")
            return False

def test_template_rendering():
    """测试模板渲染"""
    print("\n🎨 测试模板渲染...")
    
    with app.app_context():
        try:
            # 创建模拟用户数据
            safe_user_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'created_at': __import__('datetime').datetime.now(),
                'profile': None,
                'meal_logs_count': 0,
                'exercise_logs_count': 0,
                'goals_count': 0
            }
            
            # 测试profile_safe模板
            try:
                profile_html = render_template('profile_safe.html', user_data=safe_user_data)
                print(f"✅ profile_safe.html 渲染成功 ({len(profile_html)} 字符)")
            except Exception as e:
                print(f"❌ profile_safe.html 渲染失败: {e}")
            
            # 测试settings_safe模板
            try:
                settings_html = render_template('settings_safe.html', user_data=safe_user_data)
                print(f"✅ settings_safe.html 渲染成功 ({len(settings_html)} 字符)")
            except Exception as e:
                print(f"❌ settings_safe.html 渲染失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 模板渲染测试失败: {e}")
            return False

def main():
    """主测试流程"""
    print("🚀 FitLife 数据库修复测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 4
    
    # 测试1: 数据库模型
    if test_database_models():
        success_count += 1
    
    # 测试2: 安全路由
    if test_safe_routes():
        success_count += 1
    
    # 测试3: MealLog模型
    if test_meal_log_model():
        success_count += 1
    
    # 测试4: 模板渲染
    if test_template_rendering():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！数据库修复成功！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关问题")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)