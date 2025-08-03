"""
WSGI配置文件
用于生产环境部署
"""
from app import app, db, init_database

# 确保数据库已初始化
with app.app_context():
    try:
        # 尝试查询数据库，如果失败则初始化
        db.engine.execute("SELECT 1")
    except:
        # 数据库不存在或未初始化，进行初始化
        init_database()

if __name__ == "__main__":
    app.run()