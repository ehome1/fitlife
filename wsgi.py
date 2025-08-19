"""
WSGI配置文件
用于生产环境部署
"""
from app import app

# 导出app供Vercel使用
application = app

if __name__ == "__main__":
    app.run()