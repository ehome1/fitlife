#!/usr/bin/env python3

import subprocess
import os

def check_git_status():
    """检查git状态"""
    print("🔍 检查Git和部署状态")
    print("=" * 40)
    
    try:
        os.chdir('/Users/jyxc-dz-0100299/claude-2/0802')
        
        # 检查git状态
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            print("📝 未提交的文件:")
            for line in result.stdout.strip().split('\n'):
                status = line[:2]
                filename = line[3:]
                if status == '??':
                    print(f"   🆕 {filename} (新文件)")
                elif status.startswith('M'):
                    print(f"   ✏️ {filename} (已修改)")
                elif status.startswith('A'):
                    print(f"   ➕ {filename} (已添加)")
                else:
                    print(f"   📄 {filename} ({status})")
        else:
            print("✅ 工作目录干净")
        
        # 检查最后提交
        result = subprocess.run(['git', 'log', '-1', '--format=%h %s (%cr)'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"📚 最后提交: {result.stdout.strip()}")
        
        # 检查远程仓库状态
        result = subprocess.run(['git', 'status', '-b', '--porcelain'], 
                              capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if line.startswith('##'):
                branch_info = line[3:]
                print(f"🌿 分支状态: {branch_info}")
                break
        
        # 检查需要推送的提交
        result = subprocess.run(['git', 'log', '@{u}..HEAD', '--oneline'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"📤 待推送提交:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("✅ 本地与远程同步")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git命令执行失败: {e}")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == '__main__':
    check_git_status()