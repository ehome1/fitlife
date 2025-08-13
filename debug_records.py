#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add current directory to path so we can import from app
sys.path.insert(0, '/Users/jyxc-dz-0100299/claude-2/0802')

from app import app, db, MealLog, User

def check_recent_records():
    """Check recent meal records and their calorie values"""
    with app.app_context():
        print("🔍 检查最近的饮食记录...")
        
        # Get current user (assume there's at least one user)
        users = User.query.all()
        if not users:
            print("❌ 没有找到用户")
            return
            
        user = users[0]  # Use first user
        print(f"👤 用户: {user.username} (ID: {user.id})")
        
        # Get recent meal records
        meals = MealLog.query.filter_by(user_id=user.id).order_by(MealLog.created_at.desc()).limit(10).all()
        
        if not meals:
            print("❌ 没有找到饮食记录")
            return
            
        print(f"\n📊 最近的 {len(meals)} 条记录:")
        print("-" * 80)
        
        for i, meal in enumerate(meals, 1):
            print(f"{i:2d}. ID: {meal.id}")
            print(f"     日期: {meal.date}")
            print(f"     餐次: {meal.meal_type_display}")
            print(f"     食物: {meal.food_name}")
            print(f"     数据库calories字段: {meal.calories}")
            print(f"     total_calories属性: {meal.total_calories}")
            print(f"     蛋白质: {meal.protein}")
            print(f"     碳水: {meal.carbs}")
            print(f"     脂肪: {meal.fat}")
            print(f"     膳食评分: {meal.meal_score}")
            print(f"     有analysis_result: {'是' if meal.analysis_result else '否'}")
            if meal.analysis_result and isinstance(meal.analysis_result, dict):
                basic = meal.analysis_result.get('basic_nutrition', {})
                if basic:
                    print(f"     analysis_result中的热量: {basic.get('total_calories', 'N/A')}")
            print(f"     创建时间: {meal.created_at}")
            print(f"     食物描述: {meal.food_description}")
            print()

if __name__ == "__main__":
    check_recent_records()