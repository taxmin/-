@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================
echo 在本项目目录安装「完整 Python 3.8」到 Python38Portable\
echo （含 tkinter，可与本工程一起打包；非官方 embed 小包）
echo ============================================
echo.
echo 说明见: README_嵌入式与绿色Python.txt
echo.

set "INSTALLER=%ROOT%python-3.8.10-amd64.exe"
set "TARGET_PY=%ROOT%Python38Portable\python.exe"

if exist "%TARGET_PY%" (
    echo [信息] 已存在: Python38Portable\python.exe ，跳过下载与安装。
    goto :env
)

if not exist "%INSTALLER%" (
    echo [步骤1] 正在下载 Python 3.8.10 安装包（约 27MB）...
    where curl >nul 2>&1
    if not errorlevel 1 (
        curl -L -o "%INSTALLER%" "https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe' -OutFile '%INSTALLER%' -UseBasicParsing"
    )
    if not exist "%INSTALLER%" (
        echo [错误] 下载失败。请手动下载并保存到本目录，文件名: python-3.8.10-amd64.exe
        echo 地址: https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
        pause
        exit /b 1
    )
) else (
    echo [信息] 已存在安装包: python-3.8.10-amd64.exe
)

echo.
echo [步骤2] 静默安装到: %ROOT%Python38Portable
echo （若杀毒软件拦截，请允许或改用图形界面手动安装到上述目录）
echo.
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir="%ROOT%Python38Portable" Shortcuts=0

if not exist "%TARGET_PY%" (
    echo [错误] 未检测到 Python38Portable\python.exe 。
    echo 可尝试手动运行安装包，安装路径选: %ROOT%Python38Portable
    pause
    exit /b 1
)

echo [成功] 已安装完整 Python 到 Python38Portable\
echo.

:env
set "PATH=%ROOT%Python38Portable;%PATH%"
echo [步骤3] 使用 Python38Portable 创建/更新 .venv 并安装依赖（调用 install_env.bat）...
echo.
call "%ROOT%install_env.bat"
endlocal
