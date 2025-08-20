#!/usr/bin/env python3

import subprocess
import os
from datetime import datetime

def emergency_deploy():
    """紧急部署修复版本"""
    print("🚨 紧急部署修复版本")
    print("=" * 40)
    
    os.chdir('/Users/jyxc-dz-0100299/claude-2/0802')
    
    try:
        # 1. 添加紧急修复文件
        print("1️⃣ 添加紧急修复文件...")
        subprocess.run(['git', 'add', 'emergency_vercel.py', 'vercel.json'], check=True)
        print("   ✅ 文件已添加")
        
        # 2. 创建紧急提交
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"🚨 HOTFIX: 紧急修复网站无法访问问题 {timestamp}"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ 紧急提交已创建")
        elif "nothing to commit" in result.stdout:
            print("   ℹ️ 没有新的更改需要提交")
        else:
            print(f"   ❌ 提交失败: {result.stderr}")
            return False
        
        # 3. 推送到GitHub
        print("3️⃣ 紧急推送...")
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ 推送成功!")
        else:
            # 尝试master分支
            result = subprocess.run(['git', 'push', 'origin', 'master'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ 推送到master分支成功!")
            else:
                print(f"   ❌ 推送失败: {result.stderr}")
                return False
        
        print("\n" + "🎉" * 30)
        print("✅ 紧急修复版本已部署!")
        print("🔄 Vercel正在重新部署...")
        print("⏰ 预计2-3分钟内生效")
        print("🔗 网站: https://fitlife-teal.vercel.app/")
        print("\n📋 紧急版本功能:")
        print("   ✅ 基础首页显示")
        print("   ✅ 系统维护提示")
        print("   ✅ 健康检查接口")
        print("   ✅ 错误处理机制")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

if __name__ == "__main__":
    success = emergency_deploy()
    
    if success:
        print("\n🔧 后续修复步骤:")
        print("1. 检查app.py中的语法错误")
        print("2. 验证所有导入模块") 
        print("3. 测试数据库连接")
        print("4. 逐步恢复完整功能")
        print("5. 切换回vercel_app.py")
    else:
        print("\n❌ 紧急部署失败")
        print("💡 可能需要手动在Vercel控制台操作")