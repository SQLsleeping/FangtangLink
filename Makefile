# RemoteFlasher Makefile

.PHONY: help install install-dev test test-gpio run-server run-client clean lint format

# 默认目标
help:
	@echo "RemoteFlasher 可用命令:"
	@echo "  install      - 安装项目依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行所有测试"
	@echo "  test-gpio    - 运行GPIO测试"
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
	pip install -e ".[dev,gpio]"

# 运行所有测试
test:
	@echo "运行所有测试..."
	python run_tests.py

# 运行GPIO测试
test-gpio:
	@echo "运行GPIO测试..."
	python tests/test_gpio.py

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
