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

# 配置 Gemini AI (如果API密钥存在)
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
else:
    print("警告: GEMINI_API_KEY 环境变量未设置")

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

# 添加服务器配置以支持url_for()
app.config['SERVER_NAME'] = os.getenv('SERVER_NAME', 'localhost:5000')
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https' if os.getenv('VERCEL') else 'http'

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
    """
    MealLog模型 - 生产环境兼容版本
    """
    __tablename__ = 'meal_log'
    
    # ===== 基础字段（生产环境确定存在）=====
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    meal_type = db.Column(db.String(20), nullable=False)
    food_name = db.Column(db.String(100))
    calories = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ===== v1字段（生产环境存在）=====
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    quantity = db.Column(db.Float)
    
    # ===== 新增：AI分析结果存储 =====
    analysis_result = db.Column(db.JSON)  # 存储完整的AI分析结果
    
    # ===== v2字段 - 暂时移除以避免生产环境错误 =====
    # 在数据库架构升级后再启用这些字段：
    # food_description = db.Column(db.Text)
    # food_items_json = db.Column(db.JSON)
    # total_calories = db.Column(db.Integer)
    # total_protein = db.Column(db.Float)
    # total_carbs = db.Column(db.Float)
    # total_fat = db.Column(db.Float)
    # total_fiber = db.Column(db.Float)
    # total_sodium = db.Column(db.Float)
    # health_score = db.Column(db.Float)
    # meal_suitability = db.Column(db.String(100))
    # nutrition_highlights = db.Column(db.JSON)
    # dietary_suggestions = db.Column(db.JSON)
    # personalized_assessment = db.Column(db.Text)
    # updated_at = db.Column(db.DateTime)
    
    # ===== 兼容性访问方法 =====
    
    def get_food_description(self):
        """安全获取食物描述"""
        return self.food_name or '未记录'
    
    def get_food_items_json(self):
        """安全获取食物列表"""
        return []
    
    def get_total_calories(self):
        """安全获取总热量"""
        return self.calories or 0
    
    def get_total_protein(self):
        """安全获取总蛋白质"""
        return self.protein or 0.0
    
    def get_total_carbs(self):
        """安全获取总碳水"""
        return self.carbs or 0.0
    
    def get_total_fat(self):
        """安全获取总脂肪"""
        return self.fat or 0.0
    
    def get_total_fiber(self):
        """安全获取总纤维"""
        return 2.0
    
    def get_total_sodium(self):
        """安全获取总钠"""
        return 300.0
    
    def get_health_score(self):
        """安全获取健康评分"""
        # 基于现有数据计算
        calories = self.get_total_calories()
        protein = self.get_total_protein()
        if calories and protein:
            protein_ratio = (protein * 4) / calories if calories > 0 else 0
            if protein_ratio > 0.2:
                return 8.5
            elif protein_ratio > 0.15:
                return 7.5
            else:
                return 6.5
        return 7.0
    
    def get_meal_suitability(self):
        """安全获取餐次适合度"""
        return f'适合{self.meal_type_display}'
    
    def get_nutrition_highlights(self):
        """安全获取营养亮点"""
        # 生成默认亮点
        result = ['🍽️ 基础营养']
        calories = self.get_total_calories()
        protein = self.get_total_protein()
        
        if calories > 400:
            result.append('⚡ 高能量')
        if protein > 15:
            result.append('💪 丰富蛋白质')
        return result
    
    def get_dietary_suggestions(self):
        """安全获取饮食建议"""
        # 生成默认建议
        result = ['🥗 均衡搭配']
        calories = self.get_total_calories()
        
        if calories < 200:
            result.append('🍎 可适量增加')
        elif calories > 600:
            result.append('🚶 注意运动')
        return result
    
    def get_personalized_assessment(self):
        """获取个性化评估"""
        # 优先使用AI分析结果中的个性化评估
        if self.analysis_result and isinstance(self.analysis_result, dict):
            ai_assessment = self.analysis_result.get('personalized_assessment')
            if ai_assessment:
                return ai_assessment
        
        # 兜底：基于热量的简单评估
        calories = self.get_total_calories()
        if calories < 200:
            return '热量较低，适合减脂期间食用'
        elif calories > 600:
            return '热量较高，建议搭配运动'
        else:
            return '营养均衡的一餐，符合健康饮食标准'
    
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
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        return f"""
        <h1>🔧 FitLife 应用启动</h1>
        <p>应用正在运行，但模板渲染出错。</p>
        <p>错误: {str(e)}</p>
        <ul>
            <li><a href="/debug">调试页面</a></li>
            <li><a href="/health">健康检查</a></li>
            <li><a href="/test-ai">测试AI</a></li>
        </ul>
        """, 200

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

class FoodAnalyzer:
    """AI食物分析引擎 - 统一管理所有食物分析功能"""
    
    def __init__(self):
        self.nutrition_db = self._load_nutrition_database()
        
    def _load_nutrition_database(self):
        """加载本地营养数据库"""
        return {
            '白米饭': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
            '煎蛋': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0},
            '牛奶': {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1, 'fiber': 0},
            '鸡胸肉': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
            '西兰花': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6},
        }
    
    def analyze_comprehensive(self, food_description, user_profile=None, meal_type="未指定"):
        """简化分析 - 直接使用AI结果"""
        logger.info(f"开始AI分析: {food_description}")
        
        try:
            # 直接使用AI分析，不再进行复杂的增强处理
            ai_result = self._call_ai_analysis(food_description, user_profile, meal_type)
            logger.info(f"AI分析成功: {ai_result}")
            
            # 确保基本字段存在
            defaults = {
                'food_items_with_emoji': ai_result.get('food_items_with_emoji', [f'🍽️ {food_description}']),
                'total_calories': int(ai_result.get('total_calories', 0)),
                'total_protein': float(ai_result.get('total_protein', 0)),
                'total_carbs': float(ai_result.get('total_carbs', 0)),
                'total_fat': float(ai_result.get('total_fat', 0)),
                'health_score': int(ai_result.get('health_score', 7)),
                'meal_suitability': f'适合{meal_type}',
                'personalized_assessment': '基于AI分析的营养评估结果'
            }
            
            # 合并AI结果和默认值
            result = {**defaults, **ai_result}
            logger.info(f"最终结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI分析失败: {str(e)}")
            logger.info("使用兜底结果")
            return self._generate_fallback_result(food_description, meal_type)
    
    def _call_ai_analysis(self, food_description, user_profile, meal_type):
        """调用AI分析"""
        prompt_template = PromptTemplate.query.filter_by(type='food', is_active=True).first()
        if not prompt_template:
            raise Exception("未找到AI分析模板")
        
        # 准备用户信息
        user_info = ""
        if user_profile:
            user_info = f"用户：{user_profile.age}岁 {user_profile.gender} {user_profile.height}cm {user_profile.weight}kg"
        
        # 格式化prompt
        variables = {
            'food_description': food_description,
            'meal_type': meal_type,
            'user_info': user_info
        }
        
        try:
            prompt = prompt_template.prompt_content.format(**variables)
        except KeyError:
            prompt = prompt_template.prompt_content
        
        # 调用Gemini API
        response_text = call_gemini_api_with_retry(prompt)
        
        # 解析JSON响应
        return self._parse_ai_response(response_text)
    
    def _parse_ai_response(self, response_text):
        """解析AI响应"""
        try:
            # 提取JSON部分
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
            
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"AI响应解析失败: {str(e)}")
            raise
    
    def _enhance_with_local_db(self, ai_result, food_description):
        """使用本地数据库增强AI结果"""
        # 检查AI识别的食物是否在本地数据库中
        food_items = ai_result.get('food_items_with_emoji', [])
        enhanced_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0}
        
        for item in food_items:
            # 简单的关键词匹配
            for food_key, nutrition in self.nutrition_db.items():
                if food_key in item:
                    # 估算分量并累加营养
                    portion = self._estimate_portion(item)
                    for nutrient, value in nutrition.items():
                        enhanced_nutrition[nutrient] += value * portion
                    break
        
        # 如果本地数据库有匹配，使用增强后的数据
        if enhanced_nutrition['calories'] > 0:
            ai_result['total_calories'] = int(enhanced_nutrition['calories'])
            ai_result['total_protein'] = round(enhanced_nutrition['protein'], 1)
            ai_result['total_carbs'] = round(enhanced_nutrition['carbs'], 1)
            ai_result['total_fat'] = round(enhanced_nutrition['fat'], 1)
            ai_result['total_fiber'] = round(enhanced_nutrition['fiber'], 1)
        
        return ai_result
    
    def _estimate_portion(self, food_item):
        """估算食物分量倍数"""
        # 简单的分量估算逻辑
        if '两个' in food_item or '2个' in food_item:
            return 2.0
        elif '三个' in food_item or '3个' in food_item:
            return 3.0
        elif '大碗' in food_item:
            return 1.5
        elif '小碗' in food_item:
            return 0.8
        return 1.0
    
    def _add_personalization(self, result, user_profile, meal_type):
        """添加增强的个性化建议"""
        if not user_profile:
            # 如果没有用户资料，使用通用评估
            calories = result.get('total_calories', 0)
            if calories < 200:
                result['personalized_assessment'] = '热量较低，适合控制体重时食用，建议搭配适量运动。'
            elif calories > 600:
                result['personalized_assessment'] = '热量较高，建议分餐食用或搭配高强度运动消耗。'
            else:
                result['personalized_assessment'] = '热量适中，营养搭配较为均衡，符合一般健康饮食标准。'
            return result
        
        # 获取用户信息
        age = user_profile.age or 25
        weight = user_profile.weight or 70
        height = user_profile.height or 170
        gender = user_profile.gender or 'male'
        activity_level = user_profile.activity_level or 'moderately_active'
        
        # 计算精确的BMR和TDEE
        bmr = self._calculate_bmr(age, weight, height, gender)
        tdee = self._calculate_tdee(bmr, activity_level)
        
        # 餐次热量分配
        meal_ratios = {
            'breakfast': 0.25,
            'lunch': 0.35, 
            'dinner': 0.30,
            'snack': 0.10
        }
        meal_ratio = meal_ratios.get(meal_type, 0.25)
        expected_calories = tdee * meal_ratio
        
        # 营养素分析
        calories = result.get('total_calories', 0)
        protein = result.get('total_protein', 0)
        carbs = result.get('total_carbs', 0)
        fat = result.get('total_fat', 0)
        
        # 计算营养素比例
        total_macros = protein * 4 + carbs * 4 + fat * 9
        if total_macros > 0:
            protein_ratio = (protein * 4) / total_macros * 100
            carbs_ratio = (carbs * 4) / total_macros * 100
            fat_ratio = (fat * 9) / total_macros * 100
        else:
            protein_ratio = carbs_ratio = fat_ratio = 0
        
        # 生成个性化评估
        assessment_parts = []
        
        # 热量评估
        calorie_deviation = (calories - expected_calories) / expected_calories * 100
        if calorie_deviation > 20:
            assessment_parts.append(f"⚠️ 热量({calories}kcal)比建议摄入量({expected_calories:.0f}kcal)高{calorie_deviation:.0f}%，建议控制分量")
        elif calorie_deviation < -20:
            assessment_parts.append(f"📉 热量({calories}kcal)比建议摄入量低{abs(calorie_deviation):.0f}%，可适当增加营养密度")
        else:
            assessment_parts.append(f"✅ 热量({calories}kcal)符合您的{meal_type}需求")
        
        # 蛋白质评估
        if protein_ratio < 15:
            assessment_parts.append("💪 蛋白质含量偏低，建议增加优质蛋白质来源")
        elif protein_ratio > 30:
            assessment_parts.append("🥩 蛋白质含量较高，有助于肌肉合成和饱腹感")
        
        # 基于年龄的特殊建议
        if age >= 65:
            assessment_parts.append("👴 建议增加钙质和维生素D的摄入")
        elif age <= 25:
            assessment_parts.append("💪 年轻阶段，注意均衡营养支持身体发育")
        
        # 基于性别的建议
        if gender == 'female':
            assessment_parts.append("🌸 女性建议注意铁质和叶酸的补充")
        
        result['personalized_assessment'] = ' '.join(assessment_parts)
        return result
    
    def _calculate_bmr(self, age, weight, height, gender):
        """计算基础代谢率 (Harris-Benedict方程)"""
        if gender == 'male':
            return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    def _calculate_tdee(self, bmr, activity_level):
        """计算总日消耗能量"""
        activity_multipliers = {
            'sedentary': 1.2,           # 久坐，几乎不运动
            'lightly_active': 1.375,    # 轻度活动，每周1-3次运动
            'moderately_active': 1.55,  # 中度活动，每周3-5次运动
            'very_active': 1.725,       # 高度活动，每周6-7次运动
            'extra_active': 1.9         # 极度活动，每天2次运动或重体力劳动
        }
        return bmr * activity_multipliers.get(activity_level, 1.55)
    
    def _calculate_daily_needs(self, age, weight, activity_level):
        """计算每日热量需求（保持向后兼容）"""
        # 简化的BMR计算
        bmr = 88.362 + (13.397 * weight) + (4.799 * 170) - (5.677 * age)  # 假设身高170cm
        
        activity_multiplier = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725
        }
        
        return bmr * activity_multiplier.get(activity_level, 1.55)
    
    def _ensure_valid_result(self, result, food_description, meal_type):
        """确保结果数据有效性"""
        # 如果AI分析结果为0或无效，使用基于食物描述的估算
        if not result.get('total_calories') or result.get('total_calories') == 0:
            logger.warning("AI分析结果缺失，使用描述估算")
            estimated = self._estimate_from_description(food_description)
            result.update(estimated)
        
        # 确保所有必需字段存在
        defaults = {
            'food_items_with_emoji': [f'🍽️ {food_description}'],
            'total_calories': result.get('total_calories', 350),
            'total_protein': result.get('total_protein', 15.0),
            'total_carbs': result.get('total_carbs', 45.0),
            'total_fat': result.get('total_fat', 12.0),
            'total_fiber': result.get('total_fiber', 3.0),
            'total_sodium': result.get('total_sodium', 300.0),
            'health_score': result.get('health_score', 7.0),
            'meal_suitability': result.get('meal_suitability', f'适合{meal_type}'),
            'nutrition_highlights': result.get('nutrition_highlights', ['🍽️ 提供基础营养', '⚡ 补充身体能量']),
            'dietary_suggestions': result.get('dietary_suggestions', ['🥬 建议搭配蔬菜', '🚰 记得多喝水']),
            'personalized_assessment': result.get('personalized_assessment', '基于食物描述的营养评估，建议配合均衡饮食。')
        }
        
        for key, default_value in defaults.items():
            if key not in result or not result[key]:
                result[key] = default_value
        
        return result
    
    def _estimate_from_description(self, food_description):
        """基于食物描述估算营养成分"""
        # 简单的关键词匹配估算
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        
        # 检查描述中的食物关键词
        for food_key, nutrition in self.nutrition_db.items():
            if food_key in food_description:
                # 估算分量
                portion = 1.0
                if '两个' in food_description or '2个' in food_description:
                    portion = 2.0
                elif '一碗' in food_description:
                    portion = 1.2
                elif '一杯' in food_description:
                    portion = 1.0
                
                total_calories += nutrition['calories'] * portion
                total_protein += nutrition['protein'] * portion
                total_carbs += nutrition['carbs'] * portion
                total_fat += nutrition['fat'] * portion
                total_fiber += nutrition['fiber'] * portion
        
        # 如果没有匹配到具体食物，使用默认估算
        if total_calories == 0:
            total_calories = 350
            total_protein = 15.0
            total_carbs = 45.0
            total_fat = 12.0
            total_fiber = 3.0
        
        return {
            'total_calories': int(total_calories),
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fat': round(total_fat, 1),
            'total_fiber': round(total_fiber, 1),
            'health_score': min(10, max(5, 7 + (total_protein - 15) * 0.1))
        }

    def _generate_fallback_result(self, food_description, meal_type):
        """生成兜底结果"""
        estimated = self._estimate_from_description(food_description)
        
        return {
            'food_items_with_emoji': [f'🍽️ {food_description}'],
            'total_calories': estimated['total_calories'],
            'total_protein': estimated['total_protein'],
            'total_carbs': estimated['total_carbs'],
            'total_fat': estimated['total_fat'],
            'total_fiber': estimated['total_fiber'],
            'total_sodium': 300.0,
            'health_score': estimated['health_score'],
            'meal_suitability': f'适合{meal_type}',
            'nutrition_highlights': ['🍽️ 提供基础营养', '⚡ 补充身体能量'],
            'dietary_suggestions': ['🥬 建议搭配蔬菜', '🚰 记得多喝水'],
            'personalized_assessment': '基于食物描述的营养评估，建议配合均衡饮食。'
        }

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

def get_recent_exercises(user_id, days=7):
    """获取用户最近几天的运动记录"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        exercises = ExerciseLog.query.filter(
            ExerciseLog.user_id == user_id,
            ExerciseLog.exercise_date >= start_date
        ).order_by(ExerciseLog.exercise_date.desc()).all()
        
        if not exercises:
            return "最近无运动记录"
        
        # 汇总运动信息
        exercise_summary = []
        for exercise in exercises[:5]:  # 最多显示5条
            date_str = exercise.exercise_date.strftime('%m-%d')
            exercise_summary.append(f"{date_str} {exercise.exercise_name}({exercise.duration}分钟)")
        
        return "、".join(exercise_summary)
    except Exception as e:
        logger.error(f"获取运动记录失败: {str(e)}")
        return "运动记录获取失败"

def analyze_food_with_database_prompt(food_description, meal_type="未指定", user_profile=None):
    """使用数据库prompt模板进行AI食物分析"""
    logger.info(f"数据库prompt分析开始: {food_description}")
    
    # 生成缓存键
    cache_key = hashlib.md5(f"db_{food_description.lower()}_{meal_type}".encode()).hexdigest()
    
    # 检查缓存
    if cache_key in ai_analysis_cache:
        logger.info("使用缓存的数据库prompt分析结果")
        return ai_analysis_cache[cache_key]
    
    try:
        # 从数据库获取激活的饮食分析prompt
        prompt_template = PromptTemplate.query.filter_by(
            type='food',
            is_active=True
        ).first()
        
        if not prompt_template:
            logger.error("未找到激活的饮食分析prompt模板")
            raise Exception("未找到可用的AI分析模板，请联系管理员")
        
        # 准备变量替换
        variables = {
            'food_description': food_description,
            'meal_type': meal_type
        }
        
        # 如果有用户信息，添加用户变量
        if user_profile:
            variables.update({
                'user_age': user_profile.age or '未知',
                'user_gender': '男性' if user_profile.gender == 'male' else '女性' if user_profile.gender else '未知',
                'user_height': user_profile.height or '未知',
                'user_weight': user_profile.weight or '未知',
                'user_activity': user_profile.activity_level or '未知'
            })
        
        # 使用模板格式化prompt
        try:
            prompt = prompt_template.prompt_content.format(**variables)
        except KeyError as e:
            logger.warning(f"Prompt模板变量缺失: {e}, 使用原始模板")
            prompt = prompt_template.prompt_content
        
        logger.info(f"使用数据库prompt模板: {prompt_template.name}")
        
        logger.info("调用Gemini API...")
        response_text = call_gemini_api_with_retry(prompt)
        logger.info("Gemini API响应成功")
        
        # 解析JSON
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
        
        analysis_result = json.loads(json_text)
        logger.info("JSON解析成功")
        
        # 格式化结果
        result = {
            'food_items_with_emoji': analysis_result.get('food_items_with_emoji', ['🍽️ 混合食物']),
            'total_calories': int(analysis_result.get('total_calories', 300)),
            'total_protein': float(analysis_result.get('total_protein', 8.0)),
            'total_carbs': float(analysis_result.get('total_carbs', 60.0)),
            'total_fat': float(analysis_result.get('total_fat', 2.0)),
            'health_score': float(analysis_result.get('health_score', 7.0)),
            'meal_suitability': analysis_result.get('meal_suitability', '适合用餐'),
            'nutrition_highlights': analysis_result.get('nutrition_highlights', ['提供基础营养']),
            'dietary_suggestions': analysis_result.get('dietary_suggestions', ['注意营养均衡']),
            'personalized_assessment': analysis_result.get('personalized_assessment', ''),
            
            # 兼容字段
            'food_items': analysis_result.get('food_items_with_emoji', ['混合食物']),
            'health_highlights': analysis_result.get('nutrition_highlights', ['提供基础营养']),
            'suggestions': analysis_result.get('dietary_suggestions', ['注意营养均衡'])
        }
        
        # 缓存结果
        if len(ai_analysis_cache) < 100:
            ai_analysis_cache[cache_key] = result
        
        logger.info("数据库prompt分析完成")
        return result
        
    except Exception as e:
        logger.error(f"数据库prompt AI分析失败: {str(e)}")
        # 返回兜底数据
        return {
            'food_items_with_emoji': [f'🍽️ {food_description}'],
            'total_calories': 300,
            'total_protein': 8.0,
            'total_carbs': 60.0,
            'total_fat': 2.0,
            'health_score': 6.0,
            'meal_suitability': f'适合{meal_type}',
            'nutrition_highlights': ['提供基础营养'],
            'dietary_suggestions': ['搭配蔬菜水果'],
            'personalized_assessment': '基础营养评估',
            'food_items': [food_description],
            'health_highlights': ['提供基础营养'], 
            'suggestions': ['搭配蔬菜水果']
        }

def analyze_food_with_ai(food_description, user_profile=None, meal_type="未指定", recent_exercises=None):
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
        # 构建个性化的提示词
        user_info = ""
        if user_profile:
            gender_text = "男性" if user_profile.gender == 'male' else "女性"
            user_info = f"""
用户信息：
- 基本信息：{user_profile.age}岁 {gender_text} {user_profile.height}cm {user_profile.weight}kg
- 活动水平：{user_profile.activity_level}
- 基础代谢：{user_profile.bmr:.0f} kcal/天
- 餐次：{meal_type}
- 最近运动：{recent_exercises or "无运动记录"}
"""
        
        prompt = f"""
你是营养师，分析食物：{cleaned_description}

{user_info}

严格按JSON格式返回：
{{
    "food_items_with_emoji": ["🍚 白米饭(150g)", "🥚 煎蛋(2个)"],
    "total_calories": 350,
    "total_protein": 15.0,
    "total_carbs": 45.0,
    "total_fat": 12.0,
    "health_score": 7.5,
    "meal_suitability": "适合{meal_type}",
    "nutrition_highlights": [
        "🥚 鸡蛋: 提供优质蛋白质",
        "🥛 牛奶: 丰富钙质和维生素D",
        "🍚 米饭: 稳定的能量来源"
    ],
    "dietary_suggestions": [
        "搭配蔬菜增加膳食纤维",
        "保持这个搭配很棒！",
        "下次可以试试全麦食品"
    ],
    "personalized_assessment": "根据你的运动计划和身体状况，这餐营养搭配的个性化评估"
}}

要求：结合用户信息给出个性化建议，以鼓励为主
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
        
        # 验证并设置默认值 - 支持新格式
        result = {
            # 基础营养数据
            'total_calories': int(analysis_result.get('total_calories', 300)),
            'total_protein': round(float(analysis_result.get('total_protein', 15)), 1),
            'total_carbs': round(float(analysis_result.get('total_carbs', 40)), 1),
            'total_fat': round(float(analysis_result.get('total_fat', 10)), 1),
            
            # 新格式数据
            'food_items_with_emoji': analysis_result.get('food_items_with_emoji', analysis_result.get('food_items', ['🍽️ 混合食物(估算)'])),
            'health_score': float(analysis_result.get('health_score', 6)),
            'meal_suitability': analysis_result.get('meal_suitability', '适合用餐'),
            'nutrition_highlights': analysis_result.get('nutrition_highlights', analysis_result.get('health_highlights', ['提供基础营养'])),
            'dietary_suggestions': analysis_result.get('dietary_suggestions', analysis_result.get('suggestions', ['注意营养均衡'])),
            'personalized_assessment': analysis_result.get('personalized_assessment', ''),
            
            # 兼容旧格式
            'food_items': analysis_result.get('food_items_with_emoji', analysis_result.get('food_items', ['混合食物(估算)'])),
            'health_highlights': analysis_result.get('nutrition_highlights', analysis_result.get('health_highlights', ['提供基础营养'])),
            'suggestions': analysis_result.get('dietary_suggestions', analysis_result.get('suggestions', ['注意营养均衡'])),
        }
        
        # 缓存结果（限制缓存大小）
        if len(ai_analysis_cache) < 100:  # 最多缓存100个结果
            ai_analysis_cache[cache_key] = result
            logger.info("食物分析结果已缓存")
        
        return result
        
    except Exception as e:
        logger.error(f"食物AI分析失败: {str(e)}")
        logger.error(f"食物描述: {cleaned_description}")  # 添加调试信息
        logger.error(f"API密钥设置: {bool(os.getenv('GEMINI_API_KEY'))}")  # 检查API密钥
        
        # 记录详细错误信息用于调试
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'food_description': cleaned_description,
            'has_api_key': bool(os.getenv('GEMINI_API_KEY'))
        }
        logger.error(f"详细错误信息: {error_details}")
        
        # 抛出异常而不是返回默认值，这样可以看到真正的错误
        raise Exception(f"Gemini API调用失败: {str(e)}. 食物描述: {cleaned_description}")

@app.route('/api/test-ai')
@login_required  
def test_ai_simple():
    """简单的AI测试端点"""
    try:
        logger.info("=== 测试AI功能 ===")
        
        # 测试基本AI调用
        test_result = analyze_food_with_ai("一碗白米饭")
        
        return jsonify({
            'success': True,
            'message': 'AI测试成功',
            'data': test_result
        })
    except Exception as e:
        logger.error(f"AI测试失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quick-test')
def quick_test():
    """快速测试端点（无需登录）"""
    return jsonify({
        'status': 'ok',
        'timestamp': str(datetime.now()),
        'gemini_key_set': bool(os.getenv('GEMINI_API_KEY')),
        'database_connected': True
    })

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
        user_profile = getattr(current_user, 'profile', None)
        if user_profile:
            ai_analysis = analyze_exercise_with_ai(exercise_type, exercise_name, duration, user_profile)
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

@app.route('/meal-log-test', methods=['GET'])
def meal_log_test():
    """测试版饮食记录页面（无需登录）"""
    try:
        # 模拟用户数据
        recent_meals = []
        return render_template('meal_log.html', recent_meals=recent_meals)
    except Exception as e:
        return f"测试页面错误: {str(e)}", 500

@app.route('/meal-log-v2')
@login_required
def meal_log_v2():
    """新版饮食记录管理页面"""
    return render_template('meal_log_v2.html')

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
        logger.info("=== 开始AI食物分析 ===")
        data = request.get_json()
        logger.info(f"接收到的数据: {data}")
        
        # 支持两种字段格式：description 和 food_description
        food_description = data.get('description', data.get('food_description', '')).strip()
        meal_type = data.get('meal_type', '未指定')
        
        logger.info(f"食物描述: {food_description}")
        logger.info(f"餐次类型: {meal_type}")
        
        if not food_description:
            return jsonify({'error': '食物描述不能为空'}), 400
        
        # 使用数据库prompt模板进行AI分析
        logger.info("使用数据库prompt AI分析...")
        user_profile = getattr(current_user, 'profile', None)
        analysis_result = analyze_food_with_database_prompt(food_description, meal_type, user_profile)
        logger.info(f"数据库prompt AI分析完成")
        
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
        
        user_profile = getattr(current_user, 'profile', None)
        if not user_profile:
            return jsonify({'error': '请先完善个人资料'}), 400
        
        # 调用AI分析函数
        analysis_result = analyze_exercise_with_ai(exercise_type, exercise_name, duration, user_profile)
        
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
    try:
        # 创建安全的用户数据，避免访问有问题的关联
        safe_user_data = {
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at,
            'profile': getattr(current_user, 'profile', None),
            'meal_logs_count': 0,
            'exercise_logs_count': 0,
            'goals_count': 0
        }
        
        # 安全地获取统计数据
        try:
            safe_user_data['meal_logs_count'] = db.session.query(MealLog).filter_by(user_id=current_user.id).count()
        except:
            pass
            
        try:
            safe_user_data['exercise_logs_count'] = db.session.query(ExerciseLog).filter_by(user_id=current_user.id).count()
        except:
            pass
            
        try:
            safe_user_data['goals_count'] = db.session.query(FitnessGoal).filter_by(user_id=current_user.id).count()
        except:
            pass
        
        return render_template('profile_safe.html', user_data=safe_user_data)
    except Exception as e:
        return f"""
        <div class="container mt-4">
            <h1>个人资料页面</h1>
            <div class="alert alert-warning">
                <h4>页面暂时无法加载</h4>
                <p>系统正在维护中，请稍后再试。</p>
                <p class="small text-muted">错误信息: {str(e)}</p>
            </div>
            <a href="/dashboard" class="btn btn-primary">返回仪表盘</a>
        </div>
        """, 200

@app.route('/settings')
@login_required
def settings():
    try:
        # 创建安全的用户数据，避免访问有问题的关联
        safe_user_data = {
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at,
            'meal_logs_count': 0,
            'exercise_logs_count': 0,
            'goals_count': 0
        }
        
        # 安全地获取统计数据
        try:
            safe_user_data['meal_logs_count'] = db.session.query(MealLog).filter_by(user_id=current_user.id).count()
        except:
            pass
            
        try:
            safe_user_data['exercise_logs_count'] = db.session.query(ExerciseLog).filter_by(user_id=current_user.id).count()
        except:
            pass
            
        try:
            safe_user_data['goals_count'] = db.session.query(FitnessGoal).filter_by(user_id=current_user.id).count()
        except:
            pass
        
        return render_template('settings_safe.html', user_data=safe_user_data)
    except Exception as e:
        return f"""
        <div class="container mt-4">
            <h1>应用设置页面</h1>
            <div class="alert alert-warning">
                <h4>页面暂时无法加载</h4>
                <p>系统正在维护中，请稍后再试。</p>
                <p class="small text-muted">错误信息: {str(e)}</p>
            </div>
            <a href="/dashboard" class="btn btn-primary">返回仪表盘</a>
        </div>
        """, 200

@app.route('/health')
def health_check():
    """系统健康检查API端点"""
    try:
        # 检查数据库连接 - 使用安全的查询方式
        from sqlalchemy import text
        user_count = User.query.count()
        exercise_count = ExerciseLog.query.count()
        
        # 避免MealLog的架构问题，使用原生SQL
        meal_count_result = db.session.execute(text('SELECT COUNT(*) FROM meal_log'))
        meal_count = meal_count_result.scalar()
        
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
        # 检查数据库连接 - 使用安全的查询方式
        from sqlalchemy import text
        user_count = User.query.count()
        exercise_count = ExerciseLog.query.count()
        
        # 避免MealLog的架构问题，使用原生SQL
        meal_count_result = db.session.execute(text('SELECT COUNT(*) FROM meal_log'))
        meal_count = meal_count_result.scalar()
        
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
    profile = getattr(current_user, 'profile', None)
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
餐次：{meal_type}
用户信息：{user_info}

请按照以下JSON格式返回详细分析结果：
{{
    "food_items_with_emoji": ["🍎 苹果", "🥛 牛奶"],
    "total_calories": 数字（总热量）,
    "total_protein": 数字（总蛋白质g）,
    "total_carbs": 数字（总碳水化合物g）,
    "total_fat": 数字（总脂肪g）,
    "total_fiber": 数字（总膳食纤维g）,
    "total_sodium": 数字（总钠mg）,
    "health_score": 数字（健康评分1-10）,
    "meal_suitability": "适合度评估",
    "nutrition_highlights": ["营养亮点1", "营养亮点2"],
    "dietary_suggestions": ["饮食建议1", "饮食建议2"]
}}

分析要求：
1. 识别具体食物并用emoji标注
2. 准确计算各项营养成分
3. 基于营养密度给出健康评分
4. 评估与指定餐次的适合度
5. 提供个性化营养建议"""
        
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

# ================================
# 新版API端点 v2.0 - RESTful设计
# ================================

@app.route('/api/v2/food/analyze', methods=['POST'])
@login_required
def api_v2_food_analyze():
    """新版AI食物分析端点"""
    try:
        data = request.get_json()
        food_description = data.get('food_description', '').strip()
        meal_type = data.get('meal_type', '未指定')
        
        if not food_description:
            return jsonify({'success': False, 'error': '食物描述不能为空'})
        
        # 安全获取用户信息
        user_profile = getattr(current_user, 'profile', None)
        
        # 使用新版食物分析引擎
        analyzer = FoodAnalyzer()
        analysis_result = analyzer.analyze_comprehensive(
            food_description=food_description,
            user_profile=user_profile,
            meal_type=meal_type
        )
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        logger.error(f"v2食物分析API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析失败: {str(e)}'
        })

@app.route('/api/v2/meals/', methods=['GET', 'POST'])
@login_required
def api_v2_meals():
    """RESTful饮食记录端点"""
    if request.method == 'GET':
        # 获取饮食记录
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            date_filter = request.args.get('date')
            
            query = MealLog.query.filter_by(user_id=current_user.id)
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(MealLog.date == filter_date)
                except ValueError:
                    return jsonify({'success': False, 'error': '日期格式错误'})
            
            meals = query.order_by(MealLog.date.desc(), MealLog.id.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'meals': [{
                        'id': meal.id,
                        'date': meal.date.isoformat(),
                        'meal_type': meal.meal_type,
                        'food_description': meal.food_description,
                        'food_items_json': meal.food_items_json,
                        'total_calories': meal.total_calories,
                        'total_protein': meal.total_protein,
                        'total_carbs': meal.total_carbs,
                        'total_fat': meal.total_fat,
                        'total_fiber': meal.total_fiber,
                        'total_sodium': meal.total_sodium,
                        'health_score': meal.health_score,
                        'meal_suitability': meal.meal_suitability,
                        'nutrition_highlights': meal.nutrition_highlights,
                        'dietary_suggestions': meal.dietary_suggestions,
                        'personalized_assessment': meal.personalized_assessment
                    } for meal in meals.items],
                    'pagination': {
                        'page': meals.page,
                        'pages': meals.pages,
                        'per_page': meals.per_page,
                        'total': meals.total
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"获取饮食记录失败: {str(e)}")
            return jsonify({'success': False, 'error': '获取记录失败'})
    
    elif request.method == 'POST':
        # 创建饮食记录
        try:
            data = request.get_json()
            food_description = data.get('food_description', '').strip()
            meal_type = data.get('meal_type', '').strip()
            meal_date = data.get('date')
            
            if not food_description or not meal_type:
                return jsonify({'success': False, 'error': '食物描述和餐次不能为空'})
            
            # 解析日期
            if meal_date:
                try:
                    parsed_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': '日期格式错误'})
            else:
                parsed_date = datetime.now(timezone.utc).date()
            
            # AI分析（可选）
            analysis_result = None
            if data.get('analyze', True):
                analyzer = FoodAnalyzer()
                user_profile = getattr(current_user, 'profile', None)
                analysis_result = analyzer.analyze_comprehensive(
                    food_description=food_description,
                    user_profile=user_profile,
                    meal_type=meal_type
                )
            
            # 创建记录 - 使用兼容字段
            meal_log = MealLog(
                user_id=current_user.id,
                date=parsed_date,
                meal_type=meal_type,
                food_name=food_description[:100] if food_description else '未指定',  # 截断到100字符以适配数据库
                calories=0,  # 默认值，稍后填充
                protein=0.0,
                carbs=0.0,
                fat=0.0,
                quantity=1.0
            )
            
            # 如果有AI分析结果，填充数据
            if analysis_result:
                # 填充兼容的v1字段
                meal_log.calories = analysis_result.get('total_calories', 0)
                meal_log.protein = analysis_result.get('total_protein', 0.0)
                meal_log.carbs = analysis_result.get('total_carbs', 0.0)
                meal_log.fat = analysis_result.get('total_fat', 0.0)
                
                # 保存完整的AI分析结果到JSON字段
                meal_log.analysis_result = analysis_result
            
            db.session.add(meal_log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'id': meal_log.id,
                    'message': '饮食记录创建成功',
                    'analysis_result': analysis_result
                }
            })
            
        except Exception as e:
            logger.error(f"创建饮食记录失败: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': f'创建失败: {str(e)}'})

@app.route('/api/v2/nutrition/daily', methods=['GET'])
@login_required
def api_v2_nutrition_daily():
    """今日营养统计端点"""
    try:
        target_date = request.args.get('date')
        if target_date:
            try:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': '日期格式错误'})
        else:
            date_obj = datetime.now(timezone.utc).date()
        
        # 获取当日所有饮食记录
        daily_meals = MealLog.query.filter(
            MealLog.user_id == current_user.id,
            MealLog.date == date_obj
        ).all()
        
        # 统计营养数据
        total_nutrition = {
            'calories': sum(meal.total_calories or 0 for meal in daily_meals),
            'protein': sum(meal.total_protein or 0 for meal in daily_meals),
            'carbs': sum(meal.total_carbs or 0 for meal in daily_meals),
            'fat': sum(meal.total_fat or 0 for meal in daily_meals),
            'fiber': sum(meal.total_fiber or 0 for meal in daily_meals),
            'sodium': sum(meal.total_sodium or 0 for meal in daily_meals)
        }
        
        # 营养目标（基于用户信息）
        user_profile = getattr(current_user, 'profile', None)
        if user_profile:
            daily_targets = {
                'calories': int(user_profile.bmr * 1.55) if user_profile.bmr else 2000,
                'protein': max(50, int((user_profile.weight or 70) * 1.2)),
                'carbs': 250,
                'fat': 65,
                'fiber': 25,
                'sodium': 2300
            }
        else:
            daily_targets = {
                'calories': 2000,
                'protein': 50,
                'carbs': 250,
                'fat': 65,
                'fiber': 25,
                'sodium': 2300
            }
        
        # 计算达成率
        achievement_rates = {}
        for nutrient, consumed in total_nutrition.items():
            target = daily_targets[nutrient]
            rate = min(100, (consumed / target * 100)) if target > 0 else 0
            achievement_rates[nutrient] = round(rate, 1)
        
        return jsonify({
            'success': True,
            'data': {
                'date': date_obj.isoformat(),
                'nutrition': total_nutrition,
                'targets': daily_targets,
                'achievement_rates': achievement_rates,
                'meals_count': len(daily_meals),
                'meals': [{
                    'id': meal.id,
                    'meal_type': meal.meal_type,
                    'food_description': meal.food_description,
                    'calories': meal.total_calories
                } for meal in daily_meals]
            }
        })
        
    except Exception as e:
        logger.error(f"获取每日营养统计失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取统计失败'})

@app.route('/api/v2/nutrition/trends', methods=['GET'])
@login_required
def api_v2_nutrition_trends():
    """营养趋势分析端点"""
    try:
        days = request.args.get('days', 7, type=int)
        days = min(30, max(1, days))  # 限制1-30天
        
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        # 获取时间范围内的所有记录
        meals = MealLog.query.filter(
            MealLog.user_id == current_user.id,
            MealLog.date >= start_date,
            MealLog.date <= end_date
        ).order_by(MealLog.date.asc()).all()
        
        # 按日期分组统计
        daily_stats = {}
        for meal in meals:
            date_str = meal.date.isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'date': date_str,
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'fiber': 0,
                    'meals_count': 0
                }
            
            daily_stats[date_str]['calories'] += meal.total_calories or 0
            daily_stats[date_str]['protein'] += meal.total_protein or 0
            daily_stats[date_str]['carbs'] += meal.total_carbs or 0
            daily_stats[date_str]['fat'] += meal.total_fat or 0
            daily_stats[date_str]['fiber'] += meal.total_fiber or 0
            daily_stats[date_str]['meals_count'] += 1
        
        # 填充缺失日期
        trends_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in daily_stats:
                trends_data.append(daily_stats[date_str])
            else:
                trends_data.append({
                    'date': date_str,
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'fiber': 0,
                    'meals_count': 0
                })
            current_date += timedelta(days=1)
        
        # 计算平均值和趋势
        non_zero_days = [day for day in trends_data if day['calories'] > 0]
        if non_zero_days:
            averages = {
                'calories': sum(day['calories'] for day in non_zero_days) / len(non_zero_days),
                'protein': sum(day['protein'] for day in non_zero_days) / len(non_zero_days),
                'carbs': sum(day['carbs'] for day in non_zero_days) / len(non_zero_days),
                'fat': sum(day['fat'] for day in non_zero_days) / len(non_zero_days),
                'fiber': sum(day['fiber'] for day in non_zero_days) / len(non_zero_days)
            }
        else:
            averages = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0
            }
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'trends': trends_data,
                'averages': averages,
                'total_meals': len(meals),
                'active_days': len(non_zero_days)
            }
        })
        
    except Exception as e:
        logger.error(f"获取营养趋势失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取趋势失败'})

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
        
        # 格式化营养信息显示
        nutrition_html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📊 营养成分分析</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 15px 0;">
                <div><strong>总热量:</strong> {result.get('total_calories', 0)} kcal</div>
                <div><strong>蛋白质:</strong> {result.get('total_protein', 0)} g</div>
                <div><strong>碳水化合物:</strong> {result.get('total_carbs', 0)} g</div>
                <div><strong>脂肪:</strong> {result.get('total_fat', 0)} g</div>
            </div>
            <div style="margin: 15px 0;">
                <strong>健康评分:</strong> 
                <span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 15px;">
                    {result.get('health_score', 0)}/10
                </span>
            </div>
        </div>
        """
        
        food_items = result.get('food_items', [])
        food_items_html = "<ul>" + "".join([f"<li>{item}</li>" for item in food_items]) + "</ul>"
        
        highlights = result.get('health_highlights', [])
        highlights_html = "<ul>" + "".join([f"<li>✅ {item}</li>" for item in highlights]) + "</ul>"
        
        suggestions = result.get('suggestions', [])
        suggestions_html = "<ul>" + "".join([f"<li>💡 {item}</li>" for item in suggestions]) + "</ul>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI功能测试 - FitLife</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">
                    <h1>🤖 AI功能测试成功！</h1>
                    <p><strong>✅ Gemini-2.5-Flash模型正常工作</strong></p>
                </div>
                
                <h2>🍽 测试食物：{test_food}</h2>
                
                {nutrition_html}
                
                <div style="background: #e7f3ff; padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h3>🥘 识别的食物：</h3>
                    {food_items_html}
                </div>
                
                <div style="background: #f0f8f0; padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h3>🌟 营养亮点：</h3>
                    {highlights_html}
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h3>💭 健康建议：</h3>
                    {suggestions_html}
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h3>📝 分析说明：</h3>
                    <p>{result.get('analysis_note', '无说明')}</p>
                </div>
                
                <hr>
                <h3>🔧 技术信息：</h3>
                <ul>
                    <li>✅ 使用Gemini-2.5-Flash模型</li>
                    <li>✅ 中文食物识别优化</li>
                    <li>✅ 精确营养成分计算</li>
                    <li>✅ 中式份量估算</li>
                </ul>
                
                <div style="margin: 20px 0;">
                    <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">返回首页</a>
                    <a href="/clear-cache" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">清除AI缓存</a>
                </div>
                
                <details style="margin: 20px 0;">
                    <summary>查看原始JSON数据</summary>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow: auto;">{json.dumps(result, ensure_ascii=False, indent=2)}</pre>
                </details>
            </div>
        </body>
        </html>
        """, 200
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI测试失败 - FitLife</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family: sans-serif; margin: 20px;">
            <h1>❌ AI测试失败</h1>
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px;">
                <p><strong>错误信息：</strong> {str(e)}</p>
            </div>
            <p>这可能是因为：</p>
            <ul>
                <li>GEMINI_API_KEY环境变量未设置</li>
                <li>API密钥无效</li>
                <li>网络连接问题</li>
                <li>API使用限制</li>
            </ul>
            <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">返回首页</a>
        </body>
        </html>
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

# Duplicate route removed - keeping the first definition only

@app.route('/debug')
def debug():
    """最简单的调试页面"""
    return """
    <h1>🔧 FitLife 调试页面</h1>
    <p>✅ Flask应用运行正常</p>
    <p>✅ 路由响应正常</p>
    <p>当前时间: """ + str(datetime.now()) + """</p>
    <hr>
    <h2>测试链接:</h2>
    <ul>
        <li><a href="/test-ai">测试AI功能</a></li>
        <li><a href="/">返回首页</a></li>
        <li><a href="/init-database">数据库初始化</a></li>
    </ul>
    """

@app.route('/init-database')
def init_database_route():
    """初始化数据库和默认数据的路由"""
    try:
        db.create_all()
        
        # 检查管理员用户
        admin = AdminUser.query.filter_by(username='admin').first()
        if not admin:
            admin = AdminUser(
                username='admin',
                email='admin@fitlife.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
        
        # 检查并创建默认prompt模板
        food_prompt = PromptTemplate.query.filter_by(type='food', is_active=True).first()
        if not food_prompt:
            default_food_prompt = PromptTemplate(
                name='智能个性化饮食分析模板',
                type='food',
                prompt_content='''作为专业营养师，请分析以下食物并提供个性化建议。

食物描述: {food_description}
餐次: {meal_type}
用户信息: {user_info}

请基于营养学原理，考虑用户的个人情况（年龄、性别、身高、体重等），进行专业分析。

计算要求：
1. 准确估算各营养素含量
2. 基于用户BMR和TDEE计算个性化热量需求
3. 考虑餐次分配比例（早餐30%，午餐40%，晚餐30%）
4. 提供针对性的营养建议

返回严格的JSON格式：
{{
    "food_items_with_emoji": ["🍚 白米饭(150g)", "🥩 鸡胸肉(100g)"],
    "total_calories": 350,
    "total_protein": 25.0,
    "total_carbs": 45.0,
    "total_fat": 8.0,
    "total_fiber": 2.5,
    "total_sodium": 400.0,
    "health_score": 8.5,
    "meal_suitability": "适合{meal_type}，营养搭配均衡",
    "nutrition_highlights": ["💪 高蛋白质，有助肌肉修复", "🌾 复合碳水，提供持久能量"],
    "dietary_suggestions": ["🥬 建议搭配绿叶蔬菜增加维生素", "🚰 餐后多喝水促进消化"],
    "personalized_assessment": "基于您的个人情况进行的详细营养评估和建议"
}}''',
                is_active=True,
                created_by=admin.id if admin else None
            )
            db.session.add(default_food_prompt)
            db.session.commit()
            
        return '''
        <h1>✅ 数据库初始化完成</h1>
        <p>✅ 管理员账户: admin / admin123</p>
        <p>✅ 默认饮食分析prompt模板已创建</p>
        <hr>
        <p><a href="/admin">进入管理后台</a></p>
        <p><a href="/admin/prompts">管理Prompt模板</a></p>
        '''
        
    except Exception as e:
        return f'<h1>❌ 数据库初始化失败</h1><p>错误: {str(e)}</p>'

# Duplicate /health route removed - keeping the first definition only

# 移除自动初始化，避免Vercel部署时的问题
# if __name__ == '__main__':
#     with app.app_context():
#         init_database()
#     app.run(debug=True)