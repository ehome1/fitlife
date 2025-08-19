#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def fix_database():
    """修复数据库schema问题"""
    print("🔧 开始修复数据库schema...")
    
    with app.app_context():
        try:
            # 尝试添加exercise_description字段
            print("📝 添加exercise_description字段...")
            db.session.execute(text("ALTER TABLE exercise_log ADD COLUMN exercise_description TEXT"))
            db.session.commit()
            print("✅ exercise_description字段添加成功")
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate column' in error_msg:
                print("✅ exercise_description字段已存在，无需添加")
            else:
                print(f"❌ 添加字段失败: {e}")
                db.session.rollback()
                return False
        
        # 验证字段存在
        try:
            print("🔍 验证字段...")
            result = db.session.execute(text("SELECT exercise_description FROM exercise_log LIMIT 1"))
            print("✅ 字段验证成功")
            return True
        except Exception as e:
            print(f"❌ 字段验证失败: {e}")
            return False

if __name__ == '__main__':
    print("🚀 数据库修复脚本")
    print("=" * 50)
    
    if fix_database():
        print("\n🎉 数据库修复完成！")
        print("现在可以安全地使用仪表盘了")
    else:
        print("\n❌ 数据库修复失败")