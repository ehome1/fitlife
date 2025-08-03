"""
Vercel部署入口文件
"""
from app import app

# Vercel需要这个变量
application = app

if __name__ == "__main__":
    app.run()