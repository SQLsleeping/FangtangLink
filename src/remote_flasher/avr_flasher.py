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

try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("gpiozero not available, GPIO control disabled")

class AVRFlasher:
    """AVR单片机烧录器"""
    
    def __init__(self, config_name=None):
        self.config = get_config(config_name)
        self.logger = self._setup_logger()
        self.reset_pin = None
        self.power_pin = None
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
        """设置GPIO"""
        if not GPIO_AVAILABLE:
            self.logger.warning("gpiozero not available, skipping GPIO setup")
            return

        try:
            # 设置复位引脚 (默认为高电平，低电平有效复位)
            if self.config.RESET_PIN:
                self.reset_pin = OutputDevice(self.config.RESET_PIN, active_high=True, initial_value=True)
                self.logger.info(f"GPIO {self.config.RESET_PIN} configured for reset control")

            # 设置电源控制引脚 (可选)
            if self.config.POWER_PIN:
                self.power_pin = OutputDevice(self.config.POWER_PIN, active_high=True, initial_value=True)
                self.logger.info(f"GPIO {self.config.POWER_PIN} configured for power control")

        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
            self.reset_pin = None
            self.power_pin = None
    
    def _ensure_upload_dir(self):
        """确保上传目录存在"""
        upload_dir = Path(self.config.UPLOAD_FOLDER)
        upload_dir.mkdir(exist_ok=True)
        self.logger.info(f"Upload directory: {upload_dir.absolute()}")
    
    def reset_target(self, duration=0.1):
        """复位目标设备"""
        if not self.reset_pin:
            self.logger.warning("GPIO reset not available")
            return False

        try:
            self.logger.info("Resetting target device...")
            # 拉低复位引脚 (复位)
            self.reset_pin.off()
            time.sleep(duration)
            # 拉高复位引脚 (释放复位)
            self.reset_pin.on()
            time.sleep(0.1)  # 等待设备启动
            return True
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            return False

    def power_cycle_target(self, off_duration=0.5):
        """电源循环目标设备"""
        if not self.power_pin:
            self.logger.warning("GPIO power control not available")
            return False

        try:
            self.logger.info("Power cycling target device...")
            # 关闭电源
            self.power_pin.off()
            time.sleep(off_duration)
            # 开启电源
            self.power_pin.on()
            time.sleep(0.5)  # 等待设备启动
            return True
        except Exception as e:
            self.logger.error(f"Power cycle failed: {e}")
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

            # 烧录前复位目标设备
            self.logger.info("Preparing target device for flashing...")
            self.reset_target()

            # 构建avrdude命令
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

                # 烧录成功后重启目标设备
                self.logger.info("Restarting target device after successful flash...")
                self.reset_target(duration=0.1)

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
        try:
            if self.reset_pin:
                self.reset_pin.close()
                self.logger.info("Reset pin cleanup completed")
            if self.power_pin:
                self.power_pin.close()
                self.logger.info("Power pin cleanup completed")
        except Exception as e:
            self.logger.error(f"GPIO cleanup failed: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()
