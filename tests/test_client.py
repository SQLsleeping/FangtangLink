#!/usr/bin/env python3
"""
客户端模块测试
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from remote_flasher.client import RemoteFlasherClient

class TestRemoteFlasherClient(unittest.TestCase):
    """客户端测试类"""
    
    def setUp(self):
        """测试设置"""
        self.client = RemoteFlasherClient("http://localhost:5000")
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertEqual(self.client.base_url, "http://localhost:5000")
        self.assertEqual(self.client.timeout, 60)
        self.assertIsNotNone(self.client.session)
    
    @patch('requests.Session.request')
    def test_get_status(self, mock_request):
        """测试获取状态"""
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'running',
            'gpio_available': True
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 测试
        result = self.client.get_status()
        
        # 验证
        self.assertEqual(result['status'], 'running')
        self.assertTrue(result['gpio_available'])
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_get_config(self, mock_request):
        """测试获取配置"""
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'default_mcu': 'atmega328p',
            'default_port': '/dev/ttyS0'
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 测试
        result = self.client.get_config()
        
        # 验证
        self.assertEqual(result['default_mcu'], 'atmega328p')
        self.assertEqual(result['default_port'], '/dev/ttyS0')
    
    def test_url_construction(self):
        """测试URL构造"""
        # 测试去除尾部斜杠
        client = RemoteFlasherClient("http://localhost:5000/")
        self.assertEqual(client.base_url, "http://localhost:5000")
    
    @patch('requests.Session.request')
    def test_request_error_handling(self, mock_request):
        """测试请求错误处理"""
        # 模拟请求异常
        mock_request.side_effect = Exception("Connection error")
        
        # 测试
        result = self.client.get_status()
        
        # 验证错误处理
        self.assertFalse(result.get('success', True))
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()
