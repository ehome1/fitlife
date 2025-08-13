#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add current directory to path so we can import from app
sys.path.insert(0, '/Users/jyxc-dz-0100299/claude-2/0802')

from app import call_gemini_meal_analysis

def test_meal_analysis():
    """Test the meal analysis function directly"""
    print("🧪 Testing meal analysis function...")
    
    # Test parameters similar to what the form would send
    meal_type = 'breakfast'
    food_items = [{'name': '苹果', 'amount': 1, 'unit': '个'}]
    user_info = {
        'age': 30,
        'gender': '男',
        'weight': 70,
        'height': 175,
        'fitness_goal': 'maintain_weight'
    }
    food_description = "早餐吃了一个苹果"
    
    print(f"测试参数:")
    print(f"  餐次: {meal_type}")
    print(f"  食物项: {food_items}")
    print(f"  用户信息: {user_info}")
    print(f"  描述: {food_description}")
    print()
    
    try:
        print("🔄 调用AI分析...")
        result = call_gemini_meal_analysis(meal_type, food_items, user_info, food_description)
        
        print(f"✅ 分析完成!")
        print(f"结果类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"结果键: {list(result.keys())}")
            
            # 检查基础营养信息
            basic = result.get('basic_nutrition', {})
            if basic:
                print(f"🥗 基础营养信息:")
                print(f"  总热量: {basic.get('total_calories', 'N/A')}")
                print(f"  蛋白质: {basic.get('protein', 'N/A')}g")
                print(f"  碳水化合物: {basic.get('carbohydrates', 'N/A')}g")
                print(f"  脂肪: {basic.get('fat', 'N/A')}g")
            else:
                print("❌ 没有基础营养信息")
            
            # 检查膳食分析
            meal_analysis = result.get('meal_analysis', {})
            if meal_analysis:
                print(f"📊 膳食分析:")
                print(f"  膳食评分: {meal_analysis.get('meal_score', 'N/A')}")
                print(f"  平衡评级: {meal_analysis.get('balance_rating', 'N/A')}")
            else:
                print("❌ 没有膳食分析信息")
                
        else:
            print(f"❌ 结果格式错误: {result}")
            
    except Exception as e:
        import traceback
        print(f"❌ 测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_meal_analysis()