#!/usr/bin/env python3

# 直接执行部署命令
import subprocess
import os
from datetime import datetime

# 设置工作目录
os.chdir('/Users/jyxc-dz-0100299/claude-2/0802')

print("🚀 开始Git提交和部署")
print("=" * 40)

# 当前时间
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"⏰ 部署时间: {timestamp}")

try:
    # 1. Git add
    print("\n1️⃣ 添加文件...")
    subprocess.run(['git', 'add', '.'], check=True)
    print("   ✅ 文件已添加")

    # 2. Git commit
    print("\n2️⃣ 创建提交...")
    commit_msg = f"feat: 营养分析系统升级 {timestamp}"
    
    result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ 提交成功")
    else:
        if "nothing to commit" in result.stdout:
            print("   ℹ️ 没有更改需要提交")
        else:
            print(f"   ❌ 提交失败: {result.stderr}")
    
    # 3. Git push
    print("\n3️⃣ 推送到GitHub...")
    
    # 尝试push到main
    result = subprocess.run(['git', 'push', 'origin', 'main'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ 推送到main分支成功!")
        push_success = True
    else:
        # 尝试push到master
        result = subprocess.run(['git', 'push', 'origin', 'master'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ 推送到master分支成功!")
            push_success = True
        else:
            print(f"   ❌ 推送失败: {result.stderr}")
            push_success = False
    
    if push_success:
        print("\n🎉 部署完成!")
        print("🔄 Vercel会自动检测更改并重新部署")
        print("🔗 网站: https://fitlife-teal.vercel.app/")
        print("⏳ 请等待3-5分钟查看更新")
    else:
        print("\n❌ 部署失败")

except subprocess.CalledProcessError as e:
    print(f"❌ 命令执行失败: {e}")
except Exception as e:
    print(f"❌ 执行异常: {e}")

print(f"\n📋 本次更新摘要:")
print(f"   📊 扩展营养比例分析 (8个维度)")
print(f"   🔥 优化热量计算 (BMR)")
print(f"   💪 每日励志名言")
print(f"   🍽️ 饮食按餐次显示")
print(f"   🎯 修复BMI计算")

# 立即执行
if __name__ == "__main__":
    exec(open(__file__).read())