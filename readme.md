# FitLife - 智能健身管理系统

一个基于Flask的智能健身和营养管理Web应用，集成Google Gemini AI提供个性化的饮食和运动分析。

## 🌟 主要功能

- **用户管理**：注册、登录、个人资料设置
- **目标设定**：个性化健身目标管理  
- **饮食记录**：智能饮食分析，营养成分计算
- **运动记录**：运动追踪，卡路里消耗计算
- **进度监控**：数据可视化，趋势分析
- **AI分析**：基于Gemini AI的智能营养和运动建议
- **管理后台**：AI Prompt模板管理

## 🚀 在线演示

- 前端网站：[即将部署]
- 管理后台：[即将部署]/admin

## 🛠 技术栈

- **后端**：Flask, SQLAlchemy, Flask-Login
- **前端**：Bootstrap 5, Chart.js, JavaScript
- **数据库**：SQLite (开发) / MySQL (生产)
- **AI集成**：Google Gemini API
- **部署**：Vercel + PlanetScale
- **样式**：CSS Grid, 响应式设计

## 📦 本地开发

### 环境要求

- Python 3.8+
- pip

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd fitlife
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 Gemini API 密钥
```

5. **初始化数据库**
```bash
python init_db.py
```

6. **启动应用**
```bash
python start.py
```

应用将在 http://127.0.0.1:5000 启动

## 🌐 云端部署

本项目支持一键部署到 Vercel + PlanetScale。

### 部署步骤

1. **GitHub设置**
   - 将代码推送到GitHub仓库
   
2. **PlanetScale数据库**
   - 创建PlanetScale账户
   - 创建新数据库
   - 获取连接字符串

3. **Vercel部署**
   - 连接GitHub仓库到Vercel
   - 配置环境变量：
     - `GEMINI_API_KEY`：您的Gemini API密钥
     - `DATABASE_URL`：PlanetScale连接字符串
     - `SECRET_KEY`：Flask密钥
   - 部署完成

### 环境变量配置

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=mysql://username:password@host:port/database
SECRET_KEY=your_very_secure_secret_key_here
VERCEL=1
```

## 📁 项目结构

```
fitlife/
├── app.py                 # 主应用文件
├── wsgi.py               # WSGI配置
├── init_db.py            # 数据库初始化
├── start.py              # 开发服务器启动
├── requirements.txt       # Python依赖
├── vercel.json           # Vercel部署配置
├── .env.example          # 环境变量示例
├── templates/            # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile_setup.html
│   ├── goal_setup.html
│   ├── meal_log.html
│   ├── exercise_log.html
│   ├── progress.html
│   ├── dashboard.html
│   └── admin/
│       ├── base.html
│       ├── dashboard.html
│       └── prompts.html
└── static/              # 静态文件
    └── (已移除，使用CDN)
```

## 🎯 核心功能

### 智能饮食分析
- 自然语言饮食描述识别
- 精确营养成分计算
- 个性化健康评分
- 营养平衡分析
- 实时建议推荐

### 运动追踪
- 多种运动类型支持
- 基于个人资料的卡路里计算
- 运动强度评估
- 个性化运动建议

### 数据可视化
- Chart.js图表展示
- 营养趋势分析
- 进度监控仪表板
- 响应式设计

## 🔧 管理功能

### AI Prompt管理
- 饮食分析模板定制
- 运动分析模板定制
- 实时预览功能
- 模板版本管理

## 🚨 注意事项

- 确保Gemini API密钥有效
- 生产环境请使用强密码作为SECRET_KEY
- 数据库连接配置正确
- 定期备份用户数据

## 📈 更新日志

### v2.0.0 (2024-08-03)
- ✨ 完全重构饮食记录界面
- 🎨 新增流式AI分析显示
- 📊 集成Chart.js数据可视化
- 🌐 支持云端部署
- 🗄️ 数据库迁移支持

### v1.0.0 (2024-08-01)
- 🎉 项目初始版本
- 👤 用户系统完成
- 🍎 饮食记录功能
- 🏃 运动追踪功能
- 🤖 AI分析集成

## 📞 技术支持

如有问题，请查看：
1. 应用日志输出
2. 浏览器开发者工具
3. 数据库连接状态
4. API密钥配置

## 📄 许可证

本项目仅供学习和个人使用。