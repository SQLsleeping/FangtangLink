#!/usr/bin/env python3
"""
RemoteFlasher测试运行脚本
"""

import sys
import os
import subprocess
from pathlib import Path

def run_config_test():
    """运行配置测试"""
    print("=== 运行配置测试 ===")
    test_file = Path(__file__).parent / "tests" / "test_config.py"

    try:
        result = subprocess.run([sys.executable, str(test_file)],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行配置测试失败: {e}")
        return False

def run_demo():
    """运行演示"""
    print("\n=== 运行功能演示 ===")
    demo_file = Path(__file__).parent / "examples" / "demo_flash.py"
    
    try:
        result = subprocess.run([sys.executable, str(demo_file)], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行演示失败: {e}")
        return False

def run_client_test():
    """运行客户端测试"""
    print("\n=== 运行客户端测试 ===")
    test_file = Path(__file__).parent / "tests" / "test_client.py"

    try:
        result = subprocess.run([sys.executable, str(test_file)],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行客户端测试失败: {e}")
        return False

def main():
    """主函数"""
    print("RemoteFlasher 测试套件")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3

    # 运行配置测试
    if run_config_test():
        success_count += 1

    # 运行客户端测试
    if run_client_test():
        success_count += 1

    # 运行演示
    if run_demo():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
