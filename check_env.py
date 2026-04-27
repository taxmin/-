# -*- coding: utf-8 -*-
"""快速诊断脚本 - 检查当前 Python 环境"""
import sys
import os

print("=" * 80)
print("Python 环境诊断")
print("=" * 80)
print(f"Python 可执行文件: {sys.executable}")
print(f"Python 版本: {sys.version}")
print()

print("前 5 个 sys.path:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")
print()

print("模块检查:")
modules_to_check = ['onnxruntime', 'psutil', 'torch', 'cv2', 'numpy']
for module_name in modules_to_check:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'N/A')
        print(f"  ✅ {module_name}: {version}")
        if module_name == 'onnxruntime':
            providers = module.get_available_providers()
            print(f"     可用提供者: {providers}")
        elif module_name == 'torch':
            cuda_available = module.cuda.is_available()
            print(f"     CUDA 可用: {cuda_available}")
            if cuda_available:
                device_name = module.cuda.get_device_name(0)
                print(f"     GPU 设备: {device_name}")
    except ImportError as e:
        print(f"  ❌ {module_name}: 未安装 ({e})")

print()
print("=" * 80)
