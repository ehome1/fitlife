#!/usr/bin/env python3
"""
数据库初始化脚本
用于在生产环境中创建数据库表和初始数据
"""
import os
import sys
from app import app, db, AdminPrompt

def init_database():
    """初始化数据库表和基本数据"""
    print("🚀 开始初始化数据库...")
    
    with app.app_context():
        # 创建所有表
        print("📋 创建数据库表...")
        db.create_all()
        
        # 检查是否已有默认Prompt模板
        existing_prompts = AdminPrompt.query.count()
        if existing_prompts == 0:
            print("📝 创建默认AI Prompt模板...")
            
            # 创建默认饮食分析模板
            food_prompt = AdminPrompt(
                name="默认饮食分析模板",
                type="food",
                prompt_content="""作为一名专业的营养师和健康顾问，请分析以下食物描述，提供详细的营养分析和健康建议。请以JSON格式返回结果，不要包含其他文字。

食物描述：{food_description}

请按照以下JSON格式返回：
{
    "total_calories": 数字（总热量，单位kcal）,
    "total_protein": 数字（总蛋白质，单位g，保留1位小数）,
    "total_carbs": 数字（总碳水化合物，单位g，保留1位小数）,
    "total_fat": 数字（总脂肪，单位g，保留1位小数）,
    "food_items": ["食物1(份量)", "食物2(份量)", ...],
    "health_score": 数字（健康评分，1-10分，10分最健康）,
    "nutrition_balance": {
        "protein_level": "充足|适中|不足",
        "carbs_level": "充足|适中|不足|过量", 
        "fat_level": "充足|适中|不足|过量",
        "fiber_rich": true/false,
        "vitamin_rich": true/false
    },
    "health_highlights": ["营养亮点1", "营养亮点2", ...],
    "health_concerns": ["注意事项1", "注意事项2", ...],
    "suggestions": ["建议1", "建议2", ...],
    "meal_type_suitable": ["早餐", "午餐", "晚餐", "加餐"],
    "analysis_note": "简要的整体分析说明"
}

分析要求：
1. 根据常见食物的标准营养成分进行精确估算
2. 考虑中文描述中的份量词汇（如"一碗"、"两个"、"一杯"等）
3. 健康评分考虑：营养均衡性、加工程度、热量密度、维生素矿物质含量
4. 营养均衡分析要客观准确，考虑不同人群的营养需求
5. 健康亮点重点突出食物的营养优势
6. 健康顾虑指出可能的营养风险或改进空间
7. 建议要实用具体，帮助用户优化饮食
8. 适合餐次根据食物特点和营养构成判断""",
                is_active=True
            )
            
            # 创建默认运动分析模板
            exercise_prompt = AdminPrompt(
                name="默认运动分析模板",
                type="exercise", 
                prompt_content="""作为一名专业的运动健身教练和运动生理学专家，请分析以下运动信息，结合用户的个人资料，提供详细的运动分析和专业建议。请以JSON格式返回结果，不要包含其他文字。

用户个人信息：
- 年龄：{age}岁
- 性别：{gender}
- 身高：{height}cm
- 体重：{weight}kg
- 活动水平：{activity_level}
- 基础代谢率：{bmr} kcal/天

运动信息：
- 运动类型：{exercise_type}
- 具体运动：{exercise_name}
- 运动时长：{duration}分钟

请按照以下JSON格式返回：
{
    "calories_burned": 数字（消耗的卡路里，基于用户体重等精确计算）,
    "intensity_level": "低强度|中等强度|高强度",
    "fitness_score": 数字（本次运动的健身评分，1-10分）,
    "exercise_analysis": {
        "heart_rate_zone": "有氧区间|无氧区间|脂肪燃烧区间|极限区间",
        "primary_benefits": ["主要益处1", "主要益处2", ...],
        "muscle_groups": ["主要锻炼肌群1", "主要锻炼肌群2", ...],
        "energy_system": "有氧系统|无氧糖酵解|磷酸肌酸系统|混合系统"
    },
    "personalized_feedback": {
        "suitable_level": "非常适合|适合|略有挑战|过于激烈",
        "age_considerations": "基于年龄的特别建议",
        "improvement_suggestions": ["改进建议1", "改进建议2", ...]
    },
    "recommendations": {
        "next_workout": "下次训练建议",
        "recovery_time": "建议恢复时间（小时）",
        "progression": "训练进阶建议"
    }
}""",
                is_active=True
            )
            
            # 添加到数据库
            db.session.add(food_prompt)
            db.session.add(exercise_prompt)
            db.session.commit()
            
            print("✅ 默认Prompt模板创建完成")
        else:
            print("ℹ️ 发现现有Prompt模板，跳过创建")
        
        print("✅ 数据库初始化完成！")

if __name__ == "__main__":
    # 检查是否为生产环境
    if os.getenv('VERCEL') or os.getenv('DATABASE_URL'):
        print("🌐 检测到生产环境")
    else:
        print("💻 检测到开发环境")
    
    init_database()