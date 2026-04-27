# -*- coding: utf-8 -*-
"""
ONNX Runtime GPU/CPU 切换测试脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("ONNX Runtime GPU/CPU 模式切换测试")
print("=" * 70)

# 测试 1: 检查安装
print("\n[测试 1] 检查 ONNX Runtime 安装状态...")
try:
    import onnxruntime as ort
    print(f"✓ onnxruntime 版本: {ort.__version__}")
    
    # 检查可用的执行提供者
    available_providers = ort.get_available_providers()
    print(f"✓ 可用的执行提供者: {available_providers}")
    
    if 'CUDAExecutionProvider' in available_providers:
        print("  ✓ GPU 支持已安装 (CUDAExecutionProvider)")
    else:
        print("  ✗ GPU 支持未安装")
    
    if 'CPUExecutionProvider' in available_providers:
        print("  ✓ CPU 支持已安装 (CPUExecutionProvider)")
    
except ImportError as e:
    print(f"✗ onnxruntime 未安装: {e}")
    sys.exit(1)

# 测试 2: 检查配置模块
print("\n[测试 2] 检查配置模块...")
try:
    from app.onnx_config import (
        ONNXRuntimeConfig, 
        enable_gpu, 
        enable_cpu, 
        is_gpu_mode, 
        get_providers
    )
    print("✓ 配置模块导入成功")
except ImportError as e:
    print(f"✗ 配置模块导入失败: {e}")
    sys.exit(1)

# 测试 3: 显示当前状态
print("\n[测试 3] 当前配置状态...")
ONNXRuntimeConfig.print_status()

# 测试 4: 切换到 GPU 模式
print("\n[测试 4] 切换到 GPU 模式...")
enable_gpu()
print(f"  GPU 模式: {is_gpu_mode()}")
print(f"  执行提供者: {get_providers()}")

# 测试 5: 切换到 CPU 模式
print("\n[测试 5] 切换到 CPU 模式...")
enable_cpu()
print(f"  GPU 模式: {is_gpu_mode()}")
print(f"  执行提供者: {get_providers()}")

# 测试 6: 环境变量测试
print("\n[测试 6] 环境变量测试...")
os.environ['ONNX_USE_GPU'] = '1'
print(f"  设置 ONNX_USE_GPU=1")
print(f"  GPU 模式: {is_gpu_mode()}")
print(f"  执行提供者: {get_providers()}")

os.environ['ONNX_USE_GPU'] = '0'
print(f"\n  设置 ONNX_USE_GPU=0")
print(f"  GPU 模式: {is_gpu_mode()}")
print(f"  执行提供者: {get_providers()}")

# 清除环境变量
del os.environ['ONNX_USE_GPU']

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
print("\n使用方法:")
print("  1. 在 run.bat 中设置: set ONNX_USE_GPU=1  (启用 GPU)")
print("  2. 在 run.bat 中设置: set ONNX_USE_GPU=0  (使用 CPU，默认)")
print("  3. 或在代码中调用: from app.onnx_config import enable_gpu")
print("=" * 70)
