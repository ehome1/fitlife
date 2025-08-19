#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime

def examine_meal_records():
    """检查最近的饮食记录，识别问题"""
    print("🔍 检查饮食记录数据库...")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('instance/fitness_app.db')
        cursor = conn.cursor()
        
        # 获取最近5条记录
        cursor.execute("""
            SELECT id, user_id, date, meal_type, food_name, food_description, 
                   calories, protein, carbs, fat, meal_score, analysis_result,
                   created_at
            FROM meal_log 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("❌ 没有找到任何饮食记录")
            return
            
        print(f"📊 找到 {len(records)} 条最近的饮食记录:")
        print("="*80)
        
        zero_calorie_count = 0
        valid_calorie_count = 0
        
        for i, record in enumerate(records, 1):
            (id, user_id, date, meal_type, food_name, food_description, 
             calories, protein, carbs, fat, meal_score, analysis_result, created_at) = record
            
            print(f"\n记录 {i} (ID: {id}):")
            print(f"  用户ID: {user_id}")
            print(f"  日期: {date}")
            print(f"  餐次: {meal_type}")
            print(f"  食物名称: {food_name}")
            print(f"  食物描述: {food_description}")
            print(f"  热量: {calories} kcal")
            print(f"  蛋白质: {protein} g")
            print(f"  碳水: {carbs} g")
            print(f"  脂肪: {fat} g")
            print(f"  膳食评分: {meal_score}")
            print(f"  创建时间: {created_at}")
            
            # 检查analysis_result
            if analysis_result:
                try:
                    analysis_data = json.loads(analysis_result)
                    basic_nutrition = analysis_data.get('basic_nutrition', {})
                    api_calories = basic_nutrition.get('total_calories', 'N/A')
                    print(f"  AI分析热量: {api_calories} kcal")
                    
                    if api_calories and api_calories > 0:
                        print(f"  ✅ AI分析正常")
                    else:
                        print(f"  ❌ AI分析热量为空或0")
                        
                except json.JSONDecodeError:
                    print(f"  ❌ AI分析结果JSON解析失败")
                except Exception as e:
                    print(f"  ❌ AI分析结果处理错误: {e}")
            else:
                print(f"  ❌ 无AI分析结果")
            
            # 统计
            if calories and calories > 0:
                valid_calorie_count += 1
            else:
                zero_calorie_count += 1
            
            print("-" * 60)
        
        print(f"\n📈 统计分析:")
        print(f"  有效热量记录: {valid_calorie_count} 条")
        print(f"  零热量记录: {zero_calorie_count} 条")
        print(f"  零热量比例: {zero_calorie_count / len(records) * 100:.1f}%")
        
        if zero_calorie_count > 0:
            print(f"\n❌ 发现 {zero_calorie_count} 条零热量记录!")
            print("这可能就是'AI营养分析打卡无效'的原因")
            print("\n🔍 可能的原因:")
            print("  1. Gemini API调用失败")
            print("  2. API返回数据格式错误")
            print("  3. JSON解析失败")
            print("  4. 数据库更新失败")
        else:
            print(f"\n✅ 所有记录都有有效热量数据")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

if __name__ == '__main__':
    examine_meal_records()