#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, call_gemini_meal_analysis, User, MealLog

def test_ai_analysis():
    """测试AI营养分析功能"""
    print("🧪 开始测试AI营养分析功能...")
    
    with app.app_context():
        # 测试数据
        meal_type = 'lunch'
        food_items = [
            {'name': '米饭', 'amount': 1, 'unit': '碗'},
            {'name': '鸡胸肉', 'amount': 100, 'unit': '克'}
        ]
        user_info = {
            'age': 25,
            'gender': '男',
            'weight': 70,
            'height': 175,
            'fitness_goal': 'maintain_weight'
        }
        natural_language_input = "一碗米饭和100克鸡胸肉"
        
        print(f"测试参数:")
        print(f"  - meal_type: {meal_type}")
        print(f"  - food_items: {food_items}")
        print(f"  - natural_language_input: {natural_language_input}")
        print(f"  - user_info: {user_info}")
        
        try:
            # 调用AI分析
            result = call_gemini_meal_analysis(
                meal_type=meal_type,
                food_items=food_items,
                user_info=user_info,
                natural_language_input=natural_language_input
            )
            
            print(f"\n✅ AI分析完成!")
            print(f"结果类型: {type(result)}")
            
            if isinstance(result, dict):
                # 检查基础营养信息
                basic_nutrition = result.get('basic_nutrition', {})
                print(f"\n📊 基础营养信息:")
                print(f"  - 总热量: {basic_nutrition.get('total_calories', 'N/A')} kcal")
                print(f"  - 蛋白质: {basic_nutrition.get('protein', 'N/A')} g")
                print(f"  - 碳水化合物: {basic_nutrition.get('carbohydrates', 'N/A')} g")
                print(f"  - 脂肪: {basic_nutrition.get('fat', 'N/A')} g")
                
                # 检查膳食分析
                meal_analysis = result.get('meal_analysis', {})
                print(f"\n🍽️ 膳食分析:")
                print(f"  - 膳食评分: {meal_analysis.get('meal_score', 'N/A')}")
                print(f"  - 营养均衡评价: {meal_analysis.get('balance_rating', 'N/A')}")
                
                # 检查是否返回了有效的热量数据
                total_calories = basic_nutrition.get('total_calories', 0)
                if total_calories > 0:
                    print(f"\n✅ 热量分析正常: {total_calories} kcal")
                else:
                    print(f"\n❌ 热量分析异常: {total_calories}")
                    print("这可能是导致'AI营养分析打卡无效'的原因!")
            else:
                print(f"❌ 分析结果格式错误: {result}")
                
        except Exception as e:
            print(f"❌ AI分析测试失败: {e}")
            import traceback
            print(f"完整错误信息:\n{traceback.format_exc()}")

if __name__ == '__main__':
    test_ai_analysis()