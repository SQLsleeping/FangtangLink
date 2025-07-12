"""
AVR烧录器核心模块 - RemoteFlasher API
基于FangTangLink的实现，适配Raspberry Pi环境
"""

import os
import subprocess
import time
import logging
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from .config import get_config

# 使用gpio命令行工具进行GPIO控制，不依赖gpiozero

class AVRFlasher:
    """AVR单片机烧录器"""
    
    def __init__(self, config_name=None):
        self.config = get_config(config_name)
        self.logger = self._setup_logger()
        self.gpio_available = False
        self._setup_gpio()
        self._ensure_upload_dir()
    
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('AVRFlasher')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # 文件日志
            if self.config.LOG_FILE:
                file_handler = logging.FileHandler(self.config.LOG_FILE)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    def _setup_gpio(self):
        """设置GPIO - 使用gpio命令行工具"""
        try:
            # 检查gpio命令是否可用
            result = subprocess.run(["gpio", "-v"], capture_output=True, text=True)
            if result.returncode == 0:
                self.gpio_available = True
                # 初始化GPIO 4为输出模式，默认高电平
                subprocess.run(["gpio", "mode", "4", "out"], capture_output=True, text=True, check=True)
                subprocess.run(["gpio", "write", "4", "1"], capture_output=True, text=True, check=True)
                self.logger.info("GPIO 4 configured for reset control (using gpio command)")
            else:
                self.gpio_available = False
                self.logger.warning("gpio command not available")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.gpio_available = False
            self.logger.warning(f"GPIO setup failed: {e}")
        except Exception as e:
            self.gpio_available = False
            self.logger.error(f"GPIO setup error: {e}")
    
    def _ensure_upload_dir(self):
        """确保上传目录存在"""
        upload_dir = Path(self.config.UPLOAD_FOLDER)
        upload_dir.mkdir(exist_ok=True)
        self.logger.info(f"Upload directory: {upload_dir.absolute()}")
    
    def control_arduino_reset(self, reset=True):
        """
        通过GPIO控制Arduino的复位 (使用gpio命令行工具)
        reset=True: 使Arduino进入复位状态 (GPIO 4 设为0)
        reset=False: 使Arduino退出复位状态 (GPIO 4 设为1)
        """
        if not self.gpio_available:
            self.logger.warning("GPIO控制不可用")
            return False

        state = "0" if reset else "1"
        cmd = ["gpio", "write", "4", state]  # 使用GPIO 4

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            action = "进入" if reset else "退出"
            self.logger.info(f"Arduino {action}复位状态 (GPIO 4)")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"GPIO控制失败: {e.stderr}")
            return False
        except FileNotFoundError:
            self.logger.warning("gpio命令未找到，无法控制复位")
            return False

    def reset_target(self, duration=0.1):
        """简单复位目标设备 (兼容旧接口)"""
        if not self.control_arduino_reset(reset=True):
            return False
        time.sleep(duration)
        return self.control_arduino_reset(reset=False)

    def power_cycle_target(self, off_duration=0.5):
        """电源循环目标设备 (暂不支持，因为只配置了复位引脚)"""
        self.logger.warning("电源循环功能未配置")
        return False
    
    def download_hex_file(self, url: str) -> Optional[str]:
        """从URL下载hex文件"""
        try:
            self.logger.info(f"Downloading hex file from: {url}")
            response = requests.get(url, timeout=self.config.DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.hex', 
                dir=self.config.UPLOAD_FOLDER,
                delete=False
            ) as f:
                f.write(response.text)
                temp_file = f.name
            
            self.logger.info(f"Downloaded hex file to: {temp_file}")
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None
    
    def validate_hex_file(self, file_path: str) -> bool:
        """验证hex文件格式"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return False
            
            # 检查Intel HEX格式
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if not line.startswith(':'):
                    return False
                if len(line) < 11:  # 最小长度检查
                    return False
            
            self.logger.info(f"Hex file validation passed: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Hex file validation failed: {e}")
            return False
    
    def build_avrdude_command(self, hex_file: str, **kwargs) -> list:
        """构建avrdude命令"""
        mcu = kwargs.get('mcu', self.config.DEFAULT_MCU)
        programmer = kwargs.get('programmer', self.config.DEFAULT_PROGRAMMER)
        port = kwargs.get('port', self.config.DEFAULT_PORT)
        baudrate = kwargs.get('baudrate', self.config.DEFAULT_BAUDRATE)
        
        cmd = [
            self.config.AVRDUDE_PATH,
            '-C', self.config.AVRDUDE_CONF,
            '-p', mcu,
            '-c', programmer,
            '-P', port,
            '-b', str(baudrate),
            '-U', f'flash:w:{hex_file}:i'
        ]
        
        # 添加详细输出
        if self.config.DEBUG:
            cmd.append('-v')
        
        return cmd

    def flash_hex_file(self, hex_file: str, **kwargs) -> Dict[str, Any]:
        """烧录hex文件到AVR单片机"""
        result = {
            'success': False,
            'message': '',
            'output': '',
            'error': '',
            'duration': 0
        }

        start_time = time.time()

        try:
            # 验证hex文件
            if not self.validate_hex_file(hex_file):
                result['message'] = 'Invalid hex file format'
                return result

            # 实现FangTangLink的Reset-Flash-Reset时序
            self.logger.info("开始烧录程序到Arduino...")

            # 1. 使Arduino进入复位状态
            if not self.control_arduino_reset(reset=True):
                self.logger.warning("无法控制Arduino复位，继续尝试烧录...")
            else:
                # 2. 等待一小段时间确保复位生效
                time.sleep(0.5)

                # 3. 使Arduino退出复位状态，进入bootloader
                if not self.control_arduino_reset(reset=False):
                    self.logger.warning("无法退出Arduino复位状态")
                else:
                    # 4. 给bootloader一点时间初始化
                    time.sleep(0.5)

            # 5. 构建并执行avrdude命令
            cmd = self.build_avrdude_command(hex_file, **kwargs)
            self.logger.info(f"Executing command: {' '.join(cmd)}")

            # 执行烧录
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=self.config.FLASH_TIMEOUT)
            except TypeError:
                # Python < 3.3 不支持timeout参数，使用旧方式
                stdout, stderr = process.communicate()

            result['output'] = stdout
            result['error'] = stderr
            result['duration'] = time.time() - start_time

            if process.returncode == 0:
                result['success'] = True
                result['message'] = 'Flash completed successfully'
                self.logger.info(f"Flash successful in {result['duration']:.2f}s")

                # 6. 操作后再次复位Arduino使程序开始运行 (FangTangLink方式)
                self.control_arduino_reset(reset=True)
                time.sleep(0.1)
                self.control_arduino_reset(reset=False)
                self.logger.info("Arduino已重启，程序开始运行")

            else:
                result['message'] = f'Flash failed with return code {process.returncode}'
                self.logger.error(f"Flash failed: {stderr}")

        except subprocess.TimeoutExpired:
            result['message'] = 'Flash operation timed out'
            self.logger.error("Flash operation timed out")
        except FileNotFoundError:
            result['message'] = 'avrdude not found. Please install avrdude.'
            self.logger.error("avrdude not found")
        except Exception as e:
            result['message'] = f'Flash operation failed: {str(e)}'
            self.logger.error(f"Flash operation failed: {e}")

        return result

    def perform_arduino_operation(self, hex_file=None, **kwargs):
        """
        完整的Arduino操作流程，完全模拟FangTangLink的实现
        包括复位控制和时序管理
        """
        try:
            if hex_file and not os.path.exists(hex_file):
                self.logger.error(f"文件 {hex_file} 不存在")
                return {
                    'success': False,
                    'message': f'文件 {hex_file} 不存在',
                    'error': 'File not found',
                    'output': '',
                    'duration': 0
                }

            operation_type = "上传程序" if hex_file else "执行操作"
            self.logger.info(f"开始{operation_type}到Arduino...")

            # 1. 使Arduino进入复位状态
            if not self.control_arduino_reset(reset=True):
                self.logger.error("错误: 无法控制Arduino复位")
                # 继续尝试，不返回失败

            # 2. 等待一小段时间确保复位生效
            time.sleep(0.5)

            # 3. 使Arduino退出复位状态，进入bootloader
            if not self.control_arduino_reset(reset=False):
                self.logger.error("错误: 无法退出Arduino复位状态")
                # 继续尝试，不返回失败

            # 4. 给bootloader一点时间初始化
            time.sleep(0.5)

            # 5. 执行烧录操作
            if hex_file:
                result = self.flash_hex_file(hex_file, **kwargs)
            else:
                # 如果没有hex文件，只是执行复位操作
                result = {
                    'success': True,
                    'message': '复位操作完成',
                    'error': '',
                    'output': '',
                    'duration': 1.0
                }

            # 6. 操作后再次复位Arduino使程序开始运行
            if result['success']:
                self.control_arduino_reset(reset=True)
                time.sleep(0.1)
                self.control_arduino_reset(reset=False)
                self.logger.info("Arduino已重启，程序开始运行")
                self.logger.info("操作成功完成!")
            else:
                self.logger.info("操作失败!")

            return result

        except Exception as e:
            self.logger.error(f"操作过程中发生异常: {str(e)}")
            return {
                'success': False,
                'message': f'操作异常: {str(e)}',
                'error': str(e),
                'output': '',
                'duration': 0
            }

    def flash_from_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """从URL下载并烧录hex文件"""
        # 下载文件
        hex_file = self.download_hex_file(url)
        if not hex_file:
            return {
                'success': False,
                'message': 'Failed to download hex file',
                'output': '',
                'error': '',
                'duration': 0
            }

        try:
            # 烧录文件
            result = self.flash_hex_file(hex_file, **kwargs)
            return result
        finally:
            # 清理临时文件
            try:
                os.unlink(hex_file)
                self.logger.info(f"Cleaned up temporary file: {hex_file}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary file: {e}")

    def get_device_info(self, **kwargs) -> Dict[str, Any]:
        """获取设备信息"""
        result = {
            'success': False,
            'message': '',
            'device_signature': '',
            'output': '',
            'error': ''
        }

        try:
            mcu = kwargs.get('mcu', self.config.DEFAULT_MCU)
            programmer = kwargs.get('programmer', self.config.DEFAULT_PROGRAMMER)
            port = kwargs.get('port', self.config.DEFAULT_PORT)
            baudrate = kwargs.get('baudrate', self.config.DEFAULT_BAUDRATE)

            cmd = [
                self.config.AVRDUDE_PATH,
                '-C', self.config.AVRDUDE_CONF,
                '-p', mcu,
                '-c', programmer,
                '-P', port,
                '-b', str(baudrate),
                '-v'
            ]

            self.logger.info(f"Getting device info: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=30)

            result['output'] = stdout
            result['error'] = stderr

            if process.returncode == 0:
                result['success'] = True
                result['message'] = 'Device info retrieved successfully'

                # 提取设备签名
                for line in stderr.split('\n'):
                    if 'Device signature' in line:
                        result['device_signature'] = line.strip()
                        break

            else:
                result['message'] = f'Failed to get device info: {stderr}'

        except Exception as e:
            result['message'] = f'Error getting device info: {str(e)}'
            self.logger.error(f"Error getting device info: {e}")

        return result

    def cleanup(self):
        """清理资源"""
        # 使用gpio命令行工具时无需特殊清理
        if self.gpio_available:
            self.logger.info("GPIO cleanup completed")
        pass

    def __del__(self):
        """析构函数"""
        self.cleanup()
