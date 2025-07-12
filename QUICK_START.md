# RemoteFlasher 快速开始

## 概述

RemoteFlasher是基于FangTangLink的AVR单片机远程烧录API，专为Raspberry Pi设计，使用GPIO 4控制Arduino复位，采用Reset-Flash-Reset时序确保烧录成功。

## 硬件连接

```
Raspberry Pi                Arduino Uno
┌─────────────┐            ┌─────────────┐
│ GPIO 14(TX) │────────────│ Pin 0 (RX)  │
│ GPIO 15(RX) │────────────│ Pin 1 (TX)  │
│ GPIO 4      │────────────│ RST         │
│ GND         │────────────│ GND         │
│ 5V          │────────────│ VIN         │
└─────────────┘            └─────────────┘
```

## 快速安装

```bash
# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install avrdude wiringpi

# 2. 克隆并安装
git clone <your-repo-url>
cd RemoteFlasher
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动服务器
make run-server
# 或
python run_server.py --debug
```

## 基本使用

### 1. 检查状态
```bash
curl http://localhost:5000/status
```

### 2. 测试GPIO控制
```bash
make reset-test
```

### 3. 烧录Arduino
```bash
# 上传文件烧录
curl -X POST -F "file=@firmware.hex" \
     "http://localhost:5000/flash/file?mcu=atmega328p&port=/dev/ttyS0"

# 复位控制
curl -X POST -H "Content-Type: application/json" \
     -d '{"reset": true, "duration": 0.2}' \
     http://localhost:5000/control/reset
```

### 4. Python客户端
```python
from remote_flasher import RemoteFlasherClient

client = RemoteFlasherClient("http://localhost:5000")
result = client.flash_file("firmware.hex", mcu="atmega328p", port="/dev/ttyS0")

if result['success']:
    print("烧录成功！")
```

## 主要API端点

- `GET /status` - 服务状态
- `POST /flash/file` - 烧录上传文件
- `POST /flash/url` - 从URL烧录
- `POST /control/reset` - 控制复位
- `POST /operation/arduino` - 完整Arduino操作
- `GET /device/info` - 获取设备信息

## 常用命令

```bash
# Makefile命令
make help          # 显示帮助
make run-server    # 启动服务器
make reset-test    # 测试GPIO复位
make test          # 运行测试
make clean         # 清理文件

# 手动GPIO测试
gpio mode 4 out    # 设置GPIO 4为输出
gpio write 4 0     # 复位
gpio write 4 1     # 释放复位

# 客户端工具
python run_client.py --action status
python run_client.py --action flash-file --file firmware.hex
```

## 支持的硬件

### MCU类型
- ATmega328P (Arduino Uno/Nano)
- ATmega168, ATmega8
- ATmega32U4 (Arduino Leonardo)
- ATmega2560 (Arduino Mega)
- ATtiny85, ATtiny13

### 编程器
- arduino (Arduino bootloader)
- usbasp (USBasp)
- avrisp (AVR ISP)
- stk500v1/v2

## 故障排除

### GPIO不工作
```bash
# 检查wiringpi
gpio -v

# 检查权限
sudo usermod -a -G gpio $USER

# 手动测试
gpio mode 4 out
gpio write 4 0; gpio write 4 1
```

### 烧录失败
- 检查串口: `/dev/ttyS0`
- 检查avrdude: `avrdude -?`
- 检查硬件连接
- 查看日志: `tail -f flasher.log`

## 项目结构

```
RemoteFlasher/
├── src/remote_flasher/    # 核心功能
├── tests/                 # 测试代码
├── examples/              # 使用示例
├── docs/                  # 文档
├── run_server.py          # 服务器启动器
├── run_client.py          # 客户端工具
├── Makefile               # 构建工具
└── README.md              # 详细文档
```

更多详细信息请参考 [README.md](README.md) 和 [硬件配置指南](docs/HARDWARE_SETUP.md)。
