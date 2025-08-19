#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, ExerciseLog, WeightLog
from datetime import date, datetime, timezone

def test_dashboard():
    """测试仪表盘能否正常加载"""
    print("🧪 测试仪表盘加载...")
    
    with app.app_context():
        try:
            # 获取测试用户
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到测试用户")
                return False
            
            print(f"✅ 找到测试用户: {test_user.username}")
            
            # 测试查询今日运动记录（这是导致错误的查询）
            today = date.today()
            exercise_query = ExerciseLog.query.filter_by(
                user_id=test_user.id
            ).filter(
                db.func.date(ExerciseLog.created_at) == today
            )
            
            today_exercises = exercise_query.all()
            print(f"✅ 成功查询今日运动记录: {len(today_exercises)}条")
            
            # 测试WeightLog表
            weight_logs = WeightLog.query.filter_by(user_id=test_user.id).limit(5).all()
            print(f"✅ 成功查询体重记录: {len(weight_logs)}条")
            
            # 模拟dashboard路由的关键查询
            with app.test_client() as client:
                # 模拟登录
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # 测试仪表盘页面
                response = client.get('/dashboard')
                if response.status_code == 200:
                    print("✅ 仪表盘页面加载成功")
                    return True
                else:
                    print(f"❌ 仪表盘加载失败，状态码: {response.status_code}")
                    print(f"错误信息: {response.data.decode('utf-8')[:500]}...")
                    return False
                    
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🚀 仪表盘加载测试")
    print("=" * 50)
    
    if test_dashboard():
        print("\n🎉 仪表盘测试通过！")
    else:
        print("\n❌ 仪表盘测试失败")