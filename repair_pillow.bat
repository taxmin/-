@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [错误] 未找到 .venv，请先运行 install_env.bat
    pause
    exit /b 1
)

echo 正在安装 Pillow（提供 PIL 模块）...
"%PY%" -m pip install "Pillow==10.4.0" -i https://mirrors.aliyun.com/pypi/simple

echo.
echo 验证 from PIL import Image:
"%PY%" -c "from PIL import Image; print('PIL OK:', getattr(Image, '__version__', 'ok'))"
if errorlevel 1 (
    echo [失败] 仍无法导入 PIL，请把上方完整输出截图给维护者。
    pause
    exit /b 1
)
echo.
echo [完成] 请重新运行 run.bat
pause
