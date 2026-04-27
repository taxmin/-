# dx多开框架 - 环境安装脚本 (PowerShell)
# 编码: UTF-8

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "dx多开框架 - 环境安装脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[信息] 检测到Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Python，请先安装Python 3.8.x" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/release/python-388/" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""

# 检查pip是否可用
try {
    $pipVersion = pip --version 2>&1
    Write-Host "[信息] 检测到pip版本: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] pip不可用，请检查Python安装" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""

# 升级pip
Write-Host "[步骤1] 升级pip到最新版本..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple
    Write-Host "[成功] pip升级完成" -ForegroundColor Green
} catch {
    Write-Host "[警告] pip升级失败，继续安装依赖..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[步骤2] 安装项目依赖包..." -ForegroundColor Yellow
Write-Host "使用镜像源: https://mirrors.aliyun.com/pypi/simple" -ForegroundColor Gray
Write-Host ""

# 安装依赖
try {
    pip install -r requirement.txt -i https://mirrors.aliyun.com/pypi/simple
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "[成功] 所有依赖安装完成！" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Yellow
    Write-Host "1. 运行环境检查: python check_ocr_env.py" -ForegroundColor Gray
    Write-Host "2. 启动主程序: python main.py" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[错误] 依赖安装失败！" -ForegroundColor Red
    Write-Host "请检查网络连接或尝试使用其他镜像源" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "可尝试的镜像源:" -ForegroundColor Yellow
    Write-Host "  -i https://pypi.tuna.tsinghua.edu.cn/simple" -ForegroundColor Gray
    Write-Host "  -i https://pypi.douban.com/simple" -ForegroundColor Gray
    Write-Host ""
    Read-Host "按Enter键退出"
    exit 1
}

Read-Host "按Enter键退出"

