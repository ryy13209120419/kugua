@echo off
chcp 65001 >nul
title 苦瓜大王交易复盘工具 - 环境配置

echo ╔══════════════════════════════════════════════════╗
echo ║      苦瓜大王交易复盘工具 - 环境配置向导        ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 正在检测 Python 环境...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    echo 安装完成后重新运行本脚本即可。
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

echo 正在安装依赖包...
pip install flask>=3.0.0 flask-cors>=4.0.0 waitress>=2.1.2 requests>=2.31.0 -q
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 依赖安装失败，请尝试手动运行:
    echo pip install flask flask-cors waitress requests
    pause
    exit /b 1
)

echo ✅ 依赖安装完成！
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║               🚀 如何使用                       ║
echo ╠══════════════════════════════════════════════════╣
echo ║  1. 双击 index.html 打开工具（基础模式）        ║
echo ║  2. 运行 start.bat 启动服务器（完整模式）       ║
echo ║  3. 手机浏览器打开工具也可使用                  ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 详细使用说明请阅读「使用说明.txt」
echo.
pause
