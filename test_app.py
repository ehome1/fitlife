#!/usr/bin/env python3
"""
简化的健身饮食管理应用测试版本
不依赖外部包，展示核心功能
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
from datetime import datetime

class FitnessHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_static_file('static_index.html')
        elif self.path == '/app.css':
            self.serve_css()
        else:
            self.send_error(404)
    
    def serve_static_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_css(self):
        css_content = """
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(120deg, #f6f9fc 0%, #f1f5f9 100%);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            padding: 20px;
        }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
        }
        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .stat {
            flex: 1;
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stat:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.2);
        }
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))

def create_static_html():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitLife - 健身饮食管理</title>
        <link rel="stylesheet" href="/app.css">
    </head>
    <body>
        <div class="container">
            <div class="gradient-bg">
                <h1>🏃‍♂️ FitLife 健身饮食管理系统</h1>
                <p>科学管理你的健身和饮食，用数据见证蜕变之路</p>
                <a href="#features" class="btn">开始体验</a>
            </div>
            
            <div class="card" id="features">
                <h2>✨ 核心功能展示</h2>
                <div class="stats">
                    <div class="stat" onclick="showFeatureDetail('goal')" style="cursor: pointer;">
                        <div class="stat-number">🎯</div>
                        <h3>目标设定</h3>
                        <p>详细的健身目标制定，包括减脂、增肌、提升体能等多种目的</p>
                    </div>
                    <div class="stat" onclick="showFeatureDetail('exercise')" style="cursor: pointer;">
                        <div class="stat-number">🏃</div>
                        <h3>运动打卡</h3>
                        <p>智能热量计算，支持多种运动类型，科学记录运动数据</p>
                    </div>
                    <div class="stat" onclick="showFeatureDetail('nutrition')" style="cursor: pointer;">
                        <div class="stat-number">🍎</div>
                        <h3>饮食管理</h3>
                        <p>营养成分分析，三餐记录，智能计算卡路里摄入</p>
                    </div>
                    <div class="stat" onclick="showFeatureDetail('charts')" style="cursor: pointer;">
                        <div class="stat-number">📊</div>
                        <h3>数据可视化</h3>
                        <p>美观的图表展示，热量平衡分析，进度追踪</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📱 主要页面展示</h2>
                <div class="stats">
                    <div class="stat">
                        <h4>🏠 仪表盘</h4>
                        <p>今日概览、快速打卡、目标进度</p>
                    </div>
                    <div class="stat">
                        <h4>📝 运动记录</h4>
                        <p>运动类型选择、时长记录、强度设置</p>
                    </div>
                    <div class="stat">
                        <h4>🍽️ 饮食记录</h4>
                        <p>餐次分类、营养分析、热量计算</p>
                    </div>
                    <div class="stat">
                        <h4>📈 进度分析</h4>
                        <p>趋势图表、数据统计、成就展示</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🚀 技术亮点</h2>
                <ul>
                    <li><strong>科学算法</strong>：基于MET值的热量计算，BMR基础代谢率计算</li>
                    <li><strong>智能分析</strong>：营养成分自动计算，食物数据库支持</li>
                    <li><strong>美观界面</strong>：现代化设计，渐变色彩，响应式布局</li>
                    <li><strong>数据可视化</strong>：Chart.js图表库，多维度数据展示</li>
                    <li><strong>用户体验</strong>：便捷打卡，智能提示，激励机制</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>💡 使用场景</h2>
                <div class="stats">
                    <div class="stat">
                        <h4>🎯 减脂塑形</h4>
                        <p>制定减重目标，控制热量摄入，增加运动消耗</p>
                    </div>
                    <div class="stat">
                        <h4>💪 增肌增重</h4>
                        <p>合理增加热量摄入，力量训练记录，蛋白质补充</p>
                    </div>
                    <div class="stat">
                        <h4>❤️ 健康生活</h4>
                        <p>保持运动习惯，均衡营养摄入，数据化管理</p>
                    </div>
                    <div class="stat">
                        <h4>🏃 运动爱好</h4>
                        <p>记录运动成果，追踪运动表现，制定训练计划</p>
                    </div>
                </div>
            </div>
            
            <div class="gradient-bg">
                <h2>🔥 完整版本特性</h2>
                <p>完整的Flask应用包含：</p>
                <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                    <li>用户注册登录系统</li>
                    <li>个人资料管理</li>
                    <li>详细的目标设定流程</li>
                    <li>运动和饮食打卡功能</li>
                    <li>数据可视化仪表盘</li>
                    <li>进度分析和统计</li>
                    <li>激励机制和成就系统</li>
                </ul>
                
                <div style="margin-top: 30px;">
                    <button onclick="startFullApp()" class="btn" style="margin: 5px;">
                        🚀 启动完整应用
                    </button>
                    <button onclick="showDemo()" class="btn" style="margin: 5px;">
                        📱 查看功能演示
                    </button>
                </div>
                
                <p style="margin-top: 20px;"><strong>终端命令：</strong> python3 app.py</p>
            </div>
        </div>
        
        <script>
            console.log('FitLife 健身饮食管理系统演示页面已加载');
            console.log('完整功能请运行: python3 app.py');
            
            function startFullApp() {
                alert('🚀 要体验完整功能，请在终端运行：\\n\\npython3 app.py\\n\\n然后访问：http://localhost:5000');
            }
            
            function showDemo() {
                alert('📱 当前页面展示了所有功能特性！\\n\\n✅ 科学的热量计算算法\\n✅ 美观的数据可视化界面\\n✅ 完整的用户管理系统\\n✅ 智能的营养分析功能\\n\\n要体验交互功能，请运行完整版本！');
            }
            
            function showFeatureDetail(feature) {
                const details = {
                    'goal': {
                        title: '🎯 目标设定系统',
                        content: '• 多种健身目的：减脂塑形、增肌增重、提升体能、保持健康\\n• 科学计划制定：根据个人情况设定合理时间周期\\n• 智能建议系统：基于BMR和TDEE的个性化建议\\n• 进度可视化：目标完成度实时追踪'
                    },
                    'exercise': {
                        title: '🏃 运动打卡系统',
                        content: '• 8种运动类型：有氧、力量、瑜伽、球类、步行、跑步等\\n• 科学热量计算：基于MET值和个人体重自动计算\\n• 三级强度分类：低、中、高强度精确记录\\n• 运动感受记录：支持记录心情和训练感受'
                    },
                    'nutrition': {
                        title: '🍎 饮食管理系统',
                        content: '• 四餐分类记录：早餐、午餐、晚餐、加餐\\n• 营养成分分析：蛋白质、碳水化合物、脂肪计算\\n• 食物数据库：内置常见食物营养信息\\n• 智能计算：实时显示实际营养摄入量'
                    },
                    'charts': {
                        title: '📊 数据可视化系统',
                        content: '• 热量平衡趋势图：每日摄入与消耗对比\\n• 运动强度分布：饼图展示运动类型比例\\n• 营养成分雷达图：三大营养素摄入分析\\n• 打卡热力图：日历视图展示活跃度'
                    }
                };
                
                const detail = details[feature];
                if (detail) {
                    alert(detail.title + '\\n\\n' + detail.content + '\\n\\n💡 完整功能请运行：python3 app.py');
                }
            }
            
            // 页面加载后添加平滑滚动效果
            document.addEventListener('DOMContentLoaded', function() {
                // 为所有锚点链接添加平滑滚动
                const anchorLinks = document.querySelectorAll('a[href^="#"]');
                anchorLinks.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const targetId = this.getAttribute('href').substring(1);
                        const targetElement = document.getElementById(targetId);
                        if (targetElement) {
                            targetElement.scrollIntoView({ 
                                behavior: 'smooth',
                                block: 'start'
                            });
                            
                            // 添加视觉反馈效果
                            setTimeout(() => {
                                targetElement.style.transform = 'scale(1.02)';
                                targetElement.style.transition = 'all 0.3s ease';
                                targetElement.style.boxShadow = '0 20px 40px rgba(102, 126, 234, 0.3)';
                                
                                setTimeout(() => {
                                    targetElement.style.transform = 'scale(1)';
                                    targetElement.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
                                }, 300);
                            }, 500);
                        }
                    });
                });
                
                console.log('✅ 交互功能已激活！');
                console.log('🖱️ 点击"开始体验"或功能卡片试试看！');
            });
        </script>
    </body>
    </html>
    """
    
    with open('static_index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def start_demo_server():
    create_static_html()
    
    print("="*60)
    print("🚀 FitLife 健身饮食管理系统演示服务器")
    print("="*60)
    print("📱 演示页面: http://localhost:8888")
    print("💡 这是功能展示页面，完整功能请运行: python3 app.py")
    print("⚡ 按 Ctrl+C 停止演示服务器")
    print("="*60)
    
    server = HTTPServer(('localhost', 8888), FitnessHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n📴 演示服务器已停止")
        server.shutdown()

if __name__ == '__main__':
    start_demo_server()