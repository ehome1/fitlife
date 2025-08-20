#!/usr/bin/env python3

def test_bmi_calculation():
    """测试BMI计算公式"""
    print("🧮 BMI计算测试")
    print("=" * 40)
    
    test_cases = [
        {"weight": 70, "height_cm": 170, "expected_bmi": 24.2},
        {"weight": 60, "height_cm": 165, "expected_bmi": 22.0},
        {"weight": 80, "height_cm": 175, "expected_bmi": 26.1},
        {"weight": 65, "height_cm": 160, "expected_bmi": 25.4},
        {"weight": 55, "height_cm": 155, "expected_bmi": 22.9}
    ]
    
    print("BMI = 体重(kg) / (身高(m))²")
    print("标准分类:")
    print("- < 18.5: 偏瘦")
    print("- 18.5-24: 正常") 
    print("- 24-28: 偏胖")
    print("- ≥ 28: 肥胖")
    print()
    
    for i, case in enumerate(test_cases, 1):
        weight = case["weight"]
        height_cm = case["height_cm"]
        expected = case["expected_bmi"]
        
        # 使用应用中的计算方式
        height_m = height_cm / 100
        calculated_bmi = round(weight / (height_m ** 2), 1)
        
        # 分类
        if calculated_bmi < 18.5:
            status = '偏瘦'
        elif calculated_bmi < 24:
            status = '正常'
        elif calculated_bmi < 28:
            status = '偏胖'
        else:
            status = '肥胖'
        
        print(f"测试 {i}:")
        print(f"  体重: {weight}kg, 身高: {height_cm}cm")
        print(f"  计算: {weight} / ({height_m}²) = {calculated_bmi}")
        print(f"  预期: {expected}, 实际: {calculated_bmi}")
        print(f"  状态: {status}")
        print(f"  ✅ {'正确' if abs(calculated_bmi - expected) < 0.1 else '可能有误差'}")
        print()

def interactive_bmi_test():
    """交互式BMI计算测试"""
    print("🔧 交互式BMI计算器")
    print("输入您的数据来测试BMI计算:")
    
    try:
        weight = float(input("请输入体重(kg): "))
        height_cm = float(input("请输入身高(cm): "))
        
        if weight <= 0 or height_cm <= 0:
            print("❌ 输入数据无效")
            return
        
        height_m = height_cm / 100
        bmi = round(weight / (height_m ** 2), 1)
        
        if bmi < 18.5:
            status = '偏瘦'
            color = '蓝色'
        elif bmi < 24:
            status = '正常'
            color = '绿色'
        elif bmi < 28:
            status = '偏胖'
            color = '橙色'
        else:
            status = '肥胖'
            color = '红色'
        
        print()
        print(f"📊 计算结果:")
        print(f"BMI = {weight} / ({height_m}²) = {bmi}")
        print(f"状态: {status} ({color})")
        print()
        
        # 提供改进建议
        if bmi < 18.5:
            print("💡 建议: 适当增加营养摄入，增强体质")
        elif bmi >= 24:
            print("💡 建议: 适当控制饮食，增加运动")
        else:
            print("💡 建议: 保持当前良好状态")
            
    except ValueError:
        print("❌ 请输入有效的数字")
    except Exception as e:
        print(f"❌ 计算出错: {e}")

if __name__ == '__main__':
    test_bmi_calculation()
    print("\n" + "=" * 40)
    interactive_bmi_test()