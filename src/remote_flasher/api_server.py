"""
REST API服务器 - RemoteFlasher API
提供简洁的HTTP API接口用于AVR单片机烧录
"""

import os
import json
import logging
from pathlib import Path
from werkzeug.utils import secure_filename

# 由于依赖安装问题，我们先创建一个简化版本，稍后可以添加Flask
try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Please install: pip install Flask Flask-CORS")

from .avr_flasher import AVRFlasher
from .config import get_config

class FlasherAPI:
    """AVR烧录器API服务"""
    
    def __init__(self, config_name=None):
        self.config = get_config(config_name)
        self.flasher = AVRFlasher(config_name)
        self.logger = self._setup_logger()
        
        if FLASK_AVAILABLE:
            self.app = self._create_flask_app()
        else:
            self.app = None
            self.logger.error("Flask not available, API server cannot start")
    
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('FlasherAPI')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _create_flask_app(self):
        """创建Flask应用"""
        app = Flask(__name__)
        app.config.from_object(self.config)
        
        # 启用CORS
        CORS(app)
        
        # 注册路由
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app):
        """注册API路由"""
        
        @app.route('/', methods=['GET'])
        def index():
            """API根路径"""
            return jsonify({
                'name': 'RemoteFlasher API',
                'version': '1.0.0',
                'description': 'AVR microcontroller programming API',
                'endpoints': {
                    'GET /': 'API information',
                    'GET /status': 'Service status',
                    'POST /flash/file': 'Flash uploaded hex file',
                    'POST /flash/url': 'Flash hex file from URL',
                    'GET /device/info': 'Get device information',
                    'GET /config': 'Get current configuration'
                }
            })
        
        @app.route('/status', methods=['GET'])
        def status():
            """获取服务状态"""
            return jsonify({
                'status': 'running',
                'flasher_ready': True,
                'gpio_available': bool(self.flasher.reset_pin),
                'upload_folder': self.config.UPLOAD_FOLDER,
                'supported_mcus': self.config.SUPPORTED_MCUS,
                'supported_programmers': self.config.SUPPORTED_PROGRAMMERS
            })
        
        @app.route('/flash/file', methods=['POST'])
        def flash_file():
            """烧录上传的hex文件"""
            try:
                # 检查文件
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not self._allowed_file(file.filename):
                    return jsonify({'error': 'Invalid file type'}), 400
                
                # 保存文件
                filename = secure_filename(file.filename)
                file_path = os.path.join(self.config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # 获取烧录参数
                flash_params = self._get_flash_params(request)
                
                # 执行烧录
                result = self.flasher.flash_hex_file(file_path, **flash_params)
                
                # 清理文件
                try:
                    os.unlink(file_path)
                except:
                    pass
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Flash file error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/flash/url', methods=['POST'])
        def flash_url():
            """从URL下载并烧录hex文件"""
            try:
                data = request.get_json()
                if not data or 'url' not in data:
                    return jsonify({'error': 'URL required'}), 400
                
                url = data['url']
                
                # 获取烧录参数
                flash_params = self._get_flash_params(request, data)
                
                # 执行烧录
                result = self.flasher.flash_from_url(url, **flash_params)
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Flash URL error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/device/info', methods=['GET'])
        def device_info():
            """获取设备信息"""
            try:
                # 获取设备参数
                device_params = self._get_flash_params(request)
                
                # 获取设备信息
                result = self.flasher.get_device_info(**device_params)
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Device info error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/config', methods=['GET'])
        def get_config():
            """获取当前配置"""
            return jsonify({
                'default_mcu': self.config.DEFAULT_MCU,
                'default_programmer': self.config.DEFAULT_PROGRAMMER,
                'default_baudrate': self.config.DEFAULT_BAUDRATE,
                'default_port': self.config.DEFAULT_PORT,
                'supported_mcus': self.config.SUPPORTED_MCUS,
                'supported_programmers': self.config.SUPPORTED_PROGRAMMERS,
                'supported_baudrates': self.config.SUPPORTED_BAUDRATES,
                'max_file_size': self.config.MAX_CONTENT_LENGTH,
                'flash_timeout': self.config.FLASH_TIMEOUT
            })
    
    def _allowed_file(self, filename):
        """检查文件类型是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
    
    def _get_flash_params(self, request, data=None):
        """从请求中提取烧录参数"""
        params = {}
        
        # 从URL参数获取
        params['mcu'] = request.args.get('mcu', self.config.DEFAULT_MCU)
        params['programmer'] = request.args.get('programmer', self.config.DEFAULT_PROGRAMMER)
        params['port'] = request.args.get('port', self.config.DEFAULT_PORT)
        params['baudrate'] = int(request.args.get('baudrate', self.config.DEFAULT_BAUDRATE))
        
        # 从JSON数据获取（优先级更高）
        if data:
            params.update({k: v for k, v in data.items() 
                          if k in ['mcu', 'programmer', 'port', 'baudrate']})
        
        return params
    
    def run(self, host=None, port=None, debug=None):
        """运行API服务器"""
        if not self.app:
            self.logger.error("Flask app not available")
            return
        
        host = host or self.config.HOST
        port = port or self.config.PORT
        debug = debug if debug is not None else self.config.DEBUG
        
        self.logger.info(f"Starting FlasherAPI server on {host}:{port}")
        
        try:
            self.app.run(host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.flasher.cleanup()

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
