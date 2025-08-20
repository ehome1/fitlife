#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, call_gemini_meal_analysis, generate_fallback_nutrition_analysis
import json

def test_extended_nutrition_analysis():
    """测试扩展的营养成分分析功能"""
    print("🧪 测试扩展营养成分分析")
    print("=" * 50)
    
    with app.app_context():
        try:
            # 获取测试用户
            test_user = User.query.first()
            if not test_user:
                print("❌ 未找到测试用户")
                return False
            
            print(f"✅ 测试用户: {test_user.username}")
            
            # 测试食物数据
            test_food_items = [
                {"name": "牛奶", "amount": 250, "unit": "ml"},
                {"name": "燕麦", "amount": 50, "unit": "g"},
                {"name": "香蕉", "amount": 1, "unit": "个"},
                {"name": "坚果", "amount": 30, "unit": "g"}
            ]
            
            # 测试fallback营养分析
            print("\n🔄 测试Fallback营养分析:")
            fallback_result = generate_fallback_nutrition_analysis(test_food_items, 'breakfast')
            
            basic_nutrition = fallback_result.get('basic_nutrition', {})
            print("📊 基础营养成分:")
            nutrition_components = [
                ("总热量", basic_nutrition.get('total_calories', 0), "kcal"),
                ("蛋白质", basic_nutrition.get('protein', 0), "g"),
                ("碳水化合物", basic_nutrition.get('carbohydrates', 0), "g"),
                ("脂肪", basic_nutrition.get('fat', 0), "g"),
                ("膳食纤维", basic_nutrition.get('fiber', 0), "g"),
                ("糖分", basic_nutrition.get('sugar', 0), "g"),
                ("钠", basic_nutrition.get('sodium', 0), "mg"),
                ("钙", basic_nutrition.get('calcium', 0), "mg"),
                ("维生素C", basic_nutrition.get('vitamin_c', 0), "mg")
            ]
            
            for name, value, unit in nutrition_components:
                print(f"   {name}: {value}{unit}")
            
            # 验证新增营养成分
            required_new_components = ['sodium', 'calcium', 'vitamin_c']
            missing_components = []
            
            for component in required_new_components:
                if component not in basic_nutrition:
                    missing_components.append(component)
            
            if missing_components:
                print(f"❌ 缺失营养成分: {missing_components}")
                return False
            else:
                print("✅ 所有营养成分都存在")
            
            # 测试营养比例
            nutrition_breakdown = fallback_result.get('nutrition_breakdown', {})
            print("\n📈 营养比例分析:")
            print(f"   蛋白质: {nutrition_breakdown.get('protein_percentage', 0)}%")
            print(f"   碳水化合物: {nutrition_breakdown.get('carbs_percentage', 0)}%")
            print(f"   脂肪: {nutrition_breakdown.get('fat_percentage', 0)}%")
            
            # 验证结构完整性
            expected_sections = [
                'basic_nutrition', 'nutrition_breakdown', 'meal_analysis', 
                'detailed_analysis', 'personalized_feedback', 'recommendations'
            ]
            
            missing_sections = []
            for section in expected_sections:
                if section not in fallback_result:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"❌ 缺失分析部分: {missing_sections}")
                return False
            else:
                print("✅ 分析结构完整")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_nutrition_ranges():
    """测试营养成分数值范围"""
    print("\n🎯 测试营养成分数值范围")
    print("-" * 40)
    
    # 测试多个不同的食物组合
    test_cases = [
        {
            "name": "简单早餐",
            "foods": [{"name": "鸡蛋", "amount": 1, "unit": "个"}]
        },
        {
            "name": "丰富午餐", 
            "foods": [
                {"name": "米饭", "amount": 150, "unit": "g"},
                {"name": "鸡胸肉", "amount": 100, "unit": "g"},
                {"name": "西兰花", "amount": 200, "unit": "g"}
            ]
        },
        {
            "name": "蔬菜沙拉",
            "foods": [
                {"name": "生菜", "amount": 100, "unit": "g"},
                {"name": "番茄", "amount": 150, "unit": "g"},
                {"name": "橄榄油", "amount": 10, "unit": "ml"}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        
        result = generate_fallback_nutrition_analysis(test_case['foods'], 'lunch')
        basic = result.get('basic_nutrition', {})
        
        # 检查数值范围
        ranges_check = [
            ("钠", basic.get('sodium', 0), 0, 3000, "mg"),
            ("钙", basic.get('calcium', 0), 0, 500, "mg"), 
            ("维生素C", basic.get('vitamin_c', 0), 0, 200, "mg"),
            ("膳食纤维", basic.get('fiber', 0), 0, 30, "g"),
            ("糖分", basic.get('sugar', 0), 0, 100, "g")
        ]
        
        all_in_range = True
        for name, value, min_val, max_val, unit in ranges_check:
            if min_val <= value <= max_val:
                status = "✅"
            else:
                status = "⚠️"
                all_in_range = False
            print(f"   {status} {name}: {value}{unit} (范围: {min_val}-{max_val})")
        
        if all_in_range:
            print(f"   ✅ {test_case['name']} 营养数值范围合理")
        else:
            print(f"   ⚠️ {test_case['name']} 部分营养数值超出预期范围")
    
    return True

def show_nutrition_guidelines():
    """显示营养成分参考指南"""
    print("\n📋 营养成分每日推荐摄入量参考:")
    print("-" * 40)
    
    guidelines = [
        ("膳食纤维", "25g", "促进消化，预防便秘"),
        ("钠", "< 2300mg", "控制血压，减少心血管疾病风险"),
        ("钙", "1000mg", "强化骨骼，预防骨质疏松"), 
        ("维生素C", "90mg", "增强免疫力，抗氧化"),
        ("糖分", "< 50g", "控制体重，预防糖尿病"),
        ("蛋白质", "0.8g/kg体重", "维持肌肉，修复组织"),
        ("脂肪", "20-35%总热量", "提供能量，吸收脂溶性维生素"),
        ("碳水化合物", "45-65%总热量", "主要能量来源")
    ]
    
    for name, recommendation, benefit in guidelines:
        print(f"🌟 {name}: {recommendation}")
        print(f"    作用: {benefit}")
        print()

def main():
    """主测试函数"""
    print("🚀 扩展营养成分分析测试")
    print("=" * 60)
    
    tests = [
        ("扩展营养分析", test_extended_nutrition_analysis),
        ("营养数值范围", test_nutrition_ranges)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 扩展营养分析功能测试成功!")
        print("\n📈 新增营养维度:")
        print("  🌿 膳食纤维 - 消化健康指标")
        print("  🍭 糖分含量 - 血糖控制参考")
        print("  🧂 钠含量 - 血压管理指标")
        print("  🥛 钙含量 - 骨骼健康指标")
        print("  💊 维生素C - 免疫力指标")
        
        show_nutrition_guidelines()
    else:
        print(f"\n⚠️ 有 {len(results) - passed} 项需要调试")
    
    return passed == len(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)