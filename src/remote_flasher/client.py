"""
RemoteFlasher客户端SDK
便于其他应用集成调用AVR烧录功能
"""

import requests
import json
import time
from typing import Optional, Dict, Any, Union, Generator
from pathlib import Path

class RemoteFlasherClient:
    """RemoteFlasher API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 60):
        """
        初始化客户端
        
        Args:
            base_url: API服务器地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Request failed: {e}'
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid JSON response',
                'message': 'Server returned invalid JSON'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return self._make_request('GET', '/status')
    
    def get_config(self) -> Dict[str, Any]:
        """获取服务配置"""
        return self._make_request('GET', '/config')
    
    def get_device_info(self, 
                       mcu: str = None,
                       programmer: str = None,
                       port: str = None,
                       baudrate: int = None) -> Dict[str, Any]:
        """
        获取设备信息
        
        Args:
            mcu: 微控制器型号
            programmer: 编程器类型
            port: 串口
            baudrate: 波特率
        """
        params = {}
        if mcu:
            params['mcu'] = mcu
        if programmer:
            params['programmer'] = programmer
        if port:
            params['port'] = port
        if baudrate:
            params['baudrate'] = baudrate
        
        return self._make_request('GET', '/device/info', params=params)
    
    def flash_file(self, 
                   file_path: Union[str, Path],
                   mcu: str = None,
                   programmer: str = None,
                   port: str = None,
                   baudrate: int = None) -> Dict[str, Any]:
        """
        烧录本地hex文件
        
        Args:
            file_path: hex文件路径
            mcu: 微控制器型号
            programmer: 编程器类型
            port: 串口
            baudrate: 波特率
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'success': False,
                'error': 'File not found',
                'message': f'File not found: {file_path}'
            }
        
        # 准备参数
        params = {}
        if mcu:
            params['mcu'] = mcu
        if programmer:
            params['programmer'] = programmer
        if port:
            params['port'] = port
        if baudrate:
            params['baudrate'] = baudrate
        
        # 上传文件
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                return self._make_request('POST', '/flash/file', 
                                        files=files, params=params)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to read file: {e}'
            }
    
    def flash_url(self, 
                  url: str,
                  mcu: str = None,
                  programmer: str = None,
                  port: str = None,
                  baudrate: int = None) -> Dict[str, Any]:
        """
        从URL下载并烧录hex文件
        
        Args:
            url: hex文件URL
            mcu: 微控制器型号
            programmer: 编程器类型
            port: 串口
            baudrate: 波特率
        """
        data = {'url': url}
        
        if mcu:
            data['mcu'] = mcu
        if programmer:
            data['programmer'] = programmer
        if port:
            data['port'] = port
        if baudrate:
            data['baudrate'] = baudrate
        
        return self._make_request('POST', '/flash/url', json=data)
    
    def wait_for_service(self, max_wait: int = 30, check_interval: float = 1.0) -> bool:
        """
        等待服务可用
        
        Args:
            max_wait: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            服务是否可用
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                status = self.get_status()
                if status.get('status') == 'running':
                    return True
            except:
                pass
            
            time.sleep(check_interval)
        
        return False
    
    def is_service_available(self) -> bool:
        """检查服务是否可用"""
        try:
            status = self.get_status()
            return status.get('status') == 'running'
        except:
            return False

    def flash_file_stream(self, file_path: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        流式烧录本地hex文件

        Args:
            file_path: hex文件路径
            **kwargs: 烧录参数

        Yields:
            Dict: 流式输出数据
        """
        try:
            if not Path(file_path).exists():
                yield {"type": "error", "message": f"File not found: {file_path}"}
                return

            files = {'file': open(file_path, 'rb')}
            data = kwargs

            response = self.session.post(
                f"{self.base_url}/flash/stream",
                files=files,
                data=data,
                stream=True,
                timeout=self.timeout
            )

            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        yield data
                    except json.JSONDecodeError:
                        yield {"type": "output", "message": line}

            files['file'].close()

        except Exception as e:
            yield {"type": "error", "message": f"Stream flash failed: {str(e)}"}

    def serial_open(self, port: str = None, baudrate: int = 9600, timeout: int = 1) -> Dict[str, Any]:
        """打开串口连接"""
        try:
            data = {
                'port': port or '/dev/ttyS0',
                'baudrate': baudrate,
                'timeout': timeout
            }

            response = self.session.post(
                f"{self.base_url}/serial/open",
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return self._handle_error(f"Serial open failed: {e}")

    def serial_read(self, port: str = None, baudrate: int = 9600, max_lines: int = 100) -> Dict[str, Any]:
        """读取串口数据"""
        try:
            data = {
                'port': port or '/dev/ttyS0',
                'baudrate': baudrate,
                'max_lines': max_lines
            }

            response = self.session.post(
                f"{self.base_url}/serial/read",
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return self._handle_error(f"Serial read failed: {e}")

    def serial_write(self, data: str, port: str = None, baudrate: int = 9600, add_newline: bool = True) -> Dict[str, Any]:
        """向串口写入数据"""
        try:
            payload = {
                'port': port or '/dev/ttyS0',
                'baudrate': baudrate,
                'data': data,
                'add_newline': add_newline
            }

            response = self.session.post(
                f"{self.base_url}/serial/write",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return self._handle_error(f"Serial write failed: {e}")

    def serial_close(self, port: str = None, baudrate: int = 9600) -> Dict[str, Any]:
        """关闭串口连接"""
        try:
            data = {
                'port': port or '/dev/ttyS0',
                'baudrate': baudrate
            }

            response = self.session.post(
                f"{self.base_url}/serial/close",
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return self._handle_error(f"Serial close failed: {e}")

    def serial_status(self) -> Dict[str, Any]:
        """获取串口连接状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/serial/status",
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return self._handle_error(f"Serial status failed: {e}")

# 便捷函数
def flash_hex_file(file_path: Union[str, Path], 
                   server_url: str = "http://localhost:5000",
                   **kwargs) -> Dict[str, Any]:
    """
    便捷函数：烧录本地hex文件
    
    Args:
        file_path: hex文件路径
        server_url: API服务器地址
        **kwargs: 其他烧录参数
    """
    client = RemoteFlasherClient(server_url)
    return client.flash_file(file_path, **kwargs)

def flash_hex_url(url: str,
                  server_url: str = "http://localhost:5000",
                  **kwargs) -> Dict[str, Any]:
    """
    便捷函数：从URL烧录hex文件
    
    Args:
        url: hex文件URL
        server_url: API服务器地址
        **kwargs: 其他烧录参数
    """
    client = RemoteFlasherClient(server_url)
    return client.flash_url(url, **kwargs)

def get_device_info(server_url: str = "http://localhost:5000",
                   **kwargs) -> Dict[str, Any]:
    """
    便捷函数：获取设备信息
    
    Args:
        server_url: API服务器地址
        **kwargs: 设备参数
    """
    client = RemoteFlasherClient(server_url)
    return client.get_device_info(**kwargs)

# 示例用法
if __name__ == '__main__':
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
            exit(1)
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
            exit(1)
        result = client.flash_url(
            args.url,
            mcu=args.mcu,
            programmer=args.programmer,
            port=args.port,
            baudrate=args.baudrate
        )
    
    # 输出结果
    print(json.dumps(result, indent=2))
