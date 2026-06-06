@echo off
title TradeLens Pro Server
echo ==================================================
echo   TradeLens Pro v3.2 — 启动中...
echo ==================================================
echo.

cd /d "%~dp0"

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python 3.8+：https://www.python.org/downloads/
    echo 安装时记得勾选 "Add Python to PATH"
    pause
    exit /b 1
)

python --version

REM Auto-install dependencies
echo.
echo [信息] 正在检查依赖...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [信息] 首次运行，正在安装依赖...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败！
        echo 请尝试手动安装：
        echo   pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [信息] 依赖安装成功！
)

echo.
echo [信息] 启动后手机浏览器访问: http://本机IP:5000
echo [信息] 代理设置在: 设置页 -> 交易所API自动同步
echo.
echo [信息] 正在启动服务器...
python start_server.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 服务器启动失败！
    pause
)