#!/usr/bin/env python3

import subprocess
import sys
import os
from datetime import datetime

# 切换到项目目录
os.chdir('/Users/jyxc-dz-0100299/claude-2/0802')

def run_git_command(cmd):
    """运行git命令"""
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

print("🚀 快速部署到Vercel")
print("=" * 30)

# 1. 检查git状态
print("1. 检查git状态...")
success, stdout, stderr = run_git_command("git status --porcelain")
if success:
    if stdout.strip():
        print("   📝 发现未提交文件:")
        for line in stdout.strip().split('\n')[:10]:  # 只显示前10个
            print(f"      {line}")
        if len(stdout.strip().split('\n')) > 10:
            print(f"      ... 还有{len(stdout.strip().split('\n')) - 10}个文件")
    else:
        print("   ✅ 工作目录干净")
else:
    print(f"   ❌ 检查失败: {stderr}")

# 2. 添加所有更改
print("\n2. 添加所有更改...")
success, stdout, stderr = run_git_command("git add .")
if success:
    print("   ✅ 文件已添加到暂存区")
else:
    print(f"   ❌ 添加失败: {stderr}")

# 3. 创建提交
print("\n3. 创建提交...")
commit_msg = f"feat: 升级营养分析和热量计算系统 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

# 使用更简单的方式创建提交
try:
    result = subprocess.run([
        'git', 'commit', '-m', commit_msg
    ], capture_output=True, text=True, cwd='/Users/jyxc-dz-0100299/claude-2/0802')
    
    if result.returncode == 0:
        print("   ✅ 提交创建成功")
        print(f"   📝 提交信息: {commit_msg}")
    else:
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print("   ℹ️ 没有需要提交的更改")
        else:
            print(f"   ❌ 提交失败: {result.stderr}")
except Exception as e:
    print(f"   ❌ 提交异常: {e}")

# 4. 推送到远程
print("\n4. 推送到GitHub...")
success, stdout, stderr = run_git_command("git push origin main")
if success:
    print("   ✅ 推送成功!")
    print("   🔄 Vercel应该会自动开始部署")
else:
    # 尝试master分支
    success2, stdout2, stderr2 = run_git_command("git push origin master") 
    if success2:
        print("   ✅ 推送到master分支成功!")
        print("   🔄 Vercel应该会自动开始部署")
    else:
        print(f"   ❌ 推送失败: {stderr}")
        print(f"   尝试master分支也失败: {stderr2}")

print("\n" + "=" * 30)
print("🎯 部署完成!")
print("🔗 网站: https://fitlife-teal.vercel.app/")
print("⏳ 请等待2-3分钟让Vercel完成部署")
print("💡 如果仍未更新，检查Vercel控制台是否有部署错误")