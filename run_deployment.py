#!/usr/bin/env python3

import subprocess
import os
import sys
from datetime import datetime

def deploy_changes():
    """部署更改到Vercel"""
    print("🚀 自动部署脚本")
    print("=" * 50)
    
    # 确保在正确的目录
    project_dir = "/Users/jyxc-dz-0100299/claude-2/0802"
    os.chdir(project_dir)
    print(f"📁 工作目录: {os.getcwd()}")
    
    try:
        # 步骤1: 添加所有更改
        print("\n🔄 步骤1: 添加文件到git...")
        result = subprocess.run(['git', 'add', '.'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("   ✅ 文件添加成功")
        else:
            print(f"   ❌ 添加失败: {result.stderr}")
            return False
        
        # 步骤2: 检查暂存区
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("   📋 暂存区文件:")
            files = result.stdout.strip().split('\n')
            for i, file in enumerate(files[:10]):  # 只显示前10个
                print(f"      📄 {file}")
            if len(files) > 10:
                print(f"      ... 还有 {len(files) - 10} 个文件")
        else:
            print("   ℹ️ 暂存区为空")
        
        # 步骤3: 创建提交
        print("\n📝 步骤2: 创建提交...")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"""升级营养分析功能和系统优化

主要更新:
- 扩展营养比例分析: 新增膳食纤维、糖分、钠、钙、维生素C等5个维度  
- 优化热量计算: 总消耗 = 运动消耗 + 基础代谢率(BMR)
- 修复BMI计算: 使用用户真实身高数据
- 实现每日励志名言: 替换固定激励文案
- 优化饮食记录显示: 按餐次合并展示
- 更新AI分析提示词: 支持更全面营养成分估算
- 修复Vercel部署和数据库schema问题

更新时间: {timestamp}

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"""
        
        result = subprocess.run(['git', 'commit', '-m', commit_message], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ 提交创建成功")
            print(f"   📝 提交哈希: {result.stdout.strip()}")
        elif "nothing to commit" in result.stdout.lower():
            print("   ℹ️ 没有需要提交的更改")
            print("   🔍 检查是否所有更改都已提交")
        else:
            print(f"   ❌ 提交失败: {result.stderr}")
            return False
        
        # 步骤4: 推送到GitHub
        print("\n🚀 步骤3: 推送到GitHub...")
        
        # 首先尝试推送到main分支
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ 推送到main分支成功!")
        else:
            # 如果main失败，尝试master
            print("   ⚠️ main分支推送失败，尝试master分支...")
            result = subprocess.run(['git', 'push', 'origin', 'master'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("   ✅ 推送到master分支成功!")
            else:
                print(f"   ❌ 推送失败: {result.stderr}")
                return False
        
        # 成功完成
        print("\n" + "🎉" * 20)
        print("✅ 部署完成！代码已推送到GitHub")
        print("🔄 Vercel会自动检测更改并开始重新部署")
        print(f"⏰ 部署时间: {timestamp}")
        print("🔗 网站地址: https://fitlife-teal.vercel.app/")
        print("⏳ 请等待3-5分钟完成自动部署")
        print("💡 可在Vercel控制台查看部署进度")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("   ⏰ 命令执行超时")
        return False
    except Exception as e:
        print(f"   ❌ 执行异常: {e}")
        return False

def check_deployment_status():
    """检查部署状态信息"""
    print("\n📊 部署状态检查")
    print("-" * 30)
    
    try:
        # 检查远程仓库配置
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("📡 远程仓库:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        
        # 检查最近的提交
        result = subprocess.run(['git', 'log', '--oneline', '-3'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("\n📚 最近的提交:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        
        # 检查当前分支
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"\n🌿 当前分支: {result.stdout.strip()}")
            
    except Exception as e:
        print(f"检查状态时出错: {e}")

if __name__ == "__main__":
    print("🔧 FitLife Vercel自动部署工具")
    
    # 显示部署前状态
    check_deployment_status()
    
    # 执行部署
    success = deploy_changes()
    
    if success:
        print("\n✅ 自动部署流程完成!")
        print("🌐 访问网站检查更新: https://fitlife-teal.vercel.app/")
        
        # 显示更新内容摘要
        print("\n📋 本次更新内容摘要:")
        print("   🍽️ 营养比例分析扩展 (8个营养维度)")  
        print("   🔥 热量计算优化 (包含BMR)")
        print("   💪 每日励志名言功能")
        print("   📊 饮食记录按餐次合并")
        print("   🎯 BMI计算修复")
        print("   🤖 AI分析功能增强")
    else:
        print("\n❌ 部署过程中出现问题")
        print("💡 可能需要手动检查git配置或网络连接")
    
    sys.exit(0 if success else 1)

# 直接运行部署
if __name__ == "__main__":
    # 执行部署逻辑
    success = deploy_changes()
    check_deployment_status()
    
    if success:
        print(f"\n🎯 部署总结:")
        print(f"   ✅ 代码已推送到GitHub")
        print(f"   🔄 Vercel自动部署已触发") 
        print(f"   ⏰ 预计3-5分钟完成")
        print(f"   🔗 检查: https://fitlife-teal.vercel.app/")
        
        # 输出关键功能更新
        print(f"\n🚀 主要功能更新:")
        print(f"   📊 营养分析: 蛋白质/碳水/脂肪 → 8个营养维度")
        print(f"   🔥 热量计算: 运动消耗 → 运动+基础代谢(BMR)")  
        print(f"   🍽️ 饮食显示: 单个食物 → 按餐次合并")
        print(f"   💪 励志功能: 固定文案 → 每日名人名言")
        print(f"   📐 BMI计算: 固定身高 → 用户真实身高")
    else:
        print("\n❌ 部署失败，请检查:")
        print("   🔧 Git配置是否正确")
        print("   🌐 网络连接是否正常")
        print("   🔑 GitHub访问权限")
        print("   📁 文件权限设置")