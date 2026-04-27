# -*- coding: utf-8 -*-
"""
OCR识别模块
基于EasyOCR实现区域文字识别功能
支持VNC截图和多窗口
"""
import cv2
import numpy as np
import os
import time
import logging
from typing import Tuple, Optional, List, Callable

logger = logging.getLogger(__name__)

# 尝试导入EasyOCR
EASYOCR_AVAILABLE = False
easyocr = None
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None
    logger.debug("EasyOCR未安装，OCR功能将不可用。请安装: pip install easyocr")
except Exception as e:
    EASYOCR_AVAILABLE = False
    easyocr = None
    error_msg = str(e)
    # 检查是否是DLL加载问题
    if "dll" in error_msg.lower() or "shm.dll" in error_msg.lower():
        logger.debug(f"EasyOCR导入失败（PyTorch DLL问题）: {error_msg[:100]}...")
    else:
        logger.debug(f"EasyOCR导入失败: {error_msg[:100]}...")


class OCR:
    """OCR识别器，支持区域文字识别"""
    
    def __init__(self, vnc_capture_func: Optional[Callable] = None, 
                 vnc_instance=None,
                 languages: List[str] = ['ch_sim', 'en'], 
                 gpu: bool = False,
                 confidence_threshold: float = 0.1):
        """
        初始化OCR识别器
        
        Args:
            vnc_capture_func: VNC截图函数，接收window_handle参数，返回numpy图像数组（已废弃，优先使用vnc_instance）
            vnc_instance: VNC截图实例（优先使用），如果提供则直接使用VNC.Capture()方法
            languages: 支持的语言列表，默认['ch_sim', 'en']（简体中文和英文）
            gpu: 是否启用GPU加速（需要安装CUDA和cuDNN）
            confidence_threshold: 置信度阈值（0-1），低于此值的识别结果将被过滤
        """
        self.vnc_capture_func = vnc_capture_func
        self.vnc_instance = vnc_instance
        self.confidence_threshold = confidence_threshold
        self.reader = None
        
        if not EASYOCR_AVAILABLE:
            logger.error("EasyOCR未安装，无法初始化OCR识别器")
            return
        
        try:
            # 初始化EasyOCR引擎
            logger.info(f"正在初始化EasyOCR引擎，语言: {languages}, GPU: {gpu}")
            self.reader = easyocr.Reader(languages, gpu=gpu)
            logger.info("EasyOCR引擎初始化成功")
        except Exception as e:
            logger.error(f"初始化EasyOCR失败: {e}")
            logger.error("请确保已安装EasyOCR: pip install easyocr")
            self.reader = None
    
    def preprocess_image(self, image: np.ndarray, method: str = 'auto') -> np.ndarray:
        """
        预处理图像以提高OCR识别准确率
        
        Args:
            image: 输入图像（BGR格式）
            method: 预处理方法 ('auto', 'enhanced', 'binary', 'lab', 'original')
            
        Returns:
            预处理后的图像
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # 如果图像太小，先放大（提高小文字识别率）
            h, w = image.shape[:2]
            scale_factor = 1.0
            if h < 50 or w < 50:
                # 小图像放大2-4倍
                scale_factor = max(2.0, min(4.0, 100.0 / max(h, w)))
                new_h, new_w = int(h * scale_factor), int(w * scale_factor)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                logger.debug(f"图像放大: {h}x{w} -> {new_h}x{new_w}, 倍数: {scale_factor:.2f}")
            
            if method == 'original':
                return image
            
            # 方法1: LAB色彩空间增强（适合彩色图像）
            if method == 'lab' or method == 'auto':
                try:
                    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    cl = clahe.apply(l)
                    enhanced = cv2.merge((cl, a, b))
                    result = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
                    if method == 'lab':
                        return result
                except Exception as e:
                    logger.warning(f"LAB预处理失败: {e}")
            
            # 方法2: 灰度图增强（适合黑白图像）
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 轻微高斯模糊去噪
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # CLAHE增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(blurred)
            
            if method == 'enhanced':
                return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            # 方法3: 二值化（适合高对比度文字）
            # 尝试自适应阈值
            binary_adaptive = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 也尝试OTSU阈值
            _, binary_otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 选择更好的二值化结果（选择更清晰的）
            # 通过计算边缘数量来判断
            edges_adaptive = cv2.Canny(binary_adaptive, 50, 150)
            edges_otsu = cv2.Canny(binary_otsu, 50, 150)
            
            if cv2.countNonZero(edges_adaptive) > cv2.countNonZero(edges_otsu):
                binary = binary_adaptive
            else:
                binary = binary_otsu
            
            if method == 'binary':
                return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            # auto模式：返回增强后的灰度图（EasyOCR对灰度图识别效果更好）
            return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            logger.warning(f"图像预处理失败，使用原图: {e}")
            return image
    
    def ocr_image(self, image: np.ndarray, save_debug: bool = False) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        对图像进行OCR识别（尝试多种预处理方法，选择最佳结果）
        
        Args:
            image: 输入图像（numpy数组，BGR格式）
            save_debug: 是否保存调试图像
            
        Returns:
            识别结果列表，每个元素为(文本, 中心坐标(x, y), 置信度)
            如果识别失败或未找到文本，返回空列表
        """
        if self.reader is None:
            logger.error("OCR引擎未初始化")
            return []
        
        if image is None or image.size == 0:
            logger.warning("输入图像为空")
            return []
        
        try:
            # 生成临时文件路径
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary")
            os.makedirs(temp_dir, exist_ok=True)
            timestamp = int(time.time() * 1000000)
            
            # 尝试多种预处理方法，选择识别结果最好的
            best_results = []
            best_count = 0
            methods = ['auto', 'enhanced', 'lab', 'binary', 'original']
            
            for method in methods:
                try:
                    # 预处理图像
                    processed_image = self.preprocess_image(image, method=method)
                    
                    # 保存调试图像
                    if save_debug:
                        debug_path = os.path.join(temp_dir, f"ocr_debug_{method}_{timestamp}.png")
                        cv2.imwrite(debug_path, processed_image)
                        logger.debug(f"保存调试图像: {debug_path}")
                    
                    # 保存临时图像用于OCR
                    temp_path = os.path.join(temp_dir, f"ocr_temp_{method}_{timestamp}.png")
                    cv2.imwrite(temp_path, processed_image)
                    
                    try:
                        # 执行OCR识别（降低阈值以提高识别率）
                        results = self.reader.readtext(
                            temp_path,
                            detail=1,
                            text_threshold=0.05,  # 降低阈值
                            low_text=0.05,       # 降低阈值
                            link_threshold=0.05,  # 降低阈值
                            mag_ratio=1.5,       # 降低放大倍数（避免过度放大）
                            slope_ths=0.1,       # 降低斜率阈值
                            ycenter_ths=0.5,     # 降低中心阈值
                            width_ths=0.3,       # 降低宽度阈值
                            add_margin=0.2,      # 增加边距
                            allowlist=None,
                            blocklist=None,
                            min_size=5           # 降低最小尺寸
                        )
                        
                        # 处理识别结果
                        processed_results = []
                        for result in results:
                            bbox = result[0]
                            text = result[1].strip()
                            confidence = result[2]
                            
                            # 过滤低置信度结果（但阈值更低）
                            if confidence < max(0.05, self.confidence_threshold):
                                continue
                            
                            # 过滤空文本
                            if not text:
                                continue
                            
                            # 计算中心坐标
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            x_center = int(sum(x_coords) / len(x_coords))
                            y_center = int(sum(y_coords) / len(y_coords))
                            
                            processed_results.append((text, (x_center, y_center), confidence))
                        
                        # 选择结果最多的方法
                        if len(processed_results) > best_count:
                            best_results = processed_results
                            best_count = len(processed_results)
                            logger.debug(f"方法 '{method}' 识别到 {best_count} 个文本")
                        
                    finally:
                        # 删除临时文件
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except Exception as e:
                            logger.warning(f"删除临时文件失败: {e}")
                            
                except Exception as e:
                    logger.warning(f"预处理方法 '{method}' 失败: {e}")
                    continue
            
            if best_results:
                logger.info(f"最佳识别结果: {best_count} 个文本（使用多种预处理方法）")
            
            return best_results
                    
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def ocr_region(self, window_handle: int, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        对指定窗口的指定区域进行OCR识别
        
        Args:
            window_handle: 窗口句柄（VNC模式下不使用）
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
            
        Returns:
            识别结果列表，每个元素为(文本, 中心坐标(相对于区域的坐标), 置信度)
        """
        try:
            # 优先使用VNC实例直接截图
            if self.vnc_instance is not None:
                # 直接使用VNC的Capture方法获取区域截图
                region_image = self.vnc_instance.Capture(x1, y1, x2, y2)
                
                if region_image is None:
                    logger.error(f"VNC区域截图失败: ({x1}, {y1}, {x2}, {y2})")
                    return []
                
                # 转换为numpy数组
                if not isinstance(region_image, np.ndarray):
                    try:
                        # 优先使用get_memoryview方法（ManagedMemoryView）
                        if hasattr(region_image, 'get_memoryview'):
                            try:
                                mv = region_image.get_memoryview()
                                region_image = np.array(mv, copy=False)
                                logger.debug(f"✓ 使用get_memoryview()转换成功: shape={region_image.shape}")
                            except Exception as e1:
                                logger.debug(f"get_memoryview()转换失败: {e1}，尝试np.asarray")
                                region_image = np.asarray(region_image, dtype=np.uint8)
                        else:
                            region_image = np.asarray(region_image, dtype=np.uint8)
                        
                        # 验证转换结果
                        if not isinstance(region_image, np.ndarray):
                            raise ValueError(f"无法转换为numpy数组，类型: {type(region_image)}")
                        
                        if not hasattr(region_image, 'shape') or len(region_image.shape) == 0:
                            raise ValueError(f"转换后的数组shape无效")
                            
                    except Exception as e:
                        logger.error(f"转换图像格式失败: {e}, 类型: {type(region_image)}")
                        # 最后尝试get_memoryview
                        if hasattr(region_image, 'get_memoryview'):
                            try:
                                mv = region_image.get_memoryview()
                                region_image = np.array(mv, copy=False)
                                logger.info(f"✓ 使用get_memoryview转换成功")
                            except:
                                return []
                        else:
                            return []
                
                # 检查图像有效性
                if region_image.size == 0:
                    logger.error(f"区域无效（图像大小为0）: ({x1}, {y1}, {x2}, {y2})")
                    return []
                
                # 检查图像形状
                if len(region_image.shape) < 2:
                    logger.error(f"图像形状无效: {region_image.shape}, 类型: {region_image.dtype}")
                    return []
                
                # 确保数据类型正确
                if region_image.dtype != np.uint8:
                    try:
                        if region_image.dtype == np.float32 or region_image.dtype == np.float64:
                            region_image = np.clip(region_image * 255, 0, 255).astype(np.uint8)
                        else:
                            region_image = region_image.astype(np.uint8)
                    except Exception as e:
                        logger.error(f"转换图像数据类型失败: {e}")
                        return []
                
                # 执行OCR识别（保存调试图像）
                results = self.ocr_image(region_image, save_debug=True)
                
                # 将坐标转换为绝对坐标（相对于整个窗口）
                absolute_results = []
                for text, (cx, cy), confidence in results:
                    absolute_x = x1 + cx
                    absolute_y = y1 + cy
                    absolute_results.append((text, (absolute_x, absolute_y), confidence))
                
                return absolute_results
            
            # 兼容旧方式：使用vnc_capture_func
            elif self.vnc_capture_func:
                # 获取窗口截图
                screen_image = self.vnc_capture_func(window_handle)
                if screen_image is None:
                    logger.error(f"窗口 {window_handle} 截图失败")
                    return []
                
                # 确保坐标在图像范围内
                h, w = screen_image.shape[:2]
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(x1 + 1, min(x2, w))
                y2 = max(y1 + 1, min(y2, h))
                
                # 裁剪区域
                region_image = screen_image[y1:y2, x1:x2]
                
                if region_image.size == 0:
                    logger.error(f"区域无效: ({x1}, {y1}, {x2}, {y2})")
                    return []
                
                # 执行OCR识别（保存调试图像）
                results = self.ocr_image(region_image, save_debug=True)
                
                # 将坐标转换为绝对坐标（相对于整个窗口）
                absolute_results = []
                for text, (cx, cy), confidence in results:
                    absolute_x = x1 + cx
                    absolute_y = y1 + cy
                    absolute_results.append((text, (absolute_x, absolute_y), confidence))
                
                return absolute_results
            else:
                logger.error("VNC截图函数或VNC实例未设置")
                return []
            
        except Exception as e:
            logger.error(f"区域OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def find_text(self, window_handle: int, x1: int, y1: int, x2: int, y2: int, 
                  target_text: Optional[str] = None) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        在指定区域查找文本
        
        Args:
            window_handle: 窗口句柄
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
            target_text: 目标文本（可选），如果提供则只返回包含此文本的结果
            
        Returns:
            识别结果列表，如果提供了target_text，则只返回包含该文本的结果
        """
        results = self.ocr_region(window_handle, x1, y1, x2, y2)
        
        if target_text is None:
            return results
        
        # 过滤包含目标文本的结果
        filtered_results = []
        target_text_lower = target_text.lower()
        for text, pos, confidence in results:
            if target_text_lower in text.lower():
                filtered_results.append((text, pos, confidence))
        
        return filtered_results


# 全局OCR实例（延迟初始化）
_ocr_instance: Optional[OCR] = None


def get_ocr_instance(vnc_capture_func: Optional[Callable] = None, 
                     languages: List[str] = ['ch_sim', 'en'],
                     gpu: bool = False,
                     confidence_threshold: float = 0.1) -> Optional[OCR]:
    """
    获取全局OCR实例（单例模式）
    
    Args:
        vnc_capture_func: VNC截图函数
        languages: 支持的语言列表
        gpu: 是否启用GPU加速
        confidence_threshold: 置信度阈值
        
    Returns:
        OCR实例或None
    """
    global _ocr_instance
    
    if _ocr_instance is None:
        if not EASYOCR_AVAILABLE:
            logger.error("EasyOCR未安装，无法创建OCR实例")
            return None
        
        _ocr_instance = OCR(
            vnc_capture_func=vnc_capture_func,
            languages=languages,
            gpu=gpu,
            confidence_threshold=confidence_threshold
        )
    elif vnc_capture_func and _ocr_instance.vnc_capture_func != vnc_capture_func:
        # 如果提供了新的截图函数，更新它
        _ocr_instance.vnc_capture_func = vnc_capture_func
    
    return _ocr_instance

