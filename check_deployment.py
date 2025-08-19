#!/usr/bin/env python3

import os
import requests
import time

def check_vercel_deployment():
    """检查Vercel部署状态"""
    print("🔍 检查Vercel部署状态...")
    
    url = "https://fitlife-teal.vercel.app/"
    
    try:
        print(f"📡 正在访问: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 网站可以正常访问")
            content = response.text
            if "FitLife" in content:
                print("✅ 应用内容正常")
            else:
                print("⚠️ 内容可能不完整")
                print(f"内容预览: {content[:200]}...")
        else:
            print(f"❌ 网站访问异常: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时 - 服务器可能正在冷启动")
        print("💡 建议: 等待30-60秒后重试")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误 - 检查网络或域名配置")
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def check_health_endpoint():
    """检查健康检查端点"""
    try:
        url = "https://fitlife-teal.vercel.app/health"
        response = requests.get(url, timeout=10)
        print(f"🏥 健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"🏥 健康检查失败: {e}")

def main():
    print("🚀 FitLife Vercel部署检查")
    print("=" * 50)
    
    check_vercel_deployment()
    print()
    check_health_endpoint()
    
    print("\n📋 修复建议:")
    print("1. 如果显示'应用启动中'，等待1-2分钟后刷新")
    print("2. 如果持续无法访问，检查Vercel控制台部署日志")
    print("3. 确认环境变量已正确配置")
    print("4. 检查数据库连接配置")

if __name__ == '__main__':
    main()