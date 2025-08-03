from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # 解析路径
        path = urlparse(self.path).path
        
        if path == '/':
            html = '''
            <h1>🏥 FitLife Flask测试</h1>
            <p>✅ Flask模拟路由正常工作</p>
            <ul>
                <li><a href="/debug">调试信息</a></li>
                <li><a href="/test">测试页面</a></li>
            </ul>
            '''
        elif path == '/debug':
            html = '''
            <h1>🔧 调试信息</h1>
            <p>路径: ''' + path + '''</p>
            <p>serverless函数正常工作</p>
            '''
        elif path == '/test':
            html = '''
            <h1>🧪 测试页面</h1>
            <p>这个页面模拟Flask路由</p>
            '''
        else:
            html = '''
            <h1>❌ 404 Not Found</h1>
            <p>路径不存在: ''' + path + '''</p>
            '''
        
        self.wfile.write(html.encode('utf-8'))
        return