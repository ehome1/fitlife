#!/usr/bin/env python3
import os
import sys
import json
from datetime import date
from dotenv import load_dotenv
load_dotenv()

# Add current directory to path so we can import from app
sys.path.insert(0, '/Users/jyxc-dz-0100299/claude-2/0802')

from app import app, db, MealLog, User

def simulate_meal_submission():
    """Simulate a meal submission exactly like the form would do"""
    with app.app_context():
        print("🧪 模拟饮食提交流程...")
        
        # Get current user
        user = User.query.first()
        if not user:
            print("❌ 没有找到用户")
            return
            
        print(f"👤 当前用户: {user.username}")
        
        # Simulate form data
        meal_date = date.today()
        meal_type = 'breakfast'
        food_description = "早餐吃了一个苹果和一杯牛奶"
        notes = ""
        
        # No manual food items (using food_description only)
        food_items = []
        
        print(f"📝 提交数据:")
        print(f"  日期: {meal_date}")
        print(f"  餐次: {meal_type}")
        print(f"  描述: {food_description}")
        print(f"  手动食物项: {food_items}")
        
        # Simulate the form processing logic
        if food_description and not food_items:
            # Create a single food item from description
            food_items = [{
                'name': food_description[:100],
                'amount': 1,
                'unit': '份'
            }]
            
        print(f"🔄 处理后的食物项: {food_items}")
        
        # Create meal record (simulate backend logic)
        try:
            combined_notes = {'notes': notes}
            if food_description:
                combined_notes['original_description'] = food_description
                
            saved_entries = []
            for food_item in food_items:
                meal_log_entry = MealLog(
                    user_id=user.id,
                    date=meal_date,
                    meal_type=meal_type,
                    food_name=food_item.get('name', '未知食物'),
                    quantity=food_item.get('amount', 1),
                    amount=food_item.get('amount', 1),
                    unit=food_item.get('unit', '份'),
                    food_description=food_description,
                    calories=0,  # Initial value, will be updated by AI
                    analysis_result=combined_notes
                )
                db.session.add(meal_log_entry)
                saved_entries.append(meal_log_entry)
                
            db.session.commit()
            print(f"✅ 已创建 {len(saved_entries)} 条记录")
            
            # Get user profile for AI analysis
            user_profile = getattr(user, 'profile', None)
            if not user_profile:
                weight = 70
                height = 170
                age = 30
                gender = '未知'
                fitness_goal = 'maintain_weight'
            else:
                weight = user_profile.weight or 70
                height = user_profile.height or 170
                age = user_profile.age or 30
                gender = user_profile.gender or '未知'
                fitness_goal = getattr(user_profile, 'fitness_goals', 'maintain_weight')
                
            # Call AI analysis
            from app import call_gemini_meal_analysis
            
            print(f"🤖 开始AI分析...")
            analysis_result = call_gemini_meal_analysis(meal_type, food_items, {
                'age': age,
                'gender': gender,
                'weight': weight,
                'height': height,
                'fitness_goal': fitness_goal
            }, food_description)
            
            print(f"📊 AI分析结果: {'成功' if analysis_result else '失败'}")
            
            if analysis_result:
                basic_nutrition = analysis_result.get('basic_nutrition', {})
                total_calories = basic_nutrition.get('total_calories', 0)
                protein = basic_nutrition.get('protein', 0)
                carbs = basic_nutrition.get('carbohydrates', 0)
                fat = basic_nutrition.get('fat', 0)
                
                meal_analysis = analysis_result.get('meal_analysis', {})
                meal_score = meal_analysis.get('meal_score', 7)
                
                print(f"💡 营养信息:")
                print(f"  总热量: {total_calories}")
                print(f"  蛋白质: {protein}g")
                print(f"  碳水化合物: {carbs}g")  
                print(f"  脂肪: {fat}g")
                print(f"  膳食评分: {meal_score}")
                
                # Update nutrition data
                food_count = len(saved_entries)
                for entry in saved_entries:
                    entry.calories = int(total_calories / food_count) if food_count > 0 else total_calories
                    entry.protein = round(protein / food_count, 1) if food_count > 0 else protein
                    entry.carbs = round(carbs / food_count, 1) if food_count > 0 else carbs
                    entry.fat = round(fat / food_count, 1) if food_count > 0 else fat
                    entry.meal_score = meal_score
                    entry.analysis_result = analysis_result
                    
                db.session.commit()
                print(f"✅ 已更新营养数据")
                
                # Check the saved record
                saved_entry = saved_entries[0]
                print(f"\n🔍 验证保存的记录:")
                print(f"  ID: {saved_entry.id}")
                print(f"  数据库calories: {saved_entry.calories}")
                print(f"  total_calories属性: {saved_entry.total_calories}")
                print(f"  蛋白质: {saved_entry.protein}")
                print(f"  分析结果存在: {'是' if saved_entry.analysis_result else '否'}")
                
            else:
                print("❌ AI分析失败")
                
        except Exception as e:
            import traceback
            print(f"❌ 提交失败: {e}")
            print(f"错误详情: {traceback.format_exc()}")
            db.session.rollback()

if __name__ == "__main__":
    simulate_meal_submission()