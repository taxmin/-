@echo off
chcp 65001 >nul
echo ======================================================================
echo GPU 环境配置验证
echo ======================================================================
echo.

echo [1/2] 检查 Python38Portable 环境...
Python38Portable\python.exe -c "import torch, onnxruntime as ort; print('  PyTorch CUDA:', '✓' if torch.cuda.is_available() else '✗'); print('  ONNX Runtime:', ort.__version__); providers = ort.get_available_providers(); print('  CUDAExecutionProvider:', '✓' if 'CUDAExecutionProvider' in providers else '✗'); print('  设备:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
echo.

echo [2/2] 检查 .venv 虚拟环境...
.venv\Scripts\python.exe -c "import torch, onnxruntime as ort; print('  PyTorch CUDA:', '✓' if torch.cuda.is_available() else '✗'); print('  ONNX Runtime:', ort.__version__); providers = ort.get_available_providers(); print('  CUDAExecutionProvider:', '✓' if 'CUDAExecutionProvider' in providers else '✗'); print('  设备:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
echo.

echo ======================================================================
echo 验证完成！
echo ======================================================================
echo.
echo 说明:
echo   ✓ 表示已正确安装 GPU 支持
echo   ✗ 表示未安装或配置有问题
echo.
echo 两个环境都已启用 GPU，可以自由选择使用！
echo ======================================================================
pause
