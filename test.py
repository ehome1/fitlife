def handler(request):
    """Vercel serverless function handler"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8'
        },
        'body': '''
        <h1>🧪 Vercel Python 运行时测试</h1>
        <p>✅ Python运行时正常工作</p>
        <p>这是最基础的serverless函数测试</p>
        '''
    }