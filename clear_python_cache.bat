@echo off
chcp 65001 >nul
echo ========================================
echo   清理 Python 缓存并重启程序
echo ========================================
echo.

echo [1/3] 停止运行中的程序...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] 清理 Python 缓存文件...
cd /d "%~dp0"

:: 删除所有 __pycache__ 目录
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo   删除: %%d
        rd /s /q "%%d"
    )
)

:: 删除所有 .pyc 文件
for /r %%f in (*.pyc) do (
    if exist "%%f" (
        echo   删除: %%f
        del /f /q "%%f"
    )
)

:: 删除所有 .pyo 文件
for /r %%f in (*.pyo) do (
    if exist "%%f" (
        echo   删除: %%f
        del /f /q "%%f"
    )
)

echo.
echo [3/3] 清理完成！
echo.
echo 请手动运行 run.bat 重新启动程序
echo.
pause

