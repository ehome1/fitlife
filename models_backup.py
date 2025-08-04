#!/usr/bin/env python3
"""
备份当前模型定义
"""

# 当前的完整MealLog模型（v2.0）
FULL_MEALLOG_MODEL = """
class MealLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    
    # 原始输入信息 - V2.0 新增
    food_description = db.Column(db.Text)  # 用户输入的原始描述
    food_items_json = db.Column(db.JSON)  # AI识别的食物列表
    
    # 营养成分 (总计) - V2.0 新增
    total_calories = db.Column(db.Integer, nullable=False)
    total_protein = db.Column(db.Float)  # grams
    total_carbs = db.Column(db.Float)  # grams  
    total_fat = db.Column(db.Float)  # grams
    total_fiber = db.Column(db.Float)  # grams - 新增
    total_sodium = db.Column(db.Float)  # mg - 新增
    
    # AI分析结果 - V2.0 新增
    health_score = db.Column(db.Float)  # 1-10分
    meal_suitability = db.Column(db.String(100))  # 餐次适合度描述
    nutrition_highlights = db.Column(db.JSON)  # 营养亮点列表
    dietary_suggestions = db.Column(db.JSON)  # 饮食建议列表
    personalized_assessment = db.Column(db.Text)  # 个性化评估
    
    # 兼容性字段 (保持向后兼容)
    food_name = db.Column(db.String(100))  # 主要食物名称
    quantity = db.Column(db.Float)  # 总重量估算(grams)
    calories = db.Column(db.Integer)  # 等同于total_calories
    protein = db.Column(db.Float)  # 等同于total_protein
    carbs = db.Column(db.Float)  # 等同于total_carbs
    fat = db.Column(db.Float)  # 等同于total_fat
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
"""

# 生产数据库实际存在的字段（从错误推断）
PRODUCTION_MEALLOG_FIELDS = [
    'id',
    'user_id', 
    'date',
    'meal_type',
    'food_name',
    'calories',
    'protein',
    'carbs', 
    'fat',
    'created_at'
    # 可能还有 quantity, updated_at
]