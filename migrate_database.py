#!/usr/bin/env python3
"""
数据库迁移脚本：为ExerciseLog表添加新字段
添加 analysis_status 和 ai_analysis_result 字段
"""

import sqlite3
import os
import json
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    print("🔄 开始数据库迁移...")
    
    # 检查数据库文件位置
    possible_paths = ['fitness_app.db', 'instance/fitness_app.db']
    db_path = None
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 数据库文件不存在，请先运行应用创建数据库")
        print(f"查找路径: {', '.join(possible_paths)}")
        return False
    
    print(f"💾 使用数据库文件: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute("PRAGMA table_info(exercise_log)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 当前ExerciseLog表字段: {', '.join(column_names)}")
        
        # 检查是否需要添加analysis_status字段
        if 'analysis_status' not in column_names:
            print("➕ 添加 analysis_status 字段...")
            cursor.execute("""
                ALTER TABLE exercise_log 
                ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'completed'
            """)
            print("✅ analysis_status 字段添加成功")
        else:
            print("✅ analysis_status 字段已存在")
        
        # 检查是否需要添加ai_analysis_result字段
        if 'ai_analysis_result' not in column_names:
            print("➕ 添加 ai_analysis_result 字段...")
            cursor.execute("""
                ALTER TABLE exercise_log 
                ADD COLUMN ai_analysis_result JSON
            """)
            print("✅ ai_analysis_result 字段添加成功")
        else:
            print("✅ ai_analysis_result 字段已存在")
        
        # 提交更改
        conn.commit()
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(exercise_log)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"📋 迁移后ExerciseLog表字段: {', '.join(new_column_names)}")
        
        # 更新现有记录的analysis_status为completed（如果为NULL）
        cursor.execute("""
            UPDATE exercise_log 
            SET analysis_status = 'completed' 
            WHERE analysis_status IS NULL
        """)
        
        updated_rows = cursor.rowcount
        if updated_rows > 0:
            print(f"📝 更新了 {updated_rows} 条现有记录的状态为 'completed'")
        
        conn.commit()
        conn.close()
        
        print("🎉 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_migration():
    """测试迁移结果"""
    print("\n🧪 测试迁移结果...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 测试插入带新字段的记录
        test_data = {
            'basic_metrics': {
                'calories_burned': 250,
                'intensity_level': 'medium',
                'fitness_score': 7.0
            },
            'exercise_analysis': {
                'heart_rate_zone': '有氧区间',
                'energy_system': '有氧系统'
            }
        }
        
        cursor.execute("""
            INSERT INTO exercise_log 
            (user_id, date, exercise_type, exercise_name, duration, 
             analysis_status, ai_analysis_result, created_at)
            VALUES (1, ?, 'running', '迁移测试跑步', 30, 'completed', ?, ?)
        """, (datetime.now().date().isoformat(), json.dumps(test_data), datetime.now()))
        
        conn.commit()
        
        # 查询测试记录
        cursor.execute("""
            SELECT analysis_status, ai_analysis_result 
            FROM exercise_log 
            WHERE exercise_name = '迁移测试跑步'
        """)
        
        result = cursor.fetchone()
        if result:
            status, analysis_result = result
            print(f"✅ 测试记录创建成功: status={status}")
            
            if analysis_result:
                parsed_result = json.loads(analysis_result)
                print(f"✅ JSON字段解析成功: {list(parsed_result.keys())}")
            
            # 清理测试记录
            cursor.execute("DELETE FROM exercise_log WHERE exercise_name = '迁移测试跑步'")
            conn.commit()
            print("🧹 清理测试记录")
        
        conn.close()
        print("✅ 迁移测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 迁移测试失败: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """主函数"""
    print("🚀 FitLife 数据库迁移工具")
    print("=" * 50)
    print("目标: 为ExerciseLog表添加AI分析支持字段")
    print("字段: analysis_status, ai_analysis_result")
    print("=" * 50)
    
    # 执行迁移
    migration_success = migrate_database()
    
    if migration_success:
        # 测试迁移
        test_success = test_migration()
        
        if test_success:
            print("\n🎉 数据库迁移和测试全部完成！")
            print("💡 现在可以重新运行应用测试统一AI分析功能")
            return True
        else:
            print("\n⚠️ 迁移成功但测试失败")
            return False
    else:
        print("\n❌ 数据库迁移失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)