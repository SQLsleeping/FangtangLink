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
    from flask import Flask, request, jsonify, send_from_directory, Response, stream_template
    from flask_cors import CORS
    import threading
    import queue
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
                'gpio_available': self.flasher.gpio_available,
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
                
                # 执行烧录 (使用FangTangLink风格的完整操作流程)
                result = self.flasher.perform_arduino_operation(file_path, **flash_params)
                
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

        @app.route('/control/reset', methods=['POST'])
        def control_reset():
            """控制Arduino复位"""
            try:
                data = request.get_json() or {}
                reset_state = data.get('reset', True)  # True=进入复位, False=退出复位
                duration = data.get('duration', 0.1)   # 复位持续时间

                if reset_state in [True, 'true', '1', 1]:
                    # 进入复位状态
                    success = self.flasher.control_arduino_reset(reset=True)
                    if duration > 0:
                        import time
                        time.sleep(duration)
                        # 自动退出复位状态
                        success = success and self.flasher.control_arduino_reset(reset=False)
                        message = f"复位操作完成 (持续{duration}秒)"
                    else:
                        message = "Arduino进入复位状态"
                elif reset_state in [False, 'false', '0', 0]:
                    # 退出复位状态
                    success = self.flasher.control_arduino_reset(reset=False)
                    message = "Arduino退出复位状态"
                else:
                    return jsonify({'error': 'Invalid reset state. Use true/false'}), 400

                return jsonify({
                    'success': success,
                    'message': message,
                    'reset_state': reset_state,
                    'duration': duration
                })

            except Exception as e:
                self.logger.error(f"Reset control error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/operation/arduino', methods=['POST'])
        def arduino_operation():
            """执行完整的Arduino操作 (FangTangLink风格)"""
            try:
                # 检查是否有文件上传
                hex_file_path = None
                if 'file' in request.files:
                    file = request.files['file']
                    if file.filename != '' and self._allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        hex_file_path = os.path.join(self.config.UPLOAD_FOLDER, filename)
                        file.save(hex_file_path)

                # 获取操作参数
                flash_params = self._get_flash_params(request)

                # 执行完整的Arduino操作
                result = self.flasher.perform_arduino_operation(hex_file_path, **flash_params)

                # 清理临时文件
                if hex_file_path:
                    try:
                        os.unlink(hex_file_path)
                    except:
                        pass

                return jsonify(result)

            except Exception as e:
                self.logger.error(f"Arduino operation error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/flash/stream', methods=['POST'])
        def flash_stream():
            """流式烧录端点"""
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

                def generate():
                    """生成流式响应"""
                    try:
                        for output in self.flasher.flash_hex_file_stream(file_path, **flash_params):
                            yield f"data: {json.dumps(output)}\n\n"
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    finally:
                        # 清理文件
                        try:
                            os.unlink(file_path)
                        except:
                            pass

                return Response(
                    generate(),
                    mimetype='text/plain',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'X-Accel-Buffering': 'no'  # 禁用nginx缓冲
                    }
                )

            except Exception as e:
                self.logger.error(f"Stream flash error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/serial/open', methods=['POST'])
        def serial_open():
            """打开串口连接"""
            try:
                data = request.get_json() or {}
                port = data.get('port', self.config.DEFAULT_PORT)
                baudrate = data.get('baudrate', 9600)
                timeout = data.get('timeout', 1)

                # 存储串口连接（简化版本，实际应用中可能需要会话管理）
                serial_conn = self.flasher.open_serial_connection(port, baudrate, timeout)

                if serial_conn:
                    # 将连接存储在应用上下文中（简化处理）
                    app.serial_connections = getattr(app, 'serial_connections', {})
                    conn_id = f"{port}_{baudrate}"
                    app.serial_connections[conn_id] = serial_conn

                    return jsonify({
                        'success': True,
                        'message': f'Serial connection opened: {port} @ {baudrate}',
                        'connection_id': conn_id,
                        'port': port,
                        'baudrate': baudrate
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to open serial connection'
                    }), 500

            except Exception as e:
                self.logger.error(f"Serial open error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/serial/read', methods=['POST'])
        def serial_read():
            """读取串口数据"""
            try:
                data = request.get_json() or {}
                port = data.get('port', self.config.DEFAULT_PORT)
                baudrate = data.get('baudrate', 9600)
                max_lines = data.get('max_lines', 100)

                conn_id = f"{port}_{baudrate}"
                serial_connections = getattr(app, 'serial_connections', {})

                if conn_id not in serial_connections:
                    return jsonify({
                        'success': False,
                        'message': 'Serial connection not found. Please open connection first.'
                    }), 404

                serial_conn = serial_connections[conn_id]
                lines = self.flasher.read_serial_data(serial_conn, max_lines)

                return jsonify({
                    'success': True,
                    'data': lines,
                    'lines_count': len(lines)
                })

            except Exception as e:
                self.logger.error(f"Serial read error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/serial/write', methods=['POST'])
        def serial_write():
            """向串口写入数据"""
            try:
                data = request.get_json() or {}
                port = data.get('port', self.config.DEFAULT_PORT)
                baudrate = data.get('baudrate', 9600)
                message = data.get('data', '')
                add_newline = data.get('add_newline', True)

                if add_newline and not message.endswith('\n'):
                    message += '\n'

                conn_id = f"{port}_{baudrate}"
                serial_connections = getattr(app, 'serial_connections', {})

                if conn_id not in serial_connections:
                    return jsonify({
                        'success': False,
                        'message': 'Serial connection not found. Please open connection first.'
                    }), 404

                serial_conn = serial_connections[conn_id]
                success = self.flasher.write_serial_data(serial_conn, message)

                return jsonify({
                    'success': success,
                    'message': 'Data written to serial' if success else 'Failed to write data'
                })

            except Exception as e:
                self.logger.error(f"Serial write error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/serial/close', methods=['POST'])
        def serial_close():
            """关闭串口连接"""
            try:
                data = request.get_json() or {}
                port = data.get('port', self.config.DEFAULT_PORT)
                baudrate = data.get('baudrate', 9600)

                conn_id = f"{port}_{baudrate}"
                serial_connections = getattr(app, 'serial_connections', {})

                if conn_id in serial_connections:
                    serial_conn = serial_connections[conn_id]
                    serial_conn.close()
                    del serial_connections[conn_id]

                    return jsonify({
                        'success': True,
                        'message': f'Serial connection closed: {port}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Serial connection not found'
                    }), 404

            except Exception as e:
                self.logger.error(f"Serial close error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/serial/status', methods=['GET'])
        def serial_status():
            """获取串口连接状态"""
            try:
                serial_connections = getattr(app, 'serial_connections', {})

                connections = []
                for conn_id, conn in serial_connections.items():
                    port, baudrate = conn_id.split('_')
                    connections.append({
                        'connection_id': conn_id,
                        'port': port,
                        'baudrate': int(baudrate),
                        'is_open': conn.is_open if hasattr(conn, 'is_open') else True
                    })

                return jsonify({
                    'success': True,
                    'connections': connections,
                    'total_connections': len(connections)
                })

            except Exception as e:
                self.logger.error(f"Serial status error: {e}")
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
