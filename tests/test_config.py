#!/usr/bin/env python3
"""
配置模块测试
"""

import sys
import os
import unittest

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from remote_flasher.config import get_config, Config, DevelopmentConfig, ProductionConfig

class TestConfig(unittest.TestCase):
    """配置测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = get_config()
        self.assertIsInstance(config, type)
        self.assertTrue(hasattr(config, 'DEFAULT_MCU'))
        self.assertTrue(hasattr(config, 'DEFAULT_PORT'))
        self.assertTrue(hasattr(config, 'RESET_PIN'))
    
    def test_development_config(self):
        """测试开发环境配置"""
        config = get_config('development')
        self.assertEqual(config, DevelopmentConfig)
        self.assertTrue(config.DEBUG)
    
    def test_production_config(self):
        """测试生产环境配置"""
        config = get_config('production')
        self.assertEqual(config, ProductionConfig)
        self.assertFalse(config.DEBUG)
    
    def test_config_values(self):
        """测试配置值"""
        config = get_config('development')
        
        # 测试基本配置
        self.assertEqual(config.DEFAULT_MCU, 'atmega328p')
        self.assertEqual(config.DEFAULT_PORT, '/dev/ttyS0')
        self.assertEqual(config.RESET_PIN, 23)
        self.assertEqual(config.DEFAULT_BAUDRATE, 115200)
        
        # 测试支持的设备列表
        self.assertIn('atmega328p', config.SUPPORTED_MCUS)
        self.assertIn('arduino', config.SUPPORTED_PROGRAMMERS)
        self.assertIn(115200, config.SUPPORTED_BAUDRATES)

if __name__ == '__main__':
    unittest.main()
