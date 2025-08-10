#!/usr/bin/env python3
"""
生产环境数据库迁移脚本
添加缺失的字段到exercise_log表
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_exercise_log_table():
    """为exercise_log表添加缺失的字段"""
    
    # 获取数据库URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL环境变量未设置")
        return False
    
    try:
        # 连接数据库
        engine = create_engine(database_url)
        
        print("🔄 连接到生产数据库...")
        
        with engine.connect() as conn:
            # 检查当前表结构
            print("📋 检查当前exercise_log表结构...")
            
            # 检查analysis_status字段是否存在
            try:
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'exercise_log' AND column_name = 'analysis_status'
                """))
                analysis_status_exists = len(result.fetchall()) > 0
            except:
                analysis_status_exists = False
            
            # 检查ai_analysis_result字段是否存在
            try:
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'exercise_log' AND column_name = 'ai_analysis_result'
                """))
                ai_analysis_result_exists = len(result.fetchall()) > 0
            except:
                ai_analysis_result_exists = False
            
            print(f"analysis_status字段存在: {analysis_status_exists}")
            print(f"ai_analysis_result字段存在: {ai_analysis_result_exists}")
            
            # 添加缺失的字段
            if not analysis_status_exists:
                print("➕ 添加analysis_status字段...")
                conn.execute(text("""
                    ALTER TABLE exercise_log 
                    ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'pending'
                """))
                print("✅ analysis_status字段添加成功")
            
            if not ai_analysis_result_exists:
                print("➕ 添加ai_analysis_result字段...")
                conn.execute(text("""
                    ALTER TABLE exercise_log 
                    ADD COLUMN ai_analysis_result JSON
                """))
                print("✅ ai_analysis_result字段添加成功")
            
            # 提交更改
            conn.commit()
            
            # 验证更改
            print("🔍 验证数据库更改...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'exercise_log'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("📋 当前exercise_log表结构:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            
            print("✅ 数据库迁移完成！")
            return True
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始生产环境数据库迁移...")
    success = migrate_exercise_log_table()
    
    if success:
        print("✅ 迁移完成，可以重新部署应用")
        sys.exit(0)
    else:
        print("❌ 迁移失败")
        sys.exit(1)