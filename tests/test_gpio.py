#!/usr/bin/env python3
"""
GPIO功能测试脚本
测试gpiozero库的GPIO控制功能
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from remote_flasher import AVRFlasher

def test_gpio_availability():
    """测试GPIO可用性"""
    print("=== GPIO可用性测试 ===")
    
    try:
        from gpiozero import OutputDevice
        print("✓ gpiozero库可用")
        return True
    except ImportError as e:
        print(f"✗ gpiozero库不可用: {e}")
        return False

def test_flasher_gpio():
    """测试AVRFlasher的GPIO功能"""
    print("\n=== AVRFlasher GPIO测试 ===")
    
    try:
        flasher = AVRFlasher()
        
        # 检查GPIO引脚是否初始化
        if flasher.reset_pin:
            print(f"✓ 复位引脚 (GPIO {flasher.config.RESET_PIN}) 已初始化")
        else:
            print("✗ 复位引脚未初始化")
            
        if flasher.power_pin:
            print(f"✓ 电源引脚 (GPIO {flasher.config.POWER_PIN}) 已初始化")
        else:
            print("ℹ 电源引脚未配置 (正常)")
            
        return flasher
        
    except Exception as e:
        print(f"✗ AVRFlasher初始化失败: {e}")
        return None

def test_reset_function(flasher):
    """测试复位功能"""
    print("\n=== 复位功能测试 ===")
    
    if not flasher or not flasher.reset_pin:
        print("✗ 无法测试复位功能 - GPIO未初始化")
        return False
    
    try:
        print("执行复位操作...")
        result = flasher.reset_target(duration=0.2)
        
        if result:
            print("✓ 复位操作成功")
            print("  - GPIO 23 拉低 0.2秒")
            print("  - GPIO 23 拉高")
            print("  - 等待设备启动")
        else:
            print("✗ 复位操作失败")
            
        return result
        
    except Exception as e:
        print(f"✗ 复位测试失败: {e}")
        return False

def test_power_cycle_function(flasher):
    """测试电源循环功能"""
    print("\n=== 电源循环测试 ===")
    
    if not flasher or not flasher.power_pin:
        print("ℹ 跳过电源循环测试 - 电源引脚未配置")
        return True
    
    try:
        print("执行电源循环...")
        result = flasher.power_cycle_target(off_duration=1.0)
        
        if result:
            print("✓ 电源循环成功")
        else:
            print("✗ 电源循环失败")
            
        return result
        
    except Exception as e:
        print(f"✗ 电源循环测试失败: {e}")
        return False

def test_manual_gpio_control():
    """手动GPIO控制测试"""
    print("\n=== 手动GPIO控制测试 ===")
    
    try:
        from gpiozero import OutputDevice
        
        # 测试GPIO 23
        print("测试GPIO 23控制...")
        reset_pin = OutputDevice(23, active_high=True, initial_value=True)
        
        print("  - 初始状态: 高电平")
        time.sleep(1)
        
        print("  - 拉低 (复位)")
        reset_pin.off()
        time.sleep(0.5)
        
        print("  - 拉高 (释放复位)")
        reset_pin.on()
        time.sleep(0.5)
        
        print("✓ 手动GPIO控制成功")
        
        # 清理
        reset_pin.close()
        return True
        
    except Exception as e:
        print(f"✗ 手动GPIO控制失败: {e}")
        return False

def main():
    """主测试函数"""
    print("RemoteFlasher GPIO功能测试")
    print("=" * 50)
    
    # 检查是否在Raspberry Pi上运行
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        if 'Raspberry Pi' not in cpuinfo:
            print("⚠️  警告: 似乎不在Raspberry Pi上运行")
            print("   GPIO功能可能不可用")
    except:
        pass
    
    success_count = 0
    total_tests = 0
    
    # 测试1: GPIO库可用性
    total_tests += 1
    if test_gpio_availability():
        success_count += 1
    
    # 测试2: AVRFlasher GPIO初始化
    total_tests += 1
    flasher = test_flasher_gpio()
    if flasher and flasher.reset_pin:
        success_count += 1
    
    # 测试3: 复位功能
    total_tests += 1
    if test_reset_function(flasher):
        success_count += 1
    
    # 测试4: 电源循环功能 (可选)
    if flasher and flasher.power_pin:
        total_tests += 1
        if test_power_cycle_function(flasher):
            success_count += 1
    
    # 测试5: 手动GPIO控制
    total_tests += 1
    if test_manual_gpio_control():
        success_count += 1
    
    # 清理资源
    if flasher:
        flasher.cleanup()
    
    # 测试结果
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过! GPIO功能正常")
        return 0
    else:
        print("⚠️  部分测试失败，请检查:")
        print("   1. 是否在Raspberry Pi上运行")
        print("   2. 是否有GPIO权限 (sudo usermod -a -G gpio $USER)")
        print("   3. 硬件连接是否正确")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        sys.exit(1)
