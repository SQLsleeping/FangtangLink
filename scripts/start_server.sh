#!/bin/bash
# RemoteFlasher API服务器启动脚本

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== RemoteFlasher API Server ===${NC}"
echo "配置信息："
echo "- 串口: /dev/ttyS0"
echo "- 复位GPIO: 23"
echo "- 默认MCU: atmega328p"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
source venv/bin/activate

if ! python -c "import flask" 2>/dev/null; then
    echo -e "${RED}错误: Flask未安装${NC}"
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

if ! python -c "import gpiozero" 2>/dev/null; then
    echo -e "${RED}错误: gpiozero未安装${NC}"
    echo "正在安装gpiozero..."
    pip install gpiozero
fi

# 检查串口权限
if [ ! -r "/dev/ttyS0" ]; then
    echo -e "${YELLOW}警告: 无法读取 /dev/ttyS0${NC}"
    echo "可能需要运行: sudo usermod -a -G dialout \$USER"
    echo "然后重新登录或重启"
fi

# 检查GPIO权限
if [ ! -w "/sys/class/gpio/export" ]; then
    echo -e "${YELLOW}警告: 无GPIO写权限${NC}"
    echo "可能需要运行: sudo usermod -a -G gpio \$USER"
fi

# 检查avrdude
if ! command -v avrdude &> /dev/null; then
    echo -e "${YELLOW}警告: avrdude未安装${NC}"
    echo "请运行: sudo apt-get install avrdude"
fi

echo ""
echo -e "${GREEN}启动API服务器...${NC}"
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python ../run_server.py --debug
