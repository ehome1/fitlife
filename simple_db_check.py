import sqlite3
import os

# 检查数据库文件
db_path = "instance/fitness_app.db"
if os.path.exists(db_path):
    print(f"✅ 数据库文件存在: {db_path}")
else:
    print(f"❌ 数据库文件不存在: {db_path}")
    exit(1)

# 连接并查询
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表结构
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='meal_log'")
table_schema = cursor.fetchone()
print(f"📋 MealLog表结构: {table_schema[0] if table_schema else '表不存在'}")

# 查询最近记录
cursor.execute("SELECT id, calories, food_name, food_description FROM meal_log ORDER BY id DESC LIMIT 5")
records = cursor.fetchall()

print(f"\n📊 最近5条记录:")
for record in records:
    id, calories, food_name, food_description = record
    print(f"  ID:{id} | 热量:{calories} | 食物:{food_name} | 描述:{food_description}")

conn.close()