from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time
import hashlib
# PostgreSQL支持 - 无需特殊配置

# 加载环境变量
load_dotenv()

# 配置 Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 简单的内存缓存用于AI分析结果
ai_analysis_cache = {}

app = Flask(__name__)

# 配置根据环境变量设置
if os.getenv('VERCEL') or os.getenv('DATABASE_URL'):
    # 生产环境配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-production-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['DEBUG'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
else:
    # 开发环境配置
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_app.db'
    app.config['DEBUG'] = True

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 移除CSP限制以确保所有JavaScript功能正常
@app.after_request
def after_request(response):
    # 完全禁用CSP限制
    response.headers.pop('Content-Security-Policy', None)
    # 添加其他有用的安全头
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # 首先尝试加载普通用户
    user = User.query.get(int(user_id))
    if user:
        return user
    
    # 如果不是普通用户，尝试加载管理员用户
    admin = AdminUser.query.get(int(user_id))
    if admin:
        return admin
    
    return None

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    goals = db.relationship('FitnessGoal', backref='user', cascade='all, delete-orphan')
    exercise_logs = db.relationship('ExerciseLog', backref='user', cascade='all, delete-orphan')
    meal_logs = db.relationship('MealLog', backref='user', cascade='all, delete-orphan')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    height = db.Column(db.Float)  # cm
    weight = db.Column(db.Float)  # kg
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    activity_level = db.Column(db.String(20))  # sedentary, lightly_active, moderately_active, very_active
    bmr = db.Column(db.Float)  # 基础代谢率
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class FitnessGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)  # weight_loss, muscle_gain, fitness_improvement
    current_weight = db.Column(db.Float, nullable=False)
    target_weight = db.Column(db.Float)
    target_date = db.Column(db.Date, nullable=False)
    weekly_weight_change = db.Column(db.Float)  # kg per week
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    @property
    def goal_type_display(self):
        type_map = {
            'weight_loss': '减脂塑形',
            'muscle_gain': '增肌增重',
            'fitness_improvement': '提升体能',
            'maintain_health': '保持健康'
        }
        return type_map.get(self.goal_type, self.goal_type)

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    exercise_type = db.Column(db.String(50), nullable=False)  # cardio, strength, yoga, sports
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    intensity = db.Column(db.String(20))  # low, medium, high
    calories_burned = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def exercise_type_display(self):
        type_map = {
            'cardio': '有氧运动',
            'strength': '力量训练',
            'yoga': '瑜伽',
            'sports': '球类运动',
            'walking': '步行',
            'running': '跑步',
            'cycling': '骑行',
            'swimming': '游泳'
        }
        return type_map.get(self.exercise_type, self.exercise_type)
    
    @property
    def intensity_display(self):
        intensity_map = {
            'low': '低强度',
            'medium': '中等强度',
            'high': '高强度'
        }
        return intensity_map.get(self.intensity, self.intensity)

class MealLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # grams
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float)  # grams
    carbs = db.Column(db.Float)  # grams
    fat = db.Column(db.Float)  # grams
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def meal_type_display(self):
        type_map = {
            'breakfast': '早餐',
            'lunch': '午餐',
            'dinner': '晚餐',
            'snack': '加餐'
        }
        return type_map.get(self.meal_type, self.meal_type)
    
    @property
    def meal_type_color(self):
        color_map = {
            'breakfast': 'warning',
            'lunch': 'success',
            'dinner': 'primary',
            'snack': 'info'
        }
        return color_map.get(self.meal_type, 'secondary')

# 后台管理系统数据模型
class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)

class PromptTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # exercise, food
    prompt_content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def type_display(self):
        return '运动分析' if self.type == 'exercise' else '饮食分析'

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('profile_setup'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        age = int(request.form['age'])
        gender = request.form['gender']
        activity_level = request.form['activity_level']
        
        # 计算BMR (基础代谢率)
        if gender == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        profile = UserProfile(
            user_id=current_user.id,
            height=height,
            weight=weight,
            age=age,
            gender=gender,
            activity_level=activity_level,
            bmr=bmr
        )
        db.session.add(profile)
        db.session.commit()
        
        return redirect(url_for('goal_setup'))
    
    return render_template('profile_setup.html')

@app.route('/goal-setup', methods=['GET', 'POST'])
@login_required
def goal_setup():
    if request.method == 'POST':
        goal_type = request.form['goal_type']
        current_weight = float(request.form['current_weight'])
        target_weight = float(request.form['target_weight'])
        weeks = int(request.form['weeks'])
        
        target_date = datetime.now().date() + timedelta(weeks=weeks)
        weekly_weight_change = (target_weight - current_weight) / weeks
        
        goal = FitnessGoal(
            user_id=current_user.id,
            goal_type=goal_type,
            current_weight=current_weight,
            target_weight=target_weight,
            target_date=target_date,
            weekly_weight_change=weekly_weight_change
        )
        db.session.add(goal)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    return render_template('goal_setup.html')

def calculate_smart_intensity_and_calories(exercise_type, duration, weight):
    """智能计算运动强度和消耗的卡路里"""
    # 智能MET配置表
    met_config = {
        'cardio': {'base': 7.0, 'low_threshold': 20, 'high_threshold': 45},
        'strength': {'base': 6.0, 'low_threshold': 15, 'high_threshold': 60},
        'yoga': {'base': 3.0, 'low_threshold': 30, 'high_threshold': 90},
        'sports': {'base': 8.0, 'low_threshold': 30, 'high_threshold': 60},
        'walking': {'base': 4.5, 'low_threshold': 30, 'high_threshold': 60},
        'running': {'base': 11.0, 'low_threshold': 20, 'high_threshold': 40},
        'cycling': {'base': 8.0, 'low_threshold': 30, 'high_threshold': 60},
        'swimming': {'base': 8.0, 'low_threshold': 20, 'high_threshold': 45}
    }
    
    config = met_config.get(exercise_type, {'base': 6.0, 'low_threshold': 30, 'high_threshold': 60})
    
    # 根据时长自动判断强度
    if duration < config['low_threshold']:
        met = config['base'] * 0.8
        intensity = 'low'
    elif duration > config['high_threshold']:
        met = config['base'] * 1.3
        intensity = 'high'
    else:
        met = config['base']
        intensity = 'medium'
    
    # 卡路里 = MET × 体重(kg) × 时间(小时)
    calories = met * weight * (duration / 60)
    return round(calories), intensity

def call_gemini_api_with_retry(prompt, max_retries=3, base_delay=1):
    """调用Gemini API并处理重试逻辑"""
    
    # 检查API密钥
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY环境变量未设置")
        raise Exception("AI服务配置错误：API密钥未设置")
    
    logger.info(f"使用Gemini API密钥: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning(f"Gemini返回空响应 (尝试 {attempt + 1})")
                raise Exception("API返回空响应")
                
            logger.info(f"Gemini API调用成功 (尝试 {attempt + 1})")
            return response.text.strip()
        
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Gemini API调用失败 (尝试 {attempt + 1}/{max_retries}): {error_str}")
            
            # 检查是否是速率限制错误
            if "500" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 指数退避
                    logger.info(f"检测到速率限制，等待 {delay} 秒后重试...")
                    time.sleep(delay)
                    continue
            
            # 对于其他错误或最后一次尝试，抛出异常
            if attempt == max_retries - 1:
                raise e
    
    raise Exception("API调用失败，已达到最大重试次数")

def analyze_food_with_ai(food_description):
    """使用Gemini AI分析食物描述，返回营养信息"""
    # 输入验证和清理
    if not food_description or not food_description.strip():
        raise ValueError("食物描述不能为空")
    
    # 清理和标准化输入
    cleaned_description = food_description.strip()[:500]  # 限制长度
    
    # 生成缓存键
    cache_key = hashlib.md5(f"food_{cleaned_description.lower()}".encode()).hexdigest()
    
    # 检查缓存
    if cache_key in ai_analysis_cache:
        logger.info("使用缓存的食物分析结果")
        return ai_analysis_cache[cache_key]
    
    try:
        # 构建增强的提示词
        prompt = f"""
你是一位专业的中国营养师和健康顾问，精通中式菜肴和食材。请仔细分析以下食物描述，提供精确的营养信息和专业评估。

食物描述：{cleaned_description}

分析任务：
1. 识别所有具体食物和烹饪方式
2. 估算准确的份量（参考中式餐具：一碗约250ml，一盘约300g等）
3. 基于《中国食物成分表》提供营养数据
4. 考虑烹饪方式对营养的影响（炒、煮、蒸、炸等）

请严格按照以下JSON格式返回，不要包含任何其他文字：

{{
    "total_calories": 总热量数字（单位kcal，整数）,
    "total_protein": 总蛋白质数字（单位g，保留1位小数）,
    "total_carbs": 总碳水化合物数字（单位g，保留1位小数）,
    "total_fat": 总脂肪数字（单位g，保留1位小数）,
    "food_items": ["具体食物名称(估算份量)", "食物2(份量)", ...],
    "health_score": 健康评分数字（1-10分，10分最健康）,
    "nutrition_balance": {{
        "protein_level": "充足|适中|不足",
        "carbs_level": "充足|适中|不足|过量", 
        "fat_level": "充足|适中|不足|过量",
        "fiber_rich": true或false,
        "vitamin_rich": true或false
    }},
    "health_highlights": ["营养优势1", "营养优势2"],
    "health_concerns": ["注意事项1", "注意事项2"],
    "suggestions": ["改善建议1", "改善建议2"],
    "meal_type_suitable": ["早餐", "午餐", "晚餐", "加餐"]中的一个或多个,
    "analysis_note": "简要分析总结"
}}

重要提示：
- 如果描述模糊，基于最可能的中式菜肴进行合理推测
- 常见份量参考：一碗米饭150g，一盘青菜200g，一块肉50-100g
- 考虑油盐糖等调料的热量贡献
- 优先识别主食、蛋白质、蔬菜的具体种类和用量
"""
        
        # 使用重试逻辑调用API
        response_text = call_gemini_api_with_retry(prompt)
        
        # 尝试提取JSON部分
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            json_text = response_text[json_start:json_end].strip()
        elif '{' in response_text and '}' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_text = response_text[json_start:json_end]
        else:
            json_text = response_text
        
        # 解析JSON
        analysis_result = json.loads(json_text)
        
        # 验证并设置默认值
        result = {
            'total_calories': int(analysis_result.get('total_calories', 300)),
            'total_protein': round(float(analysis_result.get('total_protein', 15)), 1),
            'total_carbs': round(float(analysis_result.get('total_carbs', 40)), 1),
            'total_fat': round(float(analysis_result.get('total_fat', 10)), 1),
            'food_items': analysis_result.get('food_items', ['混合食物(估算)']),
            'health_score': int(analysis_result.get('health_score', 6)),
            'nutrition_balance': analysis_result.get('nutrition_balance', {
                'protein_level': '适中',
                'carbs_level': '适中', 
                'fat_level': '适中',
                'fiber_rich': False,
                'vitamin_rich': False
            }),
            'health_highlights': analysis_result.get('health_highlights', ['提供基础能量']),
            'health_concerns': analysis_result.get('health_concerns', ['注意营养均衡']),
            'suggestions': analysis_result.get('suggestions', ['搭配蔬菜水果']),
            'meal_type_suitable': analysis_result.get('meal_type_suitable', ['午餐', '晚餐']),
            'analysis_note': analysis_result.get('analysis_note', 'AI分析完成')
        }
        
        # 缓存结果（限制缓存大小）
        if len(ai_analysis_cache) < 100:  # 最多缓存100个结果
            ai_analysis_cache[cache_key] = result
            logger.info("食物分析结果已缓存")
        
        return result
        
    except Exception as e:
        logger.error(f"食物AI分析失败: {str(e)}")
        error_msg = "AI分析暂时不可用"
        if "rate" in str(e).lower() or "quota" in str(e).lower():
            error_msg = "AI服务繁忙，请稍后重试"
        elif "500" in str(e):
            error_msg = "AI服务暂时不可用"
        
        # 如果AI分析失败，返回基本估算
        return {
            'total_calories': 300,
            'total_protein': 15.0,
            'total_carbs': 40.0,
            'total_fat': 10.0,
            'food_items': ['混合食物(估算)'],
            'health_score': 5,
            'nutrition_balance': {
                'protein_level': '适中',
                'carbs_level': '适中', 
                'fat_level': '适中',
                'fiber_rich': False,
                'vitamin_rich': False
            },
            'health_highlights': ['提供基础能量'],
            'health_concerns': [error_msg + '，建议手动评估'],
            'suggestions': ['搭配蔬菜水果，保持营养均衡'],
            'meal_type_suitable': ['午餐', '晚餐'],
            'analysis_note': f'{error_msg}，使用默认估算'
        }

def analyze_exercise_with_ai(exercise_type, exercise_name, duration, user_profile):
    """使用Gemini AI分析运动，结合用户个人信息给出专业建议"""
    # 生成缓存键（包含用户特征）
    cache_key = hashlib.md5(f"exercise_{exercise_type}_{exercise_name}_{duration}_{user_profile.gender}_{user_profile.age}_{user_profile.weight}".encode()).hexdigest()
    
    # 检查缓存
    if cache_key in ai_analysis_cache:
        logger.info("使用缓存的运动分析结果")
        return ai_analysis_cache[cache_key]
    
    try:
        # 构建包含个人信息的提示词
        prompt = f"""
作为一名专业的运动健身教练和运动生理学专家，请分析以下运动信息，结合用户的个人资料，提供详细的运动分析和专业建议。请以JSON格式返回结果，不要包含其他文字。

用户个人信息：
- 年龄：{user_profile.age}岁
- 性别：{'男性' if user_profile.gender == 'male' else '女性'}
- 身高：{user_profile.height}cm
- 体重：{user_profile.weight}kg
- 活动水平：{user_profile.activity_level}
- 基础代谢率：{user_profile.bmr:.0f} kcal/天

运动信息：
- 运动类型：{exercise_type}
- 具体运动：{exercise_name}
- 运动时长：{duration}分钟

请按照以下JSON格式返回：
{{
    "calories_burned": 数字（消耗的卡路里，基于用户体重等精确计算）,
    "intensity_level": "低强度|中等强度|高强度",
    "fitness_score": 数字（本次运动的健身评分，1-10分），
    "exercise_analysis": {{
        "heart_rate_zone": "有氧区间|无氧区间|脂肪燃烧区间|极限区间",
        "primary_benefits": ["主要益处1", "主要益处2", ...],
        "muscle_groups": ["主要锻炼肌群1", "主要锻炼肌群2", ...],
        "energy_system": "有氧系统|无氧糖酵解|磷酸肌酸系统|混合系统"
    }},
    "personalized_feedback": {{
        "suitable_level": "非常适合|适合|略有挑战|过于激烈",
        "age_considerations": "基于年龄的特别建议",
        "gender_considerations": "基于性别的特别建议",
        "fitness_level_match": "与当前活动水平的匹配度分析"
    }},
    "recommendations": {{
        "next_workout": "下次训练建议",
        "intensity_adjustment": "强度调整建议",
        "duration_suggestion": "时长建议",
        "recovery_advice": "恢复建议",
        "progression_tips": "进阶训练建议"
    }},
    "health_alerts": ["健康提醒1", "健康提醒2", ...],
    "weekly_goal_progress": "对每周运动目标的评估",
    "motivation_message": "个性化的激励信息"
}}

分析要求：
1. 基于用户的年龄、性别、体重精确计算卡路里消耗
2. 考虑用户的活动水平评估运动强度适宜性
3. 根据BMR和运动强度给出个性化建议
4. 提供专业的运动生理学分析
5. 考虑性别和年龄特点给出针对性建议
6. 评估运动与用户健身目标的匹配度
7. 提供安全、科学的训练建议
8. 激励用户坚持运动并逐步提升
"""
        
        # 使用重试逻辑调用API
        response_text = call_gemini_api_with_retry(prompt)
        
        # 尝试提取JSON部分
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            json_text = response_text[json_start:json_end].strip()
        elif '{' in response_text and '}' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_text = response_text[json_start:json_end]
        else:
            json_text = response_text
        
        # 解析JSON
        analysis_result = json.loads(json_text)
        
        # 验证并设置默认值
        result = {
            'calories_burned': int(analysis_result.get('calories_burned', 200)),
            'intensity_level': analysis_result.get('intensity_level', '中等强度'),
            'fitness_score': int(analysis_result.get('fitness_score', 7)),
            'exercise_analysis': analysis_result.get('exercise_analysis', {
                'heart_rate_zone': '有氧区间',
                'primary_benefits': ['提高心肺功能'],
                'muscle_groups': ['全身肌群'],
                'energy_system': '有氧系统'
            }),
            'personalized_feedback': analysis_result.get('personalized_feedback', {
                'suitable_level': '适合',
                'age_considerations': '适合当前年龄段',
                'gender_considerations': '符合性别特点',
                'fitness_level_match': '与活动水平匹配'
            }),
            'recommendations': analysis_result.get('recommendations', {
                'next_workout': '保持当前强度',
                'intensity_adjustment': '可适当增加强度',
                'duration_suggestion': '保持当前时长',
                'recovery_advice': '充分休息',
                'progression_tips': '逐步增加难度'
            }),
            'health_alerts': analysis_result.get('health_alerts', ['注意适度运动']),
            'weekly_goal_progress': analysis_result.get('weekly_goal_progress', '进度良好'),
            'motivation_message': analysis_result.get('motivation_message', '坚持就是胜利！')
        }
        
        # 缓存结果（限制缓存大小）
        if len(ai_analysis_cache) < 100:  # 最多缓存100个结果
            ai_analysis_cache[cache_key] = result
            logger.info("运动分析结果已缓存")
        
        return result
        
    except Exception as e:
        logger.error(f"运动AI分析失败: {str(e)}")
        error_msg = "AI分析暂时不可用"
        if "rate" in str(e).lower() or "quota" in str(e).lower():
            error_msg = "AI服务繁忙，请稍后重试"
        elif "500" in str(e):
            error_msg = "AI服务暂时不可用"
        
        # 如果AI分析失败，返回基本估算
        return {
            'calories_burned': 200,
            'intensity_level': '中等强度',
            'fitness_score': 6,
            'exercise_analysis': {
                'heart_rate_zone': '有氧区间',
                'primary_benefits': ['提高体能'],
                'muscle_groups': ['全身肌群'],
                'energy_system': '有氧系统'
            },
            'personalized_feedback': {
                'suitable_level': '适合',
                'age_considerations': error_msg,
                'gender_considerations': error_msg,
                'fitness_level_match': error_msg
            },
            'recommendations': {
                'next_workout': '继续保持',
                'intensity_adjustment': '根据感觉调整',
                'duration_suggestion': '循序渐进',
                'recovery_advice': '充分休息',
                'progression_tips': '持之以恒'
            },
            'health_alerts': [error_msg + '，建议咨询专业教练'],
            'weekly_goal_progress': '请继续努力',
            'motivation_message': '每一次运动都是进步！'
        }

@app.route('/exercise-log', methods=['GET', 'POST'])
@login_required
def exercise_log():
    if request.method == 'POST':
        exercise_date_str = request.form['exercise_date']
        exercise_type = request.form['exercise_type']
        exercise_name = request.form['exercise_name']
        duration = int(request.form['duration'])
        notes = request.form.get('notes', '')
        
        # 解析日期
        try:
            exercise_date = datetime.strptime(exercise_date_str, '%Y-%m-%d').date()
        except ValueError:
            exercise_date = datetime.now().date()
        
        # 使用AI分析运动（如果用户有个人资料）
        if current_user.profile:
            ai_analysis = analyze_exercise_with_ai(exercise_type, exercise_name, duration, current_user.profile)
            calories_burned = ai_analysis['calories_burned']
            intensity = ai_analysis['intensity_level']
        else:
            # 备用计算方法
            weight = 70  # 默认体重
            calories_burned, intensity = calculate_smart_intensity_and_calories(exercise_type, duration, weight)
        
        exercise_log = ExerciseLog(
            user_id=current_user.id,
            date=exercise_date,
            exercise_type=exercise_type,
            exercise_name=exercise_name,
            duration=duration,
            intensity=intensity,
            calories_burned=calories_burned,
            notes=notes
        )
        
        db.session.add(exercise_log)
        db.session.commit()
        
        flash(f'运动记录已保存！消耗了 {calories_burned} 卡路里')
        return redirect(url_for('exercise_log'))
    
    # 获取最近的运动记录
    recent_exercises = ExerciseLog.query.filter_by(
        user_id=current_user.id
    ).order_by(ExerciseLog.created_at.desc()).limit(10).all()
    
    return render_template('exercise_log.html', recent_exercises=recent_exercises)

@app.route('/meal-log', methods=['GET', 'POST'])
@login_required
def meal_log():
    if request.method == 'POST':
        meal_date_str = request.form['meal_date']
        meal_type = request.form['meal_type']
        food_description = request.form['food_description']
        
        # AI分析结果
        total_calories = int(request.form.get('total_calories', 0))
        total_protein = float(request.form.get('total_protein', 0))
        total_carbs = float(request.form.get('total_carbs', 0))
        total_fat = float(request.form.get('total_fat', 0))
        food_items = request.form.get('food_items', '')
        
        # 解析日期
        try:
            meal_date = datetime.strptime(meal_date_str, '%Y-%m-%d').date()
        except ValueError:
            meal_date = datetime.now().date()
        
        meal_log = MealLog(
            user_id=current_user.id,
            date=meal_date,
            meal_type=meal_type,
            food_name=food_items or food_description[:50],  # 使用AI识别的食物或描述前50字符
            quantity=0,  # 不再使用具体重量
            calories=total_calories,
            protein=total_protein,
            carbs=total_carbs,
            fat=total_fat
        )
        
        db.session.add(meal_log)
        db.session.commit()
        
        flash(f'饮食记录已保存！摄入了 {total_calories} 卡路里')
        return redirect(url_for('meal_log'))
    
    # 获取最近的饮食记录
    recent_meals = MealLog.query.filter_by(
        user_id=current_user.id
    ).order_by(MealLog.created_at.desc()).limit(10).all()
    
    return render_template('meal_log.html', recent_meals=recent_meals)

@app.route('/api/analyze-food', methods=['POST'])
@login_required
def api_analyze_food():
    """API端点：使用AI分析食物描述"""
    try:
        data = request.get_json()
        food_description = data.get('food_description', '').strip()
        
        if not food_description:
            return jsonify({'error': '食物描述不能为空'}), 400
        
        # 调用AI分析函数
        analysis_result = analyze_food_with_ai(food_description)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except ValueError as e:
        logger.warning(f"API输入验证错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API分析错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '分析失败，请稍后重试'
        }), 500

@app.route('/test-ai', methods=['POST', 'GET'])
def test_ai_endpoint():
    """测试AI分析端点（无需登录）"""
    if request.method == 'GET':
        return '''
        <h1>AI食物分析测试</h1>
        <form method="post">
        <textarea name="food_description" placeholder="描述食物，如：一碗白米饭，两个煎蛋"></textarea><br>
        <button type="submit">分析</button>
        </form>
        '''
    
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
            food_description = data.get('food_description', '').strip()
        else:
            food_description = request.form.get('food_description', '').strip()
        
        if not food_description:
            return jsonify({'error': '食物描述不能为空'}), 400
        
        # 调用AI分析函数
        analysis_result = analyze_food_with_ai(food_description)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        print(f"测试API分析错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析失败：{str(e)}'
        }), 500

@app.route('/api/analyze-exercise', methods=['POST'])
@login_required
def api_analyze_exercise():
    """API端点：使用AI分析运动"""
    try:
        data = request.get_json()
        exercise_type = data.get('exercise_type', '').strip()
        exercise_name = data.get('exercise_name', '').strip()
        duration = int(data.get('duration', 0))
        
        if not all([exercise_type, exercise_name, duration]):
            return jsonify({'error': '运动信息不完整'}), 400
        
        if not current_user.profile:
            return jsonify({'error': '请先完善个人资料'}), 400
        
        # 调用AI分析函数
        analysis_result = analyze_exercise_with_ai(exercise_type, exercise_name, duration, current_user.profile)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        print(f"运动API分析错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '分析失败，请稍后重试'
        }), 500

@app.route('/api/nutrition-trends', methods=['GET'])
@login_required
def api_nutrition_trends():
    """API端点：获取营养趋势数据"""
    try:
        range_type = request.args.get('range', 'week')
        
        if range_type == 'week':
            # 获取本周数据（过去7天）
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=6)
            
            meals = MealLog.query.filter(
                MealLog.user_id == current_user.id,
                MealLog.date >= start_date,
                MealLog.date <= end_date
            ).all()
            
            # 按日期汇总数据
            daily_data = {}
            for i in range(7):
                date = start_date + timedelta(days=i)
                daily_data[date.strftime('%Y-%m-%d')] = {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0
                }
            
            for meal in meals:
                date_str = meal.date.strftime('%Y-%m-%d')
                if date_str in daily_data:
                    daily_data[date_str]['calories'] += meal.calories or 0
                    daily_data[date_str]['protein'] += meal.protein or 0
                    daily_data[date_str]['carbs'] += meal.carbs or 0
                    daily_data[date_str]['fat'] += meal.fat or 0
            
            labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            calories_data = []
            for i in range(7):
                date = start_date + timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                calories_data.append(daily_data[date_str]['calories'])
            
        elif range_type == 'month':
            # 获取本月数据（按周汇总）
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date.replace(day=1)
            
            meals = MealLog.query.filter(
                MealLog.user_id == current_user.id,
                MealLog.date >= start_date,
                MealLog.date <= end_date
            ).all()
            
            # 按周汇总数据
            weekly_data = {'第1周': 0, '第2周': 0, '第3周': 0, '第4周': 0}
            for meal in meals:
                day_of_month = meal.date.day
                week_num = min((day_of_month - 1) // 7 + 1, 4)
                weekly_data[f'第{week_num}周'] += meal.calories or 0
            
            labels = ['第1周', '第2周', '第3周', '第4周']
            calories_data = [weekly_data[label] for label in labels]
            
        else:  # history
            # 获取历史数据（过去6个月）
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=180)
            
            meals = MealLog.query.filter(
                MealLog.user_id == current_user.id,
                MealLog.date >= start_date,
                MealLog.date <= end_date
            ).all()
            
            # 按月汇总数据
            monthly_data = {}
            for i in range(6):
                date = end_date - timedelta(days=i*30)
                month_str = date.strftime('%m月')
                monthly_data[month_str] = 0
            
            for meal in meals:
                month_str = meal.date.strftime('%m月')
                if month_str in monthly_data:
                    monthly_data[month_str] += meal.calories or 0
            
            labels = []
            for i in range(6):
                date = end_date - timedelta(days=(5-i)*30)
                labels.append(date.strftime('%m月'))
            
            calories_data = [monthly_data.get(label, 0) for label in labels]
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'calories': calories_data
            }
        })
        
    except Exception as e:
        logger.error(f"营养趋势API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取趋势数据失败'
        }), 500

@app.route('/api/daily-nutrition', methods=['GET'])
@login_required
def api_daily_nutrition():
    """API端点：获取今日营养汇总"""
    try:
        today = datetime.now(timezone.utc).date()
        
        meals = MealLog.query.filter(
            MealLog.user_id == current_user.id,
            MealLog.date == today
        ).all()
        
        total_calories = sum(meal.calories or 0 for meal in meals)
        total_protein = sum(meal.protein or 0 for meal in meals)
        total_carbs = sum(meal.carbs or 0 for meal in meals)
        total_fat = sum(meal.fat or 0 for meal in meals)
        
        return jsonify({
            'success': True,
            'data': {
                'calories': total_calories,
                'protein': round(total_protein, 1),
                'carbs': round(total_carbs, 1),
                'fat': round(total_fat, 1)
            }
        })
        
    except Exception as e:
        logger.error(f"今日营养API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取今日营养数据失败'
        }), 500

@app.route('/progress')
@login_required
def progress():
    # 获取用户的历史数据
    exercises = ExerciseLog.query.filter_by(user_id=current_user.id).order_by(ExerciseLog.date).all()
    meals = MealLog.query.filter_by(user_id=current_user.id).order_by(MealLog.date).all()
    
    # 将数据转换为JSON可序列化的格式
    exercises_data = []
    for ex in exercises:
        exercises_data.append({
            'id': ex.id,
            'date': ex.date.strftime('%Y-%m-%d'),
            'exercise_type': ex.exercise_type,
            'exercise_name': ex.exercise_name,
            'duration': ex.duration,
            'intensity': ex.intensity,
            'calories_burned': ex.calories_burned or 0,
            'created_at': ex.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    meals_data = []
    for meal in meals:
        meals_data.append({
            'id': meal.id,
            'date': meal.date.strftime('%Y-%m-%d'),
            'meal_type': meal.meal_type,
            'food_name': meal.food_name,
            'quantity': meal.quantity,
            'calories': meal.calories,
            'protein': meal.protein or 0,
            'carbs': meal.carbs or 0,
            'fat': meal.fat or 0,
            'created_at': meal.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('progress.html', 
                         exercises=exercises, 
                         meals=meals,
                         exercises_data=exercises_data,
                         meals_data=meals_data)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/health')
def health_check():
    """系统健康检查API端点"""
    try:
        # 检查数据库连接
        user_count = User.query.count()
        exercise_count = ExerciseLog.query.count()
        meal_count = MealLog.query.count()
        
        # 检查AI API（简单测试）
        ai_status = 'available'
        try:
            test_model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            ai_status = 'unavailable'
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': {
                'status': 'connected',
                'users': user_count,
                'exercises': exercise_count,
                'meals': meal_count
            },
            'ai_service': {
                'status': ai_status,
                'cache_size': len(ai_analysis_cache)
            },
            'version': '2.0'
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/test')
def test():
    """测试页面，检查应用状态"""
    try:
        # 检查数据库连接
        user_count = User.query.count()
        exercise_count = ExerciseLog.query.count()
        meal_count = MealLog.query.count()
        
        status = {
            'app_status': 'running',
            'database': 'connected',
            'users': user_count,
            'exercises': exercise_count,
            'meals': meal_count,
            'tables_created': True,
            'cache_size': len(ai_analysis_cache)
        }
        
        return f"""
        <h1>🚀 FitLife 应用状态</h1>
        <ul>
            <li>应用状态: {status['app_status']}</li>
            <li>数据库: {status['database']}</li>
            <li>用户数: {status['users']}</li>
            <li>运动记录数: {status['exercises']}</li>
            <li>饮食记录数: {status['meals']}</li>
            <li>AI缓存项数: {status['cache_size']}</li>
        </ul>
        <p><a href="/health">API健康检查</a> | <a href="/">返回首页</a></p>
        """
    except Exception as e:
        return f"<h1>❌ 错误</h1><p>{str(e)}</p>"

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    
    # 获取今日运动记录
    today_exercises = ExerciseLog.query.filter_by(
        user_id=current_user.id, 
        date=today
    ).all()
    
    # 获取今日饮食记录
    today_meals = MealLog.query.filter_by(
        user_id=current_user.id, 
        date=today
    ).all()
    
    # 计算今日总消耗和摄入
    total_burned = sum(ex.calories_burned or 0 for ex in today_exercises)
    total_consumed = sum(meal.calories for meal in today_meals)
    
    # 获取用户资料和目标
    profile = current_user.profile
    active_goal = FitnessGoal.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    return render_template('dashboard.html', 
                         today_exercises=today_exercises,
                         today_meals=today_meals,
                         total_burned=total_burned,
                         total_consumed=total_consumed,
                         profile=profile,
                         active_goal=active_goal)

# ==================== 后台管理系统路由 ====================

@app.route('/admin')
def admin_index():
    """后台管理首页 - 无需登录验证"""
    # 统计数据
    user_count = User.query.count()
    exercise_count = ExerciseLog.query.count()
    meal_count = MealLog.query.count()
    try:
        active_users = User.query.join(ExerciseLog).distinct().count()
    except:
        active_users = 0
    
    return render_template('admin/dashboard.html',
                         user_count=user_count,
                         exercise_count=exercise_count,
                         meal_count=meal_count,
                         active_users=active_users)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        logger.info(f"管理员登录尝试: {username}")
        
        admin = AdminUser.query.filter_by(username=username, is_active=True).first()
        if admin:
            logger.info(f"找到管理员: {admin.username}, 角色: {admin.role}")
            if check_password_hash(admin.password_hash, password):
                admin.last_login = datetime.now(timezone.utc)
                db.session.commit()
                login_user(admin)
                logger.info(f"管理员 {username} 登录成功")
                return redirect(url_for('admin_index'))
            else:
                logger.warning(f"管理员 {username} 密码错误")
                flash('密码错误')
        else:
            logger.warning(f"管理员账户 {username} 不存在或未激活")
            flash('用户名不存在或账户未激活')
    
    return render_template('admin/login.html')

@app.route('/admin/users')
def admin_users():
    """用户管理 - 无需登录验证"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle')
def admin_toggle_user(user_id):
    """启用/禁用用户 - 无需登录验证"""
    user = User.query.get_or_404(user_id)
    # 这里可以添加用户启用/禁用逻辑
    flash(f'用户 {user.username} 状态已更新')
    return redirect(url_for('admin_users'))

@app.route('/admin/prompts')
def admin_prompts():
    """Prompt模板管理 - 无需登录验证"""
    prompts = PromptTemplate.query.order_by(PromptTemplate.updated_at.desc()).all()
    return render_template('admin/prompts.html', prompts=prompts)

@app.route('/admin/prompts/new', methods=['GET', 'POST'])
def admin_new_prompt():
    """创建新Prompt模板 - 无需登录验证"""
    if request.method == 'POST':
        name = request.form['name']
        prompt_type = request.form['type']
        content = request.form['content']
        
        prompt = PromptTemplate(
            name=name,
            type=prompt_type,
            prompt_content=content,
            created_by=1  # 默认管理员ID
        )
        db.session.add(prompt)
        db.session.commit()
        
        flash('Prompt模板创建成功')
        return redirect(url_for('admin_prompts'))
    
    return render_template('admin/prompt_form.html', prompt=None)

@app.route('/admin/prompts/<int:prompt_id>/edit', methods=['GET', 'POST'])
def admin_edit_prompt(prompt_id):
    """编辑Prompt模板 - 无需登录验证"""
    prompt = PromptTemplate.query.get_or_404(prompt_id)
    
    if request.method == 'POST':
        prompt.name = request.form['name']
        prompt.type = request.form['type']
        prompt.prompt_content = request.form['content']
        prompt.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('Prompt模板更新成功')
        return redirect(url_for('admin_prompts'))
    
    return render_template('admin/prompt_form.html', prompt=prompt)

@app.route('/admin/prompts/<int:prompt_id>/toggle')
def admin_toggle_prompt(prompt_id):
    """启用/禁用Prompt模板 - 无需登录验证"""
    prompt = PromptTemplate.query.get_or_404(prompt_id)
    prompt.is_active = not prompt.is_active
    prompt.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    status = '启用' if prompt.is_active else '禁用'
    flash(f'Prompt模板已{status}')
    return redirect(url_for('admin_prompts'))

@app.route('/admin/settings')
def admin_settings():
    """系统设置 - 无需登录验证"""
    settings = SystemSettings.query.all()
    cache_info = {
        'cache_size': len(ai_analysis_cache),
        'cache_keys': list(ai_analysis_cache.keys())[:5]  # 显示前5个缓存键
    }
    return render_template('admin/settings.html', settings=settings, cache_info=cache_info)

@app.route('/admin/cache/clear', methods=['POST'])
def admin_clear_cache():
    """清理AI分析缓存 - 无需登录验证"""
    global ai_analysis_cache
    cache_size = len(ai_analysis_cache)
    ai_analysis_cache.clear()
    logger.info(f"清理了AI缓存，共清理了{cache_size}个缓存项")
    flash(f'AI缓存已清理，共清理了{cache_size}个缓存项')
    return redirect(url_for('admin_settings'))

def create_default_admin():
    """创建默认管理员账号"""
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
        admin = AdminUser(
            username='admin',
            email='admin@fitlife.com',
            password_hash=generate_password_hash('admin123'),
            role='super_admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账号已创建: admin / admin123")

def create_default_prompts():
    """创建默认的Prompt模板"""
    # 运动分析模板
    exercise_prompt = PromptTemplate.query.filter_by(type='exercise', name='默认运动分析模板').first()
    if not exercise_prompt:
        exercise_content = """作为一名专业的运动健身教练和运动生理学专家，请分析以下运动信息，结合用户的个人资料，提供详细的运动分析和专业建议。请以JSON格式返回结果，不要包含其他文字。

用户个人信息：
- 年龄：{user_age}岁
- 性别：{user_gender}
- 身高：{user_height}cm
- 体重：{user_weight}kg
- 活动水平：{activity_level}
- 基础代谢率：{bmr} kcal/天

运动信息：
- 运动类型：{exercise_type}
- 具体运动：{exercise_name}
- 运动时长：{duration}分钟

请按照JSON格式返回详细的运动分析结果。"""
        
        exercise_prompt = PromptTemplate(
            name='默认运动分析模板',
            type='exercise',
            prompt_content=exercise_content,
            is_active=True,
            created_by=1
        )
        db.session.add(exercise_prompt)
    
    # 饮食分析模板
    food_prompt = PromptTemplate.query.filter_by(type='food', name='默认饮食分析模板').first()
    if not food_prompt:
        food_content = """作为一名专业的营养师和健康顾问，请深入分析以下食物描述，提供详细的营养信息和健康评估。请以JSON格式返回结果，不要包含其他文字。

食物描述：{food_description}

请按照JSON格式返回详细的营养分析结果。"""
        
        food_prompt = PromptTemplate(
            name='默认饮食分析模板',
            type='food',
            prompt_content=food_content,
            is_active=True,
            created_by=1
        )
        db.session.add(food_prompt)
    
    db.session.commit()
    print("默认Prompt模板已创建")

def init_database():
    """初始化数据库函数"""
    print("🚀 初始化数据库...")
    db.create_all()
    create_default_admin()
    create_default_prompts()

@app.route('/init-database')
def init_db_route():
    """手动初始化数据库的路由"""
    try:
        with app.app_context():
            # 删除所有表并重新创建
            db.drop_all()
            db.create_all()
            create_default_admin()
            create_default_prompts()
        return """
        <h1>✅ 数据库初始化成功！</h1>
        <p>FitLife数据库已成功创建和配置。</p>
        <p>默认管理员账户：admin / admin123</p>
        <p><a href="/">返回首页</a></p>
        <p><a href="/admin">访问管理后台</a></p>
        """, 200
    except Exception as e:
        return f"""
        <h1>❌ 数据库初始化失败</h1>
        <p>错误信息：{str(e)}</p>
        <p><a href="/">返回首页</a></p>
        """, 500

@app.route('/reset-database')
def reset_db_route():
    """完全重置数据库的路由"""
    try:
        with app.app_context():
            # 强制删除并重建所有表
            db.drop_all()
            db.create_all()
            create_default_admin()
            create_default_prompts()
        return """
        <h1>🔄 数据库重置成功！</h1>
        <p>所有数据表已重新创建，使用最新结构。</p>
        <p>默认管理员账户：admin / admin123</p>
        <p><a href="/">返回首页</a></p>
        <p><a href="/admin">访问管理后台</a></p>
        """, 200
    except Exception as e:
        return f"""
        <h1>❌ 数据库重置失败</h1>
        <p>错误信息：{str(e)}</p>
        <p><a href="/init-database">尝试初始化</a></p>
        """, 500

@app.route('/test-ai')
def test_ai():
    """测试AI分析功能"""
    try:
        # 清理缓存以测试最新逻辑
        ai_analysis_cache.clear()
        
        # 测试食物分析
        test_food = "一碗白米饭，一盘西红柿炒鸡蛋，一小碗紫菜蛋花汤"
        result = analyze_food_with_ai(test_food)
        
        return f"""
        <h1>🤖 AI功能测试</h1>
        <h2>测试食物：{test_food}</h2>
        <h3>分析结果：</h3>
        <pre>{json.dumps(result, ensure_ascii=False, indent=2)}</pre>
        <hr>
        <h3>功能说明：</h3>
        <ul>
            <li>✅ 使用Gemini-2.5-Flash模型</li>
            <li>✅ 中文食物识别优化</li>
            <li>✅ 精确营养成分计算</li>
            <li>✅ 中式份量估算</li>
        </ul>
        <p><a href="/">返回首页</a></p>
        <p><a href="/clear-cache">清除AI缓存</a></p>
        """, 200
    except Exception as e:
        return f"""
        <h1>❌ AI测试失败</h1>
        <p>错误信息：{str(e)}</p>
        <p>这可能是因为：</p>
        <ul>
            <li>GEMINI_API_KEY环境变量未设置</li>
            <li>API密钥无效</li>
            <li>网络连接问题</li>
            <li>API使用限制</li>
        </ul>
        <p><a href="/">返回首页</a></p>
        """, 500

@app.route('/clear-cache')
def clear_cache():
    """清除AI分析缓存"""
    try:
        cache_size = len(ai_analysis_cache)
        ai_analysis_cache.clear()
        return f"""
        <h1>🧹 缓存清理完成</h1>
        <p>已清除 {cache_size} 个缓存项</p>
        <p>下次AI分析将使用最新的算法和模型</p>
        <p><a href="/">返回首页</a></p>
        <p><a href="/test-ai">测试AI功能</a></p>
        """, 200
    except Exception as e:
        return f"缓存清理失败: {str(e)}", 500

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True)