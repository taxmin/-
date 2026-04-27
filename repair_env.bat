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

echo ============================================
echo 一键补全依赖（按 requirements.txt 重装 + OpenCV 修正）
echo ============================================
echo.

echo [1/3] pip install -r requirements.txt ...
"%PY%" -m pip install -r "%ROOT%requirements.txt" -i https://mirrors.aliyun.com/pypi/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络或换清华镜像。
    pause
    exit /b 1
)

echo.
echo [2/3] 统一 OpenCV，并确保 Pillow ...
"%PY%" -m pip uninstall -y opencv-python opencv-python-headless 2>nul
"%PY%" -m pip install opencv-contrib-python==4.6.0.66 "Pillow==10.4.0" -i https://mirrors.aliyun.com/pypi/simple

echo.
echo [3/3] 冒烟检查（cv2 / numpy / PIL / pyperclip / PyQt5）...
"%PY%" "%ROOT%smoke_imports.py"
if errorlevel 1 (
    echo.
    echo [失败] 仍有模块缺失，请把上方输出截图给维护者。
    pause
    exit /b 1
)

echo.
echo [完成] 请运行 run.bat
pause
