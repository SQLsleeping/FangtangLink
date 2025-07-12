"""
配置文件 - RemoteFlasher API
基于FangTangLink的配置，适配Raspberry Pi环境
"""

import os

# 基本配置
class Config:
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'hex', 'bin'}
    
    # AVR配置
    DEFAULT_MCU = 'atmega328p'
    DEFAULT_PROGRAMMER = 'arduino'
    DEFAULT_BAUDRATE = 115200
    DEFAULT_PORT = '/dev/ttyS0'  # 用户指定的串口

    # GPIO配置 (Raspberry Pi)
    RESET_PIN = 4   # GPIO 4 连接Arduino RST引脚
    POWER_PIN = None  # 可选的电源控制引脚
    
    # avrdude配置
    AVRDUDE_PATH = '/usr/bin/avrdude'  # avrdude可执行文件路径
    AVRDUDE_CONF = '/etc/avrdude.conf'  # avrdude配置文件路径
    
    # 超时配置
    FLASH_TIMEOUT = 60  # 烧录超时时间（秒）
    DOWNLOAD_TIMEOUT = 30  # 下载超时时间（秒）
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'flasher.log'
    
    # 支持的MCU类型
    SUPPORTED_MCUS = [
        'atmega328p', 'atmega168', 'atmega8', 'atmega32u4',
        'atmega2560', 'atmega1280', 'attiny85', 'attiny13'
    ]
    
    # 支持的编程器类型
    SUPPORTED_PROGRAMMERS = [
        'arduino', 'usbasp', 'avrisp', 'avrispmkII', 'stk500v1', 'stk500v2'
    ]
    
    # 常用波特率
    SUPPORTED_BAUDRATES = [9600, 19200, 38400, 57600, 115200]

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    def __init__(self):
        super().__init__()
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("No SECRET_KEY set for production environment")

# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    UPLOAD_FOLDER = 'test_uploads'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])
