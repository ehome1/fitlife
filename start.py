#!/usr/bin/env python3

import os
import sys

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    os.system("pip3 install -r requirements.txt")

def create_database():
    """创建数据库"""
    print("正在创建数据库...")
    from app import app, db
    with app.app_context():
        db.create_all()
        print("数据库创建成功！")

def start_app():
    """启动应用"""
    print("启动健身饮食管理应用...")
    print("="*50)
    print("应用已启动！")
    print("访问地址: http://127.0.0.1:5001")
    print("按 Ctrl+C 停止应用")
    print("="*50)
    
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    try:
        # 检查是否需要安装依赖
        if '--install' in sys.argv or not os.path.exists('fitness_app.db'):
            install_requirements()
            create_database()
        else:
            create_database()
        
        start_app()
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请尝试运行: python start.py --install")