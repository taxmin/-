# -*- coding: utf-8 -*-
"""
ONNX Runtime 配置管理
支持在 CPU 和 GPU 模式之间自由切换
"""
import os
import logging

logger = logging.getLogger(__name__)


class ONNXRuntimeConfig:
    """ONNX Runtime 配置管理器"""
    
    # 默认使用 GPU（更快），失败时自动降级到 CPU
    _use_gpu = True
    _gpu_available = None  # None=未检测, True=可用, False=不可用
    
    @classmethod
    def use_gpu(cls):
        """启用 GPU 模式"""
        cls._use_gpu = True
        os.environ['ONNX_USE_GPU'] = '1'
        logger.info("✓ ONNX Runtime 已切换到 GPU 模式")
    
    @classmethod
    def use_cpu(cls):
        """启用 CPU 模式"""
        cls._use_gpu = False
        os.environ['ONNX_USE_GPU'] = '0'
        logger.info("✓ ONNX Runtime 已切换到 CPU 模式")
    
    @classmethod
    def is_gpu_enabled(cls):
        """
        检查是否启用 GPU
        
        Returns:
            bool: True=使用GPU, False=使用CPU
        """
        # 优先检查环境变量
        env_val = os.environ.get('ONNX_USE_GPU', '').strip().lower()
        if env_val in ('1', 'true', 'yes', 'on'):
            return True
        if env_val in ('0', 'false', 'no', 'off'):
            return False
        
        # 否则使用类变量
        return cls._use_gpu
    
    @classmethod
    def check_gpu_availability(cls):
        """
        检测 GPU 是否可用（带重试机制）
        
        Returns:
            bool: GPU是否可用
        """
        if cls._gpu_available is not None:
            return cls._gpu_available
        
        try:
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            
            logger.info(f"ONNX Runtime 可用提供者: {available_providers}")
            
            if 'CUDAExecutionProvider' in available_providers:
                # 进一步验证 CUDA 是否真正可用
                try:
                    import torch
                    cuda_available = torch.cuda.is_available()
                    logger.info(f"PyTorch CUDA 状态: {cuda_available}")
                    
                    if cuda_available:
                        device_name = torch.cuda.get_device_name(0)
                        device_count = torch.cuda.device_count()
                        cls._gpu_available = True
                        logger.info(f"✓ GPU 检测通过: {device_name} (设备数: {device_count})")
                        return True
                    else:
                        # CUDA 不可用，尝试获取更多信息
                        logger.warning("⚠ PyTorch CUDA 不可用，尝试诊断...")
                        try:
                            # 检查 CUDA 版本
                            cuda_version = torch.version.cuda
                            cudnn_version = torch.backends.cudnn.version()
                            logger.warning(f"   CUDA 版本: {cuda_version}")
                            logger.warning(f"   cuDNN 版本: {cudnn_version}")
                        except Exception as e:
                            logger.warning(f"   无法获取 CUDA 信息: {e}")
                        
                        cls._gpu_available = False
                        return False
                        
                except ImportError:
                    logger.warning("⚠ PyTorch 未安装，无法验证 GPU")
                    cls._gpu_available = False
                    return False
            else:
                logger.warning("⚠ CUDAExecutionProvider 未安装")
                logger.info(f"   当前可用: {available_providers}")
                cls._gpu_available = False
                return False
                
        except Exception as e:
            logger.warning(f"⚠ GPU 检测异常: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            cls._gpu_available = False
            return False
    
    @classmethod
    def fallback_to_cpu(cls, reason=""):
        """
        降级到 CPU 模式
        
        Args:
            reason: 降级原因
        """
        if cls._use_gpu:
            cls._use_gpu = False
            cls._gpu_available = False
            logger.warning(f"⚠️  GPU 不可用，已自动降级到 CPU 模式{f' (原因: {reason})' if reason else ''}")
    
    @classmethod
    def get_execution_providers(cls):
        """
        获取执行提供者列表（带自动降级）
        
        Returns:
            list: ['CUDAExecutionProvider', 'CPUExecutionProvider'] 或 ['CPUExecutionProvider']
        """
        if cls.is_gpu_enabled():
            # 检查 GPU 是否真正可用
            if cls.check_gpu_availability():
                return ['CUDAExecutionProvider', 'CPUExecutionProvider']
            else:
                # GPU 不可用，自动降级
                cls.fallback_to_cpu("GPU 检测失败")
                return ['CPUExecutionProvider']
        else:
            return ['CPUExecutionProvider']
    
    @classmethod
    def print_status(cls):
        """打印当前配置状态"""
        mode = "GPU" if cls.is_gpu_enabled() else "CPU"
        providers = cls.get_execution_providers()
        gpu_status = "可用" if cls._gpu_available else ("未检测" if cls._gpu_available is None else "不可用")
        logger.info(f"ONNX Runtime 配置: {mode} 模式 (GPU状态: {gpu_status})")
        logger.info(f"执行提供者: {providers}")


# 便捷函数
def enable_gpu():
    """启用 GPU 模式"""
    ONNXRuntimeConfig.use_gpu()


def enable_cpu():
    """启用 CPU 模式"""
    ONNXRuntimeConfig.use_cpu()


def is_gpu_mode():
    """检查是否为 GPU 模式"""
    return ONNXRuntimeConfig.is_gpu_enabled()


def get_providers():
    """获取执行提供者列表"""
    return ONNXRuntimeConfig.get_execution_providers()


# 初始化时检查环境变量
if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("ONNX Runtime 配置测试")
    print("=" * 60)
    
    # 显示当前状态
    ONNXRuntimeConfig.print_status()
    
    print("\n切换到 GPU 模式...")
    enable_gpu()
    ONNXRuntimeConfig.print_status()
    print(f"执行提供者: {get_providers()}")
    
    print("\n切换到 CPU 模式...")
    enable_cpu()
    ONNXRuntimeConfig.print_status()
    print(f"执行提供者: {get_providers()}")
    
    print("\n" + "=" * 60)
    print("使用方法:")
    print("  1. 环境变量: 设置 ONNX_USE_GPU=1 启用 GPU")
    print("  2. 代码调用: from app.onnx_config import enable_gpu")
    print("  3. 配置文件: 在 run.bat 中设置 set ONNX_USE_GPU=1")
    print("=" * 60)
