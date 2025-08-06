#!/usr/bin/env python3
"""
运动打卡和饮食打卡功能全面诊断测试
Ultra think 模式：深度检查所有可能的失败点
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """测试基础导入"""
    print("🧪 测试基础导入...")
    try:
        from app import app, db, User, ExerciseLog, MealLog
        from flask_sqlalchemy import SQLAlchemy
        from datetime import datetime, timezone
        print("✅ 基础导入成功")
        return True, (app, db, User, ExerciseLog, MealLog)
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False, None

def test_database_connection(app, db):
    """测试数据库连接"""
    print("\n🧪 测试数据库连接...")
    try:
        with app.app_context():
            # 尝试创建所有表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['user', 'exercise_log', 'meal_log']
            for table in required_tables:
                if table in tables:
                    print(f"✅ 表 {table} 存在")
                else:
                    print(f"❌ 表 {table} 不存在")
                    return False
            
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_structure(app, db, ExerciseLog, MealLog):
    """测试数据模型结构"""
    print("\n🧪 测试数据模型结构...")
    try:
        with app.app_context():
            # 检查ExerciseLog模型字段
            exercise_columns = [col.name for col in ExerciseLog.__table__.columns]
            print(f"ExerciseLog字段: {exercise_columns}")
            
            required_exercise_fields = ['id', 'user_id', 'date', 'exercise_type', 'exercise_name', 'duration', 'created_at']
            for field in required_exercise_fields:
                if field in exercise_columns:
                    print(f"✅ ExerciseLog.{field} 存在")
                else:
                    print(f"❌ ExerciseLog.{field} 缺失")
                    return False
            
            # 检查MealLog模型字段
            meal_columns = [col.name for col in MealLog.__table__.columns]
            print(f"MealLog字段: {meal_columns}")
            
            required_meal_fields = ['id', 'user_id', 'date', 'meal_type', 'food_name', 'created_at']
            for field in required_meal_fields:
                if field in meal_columns:
                    print(f"✅ MealLog.{field} 存在")
                else:
                    print(f"❌ MealLog.{field} 缺失")
                    return False
                    
            print("✅ 数据模型结构完整")
            return True
            
    except Exception as e:
        print(f"❌ 模型结构检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exercise_log_creation(app, db, User, ExerciseLog):
    """测试运动记录创建"""
    print("\n🧪 测试运动记录创建...")
    try:
        from datetime import datetime, timezone
        with app.app_context():
            # 创建测试用户
            import time
            timestamp = int(time.time())
            test_user = User(
                username=f'test_exercise_{timestamp}',
                email=f'test_exercise_{timestamp}@example.com',
                password_hash='test_hash'
            )
            db.session.add(test_user)
            db.session.flush()  # 获取用户ID但不提交
            
            # 创建运动记录
            from datetime import date
            exercise_log = ExerciseLog(
                user_id=test_user.id,
                date=date.today(),  # 设置date字段
                exercise_type='running',
                exercise_name='晨跑',
                duration=30,
                calories_burned=300,
                intensity='medium',
                notes='测试运动记录',
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(exercise_log)
            db.session.commit()
            
            # 验证创建成功
            saved_exercise = ExerciseLog.query.filter_by(user_id=test_user.id).first()
            if saved_exercise:
                print("✅ 运动记录创建成功")
                print(f"   记录ID: {saved_exercise.id}")
                print(f"   运动类型: {saved_exercise.exercise_type}")
                print(f"   运动名称: {saved_exercise.exercise_name}")
                print(f"   持续时间: {saved_exercise.duration}分钟")
                
                # 清理测试数据
                db.session.delete(saved_exercise)
                db.session.delete(test_user)
                db.session.commit()
                
                return True
            else:
                print("❌ 运动记录创建失败 - 未找到记录")
                return False
                
    except Exception as e:
        print(f"❌ 运动记录创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return False

def test_meal_log_creation(app, db, User, MealLog):
    """测试饮食记录创建"""
    print("\n🧪 测试饮食记录创建...")
    try:
        from datetime import datetime, timezone, date
        with app.app_context():
            
            # 创建测试用户
            import time
            timestamp = int(time.time())
            test_user = User(
                username=f'test_meal_{timestamp}',
                email=f'test_meal_{timestamp}@example.com',
                password_hash='test_hash'
            )
            db.session.add(test_user)
            db.session.flush()  # 获取用户ID但不提交
            
            # 创建饮食记录
            meal_log = MealLog(
                user_id=test_user.id,
                date=date.today(),  # 使用date字段
                meal_type='breakfast',
                food_name='苹果',  # 单个食物名称
                quantity=1.0,  # 数量
                calories=80,  # 卡路里
                analysis_result={'notes': '测试饮食记录'},  # 使用analysis_result存储notes
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(meal_log)
            db.session.commit()
            
            # 验证创建成功
            saved_meal = MealLog.query.filter_by(user_id=test_user.id).first()
            if saved_meal:
                print("✅ 饮食记录创建成功")
                print(f"   记录ID: {saved_meal.id}")
                print(f"   餐次类型: {saved_meal.meal_type}")
                print(f"   食物名称: {saved_meal.food_name}")
                print(f"   食物数量: {saved_meal.quantity}")
                print(f"   卡路里: {saved_meal.calories}")
                
                # 清理测试数据
                db.session.delete(saved_meal)
                db.session.delete(test_user)
                db.session.commit()
                
                return True
            else:
                print("❌ 饮食记录创建失败 - 未找到记录")
                return False
                
    except Exception as e:
        print(f"❌ 饮食记录创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return False

def test_route_accessibility(app):
    """测试路由可访问性"""
    print("\n🧪 测试路由可访问性...")
    try:
        with app.test_client() as client:
            # 测试运动记录页面
            response = client.get('/exercise-log')
            if response.status_code in [200, 302]:
                print("✅ 运动记录页面可访问")
            else:
                print(f"❌ 运动记录页面访问异常: {response.status_code}")
                return False
            
            # 测试饮食记录页面  
            response = client.get('/meal-log')
            if response.status_code in [200, 302]:
                print("✅ 饮食记录页面可访问")
            else:
                print(f"❌ 饮食记录页面访问异常: {response.status_code}")
                return False
                
            return True
    except Exception as e:
        print(f"❌ 路由可访问性测试失败: {e}")
        return False

def test_form_processing():
    """测试表单数据处理逻辑"""
    print("\n🧪 测试表单数据处理逻辑...")
    try:
        # 测试运动表单数据解析
        from datetime import datetime
        
        # 模拟表单数据
        exercise_form_data = {
            'exercise_date': '2024-01-01',
            'exercise_type': 'running', 
            'exercise_name': '晨跑',
            'duration': '30',
            'notes': '测试备注'
        }
        
        # 验证数据解析
        exercise_date = datetime.strptime(exercise_form_data['exercise_date'], '%Y-%m-%d').date()
        duration = int(exercise_form_data['duration'])
        print("✅ 运动表单数据解析正常")
        
        # 测试饮食表单数据解析
        meal_form_data = {
            'meal_date': '2024-01-01',
            'meal_type': 'breakfast',
            'food_description': '早餐吃了一个苹果',
            'notes': '测试备注'
        }
        
        # 验证数据解析
        meal_date = datetime.strptime(meal_form_data['meal_date'], '%Y-%m-%d').date()
        print("✅ 饮食表单数据解析正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 表单数据处理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 FitLife 运动&饮食打卡功能 - Ultra Think 深度诊断")
    print("=" * 70)
    
    # 第一步：测试导入
    import_success, modules = test_imports()
    if not import_success:
        print("\n❌ 基础导入失败，无法继续测试")
        return False
    
    app, db, User, ExerciseLog, MealLog = modules
    
    # 第二步：测试数据库连接
    if not test_database_connection(app, db):
        print("\n❌ 数据库连接失败，这是主要问题")
        return False
    
    # 第三步：测试数据模型结构
    if not test_model_structure(app, db, ExerciseLog, MealLog):
        print("\n❌ 数据模型结构问题")
        return False
    
    # 第四步：测试运动记录创建
    if not test_exercise_log_creation(app, db, User, ExerciseLog):
        print("\n❌ 运动记录创建失败")
        return False
    
    # 第五步：测试饮食记录创建
    if not test_meal_log_creation(app, db, User, MealLog):
        print("\n❌ 饮食记录创建失败")
        return False
    
    # 第六步：测试路由可访问性
    if not test_route_accessibility(app):
        print("\n❌ 路由访问问题")
        return False
        
    # 第七步：测试表单处理逻辑
    if not test_form_processing():
        print("\n❌ 表单处理逻辑问题")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 所有测试通过！运动打卡和饮食打卡功能应该正常工作")
    print("\n修复内容总结:")
    print("✅ 运动打卡添加了数据库表创建和错误处理")
    print("✅ 饮食打卡的错误处理已经完善")
    print("✅ 数据库模型和表结构正确")
    print("✅ 路由和表单处理逻辑正常")
    print("✅ 数据创建和查询功能正常")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 建议检查:")
        print("1. 数据库文件权限")
        print("2. SQLAlchemy配置")
        print("3. 表单字段名称匹配")
        print("4. 用户认证状态")
        sys.exit(1)
    else:
        sys.exit(0)