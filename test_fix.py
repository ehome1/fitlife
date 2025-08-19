#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_fix():
    """测试仪表盘修复是否成功"""
    print("🧪 测试仪表盘修复...")
    
    try:
        from app import app, db, User
        
        with app.app_context():
            # 测试用户查询
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到用户")
                return False
            
            print(f"✅ 找到用户: {test_user.username}")
            
            # 测试仪表盘页面
            with app.test_client() as client:
                # 模拟登录
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # 测试仪表盘
                response = client.get('/dashboard')
                if response.status_code == 200:
                    print("✅ 仪表盘加载成功")
                    return True
                else:
                    print(f"❌ 仪表盘错误: {response.status_code}")
                    data = response.get_data(as_text=True)
                    print(f"错误详情: {data[:500]}")
                    return False
                    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 仪表盘修复验证")
    print("=" * 40)
    
    if test_dashboard_fix():
        print("\n🎉 修复成功！仪表盘现在可以正常访问了")
        print("访问地址: http://127.0.0.1:5001/dashboard")
    else:
        print("\n❌ 修复未完成，需要进一步调试")