#!/usr/bin/env python3
"""
测试运动分析API的脚本
"""
import requests
import json

def test_exercise_api():
    """测试运动分析API"""
    
    # 测试数据
    test_data = {
        "exercise_type": "running",
        "exercise_name": "晨跑",
        "duration": 30
    }
    
    print("🧪 测试运动分析API...")
    print(f"测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求
        response = requests.post(
            'http://127.0.0.1:5001/api/analyze-exercise',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        print(f"📝 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API测试成功!")
            print(f"📈 分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ API测试失败!")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    success = test_exercise_api()
    exit(0 if success else 1)