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

echo 正在卸载可能冲突的 opencv 包...
"%PY%" -m pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python 2>nul

echo 正在安装 opencv-contrib-python==4.6.0.66 ...
"%PY%" -m pip install opencv-contrib-python==4.6.0.66 -i https://mirrors.aliyun.com/pypi/simple

echo.
echo 验证 import cv2:
"%PY%" -c "import cv2; print('cv2 OK:', cv2.__version__)"
if errorlevel 1 (
    echo [失败] 仍无法导入 cv2，请把上方完整输出截图给维护者。
    pause
    exit /b 1
)
echo.
echo [完成] 请重新运行 run.bat
pause
