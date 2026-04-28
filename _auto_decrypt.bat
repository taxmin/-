@echo off
REM Auto-decrypt script for AES-256 encrypted files
set "PYTHON_EXE=%~dp0Python38Portable\python.exe"

if exist "%~dp0public.py.enc" (
    if not exist "%~dp0public.py" (
        echo [AUTO-DECRYPT] Decrypting public.py.enc...
        "%PYTHON_EXE%" "%~dp0_tools\encrypt_core_files_aes.py" decrypt
        if errorlevel 1 (
            echo [ERROR] Decryption failed!
            exit /b 1
        )
        echo [OK] Decrypted successfully
    )
)

if exist "%~dp0task_list\task.py.enc" (
    if not exist "%~dp0task_list\task.py" (
        echo [AUTO-DECRYPT] Decrypting task_list/task.py.enc...
        "%PYTHON_EXE%" "%~dp0_tools\encrypt_core_files_aes.py" decrypt
        if errorlevel 1 (
            echo [ERROR] Decryption failed!
            exit /b 1
        )
        echo [OK] Decrypted successfully
    )
)

if exist "%~dp0dxGame\dx.py.enc" (
    if not exist "%~dp0dxGame\dx.py" (
        echo [AUTO-DECRYPT] Decrypting dxGame/dx.py.enc...
        "%PYTHON_EXE%" "%~dp0_tools\encrypt_core_files_aes.py" decrypt
        if errorlevel 1 (
            echo [ERROR] Decryption failed!
            exit /b 1
        )
        echo [OK] Decrypted successfully
    )
)

if exist "%~dp0dxGame\dx_vnc.py.enc" (
    if not exist "%~dp0dxGame\dx_vnc.py" (
        echo [AUTO-DECRYPT] Decrypting dxGame/dx_vnc.py.enc...
        "%PYTHON_EXE%" "%~dp0_tools\encrypt_core_files_aes.py" decrypt
        if errorlevel 1 (
            echo [ERROR] Decryption failed!
            exit /b 1
        )
        echo [OK] Decrypted successfully
    )
)

if exist "%~dp0dxGame\dx_vnckm.py.enc" (
    if not exist "%~dp0dxGame\dx_vnckm.py" (
        echo [AUTO-DECRYPT] Decrypting dxGame/dx_vnckm.py.enc...
        "%PYTHON_EXE%" "%~dp0_tools\encrypt_core_files_aes.py" decrypt
        if errorlevel 1 (
            echo [ERROR] Decryption failed!
            exit /b 1
        )
        echo [OK] Decrypted successfully
    )
)
