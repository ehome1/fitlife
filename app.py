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
    response.headers.pop('Content-Security-Policy', None)
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

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    height = db.Column(db.Float)  # cm
    weight = db.Column(db.Float)  # kg
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # male, female
    activity_level = db.Column(db.String(20))  # sedentary, lightly_active, moderately_active, very_active
    bmr = db.Column(db.Float)  # 基础代谢率
    # fitness_goals字段在生产环境不存在，暂时注释
    # fitness_goals = db.Column(db.String(100))  # lose_weight, maintain_weight, gain_weight, build_muscle
    
    @property
    def fitness_goals(self):
        """兼容性属性 - 返回默认值"""
        return 'maintain_weight'

class FitnessGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(20), nullable=False)  # lose_weight, gain_weight, build_muscle, improve_endurance
    target_weight = db.Column(db.Float)
    current_weight = db.Column(db.Float)
    target_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    @property
    def goal_type_display(self):
        type_map = {
            'lose_weight': '减重',
            'gain_weight': '增重',
            'build_muscle': '增肌', 
            'improve_endurance': '提升耐力'
        }
        return type_map.get(self.goal_type, self.goal_type)

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # exercise_date字段在生产环境不存在，暂时注释
    # exercise_date = db.Column(db.Date, nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # 分钟
    calories_burned = db.Column(db.Integer)
    intensity = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def exercise_date(self):
        """兼容性属性 - 从created_at提取日期"""
        if self.created_at:
            return self.created_at.date()
        return datetime.now(timezone.utc).date()
    
    @property
    def exercise_type_display(self):
        type_map = {
            'cardio': '有氧运动',
            'strength': '力量训练',
            'flexibility': '柔韧性训练',
            'sports': '体育运动',
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

# 饮食记录相关模型和功能已删除

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
    type = db.Column(db.String(20), nullable=False)  # exercise
    prompt_content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def type_display(self):
        return '运动分析' if self.type == 'exercise' else '其他分析'

@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        logger.error(f"首页访问错误: {str(e)}")
        return f"<h1>FitLife 健身应用</h1><p>系统正在维护中...</p>", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册')
            return render_template('register.html')
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('注册成功！')
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

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # 获取用户资料
        profile = current_user.profile
        
        # 获取活跃目标
        active_goal = FitnessGoal.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        # 获取今日运动记录（使用created_at字段兼容生产环境）
        today = datetime.now(timezone.utc).date()
        from sqlalchemy import func
        today_exercises = ExerciseLog.query.filter(
            ExerciseLog.user_id == current_user.id,
            func.date(ExerciseLog.created_at) == today
        ).all()
        
        # 计算今日消耗热量
        total_burned = sum(ex.calories_burned or 0 for ex in today_exercises)
        
        # 饮食数据设为0（已删除饮食功能）
        total_consumed = 0
        today_meals = []
        
        return render_template('dashboard.html',
                             profile=profile,
                             active_goal=active_goal,
                             today_exercises=today_exercises,
                             today_meals=today_meals,
                             total_burned=total_burned,
                             total_consumed=total_consumed)
    
    except Exception as e:
        logger.error(f"仪表盘访问错误: {str(e)}")
        return f"仪表盘加载错误: {str(e)}", 500

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        age = int(request.form['age'])
        gender = request.form['gender']
        activity_level = request.form['activity_level']
        # fitness_goals = request.form.get('fitness_goals', 'maintain_weight')  # 暂不保存到数据库
        
        # 计算BMR
        if gender == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # 创建或更新用户资料（不包含fitness_goals字段）
        profile = current_user.profile
        if profile:
            profile.height = height
            profile.weight = weight
            profile.age = age
            profile.gender = gender
            profile.activity_level = activity_level
            profile.bmr = bmr
            # 不设置 fitness_goals 字段
        else:
            profile = UserProfile(
                user_id=current_user.id,
                height=height,
                weight=weight,
                age=age,
                gender=gender,
                activity_level=activity_level,
                bmr=bmr
                # 不包含 fitness_goals 字段
            )
            db.session.add(profile)
        
        db.session.commit()
        flash('个人资料保存成功！')
        return redirect(url_for('dashboard'))
    
    return render_template('profile_setup.html')

@app.route('/exercise-log', methods=['GET', 'POST'])
@login_required
def exercise_log():
    if request.method == 'POST':
        exercise_date_str = request.form['exercise_date']
        exercise_type = request.form['exercise_type']
        exercise_name = request.form['exercise_name']
        duration = int(request.form['duration'])
        notes = request.form.get('notes', '')
        
        # 解析日期并转换为datetime（兼容生产环境）
        try:
            exercise_date = datetime.strptime(exercise_date_str, '%Y-%m-%d').date()
            # 将日期转换为该日期的datetime（用于created_at字段）
            exercise_datetime = datetime.combine(exercise_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        except ValueError:
            exercise_datetime = datetime.now(timezone.utc)
        
        # 估算消耗的卡路里（简化版本）
        profile = current_user.profile
        if profile:
            weight = profile.weight
        else:
            weight = 70  # 默认体重
        
        calories_burned, intensity = estimate_calories_burned(exercise_type, exercise_name, duration, weight)
        
        exercise_log = ExerciseLog(
            user_id=current_user.id,
            # 不再使用exercise_date字段，使用created_at存储用户指定的日期
            created_at=exercise_datetime,
            exercise_type=exercise_type,
            exercise_name=exercise_name,
            duration=duration,
            calories_burned=calories_burned,
            intensity=intensity,
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

def estimate_calories_burned(exercise_type, exercise_name, duration, weight):
    """估算消耗的卡路里"""
    # MET值表（代谢当量）
    met_values = {
        'walking': 3.5,
        'running': 8.0,
        'cycling': 6.0,
        'swimming': 8.0,
        'strength': 6.0,
        'yoga': 3.0,
        'basketball': 8.0,
        'football': 8.0,
        'tennis': 7.0,
        'badminton': 5.5,
        'hiking': 6.0,
        'dancing': 4.8,
        'aerobics': 7.0,
        'weightlifting': 6.0,
        'pilates': 3.0,
        'crossfit': 12.0,
        'rope_jumping': 12.0,
        'boxing': 10.0,
    }
    
    # 根据运动类型和名称获取MET值
    met = met_values.get(exercise_type, 5.0)
    if exercise_name.lower() in met_values:
        met = met_values[exercise_name.lower()]
    
    # 强度调整
    if 'high' in exercise_name.lower() or '高强度' in exercise_name:
        met *= 1.3
        intensity = 'high'
    elif 'low' in exercise_name.lower() or '低强度' in exercise_name:
        met *= 0.7
        intensity = 'low'
    else:
        intensity = 'medium'
    
    # 卡路里 = MET × 体重(kg) × 时间(小时)
    calories = met * weight * (duration / 60)
    return round(calories), intensity

@app.route('/health')
def health_check():
    """健康检查端点"""
    try:
        # 测试数据库连接
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected',
            'features': ['exercise_log', 'user_profile', 'fitness_goals']
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

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
    """创建默认的Prompt模板（仅运动相关）"""
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
    
    db.session.commit()
    print("默认Prompt模板已创建")

@app.route('/api/analyze-exercise', methods=['POST'])
@login_required
def analyze_exercise():
    """运动分析API端点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        exercise_type = data.get('exercise_type')
        exercise_name = data.get('exercise_name')
        duration = data.get('duration')
        
        if not all([exercise_type, exercise_name, duration]):
            return jsonify({'error': '缺少必要的运动信息'}), 400
        
        # 获取用户资料
        user_profile = getattr(current_user, 'profile', None)
        if not user_profile:
            # 使用默认值
            weight = 70
            height = 170
            age = 30
            gender = '未知'
        else:
            weight = user_profile.weight or 70
            height = user_profile.height or 170
            age = user_profile.age or 30
            gender = user_profile.gender or '未知'
        
        # 计算卡路里消耗
        calories_burned, intensity = calculate_calories(exercise_type, exercise_name, duration, weight)
        
        # 计算BMR
        if gender == '男':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # 计算健身得分 (简化版本)
        fitness_score = min(100, int((calories_burned / 10) + (duration / 2)))
        
        # 生成分析结果
        analysis_result = {
            'calories_burned': calories_burned,
            'intensity_level': intensity,
            'fitness_score': fitness_score,
            'exercise_analysis': {
                'heart_rate_zone': get_heart_rate_zone(intensity),
                'energy_system': get_energy_system(exercise_type, duration),
                'primary_benefits': get_primary_benefits(exercise_type),
                'muscle_groups': get_muscle_groups(exercise_type)
            },
            'personalized_feedback': {
                'suitable_level': '适合' if intensity != 'high' or age < 50 else '需谨慎',
                'age_considerations': get_age_considerations(age, intensity),
                'fitness_level_match': '与活动水平匹配'
            },
            'recommendations': {
                'next_workout': get_next_workout_suggestion(exercise_type),
                'intensity_adjustment': get_intensity_adjustment(intensity),
                'duration_suggestion': get_duration_suggestion(duration),
                'recovery_advice': get_recovery_advice(intensity, duration)
            },
            'motivation_message': get_motivation_message(fitness_score),
            'health_alerts': get_health_alerts(intensity, duration, age)
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"运动分析错误: {e}")
        return jsonify({'error': '分析过程中出现错误'}), 500

def get_heart_rate_zone(intensity):
    """获取心率区间"""
    zones = {
        'low': '脂肪燃烧区间 (60-70%)',
        'medium': '有氧区间 (70-80%)',
        'high': '无氧区间 (80-90%)'
    }
    return zones.get(intensity, '有氧区间')

def get_energy_system(exercise_type, duration):
    """获取能量系统"""
    if duration < 10:
        return '磷酸肌酸系统'
    elif duration < 60:
        return '糖酵解系统'
    else:
        return '有氧系统'

def get_primary_benefits(exercise_type):
    """获取主要益处"""
    benefits_map = {
        'cardio': ['心肺功能', '脂肪燃烧', '耐力提升'],
        'strength': ['肌肉力量', '骨密度', '基础代谢'],
        'yoga': ['柔韧性', '平衡性', '压力缓解'],
        'sports': ['协调性', '反应速度', '团队精神'],
        'walking': ['心血管健康', '关节友好', '日常活力'],
        'running': ['心肺耐力', '下肢力量', '心理健康'],
        'cycling': ['腿部力量', '心肺功能', '关节保护'],
        'swimming': ['全身协调', '心肺功能', '关节友好']
    }
    return benefits_map.get(exercise_type, ['整体健康', '体能提升'])

def get_muscle_groups(exercise_type):
    """获取肌肉群"""
    muscle_map = {
        'cardio': ['心肌', '下肢肌群'],
        'strength': ['目标肌群', '核心肌群'],
        'yoga': ['全身肌群', '深层稳定肌'],
        'sports': ['全身协调肌群'],
        'walking': ['腿部肌群', '核心肌群'],
        'running': ['下肢肌群', '核心肌群'],
        'cycling': ['股四头肌', '臀大肌', '小腿肌'],
        'swimming': ['全身肌群', '核心肌群']
    }
    return muscle_map.get(exercise_type, ['相关肌群'])

def get_age_considerations(age, intensity):
    """获取年龄建议"""
    if age < 25:
        return '年轻体力充沛，可适当增加强度'
    elif age < 45:
        return '成年期适合各种运动方式'
    elif age < 65:
        return '中年期注意关节保护和恢复'
    else:
        return '老年期建议低冲击运动'

def get_next_workout_suggestion(exercise_type):
    """获取下次锻炼建议"""
    suggestions = {
        'cardio': '可尝试力量训练作为补充',
        'strength': '建议搭配有氧运动',
        'yoga': '可增加一些力量训练',
        'sports': '注意技术练习和体能训练',
        'walking': '可逐步增加步行速度',
        'running': '可尝试间歇训练',
        'cycling': '可增加爬坡训练',
        'swimming': '可练习不同泳姿'
    }
    return suggestions.get(exercise_type, '保持规律运动习惯')

def get_intensity_adjustment(intensity):
    """获取强度调整建议"""
    adjustments = {
        'low': '可适当增加运动强度',
        'medium': '当前强度很合适',
        'high': '高强度训练，注意恢复'
    }
    return adjustments.get(intensity, '保持当前强度')

def get_duration_suggestion(duration):
    """获取时长建议"""
    if duration < 20:
        return '可适当延长运动时间'
    elif duration < 60:
        return '运动时长很合适'
    else:
        return '长时间运动，注意水分补充'

def get_recovery_advice(intensity, duration):
    """获取恢复建议"""
    if intensity == 'high' or duration > 60:
        return '充分休息24-48小时'
    elif intensity == 'medium':
        return '轻度活动有助恢复'
    else:
        return '可进行日常活动'

def get_motivation_message(fitness_score):
    """获取激励信息"""
    if fitness_score >= 80:
        return '表现卓越！继续保持这种状态！'
    elif fitness_score >= 60:
        return '做得很好！坚持就是胜利！'
    elif fitness_score >= 40:
        return '不错的开始，继续努力！'
    else:
        return '每一步都是进步，加油！'

def get_health_alerts(intensity, duration, age):
    """获取健康提醒"""
    alerts = []
    
    if intensity == 'high' and age > 50:
        alerts.append('高强度运动，请注意心率监测')
    
    if duration > 90:
        alerts.append('长时间运动，注意补充水分和电解质')
    
    if intensity == 'high' and duration > 60:
        alerts.append('高强度长时间运动，建议专业指导')
    
    return alerts

def init_database():
    """初始化数据库函数"""
    print("🚀 初始化数据库...")
    db.create_all()
    create_default_admin()
    create_default_prompts()

# Vercel环境下的初始化
if os.getenv('VERCEL'):
    with app.app_context():
        try:
            init_database()
            print("✅ Vercel环境数据库初始化成功")
        except Exception as e:
            print(f"⚠️ Vercel环境数据库初始化失败: {e}")

# 本地开发环境初始化
if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=5001)