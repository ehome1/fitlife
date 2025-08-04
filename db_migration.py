#!/usr/bin/env python3
"""
数据库迁移脚本 - FitLife v2.0
将旧版meal_log表升级到v2.0架构

⚠️ 警告：此脚本会修改生产数据库架构，请在备份数据后谨慎使用！
"""
import os
import sys
from sqlalchemy import text
from app import app, db

def check_table_structure():
    """检查当前表结构"""
    print("🔍 检查当前数据库表结构...")
    
    with app.app_context():
        try:
            # 检查meal_log表的列
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'meal_log'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            print(f"找到 {len(columns)} 个列:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                
            return [col[0] for col in columns]
            
        except Exception as e:
            print(f"❌ 无法检查表结构: {e}")
            return []

def backup_table():
    """备份现有数据"""
    print("💾 备份现有meal_log数据...")
    
    with app.app_context():
        try:
            # 创建备份表
            db.session.execute(text("""
                CREATE TABLE meal_log_backup AS 
                SELECT * FROM meal_log;
            """))
            
            # 检查备份数据条数
            result = db.session.execute(text("SELECT COUNT(*) FROM meal_log_backup;"))
            count = result.scalar()
            
            db.session.commit()
            print(f"✅ 备份完成，共 {count} 条记录")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            db.session.rollback()
            return False

def add_missing_columns():
    """添加缺失的v2.0字段"""
    print("🔧 添加v2.0新字段...")
    
    new_columns = [
        ("food_description", "TEXT"),
        ("food_items_json", "JSON"),
        ("total_calories", "INTEGER"),
        ("total_protein", "FLOAT"),
        ("total_carbs", "FLOAT"),
        ("total_fat", "FLOAT"),
        ("total_fiber", "FLOAT"),
        ("total_sodium", "FLOAT"),
        ("health_score", "FLOAT"),
        ("meal_suitability", "VARCHAR(100)"),
        ("nutrition_highlights", "JSON"),
        ("dietary_suggestions", "JSON"),
        ("personalized_assessment", "TEXT"),
        ("quantity", "FLOAT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]
    
    existing_columns = check_table_structure()
    
    with app.app_context():
        try:
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    print(f"  添加字段: {col_name} ({col_type})")
                    db.session.execute(text(f"""
                        ALTER TABLE meal_log 
                        ADD COLUMN {col_name} {col_type};
                    """))
                else:
                    print(f"  字段已存在: {col_name}")
            
            db.session.commit()
            print("✅ 字段添加完成")
            return True
            
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")
            db.session.rollback()
            return False

def migrate_data():
    """迁移现有数据到新字段"""
    print("📋 迁移现有数据...")
    
    with app.app_context():
        try:
            # 将calories复制到total_calories
            db.session.execute(text("""
                UPDATE meal_log 
                SET total_calories = COALESCE(calories, 0),
                    total_protein = COALESCE(protein, 0),
                    total_carbs = COALESCE(carbs, 0),
                    total_fat = COALESCE(fat, 0),
                    food_description = COALESCE(food_name, '未记录'),
                    health_score = 7.0,
                    meal_suitability = 'nutrition assessment',
                    updated_at = created_at
                WHERE total_calories IS NULL;
            """))
            
            db.session.commit()
            print("✅ 数据迁移完成")
            return True
            
        except Exception as e:
            print(f"❌ 数据迁移失败: {e}")
            db.session.rollback()
            return False

def verify_migration():
    """验证迁移结果"""
    print("🔍 验证迁移结果...")
    
    with app.app_context():
        try:
            # 检查新表结构
            result = db.session.execute(text("SELECT COUNT(*) FROM meal_log;"))
            total_records = result.scalar()
            
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM meal_log 
                WHERE total_calories IS NOT NULL;
            """))
            migrated_records = result.scalar()
            
            print(f"总记录数: {total_records}")
            print(f"已迁移记录数: {migrated_records}")
            
            if total_records == migrated_records:
                print("✅ 迁移验证通过")
                return True
            else:
                print("❌ 迁移验证失败")
                return False
                
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False

def rollback_migration():
    """回滚迁移（从备份恢复）"""
    print("🔄 回滚数据库迁移...")
    
    with app.app_context():
        try:
            # 删除当前表
            db.session.execute(text("DROP TABLE meal_log;"))
            
            # 从备份恢复
            db.session.execute(text("""
                CREATE TABLE meal_log AS 
                SELECT * FROM meal_log_backup;
            """))
            
            # 删除备份表
            db.session.execute(text("DROP TABLE meal_log_backup;"))
            
            db.session.commit()
            print("✅ 回滚完成")
            return True
            
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            db.session.rollback()
            return False

def main():
    """主迁移流程"""
    print("🚀 FitLife 数据库迁移工具 v2.0")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            check_table_structure()
        elif command == "backup":
            backup_table()
        elif command == "migrate":
            if not backup_table():
                print("❌ 备份失败，取消迁移")
                return
            
            if not add_missing_columns():
                print("❌ 添加字段失败，考虑回滚")
                return
            
            if not migrate_data():
                print("❌ 数据迁移失败，考虑回滚")
                return
            
            if verify_migration():
                print("🎉 迁移成功完成！")
            else:
                print("⚠️ 迁移完成但验证有问题，请检查数据")
                
        elif command == "rollback":
            rollback_migration()
        else:
            print("用法:")
            print("  python db_migration.py check    - 检查表结构")
            print("  python db_migration.py backup   - 备份数据")
            print("  python db_migration.py migrate  - 执行完整迁移")
            print("  python db_migration.py rollback - 回滚迁移")
    else:
        print("⚠️ 此脚本用于数据库架构迁移，请谨慎使用！")
        print("建议先在测试环境中验证。")
        print("\n用法:")
        print("  python db_migration.py check    - 检查表结构")
        print("  python db_migration.py migrate  - 执行迁移")
        print("  python db_migration.py rollback - 回滚迁移")

if __name__ == "__main__":
    main()