#!/usr/bin/env python3
"""
FitLife 快速启动脚本
解决端口冲突和CSP问题
"""
import os
import sys
import subprocess
import time
import signal
import socket

def check_port(port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def kill_python_processes():
    """停止所有相关Python进程"""
    try:
        subprocess.run(['pkill', '-f', 'python.*app.py'], check=False)
        time.sleep(2)
    except:
        pass

def find_available_port(start_port=5000):
    """找到可用端口"""
    for port in range(start_port, start_port + 10):
        if check_port(port):
            return port
    return None

def start_app():
    """启动FitLife应用"""
    print("🚀 FitLife 快速启动工具")
    print("="*50)
    
    # 停止现有进程
    print("1. 清理现有进程...")
    kill_python_processes()
    
    # 找到可用端口
    print("2. 寻找可用端口...")
    port = find_available_port()
    if not port:
        print("❌ 无法找到可用端口")
        return
    
    print(f"   使用端口: {port}")
    
    # 修改app.py中的端口设置
    print("3. 配置应用...")
    try:
        # 直接运行应用
        os.environ['FLASK_PORT'] = str(port)
        
        print("4. 启动应用...")
        print(f"   应用将在 http://127.0.0.1:{port} 启动")
        print("   按 Ctrl+C 停止应用")
        print("="*50)
        
        # 创建临时启动脚本
        app_code = f"""
from app import app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port={port})
"""
        
        with open('temp_start.py', 'w') as f:
            f.write(app_code)
        
        # 启动应用
        subprocess.run([sys.executable, 'temp_start.py'])
        
    except KeyboardInterrupt:
        print("\\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    finally:
        # 清理临时文件
        if os.path.exists('temp_start.py'):
            os.remove('temp_start.py')

if __name__ == "__main__":
    start_app()