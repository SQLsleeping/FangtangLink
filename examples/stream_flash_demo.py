#!/usr/bin/env python3
"""
流式烧录演示
演示如何使用流式API实时获取avrdude输出
"""

import sys
import os
import requests
import json
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def stream_flash_demo(server_url, hex_file, **params):
    """演示流式烧录"""
    print(f"=== 流式烧录演示 ===")
    print(f"服务器: {server_url}")
    print(f"文件: {hex_file}")
    print(f"参数: {params}")
    print("")
    
    try:
        # 准备文件和参数
        files = {'file': open(hex_file, 'rb')}
        data = params
        
        # 发送流式烧录请求
        print("开始流式烧录...")
        response = requests.post(
            f"{server_url}/flash/stream",
            files=files,
            data=data,
            stream=True,
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return False
        
        # 实时处理流式响应
        success = False
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                    msg_type = data.get('type', 'unknown')
                    message = data.get('message', '')
                    
                    # 根据消息类型显示不同颜色
                    if msg_type == 'error':
                        print(f"❌ {message}")
                    elif msg_type == 'warning':
                        print(f"⚠️  {message}")
                    elif msg_type == 'success':
                        print(f"✅ {message}")
                        success = True
                    elif msg_type == 'info':
                        print(f"ℹ️  {message}")
                    elif msg_type == 'output':
                        print(f"   {message}")
                    else:
                        print(f"   {message}")
                        
                except json.JSONDecodeError:
                    print(f"   {line}")
        
        files['file'].close()
        
        if success:
            print("\n🎉 流式烧录完成!")
            return True
        else:
            print("\n❌ 流式烧录失败!")
            return False
            
    except Exception as e:
        print(f"❌ 流式烧录异常: {e}")
        return False

def serial_debug_demo(server_url, port="/dev/ttyS0", baudrate=9600):
    """演示串口调试功能"""
    print(f"\n=== 串口调试演示 ===")
    print(f"服务器: {server_url}")
    print(f"串口: {port} @ {baudrate}")
    print("")
    
    try:
        # 1. 打开串口连接
        print("1. 打开串口连接...")
        response = requests.post(f"{server_url}/serial/open", json={
            'port': port,
            'baudrate': baudrate,
            'timeout': 1
        })
        
        if response.status_code != 200:
            print(f"❌ 打开串口失败: {response.text}")
            return False
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ 打开串口失败: {result.get('message')}")
            return False
        
        print(f"✅ 串口已打开: {result.get('message')}")
        
        # 2. 发送测试数据
        print("\n2. 发送测试数据...")
        test_messages = [
            "Hello Arduino!",
            "Test message 1",
            "Test message 2"
        ]
        
        for msg in test_messages:
            response = requests.post(f"{server_url}/serial/write", json={
                'port': port,
                'baudrate': baudrate,
                'data': msg,
                'add_newline': True
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 发送: {msg}")
                else:
                    print(f"❌ 发送失败: {msg}")
            else:
                print(f"❌ 发送请求失败: {response.text}")
            
            time.sleep(0.5)
        
        # 3. 读取串口数据
        print("\n3. 读取串口数据...")
        for i in range(3):
            response = requests.post(f"{server_url}/serial/read", json={
                'port': port,
                'baudrate': baudrate,
                'max_lines': 10
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    lines = result.get('data', [])
                    if lines:
                        print(f"📥 接收到 {len(lines)} 行数据:")
                        for line in lines:
                            print(f"   {line}")
                    else:
                        print("   (无数据)")
                else:
                    print(f"❌ 读取失败: {result.get('message')}")
            else:
                print(f"❌ 读取请求失败: {response.text}")
            
            time.sleep(1)
        
        # 4. 获取连接状态
        print("\n4. 获取连接状态...")
        response = requests.get(f"{server_url}/serial/status")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                connections = result.get('connections', [])
                print(f"📊 当前连接数: {len(connections)}")
                for conn in connections:
                    print(f"   {conn['port']} @ {conn['baudrate']} (ID: {conn['connection_id']})")
            else:
                print(f"❌ 获取状态失败: {result.get('message')}")
        
        # 5. 关闭串口连接
        print("\n5. 关闭串口连接...")
        response = requests.post(f"{server_url}/serial/close", json={
            'port': port,
            'baudrate': baudrate
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 串口已关闭: {result.get('message')}")
                return True
            else:
                print(f"❌ 关闭失败: {result.get('message')}")
        else:
            print(f"❌ 关闭请求失败: {response.text}")
        
        return False
        
    except Exception as e:
        print(f"❌ 串口调试异常: {e}")
        return False

def main():
    """主函数"""
    server_url = "http://localhost:5000"
    hex_file = "example.hex"
    
    print("RemoteFlasher 流式功能演示")
    print("=" * 50)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{server_url}/status", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器不可用: {server_url}")
            return 1
        
        status = response.json()
        print(f"✅ 服务器状态: {status.get('status')}")
        print(f"   GPIO可用: {status.get('gpio_available')}")
        print("")
        
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return 1
    
    # 检查hex文件
    if not os.path.exists(hex_file):
        print(f"❌ hex文件不存在: {hex_file}")
        print("请确保example.hex文件存在")
        return 1
    
    success_count = 0
    total_demos = 2
    
    # 演示1: 流式烧录
    if stream_flash_demo(server_url, hex_file, 
                        mcu="atmega328p", 
                        programmer="arduino", 
                        port="/dev/ttyS0",
                        baudrate="115200"):
        success_count += 1
    
    # 演示2: 串口调试
    if serial_debug_demo(server_url, "/dev/ttyS0", 9600):
        success_count += 1
    
    # 总结
    print("\n" + "=" * 50)
    print(f"演示完成: {success_count}/{total_demos} 成功")
    
    if success_count == total_demos:
        print("🎉 所有功能演示成功!")
    else:
        print("⚠️  部分演示失败")
    
    return 0 if success_count == total_demos else 1

if __name__ == '__main__':
    sys.exit(main())
