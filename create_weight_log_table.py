#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, WeightLog
from sqlalchemy import text

def create_weight_log_table():
    """创建体重记录表"""
    print("🔧 开始创建体重记录表...")
    
    with app.app_context():
        try:
            # 检查表是否已存在
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='weight_log'"))
            if result.fetchone():
                print("✅ weight_log表已存在，跳过创建")
                return True
            
            # 创建表
            db.create_all()
            print("✅ weight_log表创建成功")
            
            # 验证表结构
            result = db.session.execute(text("PRAGMA table_info(weight_log)"))
            columns = result.fetchall()
            print("📋 表结构验证:")
            for column in columns:
                print(f"  - {column[1]}: {column[2]} {'NOT NULL' if column[3] else 'NULL'}")
            
            # 检查唯一约束
            result = db.session.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='weight_log'"))
            table_sql = result.fetchone()
            if table_sql and 'unique_user_date' in table_sql[0].lower():
                print("✅ 唯一约束 (user_id, date) 已创建")
            else:
                print("⚠️ 唯一约束可能未正确创建")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False

def test_weight_log_operations():
    """测试体重记录基本操作"""
    print("\n🧪 测试体重记录功能...")
    
    with app.app_context():
        try:
            from datetime import date
            from app import User
            
            # 查找测试用户
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到测试用户，跳过功能测试")
                return False
            
            print(f"🔍 使用测试用户: {test_user.username}")
            
            # 创建测试体重记录
            test_date = date.today()
            test_weight = 70.5
            
            # 检查是否已存在今天的记录
            existing_record = WeightLog.query.filter_by(
                user_id=test_user.id,
                date=test_date
            ).first()
            
            if existing_record:
                print(f"📝 今天已有体重记录: {existing_record.weight}kg")
                test_record = existing_record
            else:
                # 计算BMI (需要用户身高)
                user_height = None
                if hasattr(test_user, 'profile') and test_user.profile:
                    user_height = test_user.profile.height
                
                bmi = None
                if user_height and user_height > 0:
                    bmi = round(test_weight / ((user_height / 100) ** 2), 1)
                    print(f"📊 计算BMI: {bmi} (身高: {user_height}cm)")
                
                # 创建新记录
                test_record = WeightLog(
                    user_id=test_user.id,
                    date=test_date,
                    weight=test_weight,
                    bmi=bmi,
                    notes="测试记录"
                )
                
                db.session.add(test_record)
                db.session.commit()
                print(f"✅ 创建体重记录: {test_weight}kg, BMI: {bmi}")
            
            # 测试模型属性
            print(f"📅 日期显示: {test_record.date_display}")
            print(f"⚖️ BMI状态: {test_record.bmi_status}")
            print(f"🎨 状态颜色: {test_record.bmi_color}")
            
            # 测试查询
            user_weight_logs = WeightLog.query.filter_by(user_id=test_user.id).order_by(WeightLog.date.desc()).limit(5).all()
            print(f"📈 用户最近5条体重记录数量: {len(user_weight_logs)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 体重记录表创建和测试脚本")
    print("=" * 50)
    
    # 创建表
    if create_weight_log_table():
        # 测试功能
        test_weight_log_operations()
    
    print("\n✅ 脚本执行完成")