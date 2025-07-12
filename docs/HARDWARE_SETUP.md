# 硬件连接配置指南

本文档详细说明了RemoteFlasher在Raspberry Pi上的硬件连接配置。

## 硬件需求

### Raspberry Pi
- Raspberry Pi 3/4 (推荐)
- Raspberry Pi OS (Bullseye或更新版本)
- 已启用串口功能

### Arduino/AVR目标设备
- Arduino Uno/Nano (ATmega328P)
- 或其他支持的AVR微控制器

## 连接配置

### 1. 串口连接 (/dev/ttyS0)

Raspberry Pi的硬件串口连接到Arduino：

```
Raspberry Pi GPIO    Arduino/AVR
GPIO 14 (TXD)   -->  Pin 0 (RX)
GPIO 15 (RXD)   -->  Pin 1 (TX)
GND             -->  GND
5V              -->  VIN (或3.3V到3.3V)
```

**重要说明：**
- 使用 `/dev/ttyS0` (硬件串口)，不是 `/dev/ttyAMA0`
- 确保电压兼容：Arduino Uno使用5V，某些Arduino变种使用3.3V

### 2. 复位控制 (GPIO 4)

用于程序烧录时的自动复位：

```
Raspberry Pi GPIO    Arduino
GPIO 4          -->  RST (复位引脚)
```

**复位电路：**
- 直接连接：GPIO 4 → Arduino RST
- 或通过100nF电容连接（推荐）
- 可选：添加10kΩ上拉电阻到VCC

### 3. 完整连接图

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

## Raspberry Pi配置

### 1. 启用串口

编辑 `/boot/config.txt`：
```bash
sudo nano /boot/config.txt
```

添加或修改以下行：
```
enable_uart=1
dtoverlay=disable-bt
```

### 2. 禁用串口控制台

编辑 `/boot/cmdline.txt`，移除：
```
console=serial0,115200
```

### 3. 重启系统
```bash
sudo reboot
```

### 4. 验证串口
```bash
ls -l /dev/ttyS*
# 应该看到 /dev/ttyS0
```

## 权限配置

### 1. 添加用户到相关组
```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G gpio $USER
```

### 2. 重新登录或重启
```bash
# 重新登录以使组权限生效
logout
# 或重启系统
sudo reboot
```

## 测试连接

### 1. 测试串口通信
```bash
# 发送测试数据
echo "test" > /dev/ttyS0

# 监听串口（在另一个终端）
cat /dev/ttyS0
```

### 2. 测试GPIO控制 (使用gpiozero)
```bash
# 进入项目目录并激活虚拟环境
cd /path/to/RemoteFlasher
source venv/bin/activate

# 运行GPIO测试脚本
python test_gpio.py
```

### 3. 手动测试GPIO (gpio命令)
```bash
# 设置GPIO 4为输出模式
gpio mode 4 out

# 初始化为高电平
gpio write 4 1

# 执行复位操作
echo "复位Arduino..."
gpio write 4 0  # 拉低（复位）
sleep 0.1
gpio write 4 1  # 拉高（释放复位）
echo "复位完成"
```

### 4. 使用RemoteFlasher测试
```bash
# 启动API服务器
cd /path/to/RemoteFlasher
source venv/bin/activate
python api_server.py

# 在另一个终端测试设备信息
python client.py --action info --port /dev/ttyS0

# 测试GPIO功能
python test_gpio.py
```

## 故障排除

### 串口问题

1. **权限被拒绝**
   ```bash
   sudo chmod 666 /dev/ttyS0
   # 或添加用户到dialout组
   sudo usermod -a -G dialout $USER
   ```

2. **设备不存在**
   - 检查 `/boot/config.txt` 中的 `enable_uart=1`
   - 确保已重启系统
   - 检查 `dmesg | grep tty` 输出

3. **通信失败**
   - 检查波特率设置（默认115200）
   - 验证TX/RX连接是否交叉
   - 检查GND连接

### GPIO问题

1. **GPIO权限**
   ```bash
   sudo usermod -a -G gpio $USER
   ```

2. **复位不工作**
   - 检查GPIO 4连接
   - 验证复位电路
   - 测试手动复位

### Arduino问题

1. **设备不响应**
   - 检查电源连接
   - 验证Arduino是否正常启动
   - 尝试手动复位

2. **烧录失败**
   - 确认MCU型号正确（atmega328p）
   - 检查编程器设置（arduino）
   - 验证hex文件格式

## 高级配置

### 自定义GPIO引脚

修改 `config.py`：
```python
RESET_PIN = 23  # 更改为您使用的GPIO引脚
```

### 自定义串口

修改 `config.py`：
```python
DEFAULT_PORT = '/dev/ttyS0'  # 更改为您的串口设备
```

### 添加电源控制

如果需要控制Arduino电源：
```python
POWER_PIN = 24  # 设置电源控制GPIO引脚
```

连接：
```
GPIO 24 → 继电器 → Arduino VIN
```

## 安全注意事项

1. **电压匹配**：确保Raspberry Pi和Arduino电压兼容
2. **电流限制**：GPIO输出电流有限，大功率设备需要继电器
3. **静电防护**：操作时注意防静电
4. **连接检查**：上电前仔细检查所有连接

## 支持的硬件组合

| Raspberry Pi | Arduino | 串口 | 复位GPIO | 状态 |
|-------------|---------|------|----------|------|
| Pi 3B/3B+   | Uno     | ttyS0| 23       | ✅ 测试通过 |
| Pi 4B       | Uno     | ttyS0| 23       | ✅ 测试通过 |
| Pi Zero     | Nano    | ttyS0| 23       | ✅ 应该工作 |
| Pi 2B       | Mega    | ttyS0| 23       | ⚠️ 未测试 |

如有问题，请检查硬件连接和配置设置。
