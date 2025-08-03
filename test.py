from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = '''
        <h1>🧪 Vercel Python 运行时测试</h1>
        <p>✅ Python运行时正常工作</p>
        <p>这是最基础的serverless函数测试</p>
        '''
        
        self.wfile.write(html.encode('utf-8'))
        return