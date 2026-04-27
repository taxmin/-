@echo off
echo ============================================
echo 切换到 Python38Portable 环境
echo ============================================
echo.

set "PYTHON_PATH=%~dp0Python38Portable\python.exe"

if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python38Portable 不存在: %PYTHON_PATH%
    pause
    exit /b 1
)

echo [OK] Python38Portable 路径: %PYTHON_PATH%
echo.

echo 正在验证依赖...
"%PYTHON_PATH%" -c "import onnxruntime, psutil, torch; print('✅ 所有依赖已安装')" 2>&1
if errorlevel 1 (
    echo [ERROR] 依赖检查失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo 请在 VSCode 中执行以下操作：
echo ============================================
echo 1. 点击右下角的 Python 版本
echo 2. 选择: %PYTHON_PATH%
echo 3. 按 Ctrl+Shift+P，输入 "Reload Window"
echo 4. 重新运行程序
echo ============================================
pause
