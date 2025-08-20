#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_app_startup():
    """检查应用启动状态"""
    print("🚨 紧急检查应用启动状态")
    print("=" * 50)
    
    try:
        # 尝试导入应用
        from app import app, db
        print("✅ 成功导入Flask应用")
        
        # 检查应用配置
        with app.app_context():
            print("✅ Flask应用上下文正常")
            
            # 检查数据库连接
            try:
                db.engine.execute("SELECT 1")
                print("✅ 数据库连接正常")
            except Exception as e:
                print(f"❌ 数据库连接失败: {e}")
                return False
            
            # 检查关键路由
            with app.test_client() as client:
                # 测试首页
                response = client.get('/')
                if response.status_code == 200:
                    print("✅ 首页路由正常")
                else:
                    print(f"❌ 首页路由错误: {response.status_code}")
                    print(f"   错误内容: {response.data.decode('utf-8')[:500]}")
                    return False
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入应用失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 应用启动异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_critical_files():
    """检查关键文件完整性"""
    print("\n🔍 检查关键文件")
    print("-" * 30)
    
    critical_files = [
        'app.py',
        'vercel.json', 
        'vercel_app.py',
        'requirements.txt',
        'wsgi.py'
    ]
    
    missing_files = []
    for file in critical_files:
        filepath = f'/Users/jyxc-dz-0100299/claude-2/0802/{file}'
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} 缺失!")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_syntax_errors():
    """检查Python语法错误"""
    print("\n🔍 检查Python语法")
    print("-" * 30)
    
    python_files = ['app.py', 'vercel_app.py', 'wsgi.py']
    
    for file in python_files:
        filepath = f'/Users/jyxc-dz-0100299/claude-2/0802/{file}'
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, filepath, 'exec')
                print(f"✅ {file} 语法正常")
            except SyntaxError as e:
                print(f"❌ {file} 语法错误: {e}")
                print(f"   行号: {e.lineno}")
                return False
            except Exception as e:
                print(f"❌ {file} 检查失败: {e}")
                return False
    
    return True

def check_recent_changes():
    """检查最近的更改"""
    print("\n📝 检查最近更改")
    print("-" * 30)
    
    try:
        import subprocess
        
        # 检查最近的提交
        result = subprocess.run(
            ['git', 'log', '--oneline', '-5'], 
            cwd='/Users/jyxc-dz-0100299/claude-2/0802',
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("📚 最近5次提交:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        
        # 检查工作目录状态
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            cwd='/Users/jyxc-dz-0100299/claude-2/0802',
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("\n📝 未提交的更改:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("\n✅ 工作目录干净")
        
    except Exception as e:
        print(f"检查git状态失败: {e}")

def create_emergency_vercel_app():
    """创建紧急版本的vercel_app.py"""
    print("\n🆘 创建紧急修复版本")
    print("-" * 30)
    
    emergency_content = '''"""
紧急修复版本 - 最小化Flask应用
"""
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 设置环境变量
    os.environ['FLASK_ENV'] = 'production'
    
    # 尝试导入主应用
    from app import app as flask_app
    
    # 基本配置
    flask_app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY=os.getenv('SECRET_KEY', 'emergency-secret-key')
    )
    
    app = flask_app
    logger.info("✅ 主应用加载成功")
    
except Exception as e:
    logger.error(f"❌ 主应用加载失败: {e}")
    
    # 创建紧急备用应用
    from flask import Flask, jsonify, render_template_string
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'emergency-mode'
    
    @app.route('/')
    def emergency_home():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FitLife - 系统维护中</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { background: #f8f9fa; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 FitLife 系统维护中</h1>
                <div class="status">
                    <p>我们正在进行系统升级，请稍后再试。</p>
                    <p>预计恢复时间：15-30分钟</p>
                    <p>感谢您的耐心等待！</p>
                </div>
                <br>
                <p><small>如有紧急问题，请联系技术支持</small></p>
            </div>
        </body>
        </html>
        """)
    
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "emergency_mode",
            "message": "系统维护中",
            "error": str(e)
        })
    
    @app.route('/api/<path:path>')
    def api_maintenance(path):
        return jsonify({
            "error": "系统维护中",
            "message": "API暂时不可用，请稍后重试"
        }), 503
    
    logger.info("🆘 紧急模式应用已启动")

# 导出应用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
    
    try:
        with open('/Users/jyxc-dz-0100299/claude-2/0802/emergency_vercel_app.py', 'w', encoding='utf-8') as f:
            f.write(emergency_content)
        print("✅ 紧急版本已创建: emergency_vercel_app.py")
        return True
    except Exception as e:
        print(f"❌ 创建紧急版本失败: {e}")
        return False

def show_fix_instructions():
    """显示修复说明"""
    print("\n📋 紧急修复步骤")
    print("=" * 40)
    
    print("1. 如果是语法错误:")
    print("   - 检查最近修改的文件")
    print("   - 修复Python语法问题")
    print("   - 重新提交代码")
    
    print("\n2. 如果是导入错误:")
    print("   - 检查requirements.txt")
    print("   - 确保所有依赖都已安装")
    print("   - 可能需要回滚到之前版本")
    
    print("\n3. 如果是配置错误:")
    print("   - 检查vercel.json配置")
    print("   - 确认环境变量设置")
    print("   - 验证数据库连接")
    
    print("\n4. 紧急恢复方案:")
    print("   - 使用emergency_vercel_app.py作为临时入口")
    print("   - 回滚到最后一个稳定提交")
    print("   - 联系Vercel技术支持")

def main():
    """主检查函数"""
    print("🚨 FitLife 紧急故障排查")
    print("=" * 60)
    
    checks = [
        ("关键文件完整性", check_critical_files),
        ("Python语法检查", check_syntax_errors),
        ("应用启动测试", check_app_startup)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            if not result:
                print(f"❌ {check_name} 发现问题!")
        except Exception as e:
            print(f"❌ {check_name} 检查异常: {e}")
            results.append((check_name, False))
    
    # 检查结果
    failed_checks = [name for name, result in results if not result]
    
    if failed_checks:
        print(f"\n🚨 发现 {len(failed_checks)} 个问题:")
        for check in failed_checks:
            print(f"   ❌ {check}")
        
        # 创建紧急版本
        create_emergency_vercel_app()
    else:
        print("\n✅ 所有基础检查通过")
        print("问题可能在Vercel部署层面")
    
    # 显示最近更改
    check_recent_changes()
    
    # 显示修复指南
    show_fix_instructions()

if __name__ == '__main__':
    main()