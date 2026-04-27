# -*- coding: utf-8 -*-
"""
ONNX OCR 识别类 - 企业级高性能 OCR 引擎
基于 OnnxOCR 项目，支持简体中文、繁体中文、英文、日文等多种语言
使用方法：
    self.dx.Ocr = ONNX_OCR(vnc_instance=self.dx.screenshot)  # 复用 VNC 实例
    或
    self.dx.Ocr = ONNX_OCR("127.0.0.1", "5600", "")  # IP, 端口，密码
"""
# 处理直接运行时的路径问题
import sys
import os
import threading
from contextlib import contextmanager
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
_parent_dir = os.path.dirname(_current_dir)  # dx 多开框架 目录


def _resolve_onnxocr_root():
    """OnnxOCR 源码根目录：优先环境变量 ONNXOCR_PATH，其次项目内目录。"""
    env = os.environ.get("ONNXOCR_PATH", "").strip()
    if env:
        return env
    for rel in (("OnnxOCR-main",), ("third_party", "OnnxOCR-main"), ("OnnxOCR",)):
        p = os.path.join(_parent_dir, *rel)
        if os.path.isdir(p):
            return p
    # 未找到时返回项目目录下的默认路径
    return os.path.join(_parent_dir, "OnnxOCR-main")


_onnxocr_path = _resolve_onnxocr_root()
if os.path.isdir(_onnxocr_path) and _onnxocr_path not in sys.path:
    sys.path.insert(0, _onnxocr_path)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import time
import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional

# 延迟导入 ONNX OCR 模块
ONNXOCR_AVAILABLE = False
ONNXPaddleOcr = None

def _import_onnxocr():
    """延迟导入 ONNX OCR 模块"""
    global ONNXOCR_AVAILABLE, ONNXPaddleOcr
    
    if ONNXPaddleOcr is not None:
        return  # 已经导入过了
    
    try:
        # 先尝试直接导入
        try:
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr
            ONNXOCR_AVAILABLE = True
            logging.info("✓ 成功导入 ONNX OCR 模块")
            logging.info("  → 支持语言：简体中文、繁体中文、中文拼音、英文、日文")
            logging.info("  → 模型版本：PP-OCRv5")
            return True
        except ImportError as e1:
            # 如果失败，尝试添加到路径后再导入
            logging.debug(f"第一次导入失败：{e1}，尝试重新添加路径...")
            
            # 确保路径正确
            onnxocr_module_path = os.path.join(_onnxocr_path, 'onnxocr')
            if onnxocr_module_path not in sys.path:
                sys.path.insert(0, onnxocr_module_path)
            
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr
            ONNXOCR_AVAILABLE = True
            logging.info("✓ 成功导入 ONNX OCR 模块（通过添加路径）")
            logging.info("  → 支持语言：简体中文、繁体中文、中文拼音、英文、日文")
            logging.info("  → 模型版本：PP-OCRv5")
            return True
            
    except Exception as e:
        logging.error(f"❌ 导入 ONNX OCR 模块失败：{e}")
        logging.error(f"   请设置环境变量 ONNXOCR_PATH 指向 OnnxOCR 源码根目录，或将项目放到：{_onnxocr_path}")
        req = os.path.join(_onnxocr_path, "requirements.txt")
        if os.path.isfile(req):
            logging.error(f"   并安装依赖：pip install -r {req}")
        logging.error(f"   当前 Python 路径：{sys.path[:3]}...")
        
        # 显示已安装的包
        try:
            import onnxruntime
            logging.info(f"   ✓ onnxruntime 已安装，版本：{onnxruntime.__version__}")
        except ImportError:
            logging.error(f"   ❌ onnxruntime 未安装")
        
        ONNXOCR_AVAILABLE = False
        return False

from dxGame.dx_vnc import VNC
from dxGame.dx_core import *
from dxGame import dxpyd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 多开减负：全进程只加载一份 PP-OCR ONNX 模型；推理串行化避免 onnxruntime 并发问题
_ocr_engine_init_lock = threading.Lock()
_ocr_infer_lock = threading.Lock()
_shared_ocr_engine = None


def _ocr_lock_trace_enabled() -> bool:
    """环境变量 ONNX_OCR_LOCK_TRACE=1/true 时，每次加锁都打 INFO；否则仅在排队≥50ms 时打 INFO。"""
    v = os.environ.get("ONNX_OCR_LOCK_TRACE", "").strip().lower()
    return v in ("1", "true", "yes", "on")


@contextmanager
def _ocr_infer_locked_logged(phase: str, extra: str = ""):
    """
    进入/退出 _ocr_infer_lock 时打日志，用于多开时确认是否在排队等锁。
    extra 建议传 ip:port 等，便于区分实例。
    """
    wait_start = time.time()
    _ocr_infer_lock.acquire()
    wait_ms = (time.time() - wait_start) * 1000.0
    th = threading.current_thread().name
    suffix = f" {extra}" if extra else ""
    trace = _ocr_lock_trace_enabled()
    if trace or wait_ms >= 50.0:
        logging.info(
            "[OCR infer lock] acquire phase=%s thread=%s%s wait_acquire=%.1fms",
            phase, th, suffix, wait_ms,
        )
    else:
        logging.debug(
            "[OCR infer lock] acquire phase=%s thread=%s%s wait_acquire=%.1fms",
            phase, th, suffix, wait_ms,
        )
    held_start = time.time()
    try:
        yield
    finally:
        held_ms = (time.time() - held_start) * 1000.0
        _ocr_infer_lock.release()
        if trace or wait_ms >= 50.0:
            logging.info(
                "[OCR infer lock] release phase=%s thread=%s%s held=%.1fms",
                phase, th, suffix, held_ms,
            )
        else:
            logging.debug(
                "[OCR infer lock] release phase=%s thread=%s%s held=%.1fms",
                phase, th, suffix, held_ms,
            )


class ONNX_OCR:
    """
    ONNX OCR 识别类，企业级高性能 OCR 引擎
    兼容 DX OCR 接口，支持区域识别、文本查找等功能
    """
    
    def __init__(self, ip=None, port=None, password="", hwnd=None, vnc_instance=None, 
                 use_gpu=False, drop_score=0.5):
        """
        初始化 ONNX OCR 连接
        
        Args:
            ip: VNC 服务器 IP 地址（如果提供了 vnc_instance 则不需要）
            port: VNC 服务器端口（字符串或数字，如果提供了 vnc_instance 则不需要）
            password: VNC 密码，默认空字符串（如果提供了 vnc_instance 则不需要）
            hwnd: 窗口句柄（VNC 不需要，但为了兼容 DX 接口保留）
            vnc_instance: 已有的 VNC 实例，如果提供则复用，避免重复连接
            use_gpu: 是否使用 GPU 加速，默认 False
            drop_score: 置信度阈值，低于此分数的结果会被过滤，默认 0.5
        """
        # 复用已有 VNC 实例
        if vnc_instance is not None:
            if not isinstance(vnc_instance, VNC):
                raise ValueError("vnc_instance 必须是 VNC 类的实例")
            self.vnc_screenshot = vnc_instance
            self.ip = getattr(vnc_instance, 'ip', None)
            self.port = getattr(vnc_instance, 'port', None)
            self.password = getattr(vnc_instance, 'password', None)
            self.hwnd = hwnd
            self._is_reused_instance = True
            logging.info(f"ONNX OCR 复用 VNC 截图连接：{self.ip}:{self.port}")
        else:
            # 创建新的 VNC 连接
            if ip is None or port is None:
                raise ValueError("如果未提供 vnc_instance，则必须提供 ip 和 port 参数")
            
            if isinstance(port, int):
                port = str(port)
            
            if password == "":
                password = None
            
            self.ip = ip
            self.port = port
            self.password = password
            self.hwnd = hwnd
            self._is_reused_instance = False
            
            try:
                self.vnc_screenshot = VNC(ip, port, password, hwnd, fps=2)  # 🔧 稳定性优化：降低 FPS 至 2，回合制游戏足够
                logging.info(f"ONNX OCR 创建 VNC 截图连接：{ip}:{port} (FPS=2)")
            except Exception as e:
                logging.error(f"VNC 截图连接失败：{e}")
                raise
        
        # 初始化 ONNX OCR 引擎
        self.use_gpu = use_gpu
        self.drop_score = drop_score
        self.ocr_engine = None
        self._use_shared_ocr = False

        # OCR 健康检查与监控（轻量级）
        self._ocr_error_count = 0          # 连续错误计数
        self._ocr_total_calls = 0          # 总调用次数
        self._ocr_success_count = 0        # 成功次数
        self._last_health_check = 0        # 上次健康检查时间戳
        self._health_check_interval = 60   # 健康检查间隔（秒），避免频繁检查影响性能
        self._engine_status = 'unknown'    # 引擎状态：unknown/healthy/degraded/failed

        _import_onnxocr()

        global _shared_ocr_engine
        # 环境变量 ONNX_OCR_SHARED=0 时禁用共享，每个实例独立加载模型（多开更并行）
        enable_shared = os.environ.get("ONNX_OCR_SHARED", "1").strip().lower() not in ("0", "false", "no", "off")
        
        # 从配置模块获取执行提供者（支持 CPU/GPU 切换）
        try:
            from app.onnx_config import get_providers, is_gpu_mode, ONNXRuntimeConfig
            
            # 首次使用时检测 GPU 可用性
            if ONNXRuntimeConfig._gpu_available is None:
                logging.info("正在检测 GPU 可用性...")
                ONNXRuntimeConfig.check_gpu_availability()
            
            execution_providers = get_providers()
            gpu_enabled = is_gpu_mode()
            logging.info(f"ONNX Runtime 模式: {'GPU' if gpu_enabled else 'CPU'} | 执行提供者: {execution_providers}")
        except ImportError as e:
            # 如果配置模块不存在，回退到原有逻辑
            logging.warning(f"无法导入 onnx_config 模块: {e}，使用默认配置")
            execution_providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
            gpu_enabled = use_gpu
        
        if ONNXOCR_AVAILABLE and ONNXPaddleOcr is not None and enable_shared:
            try:
                with _ocr_engine_init_lock:
                    if _shared_ocr_engine is not None:
                        self.ocr_engine = _shared_ocr_engine
                        self._use_shared_ocr = True
                        self._engine_status = 'healthy'
                        logging.info("ONNX OCR 复用进程内共享引擎（多账号共 1 份模型）")
                    else:
                        # 尝试初始化引擎（可能失败，需要降级）
                        engine = None
                        init_failed = False
                        
                        # 第一次尝试：使用配置的 GPU/CPU 模式
                        logging.info(f"正在初始化 ONNX OCR 共享引擎 (GPU={gpu_enabled})...")
                        s = time.time()
                        try:
                            engine = ONNXPaddleOcr(
                                use_angle_cls=True,
                                use_gpu=gpu_enabled,
                                drop_score=drop_score,
                            )
                            e = time.time()
                            logging.info(f"✓ ONNX OCR 引擎创建成功，耗时：{e-s:.3f}秒")
                        except Exception as init_error:
                            init_failed = True
                            error_msg = str(init_error).lower()
                            
                            # 如果是 GPU 相关错误，尝试降级到 CPU
                            if gpu_enabled and any(keyword in error_msg for keyword in ['cuda', 'gpu', 'directml']):
                                logging.warning(f"⚠️  GPU 初始化失败: {init_error}")
                                logging.info("🔄 正在尝试降级到 CPU 模式...")
                                
                                # 更新配置为 CPU 模式
                                try:
                                    from app.onnx_config import ONNXRuntimeConfig
                                    ONNXRuntimeConfig.fallback_to_cpu(f"初始化失败: {init_error}")
                                except:
                                    pass
                                
                                # 重试 CPU 模式
                                try:
                                    s = time.time()
                                    engine = ONNXPaddleOcr(
                                        use_angle_cls=True,
                                        use_gpu=False,  # 强制使用 CPU
                                        drop_score=drop_score,
                                    )
                                    e = time.time()
                                    logging.info(f"✓ ONNX OCR 引擎创建成功 (CPU 模式)，耗时：{e-s:.3f}秒")
                                except Exception as cpu_error:
                                    logging.error(f"❌ CPU 模式也失败: {cpu_error}")
                                    raise init_error  # 抛出原始错误
                            else:
                                raise  # 非 GPU 错误，直接抛出
                        
                        if engine is None:
                            raise RuntimeError("引擎创建返回 None")
                        
                        # 预热模型
                        logging.info("正在预热 OCR 模型...")
                        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                        try:
                            _tag = f" vnc={self.ip}:{self.port}" if self.ip is not None else ""
                            with _ocr_infer_locked_logged("warmup", extra=_tag):
                                _ = engine.ocr(test_img)
                            logging.info("✓ OCR 模型预热完成")
                            _shared_ocr_engine = engine
                            self.ocr_engine = engine
                            self._use_shared_ocr = True
                            self._engine_status = 'healthy'
                        except Exception as warmup_error:
                            logging.error(f"❌ OCR 模型预热失败：{warmup_error}")
                            self.ocr_engine = None
                            self._engine_status = 'failed'

            except Exception as e:
                logging.error(f"❌ ONNX OCR 引擎初始化失败：{e}")
                import traceback
                logging.error(traceback.format_exc())
                self.ocr_engine = None
                self._engine_status = 'failed'
        elif ONNXOCR_AVAILABLE and ONNXPaddleOcr is not None and not enable_shared:
            # 禁用共享模式：每个实例独立加载模型（占用更多内存，但更并行）
            try:
                engine = None
                
                # 第一次尝试：使用配置的 GPU/CPU 模式
                logging.info(f"正在初始化独立 ONNX OCR 引擎 (GPU={gpu_enabled}, 非共享模式)...")
                s = time.time()
                try:
                    engine = ONNXPaddleOcr(
                        use_angle_cls=True,
                        use_gpu=gpu_enabled,
                        drop_score=drop_score,
                    )
                    e = time.time()
                    logging.info(f"✓ 独立 ONNX OCR 引擎创建成功，耗时：{e-s:.3f}秒")
                except Exception as init_error:
                    error_msg = str(init_error).lower()
                    
                    # 如果是 GPU 相关错误，尝试降级到 CPU
                    if gpu_enabled and any(keyword in error_msg for keyword in ['cuda', 'gpu', 'directml']):
                        logging.warning(f"⚠️  GPU 初始化失败: {init_error}")
                        logging.info("🔄 正在尝试降级到 CPU 模式...")
                        
                        # 更新配置为 CPU 模式
                        try:
                            from app.onnx_config import ONNXRuntimeConfig
                            ONNXRuntimeConfig.fallback_to_cpu(f"初始化失败: {init_error}")
                        except:
                            pass
                        
                        # 重试 CPU 模式
                        try:
                            s = time.time()
                            engine = ONNXPaddleOcr(
                                use_angle_cls=True,
                                use_gpu=False,  # 强制使用 CPU
                                drop_score=drop_score,
                            )
                            e = time.time()
                            logging.info(f"✓ 独立 ONNX OCR 引擎创建成功 (CPU 模式)，耗时：{e-s:.3f}秒")
                        except Exception as cpu_error:
                            logging.error(f"❌ CPU 模式也失败: {cpu_error}")
                            raise init_error
                    else:
                        raise
                
                if engine is None:
                    raise RuntimeError("引擎创建返回 None")
                
                # 预热模型
                logging.info("正在预热 OCR 模型...")
                test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                try:
                    _ = engine.ocr(test_img)
                    logging.info("✓ OCR 模型预热完成")
                    self.ocr_engine = engine
                    self._use_shared_ocr = False  # ← 不使用共享锁
                    self._engine_status = 'healthy'
                    logging.info("✓ 独立引擎模式：此实例不会与其他实例竞争锁")
                except Exception as warmup_error:
                    logging.error(f"❌ OCR 模型预热失败：{warmup_error}")
                    self.ocr_engine = None
                    self._engine_status = 'failed'
            except Exception as e:
                logging.error(f"❌ ONNX OCR 引擎初始化失败：{e}")
                import traceback
                logging.error(traceback.format_exc())
                self.ocr_engine = None
                self._engine_status = 'failed'
        else:
            logging.error("❌ ONNX OCR 模块不可用，请检查安装")
            self.ocr_engine = None
            self._engine_status = 'failed'

    def _ocr_infer(self, image: np.ndarray):
        """
        调用底层 ocr；共享引擎时加锁，避免多线程同时推理。
        🔧 稳定性优化：增加全面异常保护
        """
        if self.ocr_engine is None:
            raise RuntimeError("OCR 引擎未初始化")
        
        try:
            if getattr(self, "_use_shared_ocr", False):
                _tag = f"vnc={self.ip}:{self.port}" if self.ip is not None else ""
                with _ocr_infer_locked_logged("infer", extra=_tag):
                    return self.ocr_engine.ocr(image)
            else:
                return self.ocr_engine.ocr(image)
        except (OSError, WindowsError, SystemError) as infer_error:
            # 底层推理系统错误（如内存分配失败）
            logging.error(f"⚠️ [OCR] 推理系统错误: {infer_error}")
            raise  # 重新抛出，由上层处理重试逻辑
        except Exception as infer_error:
            # 其他推理异常
            logging.error(f"⚠️ [OCR] 推理异常: {type(infer_error).__name__}: {infer_error}")
            raise  # 重新抛出，由上层处理重试逻辑
    
    def Ocr(self, x1: int, y1: int, x2: int, y2: int, target_text: str = None):
        """
        OCR 识别方法（核心方法）
        
        Args:
            x1: 左上角 x 坐标
            y1: 左上角 y 坐标
            x2: 右下角 x 坐标
            y2: 右下角 y 坐标
            target_text: 目标文本（可选），用于过滤结果
        
        Returns:
            list: [(text, position, confidence), ...]
                  text: 识别的文本
                  position: (center_x, center_y) 中心坐标
                  confidence: 置信度 (0-1)
        """
        # 性能优化：记录调用次数
        self._ocr_total_calls += 1
        
        # 严格检查：OCR 引擎是否已正确初始化
        if not self._validate_ocr_engine():
            return []
        
        try:
            # 获取区域截图
            if not hasattr(self.vnc_screenshot, 'Capture'):
                logging.error("VNC 对象没有 Capture 方法")
                self._ocr_error_count += 1
                return []
            
            # 轻量级 VNC 检查（避免频繁深度检查影响性能）
            if not hasattr(self.vnc_screenshot, 'client') or self.vnc_screenshot.client is None:
                # 只在第一次错误时打印详细提示，避免刷屏
                if self._ocr_error_count == 0:
                    logging.error("⚠️ VNC 客户端未连接！请检查：")
                    logging.error("   1. 模拟器是否正在运行")
                    logging.error("   2. VNC 服务是否启动")
                    logging.error("   3. 尝试重启模拟器并等待 2-3 分钟")
                else:
                    logging.error(f"VNC 客户端未连接（错误次数：{self._ocr_error_count + 1}）")
                self._ocr_error_count += 1
                return []
            
            # 🔧 稳定性优化：VNC Capture() 增加异常保护，防止访问违规崩溃
            try:
                region_image = self.vnc_screenshot.Capture(x1, y1, x2, y2)
            except (OSError, WindowsError, SystemError) as capture_error:
                # VNC 底层 API 错误（如 0xC0000005 访问违规）
                logging.error(f"⚠️ [OCR] VNC Capture 系统错误: {capture_error}")
                self._ocr_error_count += 1
                return []
            except AttributeError as attr_error:
                # VNC 对象方法缺失
                logging.error(f"⚠️ [OCR] VNC Capture 方法不存在: {attr_error}")
                self._ocr_error_count += 1
                return []
            except Exception as capture_error:
                # 其他 Capture 异常
                logging.error(f"⚠️ [OCR] VNC Capture 异常: {type(capture_error).__name__}: {capture_error}")
                self._ocr_error_count += 1
                return []
            
            if region_image is None:
                logging.debug(f"VNC 区域截图返回 None: ({x1}, {y1}, {x2}, {y2})")
                self._ocr_error_count += 1
                return []
            
            # 转换为 numpy 数组
            if not isinstance(region_image, np.ndarray):
                try:
                    if hasattr(region_image, 'get_memoryview'):
                        mv = region_image.get_memoryview()
                        region_image = np.array(mv, copy=False)
                    else:
                        region_image = np.asarray(region_image, dtype=np.uint8)
                except Exception as e:
                    logging.error(f"图像转换失败：{e}")
                    return []
            
            if region_image.size == 0:
                logging.error("区域截图数据为空")
                self._ocr_error_count += 1
                return []
            
            # 图像预处理（提高识别稳定性）
            try:
                # 确保图像是 BGR 格式（OpenCV 标准）
                if len(region_image.shape) == 2:
                    # 灰度图转 BGR
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_GRAY2BGR)
                elif len(region_image.shape) == 3 and region_image.shape[2] == 4:
                    # BGRA 转 BGR
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_BGRA2BGR)
                
                # 图像质量检查（避免无效识别）
                h, w = region_image.shape[:2]
                if h == 0 or w == 0:
                    logging.warning(f"OCR 区域尺寸为 0：{w}x{h}")
                    self._ocr_error_count += 1
                    return []
                
                # 可选：轻微增强对比度（提升识别率）
                # 注意：ONNX OCR 对原始图像处理较好，这里只做最小干预
                # alpha = 1.2  # 对比度系数 (1.0-2.0)
                # beta = 0     # 亮度偏移
                # region_image = cv2.convertScaleAbs(region_image, alpha=alpha, beta=beta)
                
            except Exception as preprocess_error:
                logging.warning(f"图像预处理异常，使用原始图像：{preprocess_error}")
            
            # 执行 OCR 识别（带重试机制）
            s = time.time()
            result = None
            max_retries = 2  # 最多重试 2 次
            
            for attempt in range(max_retries):
                try:
                    result = self._ocr_infer(region_image)
                    break  # 成功则跳出循环
                    
                except Exception as ocr_error:
                    error_msg = str(ocr_error).lower()
                    
                    # 判断是否为可重试错误
                    is_retryable = any(keyword in error_msg for keyword in [
                        'timeout', 'memory', 'allocation', 'cuda', 'directml'
                    ])
                    
                    if attempt < max_retries - 1 and is_retryable:
                        logging.warning(
                            f"ONNX OCR 第 {attempt + 1} 次尝试失败（可重试）：{ocr_error}"
                        )
                        time.sleep(0.1)  # 短暂等待后重试
                        continue
                    else:
                        # 不可重试错误或已达最大重试次数
                        logging.error(
                            f"ONNX OCR 引擎调用失败（尝试 {attempt + 1}/{max_retries}）：{ocr_error}"
                        )
                        self._ocr_error_count += 1
                        
                        # 智能降级：连续错误过多时尝试恢复
                        if self._ocr_error_count >= 5:
                            self._attempt_recovery()
                        
                        return []
            e = time.time()
            
            # 记录识别耗时（用于性能监控）
            elapsed_time = e - s
            if elapsed_time > 2.0:  # 超过 2 秒记录警告
                logging.warning(
                    f"⚠️ ONNX OCR 识别耗时较长：{elapsed_time:.2f}秒，区域：{x1},{y1},{x2},{y2}"
                )
            else:
                logging.debug(f"ONNX OCR 识别耗时：{elapsed_time:.3f}秒，区域：{x1},{y1},{x2},{y2}")
            
            # 成功，重置错误计数
            self._ocr_success_count += 1
            old_error_count = self._ocr_error_count
            self._ocr_error_count = 0
            
            # 如果之前有错误但现在恢复了，记录日志
            if old_error_count > 0:
                logging.info(f"✓ ONNX OCR 恢复正常（之前连续错误 {old_error_count} 次）")
            
            logging.debug(f"ONNX OCR 识别耗时：{e-s:.3f}秒，区域：{x1},{y1},{x2},{y2}")
            
            # 解析结果
            results = []
            if result and len(result) > 0 and len(result[0]) > 0:
                for box_data in result[0]:
                    if len(box_data) >= 2:
                        box = box_data[0]  # 边界框坐标
                        text, confidence = box_data[1]  # 文本和置信度
                        
                        # 计算中心坐标
                        if len(box) >= 4:
                            # box 格式：[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                            center_x = int(sum([p[0] for p in box]) / 4)
                            center_y = int(sum([p[1] for p in box]) / 4)
                            
                            # 转换为相对于原始坐标的绝对坐标
                            abs_x = x1 + center_x
                            abs_y = y1 + center_y
                            
                            results.append((text, (abs_x, abs_y), float(confidence)))
            
            # 如果指定了目标文本，进行过滤
            if target_text is not None:
                results = self._filter_by_text(results, target_text)
            
            logging.debug(f"ONNX OCR 识别到 {len(results)} 条结果")
            return results
            
        except Exception as e:
            logging.error(f"ONNX OCR 识别失败：{e}")
            import traceback
            logging.error(traceback.format_exc())
            self._ocr_error_count += 1
            # 智能降级：连续错误过多时尝试恢复
            if self._ocr_error_count >= 5:
                self._attempt_recovery()
            return []
    
    def _validate_ocr_engine(self) -> bool:
        """
        验证 OCR 引擎是否已正确初始化并可用
        
        Returns:
            bool: 引擎是否可用
        """
        # 1. 检查引擎对象是否存在
        if self.ocr_engine is None:
            # 只在第一次或每 20 次错误时打印，避免刷屏
            if not hasattr(self, '_engine_none_count'):
                self._engine_none_count = 0
            
            if self._engine_none_count == 0 or self._engine_none_count % 20 == 0:
                logging.error("❌ ONNX OCR 引擎未初始化！")
                if self._engine_none_count == 0:
                    logging.error("   可能原因：")
                    logging.error("   1. ONNX OCR 模块未正确安装")
                    logging.error("   2. 模型文件缺失或损坏")
                    logging.error("   3. 初始化时发生错误")
            
            self._engine_none_count += 1
            self._engine_status = 'failed'
            return False
        else:
            # 引擎存在，重置计数
            if hasattr(self, '_engine_none_count'):
                self._engine_none_count = 0
        
        # 2. 检查引擎是否有 ocr 方法
        if not hasattr(self.ocr_engine, 'ocr'):
            logging.error("❌ ONNX OCR 引擎缺少 ocr() 方法！")
            self._engine_status = 'failed'
            return False
        
        # 3. 检查 VNC 连接（OCR 依赖 VNC 截图）
        if not hasattr(self.vnc_screenshot, 'client') or self.vnc_screenshot.client is None:
            # 🔍 详细诊断：打印 VNC 对象的状态
            vnc_obj_id = id(self.vnc_screenshot)
            has_client_attr = hasattr(self.vnc_screenshot, 'client')
            client_value = getattr(self.vnc_screenshot, 'client', '<MISSING>')
            
            logging.error(f"❌ VNC 客户端未连接，OCR 无法工作！")
            logging.error(f"   📊 VNC 对象诊断信息：")
            logging.error(f"      - 对象 ID: {vnc_obj_id}")
            logging.error(f"      - 是否有 client 属性: {has_client_attr}")
            logging.error(f"      - client 值: {client_value}")
            logging.error(f"      - OCR 错误次数: {self._ocr_error_count + 1}")
            logging.error(f"      - 是否复用实例: {getattr(self, '_is_reused_instance', 'Unknown')}")
            
            # 只在第一次或每 20 次错误时打印详细提示，避免刷屏
            if self._ocr_error_count == 0:
                logging.error("   请检查：")
                logging.error("   1. 模拟器是否正在运行")
                logging.error("   2. VNC 服务是否启动")
                logging.error("   3. 尝试重启模拟器并等待 2-3 分钟")
                logging.error("   4. ⚠️ 如果看到此错误频繁出现，可能是 VNC 被意外关闭或对象被销毁")
            
            self._engine_status = 'failed'
            return False
        
        # 4. 检查引擎状态标记
        if self._engine_status == 'failed':
            logging.warning("⚠️ ONNX OCR 引擎状态为 failed，尝试恢复...")
            self._attempt_recovery()
            # 恢复后再次检查
            if self._engine_status == 'failed':
                return False
        
        return True
    
    def _check_health(self) -> bool:
        """
        轻量级健康检查（性能优化版）
        
        Returns:
            bool: 引擎是否健康
        """
        current_time = time.time()
        
        # 避免频繁检查，影响性能
        if current_time - self._last_health_check < self._health_check_interval:
            return self._engine_status != 'failed'
        
        # 执行健康检查
        self._last_health_check = current_time
        
        try:
            # 1. 检查 VNC 连接
            if not hasattr(self.vnc_screenshot, 'client') or self.vnc_screenshot.client is None:
                logging.warning("⚠️ ONNX OCR 健康检查：VNC 客户端未连接")
                self._engine_status = 'failed'
                return False
            
            # 2. 检查 OCR 引擎
            if self.ocr_engine is None:
                logging.warning("⚠️ ONNX OCR 健康检查：OCR 引擎未初始化")
                self._engine_status = 'failed'
                return False
            
            # 3. 计算成功率
            if self._ocr_total_calls > 0:
                success_rate = self._ocr_success_count / self._ocr_total_calls
                
                # 根据成功率判断状态
                if success_rate < 0.5 and self._ocr_error_count >= 3:
                    logging.warning(
                        f"⚠️ ONNX OCR 性能下降：成功率 {success_rate:.1%} "
                        f"(总调用:{self._ocr_total_calls}, 错误:{self._ocr_error_count})"
                    )
                    self._engine_status = 'degraded'
                else:
                    self._engine_status = 'healthy'
            else:
                self._engine_status = 'healthy'
            
            return True
            
        except Exception as e:
            logging.error(f"ONNX OCR 健康检查异常：{e}")
            self._engine_status = 'failed'
            return False
    
    def _attempt_recovery(self):
        """
        尝试恢复 OCR 引擎（智能降级策略）
        
        注意：此方法不会重启模型（耗时太长），而是清理状态并记录日志
        """
        logging.warning("⚠️ ONNX OCR 尝试恢复...")
        
        try:
            # 1. 重置错误计数（给引擎一次机会）
            old_error_count = self._ocr_error_count
            self._ocr_error_count = 0
            
            # 2. 检查 VNC 状态
            if hasattr(self.vnc_screenshot, 'client') and self.vnc_screenshot.client is not None:
                logging.info("✓ VNC 连接正常")
            else:
                logging.warning("⚠️ VNC 连接异常，等待自动重连...")
                # 不主动重连，由 VNC 自己的机制处理
            
            # 3. 简单预热测试（快速验证引擎是否可用）
            if self.ocr_engine is not None:
                try:
                    test_img = np.zeros((50, 50, 3), dtype=np.uint8)
                    _ = self._ocr_infer(test_img)
                    logging.info("✓ ONNX OCR 引擎预热测试通过")
                except Exception as e:
                    logging.error(f"❌ ONNX OCR 引擎预热测试失败：{e}")
                    self._engine_status = 'failed'
            
            logging.info(
                f"✓ ONNX OCR 恢复完成（重置错误计数：{old_error_count} → 0）"
            )
            
        except Exception as e:
            logging.error(f"❌ ONNX OCR 恢复失败：{e}")
            self._engine_status = 'failed'
    
    def get_stats(self) -> dict:
        """
        获取 OCR 统计信息（用于监控和调试）
        
        Returns:
            dict: 统计信息
            {
                'total_calls': int,         # 总调用次数
                'success_count': int,       # 成功次数
                'error_count': int,         # 错误次数
                'success_rate': str,        # 成功率
                'engine_status': str,       # 引擎状态
                'last_health_check': float  # 上次健康检查时间戳
            }
        """
        success_rate = 0
        if self._ocr_total_calls > 0:
            success_rate = self._ocr_success_count / self._ocr_total_calls
        
        return {
            'total_calls': self._ocr_total_calls,
            'success_count': self._ocr_success_count,
            'error_count': self._ocr_error_count,
            'success_rate': f"{success_rate:.1%}",
            'engine_status': self._engine_status,
            'last_health_check': self._last_health_check
        }
    
    def print_stats(self):
        """打印 OCR 统计信息"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("ONNX OCR 统计信息")
        print("="*60)
        print(f"  总调用次数：{stats['total_calls']}")
        print(f"  成功次数：{stats['success_count']}")
        print(f"  错误次数：{stats['error_count']}")
        print(f"  成功率：{stats['success_rate']}")
        print(f"  引擎状态：{stats['engine_status']}")
        print("="*60)
    
    def _filter_by_text(self, results: List[Tuple], target_text: str) -> List[Tuple]:
        """
        根据目标文本过滤结果
        
        Args:
            results: OCR 识别结果
            target_text: 目标文本
        
        Returns:
            过滤后的结果
        """
        if not results:
            return []
        
        filtered_results = []
        target_lower = target_text.lower()
        
        for text, pos, confidence in results:
            if target_lower in text.lower():
                filtered_results.append((text, pos, confidence))
        
        return filtered_results
    
    def FindText(self, x1: int, y1: int, x2: int, y2: int, target_text: str):
        """
        在指定区域查找文本（兼容 DX 接口）
        
        Args:
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
            target_text: 目标文本
        
        Returns:
            bool: 是否找到
        """
        results = self.Ocr(x1, y1, x2, y2, target_text)
        return len(results) > 0
    
    def GetTextPos(self, x1: int, y1: int, x2: int, y2: int, target_text: str):
        """
        获取文本位置（兼容 DX 接口）
        
        Args:
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
            target_text: 目标文本
        
        Returns:
            int: 1 表示找到，0 表示未找到
        """
        if self.FindText(x1, y1, x2, y2, target_text):
            return 1
        return 0
    
    def stop(self):
        """清理资源"""
        try:
            # 如果是自己创建的 VNC 实例，才关闭连接
            if not self._is_reused_instance and hasattr(self, 'vnc_screenshot'):
                self.vnc_screenshot.stop()
            logging.info("ONNX OCR 资源已释放")
        except Exception as e:
            logging.warning(f"清理 ONNX OCR 资源失败：{e}")
    
    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            self.stop()
        except:
            pass


# 全局 ONNX OCR 实例（单例模式）
_onnx_ocr_instance: Optional[ONNX_OCR] = None


def get_onnx_ocr_instance(vnc_instance=None, use_gpu=False, drop_score=0.5):
    """
    获取全局 ONNX OCR 实例（单例模式）
    
    Args:
        vnc_instance: VNC 实例
        use_gpu: 是否使用 GPU
        drop_score: 置信度阈值
    
    Returns:
        ONNX_OCR 实例
    """
    global _onnx_ocr_instance
    
    if _onnx_ocr_instance is None:
        if vnc_instance is not None:
            _onnx_ocr_instance = ONNX_OCR(vnc_instance=vnc_instance, use_gpu=use_gpu, drop_score=drop_score)
        else:
            logging.error("创建 ONNX OCR 实例需要提供 vnc_instance")
            return None
    
    return _onnx_ocr_instance


if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("ONNX OCR 测试")
    print("=" * 60)
    
    try:
        # 创建 VNC 实例
        vnc = VNC("127.0.0.1", "5600", "", fps=5)
        print(f"VNC 分辨率：{vnc.width}x{vnc.height}")
        
        # 创建 ONNX OCR 实例
        onnx_ocr = ONNX_OCR(vnc_instance=vnc, use_gpu=False, drop_score=0.5)
        while True:

            if onnx_ocr.ocr_engine is None:
                print("❌ ONNX OCR 引擎初始化失败")
                vnc.stop()
                sys.exit(1)

            # 测试 OCR 识别
            print("\n测试 OCR 识别...")
            x1, y1, x2, y2 = 366,334,462,461
            print(f"识别区域：({x1}, {y1}) -> ({x2}, {y2})")

            results = onnx_ocr.Ocr(x1, y1, x2, y2)
            print(f"识别到 {len(results)} 条结果:")

            for i, (text, pos, confidence) in enumerate(results):
                print(f"  [{i+1}] 文本：'{text}' | 位置：{pos} | 置信度：{confidence:.3f}")

            # 测试文本查找
            print("\n测试文本查找...")
            if results:
                target = results[0][0]  # 使用第一个识别到的文本
                print(f"查找文本：'{target}'")
                found = onnx_ocr.FindText(x1, y1, x2, y2, target)
                print(f"查找结果：{'✓ 找到' if found else '❌ 未找到'}")

            print("\n✅ 本次测试完成")
            time.sleep(5)


    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源（只在最后执行一次）
        try:
            if 'onnx_ocr' in locals():
                onnx_ocr.stop()
            if 'vnc' in locals():
                vnc.stop()
            print("\n✅ 资源已释放，程序退出")
        except:
            pass
