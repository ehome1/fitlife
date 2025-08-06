#!/usr/bin/env python3
"""
生产环境数据库初始化脚本
确保所有表结构正确创建，特别是新增的MealLog表
"""
import os
import sys
from sqlalchemy import text
from app import app, db, User, UserProfile, FitnessGoal, ExerciseLog, MealLog

def init_database():
    """初始化数据库表结构"""
    print("🚀 初始化生产环境数据库...")
    
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            
            # 验证表是否创建成功
            tables = [
                'user', 'user_profile', 'fitness_goal', 
                'exercise_log', 'meal_log'
            ]
            
            print("✅ 验证表结构:")
            for table in tables:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  - {table}: ✅ ({count} 条记录)")
                except Exception as e:
                    print(f"  - {table}: ❌ 错误: {e}")
            
            # 检查MealLog表的特定字段
            print("\n🔍 验证MealLog表字段:")
            meal_columns = [
                'id', 'user_id', 'meal_date', 'meal_type', 
                'food_items', 'total_calories', 'analysis_result', 
                'notes', 'created_at'
            ]
            
            for col in meal_columns:
                try:
                    result = db.session.execute(text(f"SELECT {col} FROM meal_log LIMIT 1"))
                    print(f"  - {col}: ✅")
                except Exception as e:
                    print(f"  - {col}: ❌ 错误: {e}")
            
            print("\n🎉 数据库初始化完成!")
            return True
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查必要的环境变量
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        print("请确保在生产环境中设置了这些变量")
    else:
        print("✅ 环境变量配置完整")
    
    # 检查数据库连接
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 FitLife 生产环境数据库初始化工具")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，请检查配置")
        sys.exit(1)
    
    # 初始化数据库
    if init_database():
        print("✅ 生产环境准备就绪!")
        sys.exit(0)
    else:
        print("❌ 初始化失败")
        sys.exit(1)

if __name__ == "__main__":
    main()