"""
FitLife 紧急维护页面
临时解决方案，让网站重新可以访问
"""
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emergency-mode-2024'

@app.route('/')
def maintenance_page():
    """显示维护页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FitLife - 系统升级中</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .logo {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            font-weight: 700;
        }
        .status {
            background: rgba(255, 255, 255, 0.2);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
        }
        .features {
            text-align: left;
            margin: 20px 0;
        }
        .feature-item {
            margin: 10px 0;
            padding-left: 25px;
        }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            margin: 10px;
            transition: all 0.3s;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: #4CAF50;
            width: 75%;
            border-radius: 3px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .footer {
            margin-top: 40px;
            font-size: 0.9rem;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🏃‍♂️💪</div>
        <h1>FitLife</h1>
        
        <div class="status">
            <h2>🔧 系统升级中</h2>
            <p><strong>我们正在为您升级系统功能</strong></p>
            
            <div class="features">
                <div class="feature-item">✨ 扩展营养分析 - 8个营养维度全面分析</div>
                <div class="feature-item">🔥 智能热量计算 - 运动+基础代谢</div>
                <div class="feature-item">💪 每日励志名言 - 名人名言鼓励</div>
                <div class="feature-item">🍽️ 优化饮食显示 - 按餐次智能合并</div>
                <div class="feature-item">🎯 精准BMI计算 - 使用真实身高数据</div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            
            <h3>⏰ 预计完成时间：30-60分钟</h3>
            <p>感谢您的耐心等待，升级完成后将带来更好的体验！</p>
        </div>
        
        <a href="javascript:location.reload()" class="btn">🔄 刷新页面</a>
        <a href="#" class="btn">📱 移动端优化</a>
        
        <div class="footer">
            <p>© 2024 FitLife - 智能健身饮食管理平台</p>
            <p>技术支持：AI驱动的个性化健康管理</p>
        </div>
    </div>

    <script>
        // 自动刷新倒计时
        let refreshTime = 300; // 5分钟后自动刷新
        
        function updateCounter() {
            const minutes = Math.floor(refreshTime / 60);
            const seconds = refreshTime % 60;
            document.title = `FitLife - 系统升级中 (${minutes}:${seconds.toString().padStart(2, '0')})`;
            
            if (refreshTime <= 0) {
                location.reload();
            }
            refreshTime--;
        }
        
        setInterval(updateCounter, 1000);
        updateCounter();
    </script>
</body>
</html>
    """

@app.route('/health')
def health_check():
    """健康检查接口"""
    return {
        "status": "maintenance",
        "message": "系统维护升级中",
        "features": [
            "扩展营养分析",
            "智能热量计算", 
            "每日励志名言",
            "优化饮食显示",
            "精准BMI计算"
        ]
    }

@app.route('/<path:path>')
def catch_all(path):
    """捕获所有其他路径"""
    return """
    <div style="text-align: center; padding: 50px; font-family: Arial;">
        <h2>🔧 FitLife 系统升级中</h2>
        <p>您访问的页面暂时不可用</p>
        <p>我们正在升级系统，增加更多智能功能</p>
        <a href="/" style="color: #007bff; text-decoration: none;">← 返回首页</a>
    </div>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)