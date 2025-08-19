#!/usr/bin/env python3

import subprocess
import sys
import os

def run_fix():
    """运行数据库修复"""
    try:
        # 改变工作目录
        os.chdir('/Users/jyxc-dz-0100299/claude-2/0802')
        
        # 执行修复脚本
        result = subprocess.run([sys.executable, 'complete_fix.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"执行失败: {e}")
        return False

if __name__ == '__main__':
    run_fix()