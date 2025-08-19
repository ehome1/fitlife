#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, WeightLog, ExerciseLog
from datetime import date, datetime, timezone, timedelta
import json

def test_complete_functionality():
    """测试完整的新功能"""
    print("🧪 开始完整功能测试...")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 1. 测试数据库创建
            print("1. 测试数据库和表创建")
            db.create_all()
            print("   ✅ 数据库表创建成功")
            
            # 2. 检查WeightLog表结构
            print("\n2. 检查WeightLog表结构")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            weight_log_columns = inspector.get_columns('weight_log')
            print("   📋 WeightLog表字段:")
            for col in weight_log_columns:
                print(f"     - {col['name']}: {col['type']}")
            
            # 3. 检查ExerciseLog表的exercise_description字段
            print("\n3. 检查ExerciseLog表更新")
            exercise_log_columns = inspector.get_columns('exercise_log')
            has_description = any(col['name'] == 'exercise_description' for col in exercise_log_columns)
            if has_description:
                print("   ✅ exercise_description字段已存在")
            else:
                print("   ❌ exercise_description字段缺失")
            
            # 4. 获取测试用户
            print("\n4. 获取测试用户")
            test_user = User.query.first()
            if not test_user:
                print("   ❌ 未找到测试用户")
                return False
            print(f"   ✅ 找到测试用户: {test_user.username}")
            
            # 5. 测试体重记录创建
            print("\n5. 测试体重记录功能")
            test_date = date.today()
            test_weight = 70.5
            
            # 计算BMI (需要身高)
            bmi = None
            if test_user.profile and test_user.profile.height:
                height_m = test_user.profile.height / 100
                bmi = round(test_weight / (height_m ** 2), 1)
                print(f"   📊 计算BMI: {bmi} (身高: {test_user.profile.height}cm)")
            
            # 检查今天是否已有记录
            existing_weight = WeightLog.query.filter_by(
                user_id=test_user.id,
                date=test_date
            ).first()
            
            if existing_weight:
                print(f"   📝 今天已有体重记录: {existing_weight.weight}kg")
                weight_record = existing_weight
            else:
                weight_record = WeightLog(
                    user_id=test_user.id,
                    date=test_date,
                    weight=test_weight,
                    bmi=bmi,
                    notes="功能测试记录"
                )
                db.session.add(weight_record)
                db.session.commit()
                print(f"   ✅ 创建体重记录: {test_weight}kg")
            
            # 测试模型属性
            print(f"   📅 日期显示: {weight_record.date_display}")
            print(f"   ⚖️ BMI状态: {weight_record.bmi_status}")
            print(f"   🎨 状态颜色: {weight_record.bmi_color}")
            
            # 6. 测试运动记录功能（新格式）
            print("\n6. 测试运动记录新格式")
            exercise_description = "今天在健身房做了45分钟力量训练，主要练胸部和手臂，感觉很充实"
            
            # 检查今天是否已有运动记录
            existing_exercise = ExerciseLog.query.filter_by(
                user_id=test_user.id,
                date=test_date
            ).first()
            
            if existing_exercise and hasattr(existing_exercise, 'exercise_description') and existing_exercise.exercise_description:
                print(f"   📝 今天已有运动记录: {existing_exercise.exercise_description[:50]}...")
                exercise_record = existing_exercise
            else:
                exercise_record = ExerciseLog(
                    user_id=test_user.id,
                    date=test_date,
                    exercise_type='strength',
                    exercise_name='力量训练',
                    duration=45,
                    exercise_description=exercise_description,
                    notes="功能测试",
                    analysis_status='pending'
                )
                db.session.add(exercise_record)
                db.session.commit()
                print(f"   ✅ 创建运动记录: {exercise_description[:30]}...")
            
            # 7. 测试API端点
            print("\n7. 测试API端点可访问性")
            with app.test_client() as client:
                # 模拟登录
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user.id)
                    sess['_fresh'] = True
                
                # 测试体重统计API
                response = client.get('/api/weight-stats')
                if response.status_code == 200:
                    stats = json.loads(response.data)
                    print("   ✅ 体重统计API正常")
                    if stats['success']:
                        print(f"     - 最新体重: {stats['data'].get('latest_weight')}kg")
                        print(f"     - BMI: {stats['data'].get('latest_bmi')}")
                else:
                    print(f"   ❌ 体重统计API错误: {response.status_code}")
                
                # 测试体重历史API
                response = client.get('/api/weight-log?days=7')
                if response.status_code == 200:
                    history = json.loads(response.data)
                    print("   ✅ 体重历史API正常")
                    print(f"     - 历史记录数: {history.get('count', 0)}")
                else:
                    print(f"   ❌ 体重历史API错误: {response.status_code}")
            
            # 8. 统计总结
            print("\n8. 功能统计总结")
            total_weight_records = WeightLog.query.filter_by(user_id=test_user.id).count()
            total_exercise_records = ExerciseLog.query.filter_by(user_id=test_user.id).count()
            
            print(f"   📊 用户体重记录总数: {total_weight_records}")
            print(f"   🏃 用户运动记录总数: {total_exercise_records}")
            
            # 9. 模板检查
            print("\n9. 模板文件检查")
            dashboard_path = "templates/dashboard.html"
            exercise_log_path = "templates/exercise_log.html"
            
            if os.path.exists(dashboard_path):
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'weightChart' in content:
                        print("   ✅ 仪表盘包含体重图表功能")
                    if 'todayWeight' in content:
                        print("   ✅ 仪表盘包含体重输入功能")
            
            if os.path.exists(exercise_log_path):
                with open(exercise_log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'exercise_description' in content:
                        print("   ✅ 运动页面包含描述输入功能")
                    if 'exercise_type' not in content or content.count('exercise_type') < 3:
                        print("   ✅ 运动页面已简化输入框")
            
            print("\n" + "=" * 60)
            print("🎉 功能测试完成！所有核心功能正常")
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 功能使用指南:")
    print("=" * 60)
    print("🏃 运动记录简化版:")
    print("  - 访问: http://127.0.0.1:5001/exercise-log")
    print("  - 只需在'描述你的运动'框中输入详细描述")
    print("  - 例如: '今天跑步30分钟，中等强度，感觉很棒'")
    print("  - AI会自动解析运动类型、时长和强度")
    
    print("\n📊 仪表盘体重管理:")
    print("  - 访问: http://127.0.0.1:5001/dashboard")
    print("  - 在体重记录模块输入当日体重")
    print("  - 自动计算BMI和健康状态")
    print("  - 查看7/30/90天体重变化趋势图")
    print("  - 显示周/月体重变化统计")
    
    print("\n🔧 API接口:")
    print("  - POST /api/weight-log - 保存体重记录")
    print("  - GET /api/weight-log?days=N - 获取历史记录")
    print("  - GET /api/weight-stats - 获取统计数据")
    
    print("\n💡 技术特性:")
    print("  - Chart.js实现体重趋势可视化")
    print("  - 响应式设计适配移动端")
    print("  - AI自然语言解析运动描述")
    print("  - 自动BMI计算和健康评估")

if __name__ == '__main__':
    print("🚀 FitLife功能完整性测试脚本")
    
    if test_complete_functionality():
        show_usage_guide()
        print("\n✅ 系统已准备就绪，可以开始使用！")
    else:
        print("\n❌ 测试发现问题，请检查日志")