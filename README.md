# RemoteFlasher API

基于FangTangLink的AVR单片机远程烧录API，专为Raspberry Pi平台设计，提供简洁的REST API接口用于集成到其他应用中。

## 功能特性

- 🔥 **远程烧录**: 支持通过HTTP API烧录AVR单片机
- 📁 **文件上传**: 支持直接上传hex文件进行烧录
- 🌐 **URL下载**: 支持从URL下载hex文件并烧录
- 🎛️ **GPIO控制**: 使用gpiozero库控制复位信号，支持烧录前复位和烧录后重启
- 🔧 **多种MCU**: 支持多种AVR微控制器型号
- 📊 **设备信息**: 获取连接设备的详细信息
- 🐍 **Python SDK**: 提供便于集成的Python客户端库

## 支持的硬件

### 微控制器 (MCU)
- ATmega328P (Arduino Uno/Nano)
- ATmega168, ATmega8
- ATmega32U4 (Arduino Leonardo)
- ATmega2560 (Arduino Mega)
- ATtiny85, ATtiny13
- 更多AVR系列...

### 编程器
- Arduino (arduino)
- USBasp (usbasp)
- AVR ISP (avrisp)
- STK500v1/v2

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd RemoteFlasher

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装avrdude (如果未安装)
sudo apt-get update
sudo apt-get install avrdude
```

### 2. 启动API服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器
python run_server.py

# 或指定参数
python run_server.py --host 0.0.0.0 --port 5000 --debug

# 或使用Makefile
make run-server
```

### 3. 使用客户端SDK

```python
from remote_flasher import RemoteFlasherClient

# 创建客户端
client = RemoteFlasherClient("http://localhost:5000")

# 检查服务状态
status = client.get_status()
print(status)

# 烧录本地文件
result = client.flash_file(
    "firmware.hex",
    mcu="atmega328p",
    programmer="arduino",
    port="/dev/ttyS0"
)

# 从URL烧录
result = client.flash_url(
    "https://example.com/firmware.hex",
    mcu="atmega328p"
)
```

## API接口文档

### 基础信息

- **基础URL**: `http://localhost:5000`
- **内容类型**: `application/json`
- **文件上传**: `multipart/form-data`

### 接口列表

#### 1. 获取API信息
```http
GET /
```

#### 2. 获取服务状态
```http
GET /status
```

#### 3. 获取配置信息
```http
GET /config
```

#### 4. 烧录上传文件
```http
POST /flash/file
Content-Type: multipart/form-data

参数:
- file: hex文件 (必需)
- mcu: 微控制器型号 (可选)
- programmer: 编程器类型 (可选)
- port: 串口 (可选)
- baudrate: 波特率 (可选)
```

#### 5. 从URL烧录
```http
POST /flash/url
Content-Type: application/json

{
  "url": "https://example.com/firmware.hex",
  "mcu": "atmega328p",
  "programmer": "arduino",
  "port": "/dev/ttyUSB0",
  "baudrate": 115200
}
```

#### 6. 获取设备信息
```http
GET /device/info?mcu=atmega328p&programmer=arduino&port=/dev/ttyUSB0
```

## 配置说明

### 环境变量
```bash
export FLASK_ENV=development  # 或 production
export SECRET_KEY=your-secret-key
```

### 配置文件 (config.py)
主要配置项：
- `DEFAULT_MCU`: 默认微控制器型号
- `DEFAULT_PROGRAMMER`: 默认编程器类型
- `DEFAULT_PORT`: 默认串口
- `RESET_PIN`: GPIO复位引脚
- `FLASH_TIMEOUT`: 烧录超时时间

## 硬件连接

### Raspberry Pi GPIO连接
```
Raspberry Pi    Arduino/AVR Target
GPIO 23    -->  RST (复位引脚)
GND        -->  GND
```

### 串口连接
```
Raspberry Pi    Arduino/AVR Target
/dev/ttyS0 -->  通过串口连接
(GPIO 14)  -->  TX (Arduino RX)
(GPIO 15)  -->  RX (Arduino TX)
GND        -->  GND
5V/3.3V    -->  VCC
```

## 使用示例

### 命令行客户端
```bash
# 检查状态
python run_client.py --action status

# 获取设备信息
python run_client.py --action info --mcu atmega328p --port /dev/ttyS0

# 烧录文件
python run_client.py --action flash-file --file firmware.hex --mcu atmega328p

# 从URL烧录
python run_client.py --action flash-url --url https://example.com/firmware.hex

# 或使用Makefile
make run-client ARGS="--action status"
```

### Python集成示例
```python
import time
from client import RemoteFlasherClient, flash_hex_file

# 方式1: 使用客户端类
client = RemoteFlasherClient("http://192.168.1.100:5000")

# 等待服务可用
if client.wait_for_service(max_wait=30):
    result = client.flash_file("my_firmware.hex")
    if result['success']:
        print("烧录成功!")
    else:
        print(f"烧录失败: {result['message']}")

# 方式2: 使用便捷函数
result = flash_hex_file(
    "firmware.hex",
    server_url="http://192.168.1.100:5000",
    mcu="atmega328p",
    programmer="arduino"
)
```

## 故障排除

### 常见问题

1. **avrdude not found**
   ```bash
   sudo apt-get install avrdude
   ```

2. **Permission denied on serial port**
   ```bash
   sudo usermod -a -G dialout $USER
   # 重新登录或重启
   ```

3. **GPIO permission denied**
   ```bash
   sudo usermod -a -G gpio $USER
   ```

4. **Device not responding**
   - 检查硬件连接
   - 确认串口设备路径
   - 检查波特率设置
   - 尝试手动复位设备

### 日志调试
```bash
# 启用调试模式
python api_server.py --debug

# 查看日志文件
tail -f flasher.log
```

## 开发说明

### 项目结构
```
RemoteFlasher/
├── src/remote_flasher/    # 核心功能模块
│   ├── __init__.py       # 包初始化
│   ├── config.py         # 配置管理
│   ├── avr_flasher.py    # 核心烧录模块
│   ├── api_server.py     # REST API服务器
│   └── client.py         # 客户端SDK
├── tests/                # 测试代码
│   ├── __init__.py
│   ├── test_config.py    # 配置测试
│   ├── test_client.py    # 客户端测试
│   └── test_gpio.py      # GPIO测试
├── examples/             # 使用示例
│   ├── example.py        # 基础示例
│   ├── demo_flash.py     # 完整演示
│   └── example.hex       # 示例hex文件
├── scripts/              # 脚本文件
│   └── start_server.sh   # 启动脚本
├── docs/                 # 文档
│   └── HARDWARE_SETUP.md # 硬件配置指南
├── run_server.py         # 服务器启动器
├── run_client.py         # 客户端工具
├── run_tests.py          # 测试运行器
├── setup.py              # 安装脚本
├── Makefile              # 构建工具
├── requirements.txt      # 依赖列表
└── README.md             # 项目文档
```

### 扩展开发
- 添加新的MCU支持: 修改 `config.py` 中的 `SUPPORTED_MCUS`
- 添加新的编程器: 修改 `SUPPORTED_PROGRAMMERS`
- 自定义GPIO控制: 修改 `avr_flasher.py` 中的GPIO相关方法

## 许可证

本项目基于FangTangLink开发，遵循相应的开源许可证。

## 贡献

欢迎提交Issue和Pull Request来改进项目！
