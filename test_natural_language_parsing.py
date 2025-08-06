#!/usr/bin/env python3
"""
自然语言饮食解析功能测试脚本
验证Gemini AI能否正确解析自然语言描述的食物
"""
import sys
from app import app, parse_natural_language_food

def test_natural_language_parsing():
    """测试自然语言解析功能"""
    print("🧪 测试自然语言饮食解析功能")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "description": "早餐吃了一个苹果，一盒蒙牛牛奶，两片全麦面包",
            "meal_type": "breakfast",
            "expected_foods": ["苹果", "牛奶", "面包"]
        },
        {
            "description": "午餐有一碗白米饭，一盘青椒炒肉丝，一个煎蛋",
            "meal_type": "lunch", 
            "expected_foods": ["米饭", "炒肉丝", "煎蛋"]
        },
        {
            "description": "晚餐喝了一碗小米粥，吃了三个小笼包，还有一盘凉拌黄瓜",
            "meal_type": "dinner",
            "expected_foods": ["小米粥", "小笼包", "凉拌黄瓜"]
        },
        {
            "description": "下午茶时间吃了两块奥利奥饼干，喝了一杯咖啡",
            "meal_type": "snack",
            "expected_foods": ["饼干", "咖啡"]
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    with app.app_context():
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}:")
            print(f"描述: {test_case['description']}")
            print(f"餐次: {test_case['meal_type']}")
            
            try:
                # 调用解析函数
                result = parse_natural_language_food(
                    test_case['description'], 
                    test_case['meal_type']
                )
                
                if result['success']:
                    print("✅ 解析成功!")
                    print(f"置信度: {result['confidence']}")
                    print("解析出的食物:")
                    
                    parsed_food_names = []
                    for food in result['food_items']:
                        food_info = f"  - {food['name']} × {food['amount']}{food['unit']}"
                        if 'estimated_weight' in food:
                            food_info += f" (约{food['estimated_weight']}g)"
                        print(food_info)
                        parsed_food_names.append(food['name'])
                    
                    # 检查是否包含预期的食物
                    expected_found = 0
                    for expected in test_case['expected_foods']:
                        found = any(expected in food_name for food_name in parsed_food_names)
                        if found:
                            expected_found += 1
                    
                    accuracy = expected_found / len(test_case['expected_foods'])
                    print(f"准确性: {accuracy:.1%} ({expected_found}/{len(test_case['expected_foods'])})")
                    
                    if accuracy >= 0.6:  # 60%以上准确率算通过
                        passed += 1
                        print("🎉 测试通过!")
                    else:
                        print("⚠️ 准确率偏低")
                
                else:
                    print(f"❌ 解析失败: {result.get('error', '未知错误')}")
                
                if result.get('notes'):
                    print(f"注意事项: {result['notes']}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {e}")
    
    print(f"\n📊 测试总结:")
    print(f"通过: {passed}/{total} ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 所有测试通过！自然语言解析功能正常")
        return True
    elif passed >= total * 0.7:
        print("✅ 大部分测试通过，功能基本正常")
        return True
    else:
        print("⚠️ 测试通过率较低，需要优化解析算法")
        return False

def test_edge_cases():
    """测试边缘情况"""
    print("\n🔍 测试边缘情况")
    print("=" * 30)
    
    edge_cases = [
        "没吃什么，就喝了点水",
        "今天吃得很少，只有半个苹果",
        "火锅，各种蔬菜和肉类",
        "一大盘意大利面配番茄酱"
    ]
    
    with app.app_context():
        for description in edge_cases:
            print(f"\n描述: {description}")
            try:
                result = parse_natural_language_food(description, "lunch")
                if result['success']:
                    print(f"✅ 解析成功，识别出{len(result['food_items'])}种食物")
                else:
                    print(f"❌ 解析失败: {result.get('error')}")
            except Exception as e:
                print(f"❌ 异常: {e}")

def main():
    """主测试函数"""
    print("🚀 FitLife 自然语言饮食解析测试")
    print("=" * 50)
    
    # 检查Gemini API配置
    import os
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️ GEMINI_API_KEY未配置，跳过API测试")
        return
    
    # 基础功能测试
    basic_success = test_natural_language_parsing()
    
    # 边缘情况测试
    test_edge_cases()
    
    print("\n" + "=" * 50)
    if basic_success:
        print("✅ 自然语言解析功能测试完成，系统准备就绪！")
        sys.exit(0)
    else:
        print("⚠️ 部分功能需要优化")
        sys.exit(1)

if __name__ == "__main__":
    main()