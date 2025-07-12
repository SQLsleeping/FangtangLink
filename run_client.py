#!/usr/bin/env python3
"""
RemoteFlasher客户端命令行工具
"""

import sys
import os
import json
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from remote_flasher import RemoteFlasherClient

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RemoteFlasher Client')
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='API server URL')
    parser.add_argument('--action', choices=['status', 'config', 'info', 'flash-file', 'flash-url'],
                       required=True, help='Action to perform')
    parser.add_argument('--file', help='Hex file path (for flash-file)')
    parser.add_argument('--url', help='Hex file URL (for flash-url)')
    parser.add_argument('--mcu', help='MCU type')
    parser.add_argument('--programmer', help='Programmer type')
    parser.add_argument('--port', help='Serial port')
    parser.add_argument('--baudrate', type=int, help='Baud rate')
    
    args = parser.parse_args()
    
    client = RemoteFlasherClient(args.server)
    
    # 执行操作
    if args.action == 'status':
        result = client.get_status()
    elif args.action == 'config':
        result = client.get_config()
    elif args.action == 'info':
        result = client.get_device_info(
            mcu=args.mcu,
            programmer=args.programmer,
            port=args.port,
            baudrate=args.baudrate
        )
    elif args.action == 'flash-file':
        if not args.file:
            print("Error: --file required for flash-file action")
            sys.exit(1)
        result = client.flash_file(
            args.file,
            mcu=args.mcu,
            programmer=args.programmer,
            port=args.port,
            baudrate=args.baudrate
        )
    elif args.action == 'flash-url':
        if not args.url:
            print("Error: --url required for flash-url action")
            sys.exit(1)
        result = client.flash_url(
            args.url,
            mcu=args.mcu,
            programmer=args.programmer,
            port=args.port,
            baudrate=args.baudrate
        )
    
    # 输出结果
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
