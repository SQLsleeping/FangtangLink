#!/usr/bin/env python3
"""
测试新功能：流式烧录和串口调试
"""

import sys
import os
import requests
import json
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from remote_flasher import RemoteFlasherClient

def test_stream_api(server_url):
    """测试流式烧录API"""
    print("=== 测试流式烧录API ===")
    
    # 创建一个简单的hex文件用于测试
    test_hex = """
:100000000C9434000C943E000C943E000C943E0082
:100010000C943E000C943E000C943E000C943E0068
:00000001FF
""".strip()
    
    with open("test.hex", "w") as f:
        f.write(test_hex)
    
    try:
        files = {'file': open("test.hex", 'rb')}
        data = {
            'mcu': 'atmega328p',
            'programmer': 'arduino',
            'port': '/dev/ttyS0',
            'baudrate': '115200'
        }
        
        print("发送流式烧录请求...")
        response = requests.post(
            f"{server_url}/flash/stream",
            files=files,
            data=data,
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ 流式响应接收中...")
            line_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        msg_type = data.get('type', 'unknown')
                        message = data.get('message', '')
                        print(f"  [{msg_type}] {message}")
                        line_count += 1
                        if line_count > 10:  # 限制输出行数
                            print("  ... (更多输出)")
                            break
                    except json.JSONDecodeError:
                        print(f"  {line}")
            
            print("✅ 流式烧录API测试完成")
            return True
        else:
            print(f"❌ 流式请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 流式烧录测试失败: {e}")
        return False
    finally:
        try:
            os.unlink("test.hex")
        except:
            pass

def test_serial_api(server_url):
    """测试串口调试API"""
    print("\n=== 测试串口调试API ===")
    
    try:
        # 1. 测试串口状态
        print("1. 获取串口状态...")
        response = requests.get(f"{server_url}/serial/status")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 当前连接数: {result.get('total_connections', 0)}")
        else:
            print(f"❌ 获取状态失败: {response.status_code}")
            return False
        
        # 2. 打开串口连接
        print("2. 打开串口连接...")
        response = requests.post(f"{server_url}/serial/open", json={
            'port': '/dev/ttyS0',
            'baudrate': 9600,
            'timeout': 1
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 串口已打开")
            else:
                print(f"❌ 打开串口失败: {result.get('message')}")
                return False
        else:
            print(f"❌ 打开串口请求失败: {response.status_code}")
            return False
        
        # 3. 发送测试数据
        print("3. 发送测试数据...")
        response = requests.post(f"{server_url}/serial/write", json={
            'port': '/dev/ttyS0',
            'baudrate': 9600,
            'data': "Hello Test!",
            'add_newline': True
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 数据已发送")
            else:
                print(f"❌ 发送失败")
        
        # 4. 关闭串口连接
        print("4. 关闭串口连接...")
        response = requests.post(f"{server_url}/serial/close", json={
            'port': '/dev/ttyS0',
            'baudrate': 9600
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 串口已关闭")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ 串口调试测试失败: {e}")
        return False

def main():
    """主函数"""
    server_url = "http://localhost:5001"  # 使用新端口
    
    print("RemoteFlasher 新功能测试")
    print("=" * 50)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{server_url}/status", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器不可用: {server_url}")
            return 1
        
        print(f"✅ 服务器运行正常")
        
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        print("请确保服务器在端口5001上运行:")
        print("  python run_server.py --port 5001 --debug")
        return 1
    
    success_count = 0
    total_tests = 2
    
    # 测试1: 流式烧录API
    if test_stream_api(server_url):
        success_count += 1
    
    # 测试2: 串口调试API
    if test_serial_api(server_url):
        success_count += 1
    
    # 总结
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有新功能测试通过!")
    else:
        print("⚠️  部分测试失败")
    
    return 0 if success_count == total_tests else 1

if __name__ == '__main__':
    sys.exit(main())
