"""
RemoteFlasher - AVR单片机远程烧录API

基于FangTangLink的AVR单片机远程烧录API，专为Raspberry Pi平台设计，
提供简洁的REST API接口用于集成到其他应用中。

主要功能:
- AVR单片机远程烧录
- GPIO控制复位和电源
- RESTful API接口
- Python客户端SDK
"""

__version__ = "1.0.0"
__author__ = "RemoteFlasher Team"
__email__ = "support@remoteflasher.com"

from .config import get_config, Config
from .avr_flasher import AVRFlasher
from .api_server import FlasherAPI
from .client import RemoteFlasherClient, flash_hex_file, flash_hex_url, get_device_info

__all__ = [
    'get_config',
    'Config', 
    'AVRFlasher',
    'FlasherAPI',
    'RemoteFlasherClient',
    'flash_hex_file',
    'flash_hex_url', 
    'get_device_info'
]
