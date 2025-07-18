# RemoteFlasher Makefile

.PHONY: help install install-dev test run-server run-client clean lint format reset-test test-features demo-stream

# 默认目标
help:
	@echo "RemoteFlasher 可用命令:"
	@echo "  install      - 安装项目依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行所有测试"
	@echo "  test-features- 测试新功能(流式烧录和串口调试)"
	@echo "  reset-test   - 测试GPIO复位功能"
	@echo "  demo-stream  - 运行流式烧录演示"
	@echo "  run-server   - 启动API服务器"
	@echo "  run-client   - 运行客户端工具"
	@echo "  clean        - 清理临时文件"
	@echo "  lint         - 代码检查"
	@echo "  format       - 代码格式化"

# 安装依赖
install:
	@echo "安装项目依赖..."
	pip install -r requirements.txt

# 安装开发依赖
install-dev: install
	@echo "安装开发依赖..."
	pip install -e ".[dev]"

# 运行所有测试
test:
	@echo "运行所有测试..."
	python run_tests.py

# 测试新功能
test-features:
	@echo "测试新功能(流式烧录和串口调试)..."
	python tests/test_new_features.py

# 运行流式烧录演示
demo-stream:
	@echo "运行流式烧录演示..."
	python examples/stream_flash_demo.py

# 测试GPIO复位功能
reset-test:
	@echo "测试GPIO复位功能..."
	@echo "手动测试GPIO 4复位控制:"
	@echo "1. 设置GPIO 4为输出: gpio mode 4 out"
	@echo "2. 复位操作: gpio write 4 0; sleep 0.1; gpio write 4 1"
	@echo "3. 或使用API: curl -X POST -H 'Content-Type: application/json' -d '{\"reset\": true, \"duration\": 0.2}' http://localhost:5000/control/reset"

# 启动API服务器
run-server:
	@echo "启动API服务器..."
	python run_server.py --debug

# 运行客户端工具
run-client:
	@echo "运行客户端工具..."
	@echo "用法: make run-client ARGS='--action status'"
	python run_client.py $(ARGS)

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage

# 代码检查
lint:
	@echo "代码检查..."
	flake8 src/ tests/ --max-line-length=100

# 代码格式化
format:
	@echo "代码格式化..."
	black src/ tests/ examples/ --line-length=100

# 构建分发包
build:
	@echo "构建分发包..."
	python setup.py sdist bdist_wheel

# 安装到系统
install-system:
	@echo "安装到系统..."
	pip install -e .

# 卸载
uninstall:
	@echo "卸载..."
	pip uninstall remote-flasher -y
