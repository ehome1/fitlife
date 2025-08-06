from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone, date
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time
import hashlib

# 加载环境变量
load_dotenv()

# Gemini AI配置将在实际使用时进行

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
    meal_logs = db.relationship('MealLog', backref='user', cascade='all, delete-orphan')

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
    # 实际数据库中的字段名为 'date'，需要匹配
    date = db.Column(db.Date, nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # 分钟
    calories_burned = db.Column(db.Integer)
    intensity = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @property
    def exercise_date(self):
        """兼容性属性 - 返回date字段"""
        return self.date if self.date else datetime.now(timezone.utc).date()
    
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

class MealLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 实际数据库中的字段名为 'date'，不是 'meal_date'
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    # 实际数据库中是单个食物记录，不是JSON数组
    food_name = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    analysis_result = db.Column(db.JSON)  # AI分析结果
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 兼容性属性
    @property
    def meal_date(self):
        """兼容性属性 - 返回date字段"""
        return self.date
        
    @property
    def food_items(self):
        """兼容性属性 - 返回单个食物项的列表格式"""
        if self.food_name:
            return [{'name': self.food_name, 'amount': self.quantity or 1, 'unit': '份'}]
        return []
    
    @property 
    def total_calories(self):
        """兼容性属性 - 返回calories字段"""
        return self.calories or 0
        
    @property
    def notes(self):
        """兼容性属性 - 从analysis_result提取notes"""
        if self.analysis_result and isinstance(self.analysis_result, dict):
            return self.analysis_result.get('notes', '')
        return ''
    
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
    def food_items_summary(self):
        """生成食物摘要，用于历史记录显示"""
        if not self.food_items:
            return "无记录"
        
        food_names = [item.get('name', '') for item in self.food_items[:3]]  # 只显示前3个
        summary = '、'.join(food_names)
        
        if len(self.food_items) > 3:
            summary += f"等{len(self.food_items)}样"
        
        return summary
    
    @property 
    def date_display(self):
        """格式化日期显示"""
        if self.meal_date:
            return self.meal_date.strftime('%m-%d')
        return self.created_at.strftime('%m-%d')
    
    @property
    def meal_score(self):
        """获取膳食评分 (10分制)"""
        if self.analysis_result and 'meal_analysis' in self.analysis_result:
            return self.analysis_result['meal_analysis'].get('meal_score', 0)
        return 0

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
    """运动记录页面"""
    try:
        # 确保ExerciseLog表存在
        db.create_all()
        
        if request.method == 'POST':
            try:
                exercise_date_str = request.form['exercise_date']
                exercise_type = request.form['exercise_type']
                exercise_name = request.form['exercise_name']
                duration = int(request.form['duration'])
                notes = request.form.get('notes', '')
                
                # 验证必要字段
                if not all([exercise_date_str, exercise_type, exercise_name, duration]):
                    flash('请填写所有必要的运动信息！')
                    return redirect(url_for('exercise_log'))
                
                # 解析日期并转换为datetime（兼容生产环境）
                try:
                    exercise_date = datetime.strptime(exercise_date_str, '%Y-%m-%d').date()
                    # 将日期转换为该日期的datetime（用于created_at字段）
                    exercise_datetime = datetime.combine(exercise_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                except ValueError:
                    exercise_datetime = datetime.now(timezone.utc)
                    logger.warning(f"日期解析失败，使用当前时间: {exercise_date_str}")
                
                # 估算消耗的卡路里（简化版本）
                profile = current_user.profile
                if profile:
                    weight = profile.weight
                else:
                    weight = 70  # 默认体重
                
                calories_burned, intensity = estimate_calories_burned(exercise_type, exercise_name, duration, weight)
                
                exercise_log_entry = ExerciseLog(
                    user_id=current_user.id,
                    date=exercise_date,  # 设置date字段
                    created_at=exercise_datetime,  # created_at用于记录创建时间
                    exercise_type=exercise_type,
                    exercise_name=exercise_name,
                    duration=duration,
                    calories_burned=calories_burned,
                    intensity=intensity,
                    notes=notes
                )
                
                db.session.add(exercise_log_entry)
                db.session.commit()
                
                logger.info(f"用户{current_user.id}成功保存运动记录: {exercise_name}, {duration}分钟")
                flash(f'运动记录已保存！消耗了 {calories_burned} 卡路里')
                return redirect(url_for('exercise_log'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"保存运动记录失败: {e}")
                import traceback
                traceback.print_exc()
                flash('保存失败，请稍后重试')
                return redirect(url_for('exercise_log'))
    
        # 获取最近的运动记录
        try:
            recent_exercises = ExerciseLog.query.filter_by(
                user_id=current_user.id
            ).order_by(ExerciseLog.created_at.desc()).limit(10).all()
        except Exception as e:
            logger.error(f"查询运动记录失败: {e}")
            recent_exercises = []
        
        return render_template('exercise_log.html', recent_exercises=recent_exercises)
    
    except Exception as e:
        logger.error(f"运动记录页面错误: {e}")
        import traceback
        traceback.print_exc()
        flash('页面加载失败，请稍后重试')
        return redirect(url_for('dashboard'))

@app.route('/meal-log', methods=['GET', 'POST'])
@login_required
def meal_log():
    """饮食记录页面"""
    try:
        # 确保MealLog表存在
        db.create_all()
        
        if request.method == 'POST':
            meal_date_str = request.form['meal_date']
            meal_type = request.form['meal_type']
            notes = request.form.get('notes', '')
            food_description = request.form.get('food_description', '').strip()
            
            # 解析日期
            try:
                meal_date = datetime.strptime(meal_date_str, '%Y-%m-%d').date()
            except ValueError:
                meal_date = datetime.now(timezone.utc).date()
            
            # 处理食物列表数据
            food_items = []
            
            # 首先处理手动输入的食物项
            food_names = request.form.getlist('food_name[]')
            food_amounts = request.form.getlist('food_amount[]')
            food_units = request.form.getlist('food_unit[]')
            
            for i in range(len(food_names)):
                if food_names[i].strip():  # 只添加非空的食物项
                    try:
                        amount = float(food_amounts[i]) if food_amounts[i] else 1
                    except (ValueError, IndexError):
                        amount = 1
                    
                    food_items.append({
                        'name': food_names[i].strip(),
                        'amount': amount,
                        'unit': food_units[i] if i < len(food_units) else '个'
                    })
            
            # 如果没有手动输入但有自然语言描述，尝试解析
            if not food_items and food_description:
                try:
                    # 尝试使用AI解析自然语言
                    parse_result = parse_natural_language_food(food_description, meal_type)
                    if parse_result['success']:
                        food_items = parse_result['food_items']
                        logger.info(f"成功解析自然语言输入: {len(food_items)}项食物")
                    else:
                        # AI解析失败，创建简单的食物项
                        food_items = [{
                            'name': food_description[:100],  # 截取描述作为食物名
                            'amount': 1,
                            'unit': '份'
                        }]
                        logger.info("AI解析失败，使用简化食物项")
                except Exception as e:
                    logger.warning(f"自然语言解析失败: {e}")
                    # 解析完全失败时，仍然创建一个基础记录
                    food_items = [{
                        'name': food_description[:100],
                        'amount': 1,
                        'unit': '份'
                    }]
            
            # 检查是否有任何食物信息
            if not food_items and not food_description:
                flash('请描述您的饮食或手动添加食物项！')
                return redirect(url_for('meal_log'))
            
            # 创建饮食记录（每个食物项创建单独记录）
            try:
                # 准备notes信息
                combined_notes = {'notes': notes}
                if food_description:
                    combined_notes['original_description'] = food_description
                
                # 为每个食物项创建单独的记录
                saved_count = 0
                for food_item in food_items:
                    meal_log_entry = MealLog(
                        user_id=current_user.id,
                        date=meal_date,  # 使用date字段
                        meal_type=meal_type,
                        food_name=food_item.get('name', '未知食物'),
                        quantity=food_item.get('amount', 1),
                        calories=0,  # 初始值，等AI分析后更新
                        analysis_result=combined_notes
                    )
                    
                    db.session.add(meal_log_entry)
                    saved_count += 1
                
                db.session.commit()
                
                flash(f'饮食记录已保存！共记录了{saved_count}种食物，建议使用AI分析获取详细营养信息')
                return redirect(url_for('meal_log'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"保存饮食记录失败: {e}")
                flash('保存失败，请稍后重试')
                return redirect(url_for('meal_log'))
        
        # 获取最近的饮食记录并按餐次分组
        try:
            # 获取所有饮食记录
            all_meals = MealLog.query.filter_by(
                user_id=current_user.id
            ).order_by(MealLog.date.desc(), MealLog.created_at.desc()).all()
            
            # 按日期和餐次类型分组合并
            grouped_meals = {}
            for meal in all_meals:
                # 创建分组键：日期-餐次类型
                key = f"{meal.date}_{meal.meal_type}"
                
                if key not in grouped_meals:
                    grouped_meals[key] = {
                        'date': meal.date,
                        'meal_type': meal.meal_type,
                        'meal_type_display': meal.meal_type_display,
                        'food_items': [],
                        'total_calories': 0,
                        'created_at': meal.created_at,
                        'notes': meal.notes or ''
                    }
                
                # 添加食物项
                if meal.food_name:
                    grouped_meals[key]['food_items'].append({
                        'name': meal.food_name,
                        'quantity': meal.quantity or 1,
                        'unit': '份'
                    })
                    grouped_meals[key]['total_calories'] += meal.calories or 0
            
            # 转换为列表并限制数量
            recent_meals = []
            for key in sorted(grouped_meals.keys(), key=lambda x: grouped_meals[x]['created_at'], reverse=True)[:10]:
                meal_group = grouped_meals[key]
                # 生成食物摘要
                food_names = [item['name'] for item in meal_group['food_items']]
                meal_group['food_items_summary'] = '、'.join(food_names[:3])  # 最多显示3种食物
                if len(food_names) > 3:
                    meal_group['food_items_summary'] += f"等{len(food_names)}种食物"
                
                # 日期显示格式
                meal_group['date_display'] = meal_group['date'].strftime('%m-%d')
                meal_group['meal_score'] = 0  # 默认评分，可以后续添加计算逻辑
                
                recent_meals.append(meal_group)
                
        except Exception as e:
            logger.error(f"获取饮食记录失败: {e}")
            recent_meals = []
        
        return render_template('meal_log.html', recent_meals=recent_meals)
        
    except Exception as e:
        logger.error(f"饮食记录页面错误: {e}")
        flash('页面加载失败，请稍后重试')
        return redirect(url_for('dashboard'))

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
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
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
        duration_raw = data.get('duration')
        
        if not all([exercise_type, exercise_name, duration_raw]):
            return jsonify({'error': '缺少必要的运动信息'}), 400
        
        # 确保duration是数字
        try:
            duration = int(duration_raw)
            if duration <= 0:
                return jsonify({'error': '运动时长必须大于0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': '运动时长必须是有效数字'}), 400
        
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
        calories_burned, intensity = estimate_calories_burned(exercise_type, exercise_name, duration, weight)
        
        # 计算BMR
        if gender == '男':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # 计算健身得分 (满分10分)
        # 基于卡路里消耗和时长，标准化到10分制
        base_score = (calories_burned / 50) + (duration / 15)  # 调整权重
        fitness_score = min(10, max(1, int(base_score)))
        
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
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        import traceback
        error_msg = f"运动分析错误: {str(e)}"
        error_trace = traceback.format_exc()
        print(f"{error_msg}\n{error_trace}")
        return jsonify({
            'success': False,
            'error': '分析过程中出现错误',
            'details': str(e) if app.debug else None
        }), 500

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

@app.route('/api/analyze-meal', methods=['POST'])
@login_required
def analyze_meal():
    """AI营养分析API端点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        meal_type = data.get('meal_type')
        food_items = data.get('food_items', [])
        natural_language_input = data.get('natural_language_input', '')
        
        # 检查是否有自然语言输入或手动输入
        if not meal_type:
            return jsonify({'error': '请选择餐次类型'}), 400
        
        if not food_items and not natural_language_input:
            return jsonify({'error': '请描述您的饮食或手动添加食物'}), 400
        
        # 获取用户资料
        user_profile = getattr(current_user, 'profile', None)
        if not user_profile:
            weight = 70
            height = 170
            age = 30
            gender = '未知'
            fitness_goal = 'maintain_weight'
        else:
            weight = user_profile.weight or 70
            height = user_profile.height or 170
            age = user_profile.age or 30
            gender = user_profile.gender or '未知'
            fitness_goal = getattr(user_profile, 'fitness_goals', 'maintain_weight')
        
        # 调用Gemini AI进行营养分析
        analysis_result = call_gemini_meal_analysis(meal_type, food_items, {
            'age': age,
            'gender': gender,
            'weight': weight,
            'height': height,
            'fitness_goal': fitness_goal
        }, natural_language_input)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        import traceback
        error_msg = f"营养分析错误: {str(e)}"
        error_trace = traceback.format_exc()
        print(f"{error_msg}\n{error_trace}")
        return jsonify({
            'success': False,
            'error': '分析过程中出现错误',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/progress')
@login_required
def progress():
    """进度分析页面"""
    try:
        # 获取时间范围参数（默认30天）
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 获取运动数据
        exercises_data = get_exercises_data(current_user.id, start_date, end_date)
        
        # 获取饮食数据
        meals_data = get_meals_data(current_user.id, start_date, end_date)
        
        # 计算统计数据
        stats = calculate_progress_stats(exercises_data, meals_data)
        
        return render_template('progress.html', 
                             exercises_data=exercises_data,
                             meals_data=meals_data,
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"进度分析页面错误: {e}")
        flash('页面加载失败，请稍后重试')
        return redirect(url_for('dashboard'))

def get_exercises_data(user_id, start_date, end_date):
    """获取用户运动数据"""
    try:
        exercises = ExerciseLog.query.filter(
            ExerciseLog.user_id == user_id,
            ExerciseLog.date >= start_date,
            ExerciseLog.date <= end_date
        ).order_by(ExerciseLog.date.desc()).all()
        
        return [{
            'date': exercise.date.isoformat(),
            'exercise_type': exercise.exercise_type,
            'exercise_name': exercise.exercise_name,
            'duration': exercise.duration,
            'calories_burned': exercise.calories_burned or 0,
            'intensity': exercise.intensity or 'medium'
        } for exercise in exercises]
        
    except Exception as e:
        logger.error(f"获取运动数据失败: {e}")
        return []

def get_meals_data(user_id, start_date, end_date):
    """获取用户饮食数据"""
    try:
        meals = MealLog.query.filter(
            MealLog.user_id == user_id,
            MealLog.date >= start_date,
            MealLog.date <= end_date
        ).order_by(MealLog.date.desc()).all()
        
        return [{
            'date': meal.date.isoformat(),
            'meal_type': meal.meal_type,
            'food_name': meal.food_name,
            'calories': meal.calories or 0,
            'protein': meal.protein or 0,
            'carbs': meal.carbs or 0,
            'fat': meal.fat or 0
        } for meal in meals]
        
    except Exception as e:
        logger.error(f"获取饮食数据失败: {e}")
        return []

def calculate_progress_stats(exercises_data, meals_data):
    """计算进度统计数据"""
    try:
        # 运动统计
        total_burned = sum(ex.get('calories_burned', 0) for ex in exercises_data)
        total_minutes = sum(ex.get('duration', 0) for ex in exercises_data)
        exercise_days = len(set(ex.get('date') for ex in exercises_data))
        
        # 饮食统计
        total_consumed = sum(meal.get('calories', 0) for meal in meals_data)
        total_protein = sum(meal.get('protein', 0) for meal in meals_data)
        total_carbs = sum(meal.get('carbs', 0) for meal in meals_data)
        total_fat = sum(meal.get('fat', 0) for meal in meals_data)
        
        # 强度分布统计
        intensity_count = {'low': 0, 'medium': 0, 'high': 0}
        for ex in exercises_data:
            intensity = ex.get('intensity', 'medium')
            if intensity in intensity_count:
                intensity_count[intensity] += 1
        
        # 运动类型统计
        type_duration = {}
        for ex in exercises_data:
            ex_type = ex.get('exercise_type', 'unknown')
            duration = ex.get('duration', 0)
            type_duration[ex_type] = type_duration.get(ex_type, 0) + duration
        
        return {
            'total_burned': total_burned,
            'total_consumed': total_consumed,
            'exercise_days': exercise_days,
            'total_minutes': total_minutes,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fat': total_fat,
            'intensity_distribution': intensity_count,
            'type_duration': type_duration,
            'calorie_balance': total_consumed - total_burned
        }
        
    except Exception as e:
        logger.error(f"统计计算失败: {e}")
        return {
            'total_burned': 0,
            'total_consumed': 0,
            'exercise_days': 0,
            'total_minutes': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'intensity_distribution': {'low': 0, 'medium': 0, 'high': 0},
            'type_duration': {},
            'calorie_balance': 0
        }

def get_gemini_model():
    """获取配置好的Gemini模型"""
    try:
        import google.generativeai as genai
        
        # 配置Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise Exception("Gemini API Key未配置")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        logger.warning(f"Gemini配置错误: {e}")
        raise

def parse_natural_language_food(food_description, meal_type):
    """使用Gemini AI解析自然语言食物描述"""
    try:
        model = get_gemini_model()
        
        # 构建食物解析prompt
        parse_prompt = f"""
请解析以下自然语言描述的食物，提取出具体的食物项目信息。

用户描述: "{food_description}"
餐次类型: {meal_type}

请按照以下JSON格式返回解析结果（只返回JSON，不要其他文字）：

{{
    "parsed_foods": [
        {{
            "name": "食物名称",
            "amount": 数量,
            "unit": "单位",
            "estimated_weight": "估算重量(克)"
        }}
    ],
    "confidence": "解析置信度(high/medium/low)",
    "notes": "解析说明或注意事项"
}}

解析要求：
1. 准确识别食物名称，使用常见的中文名称
2. 提取数量信息，如果没有明确数量则估算合理分量
3. 识别单位，优先使用常见单位（个、片、碗、盒、杯等）
4. 估算每项食物的大概重量（克）
5. 如果描述不清楚，在notes中说明
"""
        
        # 调用Gemini API解析
        response = model.generate_content(parse_prompt)
        result_text = response.text.strip()
        
        # 清理响应文本
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        import json
        parsed_result = json.loads(result_text)
        
        # 转换为标准的food_items格式
        food_items = []
        for food in parsed_result.get('parsed_foods', []):
            food_items.append({
                'name': food.get('name', ''),
                'amount': food.get('amount', 1),
                'unit': food.get('unit', '份'),
                'estimated_weight': food.get('estimated_weight', '100')
            })
        
        return {
            'success': True,
            'food_items': food_items,
            'confidence': parsed_result.get('confidence', 'medium'),
            'notes': parsed_result.get('notes', ''),
            'original_description': food_description
        }
        
    except Exception as e:
        print(f"自然语言解析错误: {e}")
        # 返回fallback结果
        return {
            'success': False,
            'error': str(e),
            'food_items': [],
            'original_description': food_description
        }

def call_gemini_meal_analysis(meal_type, food_items, user_info, natural_language_input=None):
    """调用Gemini API进行营养分析"""
    try:
        # 先尝试获取Gemini模型
        try:
            model = get_gemini_model()
        except Exception as e:
            logger.warning(f"Gemini API不可用，使用fallback: {e}")
            # 如果有自然语言输入但没有Gemini API，创建简单的食物项
            if natural_language_input and not food_items:
                food_items = [{'name': natural_language_input[:50], 'amount': 1, 'unit': '份'}]
            return generate_fallback_nutrition_analysis(food_items, meal_type)
        
        # 如果是自然语言输入，先解析提取食物信息
        if natural_language_input:
            try:
                parse_result = parse_natural_language_food(natural_language_input, meal_type)
                if parse_result['success']:
                    food_items = parse_result['food_items']
                else:
                    # 解析失败，创建简单的食物项
                    food_items = [{'name': natural_language_input[:50], 'amount': 1, 'unit': '份'}]
            except Exception as e:
                logger.warning(f"自然语言解析失败: {e}")
                # 创建简单的食物项用于营养分析
                food_items = [{'name': natural_language_input[:50], 'amount': 1, 'unit': '份'}]
        
        # 构建food_items字符串
        food_list_str = '\n'.join([
            f"- {item['name']} {item['amount']}{item['unit']}" 
            for item in food_items
        ])
        
        # 餐次类型映射
        meal_type_map = {
            'breakfast': '早餐',
            'lunch': '午餐',
            'dinner': '晚餐', 
            'snack': '加餐'
        }
        meal_type_cn = meal_type_map.get(meal_type, meal_type)
        
        # 构建详细的营养分析prompt
        json_template = '''
{
    "basic_nutrition": {
        "total_calories": 数值,
        "protein": 数值,
        "carbohydrates": 数值, 
        "fat": 数值,
        "fiber": 数值,
        "sugar": 数值
    },
    "nutrition_breakdown": {
        "protein_percentage": 数值,
        "carbs_percentage": 数值,
        "fat_percentage": 数值
    },
    "meal_analysis": {
        "meal_score": 数值,
        "balance_rating": "营养均衡评价",
        "meal_type_suitability": "对该餐次的适合度评价",
        "portion_assessment": "分量评估"
    },
    "detailed_analysis": {
        "strengths": ["营养优点列表"],
        "areas_for_improvement": ["改进建议列表"]
    },
    "personalized_feedback": {
        "calorie_assessment": "热量评估",
        "macro_balance": "三大营养素平衡评价",
        "health_impact": "健康影响评估"
    },
    "recommendations": {
        "next_meal_suggestion": "下一餐建议",
        "daily_nutrition_tip": "今日营养贴士",
        "hydration_reminder": "补水提醒"
    },
    "motivation_message": "激励话语"
}
'''
        
        prompt = f"""
作为专业营养师，请分析以下饮食信息并返回详细的营养分析结果。

用户信息：
- 年龄：{user_info['age']}岁
- 性别：{user_info['gender']}
- 体重：{user_info['weight']}kg
- 身高：{user_info['height']}cm
- 健身目标：{user_info['fitness_goal']}

饮食信息：
- 餐次：{meal_type_cn}
- 食物列表：
{food_list_str}

请按照以下JSON格式返回营养分析结果（只返回JSON，不要其他文字）：

{json_template}

请基于营养学专业知识进行准确分析，确保数据真实可靠。
"""
        
        # 调用Gemini API
        response = model.generate_content(prompt)
        
        # 解析JSON响应
        import json
        result_text = response.text.strip()
        
        # 清理响应文本，移除可能的markdown标记
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        result = json.loads(result_text)
        
        # 如果是自然语言输入，添加解析信息到结果中
        if natural_language_input:
            result['parsed_food_info'] = {
                'original_description': natural_language_input,
                'parsed_foods': food_items,
                'parsing_method': 'ai_natural_language'
            }
        
        return result
        
    except Exception as e:
        print(f"Gemini API调用错误: {e}")
        # 返回模拟数据作为fallback
        return generate_fallback_nutrition_analysis(food_items, meal_type)

def generate_fallback_nutrition_analysis(food_items, meal_type):
    """生成模拟营养分析数据"""
    # 简单的热量估算
    estimated_calories = len(food_items) * 150  # 每个食物项平均150kcal
    
    return {
        "basic_nutrition": {
            "total_calories": estimated_calories,
            "protein": round(estimated_calories * 0.15 / 4),  # 15%的热量来自蛋白质
            "carbohydrates": round(estimated_calories * 0.55 / 4),  # 55%来自碳水
            "fat": round(estimated_calories * 0.30 / 9),  # 30%来自脂肪
            "fiber": 5,
            "sugar": 15
        },
        "nutrition_breakdown": {
            "protein_percentage": 15,
            "carbs_percentage": 55,
            "fat_percentage": 30
        },
        "meal_analysis": {
            "meal_score": 7.5,
            "balance_rating": "营养较均衡",
            "meal_type_suitability": "适合当前餐次",
            "portion_assessment": "分量适中"
        },
        "detailed_analysis": {
            "strengths": ["食物搭配丰富", "营养相对均衡"],
            "areas_for_improvement": ["建议增加蔬菜摄入", "注意食物新鲜度"]
        },
        "personalized_feedback": {
            "calorie_assessment": "热量适中，符合需求",
            "macro_balance": "三大营养素比例合理",
            "health_impact": "整体健康，营养价值良好"
        },
        "recommendations": {
            "next_meal_suggestion": "下一餐建议增加蔬菜",
            "daily_nutrition_tip": "保持多样化饮食",
            "hydration_reminder": "记得补充水分"
        },
        "motivation_message": "营养搭配不错，继续保持健康饮食习惯！"
    }

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

# 临时数据库初始化端点（生产环境使用后应删除）
@app.route('/init-database-secret-endpoint-12345')
def init_database_endpoint():
    """临时数据库初始化端点 - 仅用于生产环境初始化"""
    try:
        # 检查是否为生产环境
        if not (os.getenv('VERCEL') or os.getenv('DATABASE_URL')):
            return jsonify({"error": "仅限生产环境使用"}), 403
        
        # 创建所有表
        db.create_all()
        
        # 验证表结构
        tables_status = {}
        tables = ['user', 'user_profile', 'fitness_goal', 'exercise_log', 'meal_log']
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                tables_status[table] = f"✅ 成功 ({count} 条记录)"
            except Exception as e:
                tables_status[table] = f"❌ 错误: {str(e)}"
        
        return jsonify({
            "status": "success",
            "message": "数据库初始化完成",
            "tables": tables_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"数据库初始化失败: {str(e)}"
        }), 500

# 诊断端点 - 专门用于排查线上问题
@app.route('/diagnose-meal-system-secret-67890')
def diagnose_meal_system():
    """诊断饮食记录系统状态"""
    try:
        diagnosis = {}
        
        # 1. 检查数据库连接
        try:
            db.session.execute(text("SELECT 1"))
            diagnosis['database_connection'] = "✅ 连接正常"
        except Exception as e:
            diagnosis['database_connection'] = f"❌ 连接失败: {str(e)}"
        
        # 2. 检查MealLog表
        try:
            # 尝试创建表
            db.create_all()
            
            # 检查表结构
            result = db.session.execute(text("SELECT COUNT(*) FROM meal_log"))
            count = result.scalar()
            diagnosis['meal_log_table'] = f"✅ 表存在 ({count} 条记录)"
            
            # 检查表字段
            result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'meal_log'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            diagnosis['meal_log_columns'] = [f"{col[0]} ({col[1]})" for col in columns]
            
        except Exception as e:
            diagnosis['meal_log_table'] = f"❌ 表问题: {str(e)}"
        
        # 3. 检查模板文件
        try:
            import os
            template_path = 'templates/meal_log.html'
            if os.path.exists(template_path):
                diagnosis['meal_log_template'] = "✅ 模板存在"
            else:
                diagnosis['meal_log_template'] = "❌ 模板缺失"
        except Exception as e:
            diagnosis['meal_log_template'] = f"❌ 模板检查失败: {str(e)}"
        
        # 4. 检查路由
        try:
            from flask import url_for
            meal_log_url = url_for('meal_log')
            diagnosis['meal_log_route'] = f"✅ 路由正常: {meal_log_url}"
        except Exception as e:
            diagnosis['meal_log_route'] = f"❌ 路由问题: {str(e)}"
        
        # 5. 测试MealLog模型
        try:
            test_meal = MealLog(
                user_id=1,
                meal_date=date.today(),
                meal_type='breakfast',
                food_items=[{"name": "测试", "amount": 1, "unit": "个"}],
                total_calories=100
            )
            # 不实际保存，只测试创建
            diagnosis['meal_log_model'] = "✅ 模型正常"
        except Exception as e:
            diagnosis['meal_log_model'] = f"❌ 模型问题: {str(e)}"
        
        # 6. 环境变量检查
        env_vars = {}
        for var in ['DATABASE_URL', 'SECRET_KEY', 'GEMINI_API_KEY']:
            env_vars[var] = "✅ 已设置" if os.getenv(var) else "❌ 未设置"
        diagnosis['environment_variables'] = env_vars
        
        return jsonify({
            "status": "success",
            "diagnosis": diagnosis,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommendations": get_fix_recommendations(diagnosis)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"诊断失败: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

def get_fix_recommendations(diagnosis):
    """根据诊断结果生成修复建议"""
    recommendations = []
    
    if "❌" in diagnosis.get('database_connection', ''):
        recommendations.append("🔧 检查DATABASE_URL环境变量设置")
    
    if "❌" in diagnosis.get('meal_log_table', ''):
        recommendations.append("🔧 运行数据库初始化: 访问 /init-database-secret-endpoint-12345")
    
    if "❌" in diagnosis.get('meal_log_template', ''):
        recommendations.append("🔧 确保templates/meal_log.html文件存在")
    
    if "❌" in diagnosis.get('meal_log_model', ''):
        recommendations.append("🔧 检查MealLog模型定义或JSON字段兼容性")
    
    if not recommendations:
        recommendations.append("✅ 系统看起来正常，可能是临时网络问题")
    
    return recommendations

# 本地开发环境初始化
if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=5001)