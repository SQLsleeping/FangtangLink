#!/usr/bin/env python3
"""
RemoteFlasher安装脚本
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取requirements文件
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="remote-flasher",
    version="1.0.0",
    author="RemoteFlasher Team",
    author_email="support@remoteflasher.com",
    description="AVR单片机远程烧录API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/remote-flasher",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
        ],
        "gpio": [
            "gpiozero>=1.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "remote-flasher-server=remote_flasher.api_server:main",
            "remote-flasher-client=remote_flasher.client:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
