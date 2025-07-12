# RemoteFlasher 项目结构说明

## 概述

RemoteFlasher 是一个基于 FangTangLink 的 AVR 单片机远程烧录 API 项目，专为 Raspberry Pi 平台设计。项目采用模块化设计，将功能代码、测试代码、示例代码和文档分别组织在不同的目录中。

## 目录结构

```
RemoteFlasher/
├── src/remote_flasher/        # 核心功能模块
│   ├── __init__.py           # 包初始化文件
│   ├── config.py             # 配置管理模块
│   ├── avr_flasher.py        # AVR烧录核心模块
│   ├── api_server.py         # REST API服务器
│   └── client.py             # 客户端SDK
├── tests/                    # 测试代码
│   ├── __init__.py          # 测试包初始化
│   ├── test_config.py       # 配置模块测试
│   ├── test_client.py       # 客户端模块测试
│   └── test_gpio.py         # GPIO功能测试
├── examples/                 # 使用示例
│   ├── example.py           # 基础使用示例
│   ├── demo_flash.py        # 完整烧录演示
│   └── example.hex          # 示例hex文件
├── scripts/                  # 脚本文件
│   └── start_server.sh      # 服务器启动脚本
├── docs/                     # 文档目录
│   └── HARDWARE_SETUP.md    # 硬件配置指南
├── run_server.py            # 服务器启动器
├── run_client.py            # 客户端命令行工具
├── run_tests.py             # 测试运行器
├── setup.py                 # Python包安装脚本
├── Makefile                 # 构建和管理工具
├── requirements.txt         # 项目依赖
├── README.md               # 项目主文档
└── PROJECT_STRUCTURE.md    # 本文档
```

## 核心模块说明

### src/remote_flasher/

这是项目的核心功能模块，包含所有主要的业务逻辑：

- **`__init__.py`**: 包初始化文件，定义了包的公共接口
- **`config.py`**: 配置管理模块，包含所有配置选项和环境设置
- **`avr_flasher.py`**: AVR烧录核心模块，实现GPIO控制和avrdude调用
- **`api_server.py`**: REST API服务器，提供HTTP接口
- **`client.py`**: 客户端SDK，提供便于集成的Python接口

### tests/

测试代码目录，包含各种单元测试和功能测试：

- **`test_config.py`**: 配置模块的单元测试
- **`test_client.py`**: 客户端模块的单元测试
- **`test_gpio.py`**: GPIO功能的集成测试

### examples/

使用示例目录，包含各种使用场景的示例代码：

- **`example.py`**: 基础API使用示例
- **`demo_flash.py`**: 完整的烧录流程演示
- **`example.hex`**: 用于测试的示例hex文件

### scripts/

脚本文件目录，包含各种辅助脚本：

- **`start_server.sh`**: 服务器启动脚本，包含环境检查

### docs/

文档目录，包含项目相关文档：

- **`HARDWARE_SETUP.md`**: 详细的硬件连接和配置指南

## 启动器脚本

项目根目录下的启动器脚本提供了便捷的项目管理接口：

- **`run_server.py`**: 启动API服务器
- **`run_client.py`**: 命令行客户端工具
- **`run_tests.py`**: 测试运行器

## 构建和管理工具

- **`setup.py`**: Python包安装脚本，支持pip安装
- **`Makefile`**: 提供常用的构建、测试、清理命令
- **`requirements.txt`**: 项目依赖列表

## 使用方式

### 开发模式

```bash
# 安装依赖
make install

# 启动服务器
make run-server

# 运行测试
make test

# 代码检查
make lint
```

### 生产模式

```bash
# 安装到系统
pip install -e .

# 使用命令行工具
remote-flasher-server --host 0.0.0.0 --port 5000
remote-flasher-client --action status
```

## 设计原则

1. **模块化**: 功能代码、测试代码、示例代码分离
2. **可测试性**: 每个模块都有对应的测试
3. **易用性**: 提供多种使用方式和详细文档
4. **可扩展性**: 清晰的接口设计，便于功能扩展
5. **标准化**: 遵循Python包开发最佳实践

## 依赖关系

```
src/remote_flasher/
├── config.py (独立模块)
├── avr_flasher.py (依赖 config.py)
├── api_server.py (依赖 avr_flasher.py, config.py)
└── client.py (独立模块，通过HTTP与API通信)
```

## 扩展指南

### 添加新功能

1. 在 `src/remote_flasher/` 中添加新模块
2. 在 `tests/` 中添加对应测试
3. 在 `examples/` 中添加使用示例
4. 更新 `__init__.py` 导出新接口

### 添加新测试

1. 在 `tests/` 目录下创建测试文件
2. 使用 `unittest` 框架编写测试
3. 在 `run_tests.py` 中注册新测试

### 添加新示例

1. 在 `examples/` 目录下创建示例文件
2. 确保示例代码可以独立运行
3. 在README中添加使用说明

这种项目结构使得代码组织清晰，便于维护和扩展，同时也符合Python项目的最佳实践。
