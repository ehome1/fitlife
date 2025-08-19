#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def add_exercise_description_field():
    """为exercise_log表添加exercise_description字段"""
    print("🔧 开始为exercise_log表添加exercise_description字段...")
    
    with app.app_context():
        try:
            # 检查字段是否已存在 (PostgreSQL版本)
            try:
                result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'exercise_log' AND column_name = 'exercise_description'"))
                if result.fetchone():
                    print("✅ exercise_description字段已存在，无需添加")
                    return True
            except:
                # 如果是SQLite，使用PRAGMA
                result = db.session.execute(text("PRAGMA table_info(exercise_log)"))
                columns = result.fetchall()
                existing_columns = [col[1] for col in columns]
                
                if 'exercise_description' in existing_columns:
                    print("✅ exercise_description字段已存在，无需添加")
                    return True
            
            print("📝 exercise_description字段不存在，开始添加...")
            
            # 添加字段
            db.session.execute(text("ALTER TABLE exercise_log ADD COLUMN exercise_description TEXT"))
            db.session.commit()
            
            print("✅ exercise_description字段添加成功")
            
            # 验证字段是否添加成功
            try:
                # PostgreSQL验证
                result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'exercise_log' AND column_name = 'exercise_description'"))
                if result.fetchone():
                    print("✅ 字段验证成功")
                    return True
            except:
                # SQLite验证
                result = db.session.execute(text("PRAGMA table_info(exercise_log)"))
                columns = result.fetchall()
                updated_columns = [col[1] for col in columns]
                
                if 'exercise_description' in updated_columns:
                    print("✅ 字段验证成功")
                    
                    # 显示当前表结构
                    print("\n📋 exercise_log表当前结构:")
                    for col in columns:
                        print(f"  - {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
                    
                    return True
            
            print("❌ 字段验证失败")
            return False
                
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")
            db.session.rollback()
            return False

def verify_all_tables():
    """验证所有表的完整性"""
    print("\n🔍 验证数据库表完整性...")
    
    with app.app_context():
        try:
            # 检查所有表是否存在
            tables_to_check = ['user', 'user_profile', 'fitness_goal', 'exercise_log', 'meal_log', 'weight_log']
            
            for table_name in tables_to_check:
                try:
                    # 尝试PostgreSQL查询
                    try:
                        result = db.session.execute(text(f"SELECT table_name FROM information_schema.tables WHERE table_name = '{table_name}'"))
                        if result.fetchone():
                            print(f"  ✅ {table_name} 表存在")
                        else:
                            print(f"  ❌ {table_name} 表不存在")
                    except:
                        # 如果失败，使用SQLite查询
                        result = db.session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
                        if result.fetchone():
                            print(f"  ✅ {table_name} 表存在")
                        else:
                            print(f"  ❌ {table_name} 表不存在")
                except Exception as e:
                    print(f"  ❌ {table_name} 表检查失败: {e}")
            
            # 专门检查exercise_log表的关键字段
            print(f"\n📋 exercise_log表关键字段检查:")
            try:
                # PostgreSQL查询
                result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'exercise_log'"))
                columns = [row[0] for row in result.fetchall()]
            except:
                # SQLite查询
                result = db.session.execute(text("PRAGMA table_info(exercise_log)"))
                columns = [col[1] for col in result.fetchall()]
            
            required_fields = ['id', 'user_id', 'date', 'exercise_type', 'exercise_name', 'duration', 'exercise_description', 'analysis_status']
            
            for field in required_fields:
                if field in columns:
                    print(f"  ✅ {field} 字段存在")
                else:
                    print(f"  ❌ {field} 字段缺失")
            
            return True
            
        except Exception as e:
            print(f"❌ 表完整性验证失败: {e}")
            return False

def test_exercise_log_operations():
    """测试exercise_log表的操作"""
    print("\n🧪 测试exercise_log表操作...")
    
    with app.app_context():
        try:
            from app import ExerciseLog, User
            from datetime import date
            
            # 获取测试用户
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到测试用户")
                return False
            
            # 测试创建包含exercise_description的记录
            test_record = ExerciseLog(
                user_id=test_user.id,
                date=date.today(),
                exercise_type='cardio',
                exercise_name='测试运动',
                duration=30,
                exercise_description='这是一个测试运动描述，用于验证新字段功能',
                analysis_status='pending'
            )
            
            db.session.add(test_record)
            db.session.commit()
            
            print("✅ 创建包含exercise_description的记录成功")
            
            # 测试查询
            retrieved_record = ExerciseLog.query.filter_by(id=test_record.id).first()
            if retrieved_record and retrieved_record.exercise_description:
                print(f"✅ 查询exercise_description成功: {retrieved_record.exercise_description[:50]}...")
            else:
                print("❌ 查询exercise_description失败")
                return False
            
            # 清理测试记录
            db.session.delete(test_record)
            db.session.commit()
            print("✅ 清理测试记录成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试操作失败: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 Exercise Description字段迁移脚本")
    print("=" * 60)
    
    # 添加字段
    if add_exercise_description_field():
        # 验证表完整性
        if verify_all_tables():
            # 测试操作
            if test_exercise_log_operations():
                print(f"\n🎉 迁移完成！exercise_description字段已成功添加")
                print("现在可以安全地使用运动描述功能了")
            else:
                print(f"\n❌ 操作测试失败")
        else:
            print(f"\n❌ 表完整性验证失败")
    else:
        print(f"\n❌ 字段添加失败")