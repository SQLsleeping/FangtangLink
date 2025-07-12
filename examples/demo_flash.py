#!/usr/bin/env python3
"""
RemoteFlasher完整功能演示
演示GPIO控制的烧录流程：烧录前复位 -> 烧录 -> 烧录后重启
"""

import time
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from remote_flasher import RemoteFlasherClient, AVRFlasher

def create_demo_hex():
    """创建演示用的hex文件"""
    hex_content = """:100000000C9434000C943E000C943E000C943E0082
:100010000C943E000C943E000C943E000C943E0068
:100020000C943E000C943E000C943E000C943E0058
:100030000C943E000C943E000C943E000C943E0048
:100040000C943E000C943E000C943E000C943E0038
:100050000C943E000C943E000C943E000C943E0028
:100060000C943E000C943E000C943E000C943E0018
:100070000C943E000C943E000C943E000C943E0008
:100080000C943E000C943E000C943E000C943E00F8
:100090000C943E000C943E000C943E000C943E00E8
:1000A0000C943E000C943E000C943E000C943E00D8
:1000B0000C943E000C943E000C943E000C943E00C8
:1000C0000C943E000C943E000C943E000C943E00B8
:1000D0000C943E000C943E000C943E000C943E00A8
:1000E0000C943E000C943E000C943E000C943E0098
:1000F0000C943E000C943E000C943E000C943E0088
:10010000000000000000000000000000000000007F
:10011000000000000000000000000000000000006F
:10012000000000000000000000000000000000005F
:10013000000000000000000000000000000000004F
:10014000000000000000000000000000000000003F
:10015000000000000000000000000000000000002F
:10016000000000000000000000000000000000001F
:10017000000000000000000000000000000000000F
:1001800000000000000000000000000000000000FF
:1001900000000000000000000000000000000000EF
:1001A00000000000000000000000000000000000DF
:1001B00000000000000000000000000000000000CF
:1001C00000000000000000000000000000000000BF
:1001D00000000000000000000000000000000000AF
:1001E000000000000000000000000000000000009F
:1001F000000000000000000000000000000000008F
:10020000000000000000000000000000000000007F
:10021000000000000000000000000000000000006F
:10022000000000000000000000000000000000005F
:10023000000000000000000000000000000000004F
:10024000000000000000000000000000000000003F
:10025000000000000000000000000000000000002F
:10026000000000000000000000000000000000001F
:10027000000000000000000000000000000000000F
:1002800000000000000000000000000000000000FF
:1002900000000000000000000000000000000000EF
:1002A00000000000000000000000000000000000DF
:1002B00000000000000000000000000000000000CF
:1002C00000000000000000000000000000000000BF
:1002D00000000000000000000000000000000000AF
:1002E000000000000000000000000000000000009F
:1002F000000000000000000000000000000000008F
:10030000000000000000000000000000000000007F
:10031000000000000000000000000000000000006F
:10032000000000000000000000000000000000005F
:10033000000000000000000000000000000000004F
:10034000000000000000000000000000000000003F
:10035000000000000000000000000000000000002F
:10036000000000000000000000000000000000001F
:10037000000000000000000000000000000000000F
:1003800000000000000000000000000000000000FF
:1003900000000000000000000000000000000000EF
:1003A00000000000000000000000000000000000DF
:1003B00000000000000000000000000000000000CF
:1003C00000000000000000000000000000000000BF
:1003D00000000000000000000000000000000000AF
:1003E000000000000000000000000000000000009F
:1003F000000000000000000000000000000000008F
:10040000000000000000000000000000000000007F
:10041000000000000000000000000000000000006F
:10042000000000000000000000000000000000005F
:10043000000000000000000000000000000000004F
:10044000000000000000000000000000000000003F
:10045000000000000000000000000000000000002F
:10046000000000000000000000000000000000001F
:10047000000000000000000000000000000000000F
:1004800000000000000000000000000000000000FF
:1004900000000000000000000000000000000000EF
:1004A00000000000000000000000000000000000DF
:1004B00000000000000000000000000000000000CF
:1004C00000000000000000000000000000000000BF
:1004D00000000000000000000000000000000000AF
:1004E000000000000000000000000000000000009F
:1004F000000000000000000000000000000000008F
:10050000000000000000000000000000000000007F
:10051000000000000000000000000000000000006F
:10052000000000000000000000000000000000005F
:10053000000000000000000000000000000000004F
:10054000000000000000000000000000000000003F
:10055000000000000000000000000000000000002F
:10056000000000000000000000000000000000001F
:10057000000000000000000000000000000000000F
:1005800000000000000000000000000000000000FF
:1005900000000000000000000000000000000000EF
:1005A00000000000000000000000000000000000DF
:1005B00000000000000000000000000000000000CF
:1005C00000000000000000000000000000000000BF
:1005D00000000000000000000000000000000000AF
:1005E000000000000000000000000000000000009F
:1005F000000000000000000000000000000000008F
:10060000000000000000000000000000000000007F
:10061000000000000000000000000000000000006F
:10062000000000000000000000000000000000005F
:10063000000000000000000000000000000000004F
:10064000000000000000000000000000000000003F
:10065000000000000000000000000000000000002F
:10066000000000000000000000000000000000001F
:10067000000000000000000000000000000000000F
:1006800011241FBECFEFD8E0DEBFCDBF21E0A0E0B1E001C01D92A930B207E1F70E9440000C9400
:10068000000000000000000000000000000000008F
:00000001FF"""
    
    demo_file = "demo_blink.hex"
    with open(demo_file, 'w') as f:
        f.write(hex_content)
    
    print(f"✓ 创建演示hex文件: {demo_file}")
    return demo_file

def demo_direct_flash():
    """演示直接使用AVRFlasher进行烧录"""
    print("\n=== 直接烧录演示 ===")
    
    try:
        # 创建演示文件
        hex_file = create_demo_hex()
        
        # 初始化烧录器
        flasher = AVRFlasher()
        
        # 检查GPIO状态
        if flasher.reset_pin:
            print(f"✓ GPIO {flasher.config.RESET_PIN} 已配置用于复位控制")
        else:
            print("⚠️  GPIO复位功能不可用")
        
        # 执行烧录
        print("\n开始烧录流程...")
        print("1. 烧录前复位设备")
        print("2. 执行avrdude烧录")
        print("3. 烧录后重启设备")
        
        result = flasher.flash_hex_file(
            hex_file,
            mcu="atmega328p",
            programmer="arduino",
            port="/dev/ttyS0",
            baudrate=115200
        )
        
        # 显示结果
        if result['success']:
            print(f"\n🎉 烧录成功!")
            print(f"   耗时: {result['duration']:.2f}秒")
            print("   设备已自动重启")
        else:
            print(f"\n❌ 烧录失败: {result['message']}")
            if result['error']:
                print(f"   错误详情: {result['error']}")
        
        # 清理
        flasher.cleanup()
        os.unlink(hex_file)
        
        return result['success']
        
    except Exception as e:
        print(f"❌ 直接烧录演示失败: {e}")
        return False

def demo_api_flash():
    """演示通过API进行烧录"""
    print("\n=== API烧录演示 ===")
    
    try:
        # 创建演示文件
        hex_file = create_demo_hex()
        
        # 创建API客户端
        client = RemoteFlasherClient("http://localhost:5000")
        
        # 检查服务状态
        print("检查API服务状态...")
        status = client.get_status()
        
        if status.get('status') != 'running':
            print("❌ API服务不可用，请先启动服务器:")
            print("   python api_server.py")
            return False
        
        print(f"✓ API服务运行正常")
        print(f"   GPIO可用: {status.get('gpio_available', False)}")
        
        # 执行烧录
        print("\n通过API执行烧录...")
        result = client.flash_file(
            hex_file,
            mcu="atmega328p",
            programmer="arduino",
            port="/dev/ttyS0",
            baudrate=115200
        )
        
        # 显示结果
        if result.get('success'):
            print(f"\n🎉 API烧录成功!")
            print(f"   耗时: {result.get('duration', 0):.2f}秒")
            print("   设备已自动重启")
        else:
            print(f"\n❌ API烧录失败: {result.get('message', '未知错误')}")
            if result.get('error'):
                print(f"   错误详情: {result['error']}")
        
        # 清理
        os.unlink(hex_file)
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ API烧录演示失败: {e}")
        return False

def demo_gpio_control():
    """演示GPIO控制功能"""
    print("\n=== GPIO控制演示 ===")
    
    try:
        flasher = AVRFlasher()
        
        if not flasher.reset_pin:
            print("⚠️  GPIO复位功能不可用，跳过演示")
            return True
        
        print(f"使用GPIO {flasher.config.RESET_PIN}进行复位控制演示...")
        
        # 演示复位操作
        print("\n1. 执行复位操作...")
        result1 = flasher.reset_target(duration=0.2)
        if result1:
            print("   ✓ 复位成功 (GPIO 23: 高->低->高)")
        else:
            print("   ❌ 复位失败")
        
        time.sleep(1)
        
        # 演示电源循环 (如果配置了电源引脚)
        if flasher.power_pin:
            print("\n2. 执行电源循环...")
            result2 = flasher.power_cycle_target(off_duration=1.0)
            if result2:
                print("   ✓ 电源循环成功")
            else:
                print("   ❌ 电源循环失败")
        else:
            print("\n2. 电源循环功能未配置，跳过")
            result2 = True
        
        # 清理
        flasher.cleanup()
        
        return result1 and result2
        
    except Exception as e:
        print(f"❌ GPIO控制演示失败: {e}")
        return False

def main():
    """主演示函数"""
    print("RemoteFlasher 完整功能演示")
    print("=" * 50)
    print("演示内容:")
    print("1. GPIO控制功能")
    print("2. 直接烧录 (包含烧录前复位和烧录后重启)")
    print("3. API烧录")
    print("")
    
    # 检查环境
    if not Path("venv").exists():
        print("❌ 虚拟环境不存在，请先运行:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install -r requirements.txt")
        return 1
    
    success_count = 0
    total_demos = 3
    
    try:
        # 演示1: GPIO控制
        if demo_gpio_control():
            success_count += 1
        
        # 演示2: 直接烧录
        if demo_direct_flash():
            success_count += 1
        
        # 演示3: API烧录
        if demo_api_flash():
            success_count += 1
        
        # 总结
        print("\n" + "=" * 50)
        print(f"演示完成: {success_count}/{total_demos} 成功")
        
        if success_count == total_demos:
            print("🎉 所有功能演示成功!")
            print("\nRemoteFlasher已准备就绪，可以集成到您的应用中。")
        else:
            print("⚠️  部分演示失败，请检查:")
            print("   1. 硬件连接是否正确")
            print("   2. avrdude是否已安装")
            print("   3. 串口权限是否正确")
            print("   4. API服务器是否运行")
        
        return 0 if success_count == total_demos else 1
        
    except KeyboardInterrupt:
        print("\n\n用户中断演示")
        return 1
    except Exception as e:
        print(f"\n\n演示过程中发生错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
