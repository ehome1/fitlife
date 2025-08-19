#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, ExerciseLog, WeightLog
from sqlalchemy import text
from datetime import date, datetime, timezone

def step1_fix_database():
    """步骤1: 修复数据库schema"""
    print("📝 步骤1: 修复数据库schema")
    print("-" * 40)
    
    with app.app_context():
        try:
            # 添加exercise_description字段
            db.session.execute(text("ALTER TABLE exercise_log ADD COLUMN exercise_description TEXT"))
            db.session.commit()
            print("✅ exercise_description字段添加成功")
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate column' in error_msg:
                print("✅ exercise_description字段已存在")
            else:
                print(f"❌ 添加字段失败: {e}")
                return False
        
        # 验证字段
        try:
            db.session.execute(text("SELECT exercise_description FROM exercise_log LIMIT 1"))
            print("✅ 字段验证成功")
            return True
        except Exception as e:
            print(f"❌ 字段验证失败: {e}")
            return False

def step2_test_queries():
    """步骤2: 测试关键查询"""
    print("\n📝 步骤2: 测试关键查询")
    print("-" * 40)
    
    with app.app_context():
        try:
            # 获取用户
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到用户")
                return False
            
            print(f"✅ 用户: {test_user.username}")
            
            # 测试运动记录查询
            today = date.today()
            exercises = ExerciseLog.query.filter_by(user_id=test_user.id).all()
            print(f"✅ 运动记录查询成功: {len(exercises)}条")
            
            # 测试体重记录查询
            weights = WeightLog.query.filter_by(user_id=test_user.id).all()
            print(f"✅ 体重记录查询成功: {len(weights)}条")
            
            return True
            
        except Exception as e:
            print(f"❌ 查询测试失败: {e}")
            return False

def step3_test_dashboard():
    """步骤3: 测试仪表盘页面"""
    print("\n📝 步骤3: 测试仪表盘页面")
    print("-" * 40)
    
    with app.app_context():
        try:
            test_user = User.query.first()
            
            with app.test_client() as client:
                # 模拟登录
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # 测试仪表盘
                response = client.get('/dashboard')
                if response.status_code == 200:
                    print("✅ 仪表盘加载成功")
                    
                    # 检查页面内容
                    content = response.data.decode('utf-8')
                    if '体重记录管理' in content:
                        print("✅ 体重管理模块存在")
                    if 'weightChart' in content:
                        print("✅ 体重图表功能存在")
                    
                    return True
                else:
                    print(f"❌ 仪表盘返回错误: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 仪表盘测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def step4_test_apis():
    """步骤4: 测试API接口"""
    print("\n📝 步骤4: 测试API接口")
    print("-" * 40)
    
    with app.app_context():
        try:
            test_user = User.query.first()
            
            with app.test_client() as client:
                # 模拟登录
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # 测试体重统计API
                response = client.get('/api/weight-stats')
                if response.status_code == 200:
                    print("✅ 体重统计API正常")
                else:
                    print(f"❌ 体重统计API错误: {response.status_code}")
                    return False
                
                # 测试体重历史API
                response = client.get('/api/weight-log?days=7')
                if response.status_code == 200:
                    print("✅ 体重历史API正常")
                else:
                    print(f"❌ 体重历史API错误: {response.status_code}")
                    return False
                
                return True
                
        except Exception as e:
            print(f"❌ API测试失败: {e}")
            return False

def main():
    """主函数：执行所有修复和测试步骤"""
    print("🚀 FitLife 完整修复和测试脚本")
    print("=" * 60)
    
    success = True
    
    # 执行所有步骤
    if not step1_fix_database():
        success = False
    
    if success and not step2_test_queries():
        success = False
        
    if success and not step3_test_dashboard():
        success = False
        
    if success and not step4_test_apis():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！仪表盘已修复完成")
        print("\n📖 使用指南:")
        print("- 仪表盘: http://127.0.0.1:5001/dashboard")
        print("- 运动记录: http://127.0.0.1:5001/exercise-log")
        print("- 体重管理功能已集成在仪表盘中")
    else:
        print("❌ 修复过程中发现问题，请检查日志")
    
    return success

if __name__ == '__main__':
    main()