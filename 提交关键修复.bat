@echo off
chcp 65001 >nul
echo ============================================
echo 提交关键修复文件到 Git 仓库
echo ============================================
echo.

echo [步骤1] 添加 dxpyd 模块初始化文件...
git add dxGame/dx_lib/x64/__init__.py
git add dxGame/dx_lib/x86/__init__.py
echo [完成] 已添加 __init__.py 文件
echo.

echo [步骤2] 添加增强的安装脚本...
git add install_env.bat
echo [完成] 已添加 install_env.bat
echo.

echo [步骤3] 添加部署文档...
git add 部署与使用指南.md
git add dxpyd导入问题修复说明.md
git add 稳定性修复总结.md
echo [完成] 已添加文档文件
echo.

echo [步骤4] 检查暂存状态...
git status --short
echo.

echo ============================================
echo 准备提交以下文件:
echo   - dxGame/dx_lib/x64/__init__.py (新增)
echo   - dxGame/dx_lib/x86/__init__.py (新增)
echo   - install_env.bat (增强版)
echo   - 部署与使用指南.md (新增)
echo   - dxpyd导入问题修复说明.md (新增)
echo   - 稳定性修复总结.md (更新)
echo ============================================
echo.

set /p CONFIRM="是否继续提交？(y/n): "
if /i not "%CONFIRM%"=="y" (
    echo [取消] 操作已取消
    pause
    exit /b 0
)

echo.
echo [步骤5] 提交更改...
git commit -m "feat: 完善项目部署和稳定性

- 新增 dxpyd 模块自动加载机制 (x64/x86 __init__.py)
- 增强 install_env.bat 自动修复 dxpyd 导入问题
- 新增部署与使用指南文档
- 完善 dxpyd 导入问题修复说明
- 更新稳定性修复总结（包含 task.py 全面检查）

目标：用户只需复制 Python 环境或运行 install_env.bat 即可正常运行"

if errorlevel 1 (
    echo.
    echo [错误] 提交失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo [成功] 提交完成！
echo ============================================
echo.
echo 下一步:
echo   git push  # 推送到远程仓库
echo.
pause
