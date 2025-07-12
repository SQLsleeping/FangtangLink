#!/usr/bin/env python3
"""
RemoteFlasher API服务器启动脚本
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from remote_flasher import FlasherAPI

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RemoteFlasher API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--config', default='development', help='Configuration name')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # 创建API服务器
    api = FlasherAPI(args.config)
    
    # 运行服务器
    api.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
