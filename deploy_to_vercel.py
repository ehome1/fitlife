#!/usr/bin/env python3

import subprocess
import os
import sys
from datetime import datetime

def run_command(command, description):
    """运行shell命令"""
    print(f"🚀 {description}")
    print(f"   命令: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd='/Users/jyxc-dz-0100299/claude-2/0802',
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"   ✅ 成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
        else:
            print(f"   ❌ 失败 (退出码: {result.returncode})")
            if result.stderr.strip():
                print(f"   错误: {result.stderr.strip()}")
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"   ⏰ 命令超时")
        return False, "", "Timeout"
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False, "", str(e)

def deploy_to_vercel():
    """部署到Vercel"""
    print("🔄 开始部署到Vercel")
    print("=" * 50)
    
    # 检查当前目录
    success, stdout, stderr = run_command("pwd", "检查当前目录")
    if not success:
        return False
    
    # 检查git状态
    success, stdout, stderr = run_command("git status --porcelain", "检查git状态")
    if success:
        changes = stdout.strip()
        if changes:
            print(f"📝 发现未提交的更改:")
            for line in changes.split('\n'):
                print(f"   {line}")
        else:
            print("✅ 工作目录干净")
    
    # 添加所有更改
    success, stdout, stderr = run_command("git add .", "添加所有更改到暂存区")
    if not success:
        return False
    
    # 检查暂存区
    success, stdout, stderr = run_command("git diff --cached --name-only", "检查暂存区文件")
    if success and stdout.strip():
        print("📋 暂存区文件:")
        for file in stdout.strip().split('\n'):
            print(f"   ✅ {file}")
    
    # 创建提交
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"""升级营养分析功能和热量计算

- 扩展营养比例分析：新增膳食纤维、糖分、钠、钙、维生素C等5个维度
- 优化热量计算：总消耗 = 运动消耗 + 基础代谢率(BMR)
- 修复BMI计算：使用用户真实身高数据
- 实现每日励志名言：替换固定激励文案
- 优化饮食记录显示：按餐次合并而非单个食物
- 更新AI分析提示词：支持更全面的营养成分估算
- 修复Vercel部署配置和数据库schema问题

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"""

    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"', "创建提交")
    if not success:
        if "nothing to commit" in stderr:
            print("ℹ️ 没有需要提交的更改")
        else:
            print(f"❌ 提交失败: {stderr}")
            return False
    
    # 推送到远程仓库
    success, stdout, stderr = run_command("git push origin main", "推送到远程仓库")
    if not success:
        print(f"❌ 推送失败: {stderr}")
        return False
    
    print("\n🎉 代码已成功推送到GitHub!")
    print("🔄 Vercel应该会自动检测到更改并开始重新部署")
    
    # 显示部署信息
    print("\n📋 部署信息:")
    print(f"   时间: {timestamp}")
    print(f"   仓库: https://github.com/用户名/仓库名")
    print(f"   Vercel: https://vercel.com/dashboard")
    print(f"   网站: https://fitlife-teal.vercel.app/")
    
    print("\n⏳ 等待几分钟后检查网站是否更新")
    print("💡 如果仍未更新，可以在Vercel控制台手动触发重新部署")
    
    return True

def check_git_remote():
    """检查git远程仓库配置"""
    print("\n🔍 检查git远程仓库配置")
    print("-" * 30)
    
    success, stdout, stderr = run_command("git remote -v", "查看远程仓库")
    if success and stdout.strip():
        print("📡 远程仓库:")
        for line in stdout.strip().split('\n'):
            print(f"   {line}")
        return True
    else:
        print("❌ 未配置远程仓库")
        return False

def show_recent_commits():
    """显示最近的提交"""
    print("\n📚 最近的提交记录")
    print("-" * 30)
    
    success, stdout, stderr = run_command("git log --oneline -5", "查看最近5次提交")
    if success and stdout.strip():
        for line in stdout.strip().split('\n'):
            print(f"   {line}")
    else:
        print("❌ 无法获取提交记录")

def main():
    """主函数"""
    print("🚀 FitLife Vercel部署脚本")
    print("=" * 60)
    
    # 检查git配置
    if not check_git_remote():
        print("⚠️ 请先配置git远程仓库")
        return False
    
    # 显示最近提交
    show_recent_commits()
    
    # 执行部署
    success = deploy_to_vercel()
    
    if success:
        print("\n✅ 部署脚本执行完成!")
        print("🔗 访问 https://fitlife-teal.vercel.app/ 查看更新")
    else:
        print("\n❌ 部署过程中遇到问题")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)