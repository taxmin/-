@echo off
chcp 65001 >nul
echo ========================================
echo   多开框架 Web 监控面板
echo ========================================
echo.

REM 检查Python是否可用
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python
    pause
    exit /b 1
)

echo ✅ 正在启动 Web 监控面板...
echo.
echo 📍 访问地址: http://localhost:8080
echo 📍 按 Ctrl+C 停止服务
echo.
echo ========================================
echo.

REM 启动监控服务
python web_monitor.py

pause
