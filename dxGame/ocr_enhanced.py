# -*- coding: utf-8 -*-
"""
增强版OCR识别模块
支持多种OCR引擎：PaddleOCR（推荐）、Tesseract、EasyOCR
自动选择最佳识别结果，提高稳定性和准确率
"""
import cv2
import numpy as np
import os
import time
import logging
from typing import Tuple, Optional, List, Callable

logger = logging.getLogger(__name__)

# ==================== OCR引擎检测 ====================

# 1. PaddleOCR（推荐，对中文支持好，稳定性高）
PADDLEOCR_AVAILABLE = False
PaddleOCR = None
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except Exception as e:
    PaddleOCR = None
    error_msg = str(e)
    error_type = type(e).__name__
    # 检查是否是Python版本兼容性问题
    if "not subscriptable" in error_msg or "list[int]" in error_msg or error_type == "TypeError":
        logger.debug(f"PaddleOCR导入失败（Python版本兼容性问题）: {error_msg}")
    # 检查是否是DLL加载问题
    elif "dll" in error_msg.lower() or "shm.dll" in error_msg.lower():
        logger.debug(f"PaddleOCR导入失败（PyTorch DLL问题）: {error_msg[:100]}...")
    else:
        logger.debug(f"PaddleOCR未安装或导入失败 ({error_type}): {error_msg[:100]}...")

# 2. Tesseract OCR（经典稳定）
TESSERACT_AVAILABLE = False
pytesseract = None
try:
    import pytesseract
    # 配置Tesseract路径（按优先级：环境变量 > 固定路径 > PATH）
    # 支持 TESSERACT_CMD 环境变量，确保不同IDE/平台使用同一配置
    tesseract_found = False
    tesseract_cmd_env = os.environ.get("TESSERACT_CMD", "").strip()
    if tesseract_cmd_env and os.path.exists(tesseract_cmd_env):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_env
        print(f"[OCR] 使用环境变量TESSERACT_CMD: {tesseract_cmd_env}")
        logger.info(f"✓ 使用环境变量TESSERACT_CMD: {tesseract_cmd_env}")
        tesseract_found = True
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    if not tesseract_found:
        # 检查固定路径
        for tesseract_path in tesseract_paths:
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                # 使用print确保信息输出（logger可能还未配置）
                print(f"[OCR] 已配置Tesseract路径: {tesseract_path}")
                logger.info(f"✓ 已配置Tesseract路径: {tesseract_path}")
                tesseract_found = True
                break
    
    if not tesseract_found:
        # 如果未找到，尝试从环境变量或PATH中查找
        try:
            # 测试是否能获取版本（说明已经在PATH中）
            version = pytesseract.get_tesseract_version()
            print(f"[OCR] Tesseract已在系统PATH中，版本: {version}")
            logger.info(f"✓ Tesseract已在系统PATH中，版本: {version}")
            tesseract_found = True
        except Exception as e:
            print(f"[OCR] 警告: 未找到Tesseract，请确保已安装或配置路径: {e}")
            logger.warning(f"⚠️ 未找到Tesseract，请确保已安装或配置路径: {e}")
    
    TESSERACT_AVAILABLE = True
except ImportError as e:
    pytesseract = None
    print(f"[OCR] pytesseract导入失败（ImportError）: {e}")
    print("[OCR] 请安装: pip install pytesseract")
    logger.warning(f"pytesseract未安装，将使用其他OCR引擎。安装: pip install pytesseract")
    logger.debug(f"ImportError详情: {e}")
except Exception as e:
    # 捕获其他可能的异常（如模块内部错误）
    pytesseract = None
    print(f"[OCR] pytesseract导入时出现异常: {type(e).__name__}: {e}")
    print("[OCR] 请检查pytesseract安装是否正确")
    logger.warning(f"pytesseract导入失败: {type(e).__name__}: {e}")
    import traceback
    logger.debug(traceback.format_exc())

# 3. EasyOCR（备用）
EASYOCR_AVAILABLE = False
easyocr = None
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False
    logger.debug("EasyOCR未安装，将使用其他OCR引擎。安装: pip install easyocr")
except Exception as e:
    easyocr = None
    EASYOCR_AVAILABLE = False
    error_msg = str(e)
    # 检查是否是DLL加载问题
    if "dll" in error_msg.lower() or "shm.dll" in error_msg.lower():
        logger.debug(f"EasyOCR导入失败（PyTorch DLL问题）: {error_msg[:100]}...")
    else:
        logger.debug(f"EasyOCR导入失败: {error_msg[:100]}...")


class EnhancedOCR:
    """增强版OCR识别器，支持多种OCR引擎"""
    
    @staticmethod
    def cleanup_debug_images():
        """
        清理OCR调试图像目录中的所有临时图片
        
        Returns:
            清理的文件数量
        """
        try:
            temp_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary")
            debug_dir = os.path.join(temp_base_dir, "ocr_debug")
            
            count = 0
            
            # 清理 ocr_debug 目录中的图片
            if os.path.exists(debug_dir):
                for filename in os.listdir(debug_dir):
                    # 清理所有OCR相关的临时图片
                    if (filename.startswith("ocr_region_") or 
                        filename.startswith("ocr_debug_") or 
                        filename.startswith("ocr_temp_") or
                        filename.startswith("ocr_easyocr_")) and filename.endswith(".png"):
                        file_path = os.path.join(debug_dir, filename)
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            logger.warning(f"删除调试图像失败 {filename}: {e}")
            
            # 清理 Temporary 根目录中的OCR临时图片
            if os.path.exists(temp_base_dir):
                for filename in os.listdir(temp_base_dir):
                    # 清理所有OCR相关的临时图片
                    if (filename.startswith("ocr_region_") or 
                        filename.startswith("ocr_debug_") or 
                        filename.startswith("ocr_temp_") or
                        filename.startswith("ocr_easyocr_")) and filename.endswith(".png"):
                        file_path = os.path.join(temp_base_dir, filename)
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            logger.warning(f"删除临时图片失败 {filename}: {e}")
            
            if count > 0:
                logger.debug(f"已清理 {count} 个OCR临时图片")
            return count
        except Exception as e:
            logger.error(f"清理OCR临时图片失败: {e}")
            return 0
    
    def __init__(self, vnc_capture_func: Optional[Callable] = None, 
                 vnc_instance=None,
                 languages: List[str] = ['ch', 'en'],
                 gpu: bool = False,
                 confidence_threshold: float = 0.3,
                 preferred_engine: str = 'auto'):
        """
        初始化OCR识别器
        
        Args:
            vnc_capture_func: VNC截图函数（已废弃，优先使用vnc_instance）
            vnc_instance: VNC截图实例（优先使用），如果提供则直接使用VNC.Capture()方法
            languages: 支持的语言列表
                - PaddleOCR: ['ch', 'en'] (中文和英文)
                - Tesseract: ['chi_sim', 'eng'] (简体中文和英文)
                - EasyOCR: ['ch_sim', 'en'] (简体中文和英文)
            gpu: 是否启用GPU加速
            confidence_threshold: 置信度阈值
            preferred_engine: 优先使用的引擎 ('paddle', 'tesseract', 'easyocr', 'auto')
        """
        self.vnc_capture_func = vnc_capture_func
        self.vnc_instance = vnc_instance
        self.confidence_threshold = confidence_threshold
        self.preferred_engine = preferred_engine
        
        # 初始化各OCR引擎
        self.paddle_ocr = None
        self.tesseract_available = False
        self.easyocr_reader = None
        
        # 优先初始化Tesseract（不依赖PyTorch，最稳定）
        if TESSERACT_AVAILABLE and pytesseract is not None:
            try:
                # 确保Tesseract路径已配置（优先使用环境变量 TESSERACT_CMD）
                tesseract_found = False
                tesseract_cmd_set = False
                tesseract_cmd_env = os.environ.get("TESSERACT_CMD", "").strip()
                if tesseract_cmd_env and os.path.exists(tesseract_cmd_env):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_env
                    tesseract_found = True
                    tesseract_cmd_set = True
                tesseract_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
                if not tesseract_found:
                    for tesseract_path in tesseract_paths:
                        if os.path.exists(tesseract_path):
                            pytesseract.pytesseract.tesseract_cmd = tesseract_path
                            tesseract_found = True
                            tesseract_cmd_set = True
                            logger.debug(f"已设置Tesseract路径: {tesseract_path}")
                            break
                
                # 如果路径不存在，尝试从PATH中查找
                if not tesseract_found:
                    try:
                        # 尝试获取版本（如果成功说明在PATH中）
                        version = pytesseract.get_tesseract_version()
                        tesseract_found = True
                        logger.debug(f"Tesseract在PATH中，版本: {version}")
                    except:
                        pass
                
                # 测试Tesseract是否可用
                if tesseract_found:
                    version = pytesseract.get_tesseract_version()
                    logger.info(f"✓ Tesseract OCR可用（不依赖PyTorch），版本: {version}")
                    if tesseract_cmd_set:
                        logger.info(f"  Tesseract路径: {pytesseract.pytesseract.tesseract_cmd}")
                    self.tesseract_available = True
                else:
                    raise Exception("未找到Tesseract可执行文件")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"⚠️ Tesseract OCR不可用: {error_msg}")
                logger.error(f"   请确保Tesseract已安装在: C:\\Program Files\\Tesseract-OCR\\")
                logger.error(f"   当前tesseract_cmd: {getattr(pytesseract.pytesseract, 'tesseract_cmd', '未设置')}")
                self.tesseract_available = False
        
        # 禁用PaddleOCR（已屏蔽，只使用Tesseract）
        # if PADDLEOCR_AVAILABLE and (preferred_engine == 'paddle' or preferred_engine == 'auto'):
        #     ...
        self.paddle_ocr = None
        logger.debug("PaddleOCR已禁用（只使用Tesseract OCR）")
        
        # 禁用EasyOCR（已屏蔽，只使用Tesseract）
        # if EASYOCR_AVAILABLE and not self.paddle_ocr and (preferred_engine == 'easyocr' or preferred_engine == 'auto'):
        #     ...
        self.easyocr_reader = None
        logger.debug("EasyOCR已禁用（只使用Tesseract OCR）")
        
        # 总结可用的OCR引擎（只显示Tesseract）
        if self.tesseract_available:
            logger.info("✓ OCR引擎初始化完成，使用引擎: Tesseract（已禁用PaddleOCR和EasyOCR）")
        else:
            logger.error("⚠️ Tesseract OCR不可用，请确保已安装Tesseract和pytesseract")
            logger.error("   安装方法: pip install pytesseract")
            logger.error("   并确保系统PATH中包含Tesseract可执行文件")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像以提高OCR识别准确率
        
        Args:
            image: 输入图像（BGR格式）
            
        Returns:
            预处理后的图像
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # 确保是numpy数组
            if not isinstance(image, np.ndarray):
                image = np.asarray(image)
            
            # 确保图像有正确的形状
            if len(image.shape) < 2:
                logger.warning("图像形状无效")
                return image
            
            # 确保数据类型正确（uint8）
            if image.dtype != np.uint8:
                if image.dtype == np.float32 or image.dtype == np.float64:
                    # 如果是浮点数，转换为0-255范围
                    image = (image * 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            
            h, w = image.shape[:2]
            
            if h == 0 or w == 0:
                logger.warning("图像尺寸为0")
                return image
            
            # 如果图像太小，放大
            if h < 50 or w < 50:
                scale_factor = max(2.0, min(4.0, 100.0 / max(h, w)))
                new_h, new_w = int(h * scale_factor), int(w * scale_factor)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 轻微去噪
            denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
            
            # 转换回BGR格式
            return cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            logger.warning(f"图像预处理失败: {e}")
            return image
    
    def preprocess_image_for_numbers(self, image: np.ndarray) -> np.ndarray:
        """
        专门为数字识别优化的图像预处理
        
        Args:
            image: 输入图像（BGR格式）
            
        Returns:
            预处理后的图像（灰度图，更适合数字识别）
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # 确保是numpy数组
            if not isinstance(image, np.ndarray):
                image = np.asarray(image)
            
            # 确保图像有正确的形状
            if len(image.shape) < 2:
                logger.warning("图像形状无效")
                return image
            
            # 确保数据类型正确（uint8）
            if image.dtype != np.uint8:
                if image.dtype == np.float32 or image.dtype == np.float64:
                    image = (image * 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            
            h, w = image.shape[:2]
            
            if h == 0 or w == 0:
                logger.warning("图像尺寸为0")
                return image
            
            # 放大图像（数字识别需要更高的分辨率）
            if h < 100 or w < 100:
                scale_factor = max(3.0, min(5.0, 150.0 / max(h, w)))
                new_h, new_w = int(h * scale_factor), int(w * scale_factor)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                h, w = new_h, new_w
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 使用自适应阈值进行二值化（比全局阈值更适合数字）
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 形态学操作：去除噪点，连接断开的数字
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 增强对比度（CLAHE在二值化之前）
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            binary_enhanced = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            binary_enhanced = cv2.morphologyEx(binary_enhanced, cv2.MORPH_CLOSE, kernel)
            binary_enhanced = cv2.morphologyEx(binary_enhanced, cv2.MORPH_OPEN, kernel)
            
            # 选择对比度更好的结果
            # 计算两个版本的对比度，选择更好的
            contrast1 = np.std(binary.astype(np.float32))
            contrast2 = np.std(binary_enhanced.astype(np.float32))
            
            if contrast2 > contrast1:
                final_binary = binary_enhanced
            else:
                final_binary = binary
            
            # 转换回BGR格式（保持兼容性）
            return cv2.cvtColor(final_binary, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            logger.warning(f"数字识别图像预处理失败: {e}")
            # 失败时返回普通预处理的结果
            return self.preprocess_image(image)
    
    def ocr_with_paddle(self, image: np.ndarray) -> List[Tuple[str, Tuple[int, int], float]]:
        """使用PaddleOCR识别"""
        if not self.paddle_ocr:
            return []
        
        try:
            # PaddleOCR需要RGB格式
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            results = self.paddle_ocr.ocr(rgb_image, cls=True)
            
            processed_results = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        try:
                            bbox = line[0]
                            text_info = line[1]
                            
                            # 处理不同的返回格式
                            if isinstance(text_info, tuple) and len(text_info) >= 2:
                                text, confidence = text_info[0], text_info[1]
                            elif isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                text, confidence = text_info[0], text_info[1]
                            else:
                                continue
                            
                            if confidence >= self.confidence_threshold and text and text.strip():
                                # 计算中心坐标
                                if bbox and len(bbox) > 0:
                                    x_coords = [point[0] for point in bbox]
                                    y_coords = [point[1] for point in bbox]
                                    x_center = int(sum(x_coords) / len(x_coords))
                                    y_center = int(sum(y_coords) / len(y_coords))
                                    processed_results.append((text.strip(), (x_center, y_center), confidence))
                        except Exception as e:
                            logger.debug(f"处理PaddleOCR结果时出错: {e}")
                            continue
            
            return processed_results
        except Exception as e:
            logger.error(f"PaddleOCR识别失败: {e}")
            return []
    
    def ocr_with_tesseract(self, image: np.ndarray, numbers_only: bool = False) -> List[Tuple[str, Tuple[int, int], float]]:
        """使用Tesseract OCR识别"""
        if not self.tesseract_available:
            return []
        
        try:
            # 确保是numpy数组
            if not isinstance(image, np.ndarray):
                image = np.asarray(image)
            
            # 确保图像有正确的形状
            if len(image.shape) < 2:
                logger.warning("Tesseract: 图像形状无效")
                return []
            
            # 确保数据类型是uint8
            if image.dtype != np.uint8:
                if image.dtype == np.float32 or image.dtype == np.float64:
                    # 如果是浮点数，转换为0-255范围
                    image = np.clip(image * 255, 0, 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            
            # Tesseract需要PIL Image或numpy数组
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 确保灰度图是uint8类型
            if gray.dtype != np.uint8:
                gray = gray.astype(np.uint8)
            
            # 配置Tesseract（数字识别使用特殊配置）
            if numbers_only:
                # 数字识别专用配置：只识别0-9，PSM模式设为8（单词）
                config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
            else:
                config = '--oem 3 --psm 6 -l chi_sim+eng'
            
            # 获取详细识别结果
            data = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
            
            processed_results = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0.0
                
                if text and conf >= self.confidence_threshold * 100:  # Tesseract使用0-100的置信度
                    # 如果是数字识别，过滤掉非数字字符
                    if numbers_only:
                        # 只保留数字字符
                        text = ''.join(c for c in text if c.isdigit())
                        if not text:
                            continue
                    
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    processed_results.append((text, (x, y), conf / 100.0))
            
            return processed_results
        except Exception as e:
            logger.error(f"Tesseract OCR识别失败: {e}")
            return []
    
    def ocr_with_easyocr(self, image: np.ndarray) -> List[Tuple[str, Tuple[int, int], float]]:
        """使用EasyOCR识别"""
        if not self.easyocr_reader:
            return []
        
        try:
            # 保存临时文件
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"ocr_easyocr_{int(time.time() * 1000000)}.png")
            cv2.imwrite(temp_path, image)
            
            try:
                results = self.easyocr_reader.readtext(
                    temp_path,
                    detail=1,
                    text_threshold=0.05,
                    low_text=0.05,
                    link_threshold=0.05
                )
                
                processed_results = []
                for result in results:
                    bbox, text, confidence = result
                    if confidence >= self.confidence_threshold and text.strip():
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        x_center = int(sum(x_coords) / len(x_coords))
                        y_center = int(sum(y_coords) / len(y_coords))
                        processed_results.append((text.strip(), (x_center, y_center), confidence))
                
                return processed_results
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
        except Exception as e:
            logger.error(f"EasyOCR识别失败: {e}")
            return []
    
    def ocr_numbers(self, image: np.ndarray) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        专门用于数字识别的方法，使用数字优化的预处理和配置
        
        Args:
            image: 输入图像
            
        Returns:
            识别结果列表，只包含数字字符
        """
        if image is None or image.size == 0:
            return []
        
        try:
            # 确保是numpy数组
            if not isinstance(image, np.ndarray):
                image = np.asarray(image)
            
            # 确保图像有正确的形状和数据类型
            if len(image.shape) < 2:
                logger.warning("图像形状无效")
                return []
            
            if image.dtype != np.uint8:
                if image.dtype == np.float32 or image.dtype == np.float64:
                    image = np.clip(image * 255, 0, 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            
            # 使用数字识别专用预处理
            processed_image = self.preprocess_image_for_numbers(image)
            
            if processed_image is None or processed_image.size == 0:
                logger.warning("图像预处理后无效")
                return []
            
            all_results = []
            
            # 只使用Tesseract（数字识别最准确，其他引擎已禁用）
            if self.tesseract_available:
                results = self.ocr_with_tesseract(processed_image, numbers_only=True)
                if results:
                    logger.debug(f"Tesseract数字识别: {len(results)} 个结果")
                    all_results.extend(results)
            
            # PaddleOCR和EasyOCR已禁用
            # if self.paddle_ocr:
            #     ...
            # if self.easyocr_reader:
            #     ...
            
            # 对所有结果进行后处理：移除非数字字符
            final_results = []
            for text, pos, conf in all_results:
                cleaned = ''.join(c for c in text if c.isdigit())
                if cleaned:
                    final_results.append((cleaned, pos, conf))
            
            return final_results
            
        except Exception as e:
            logger.error(f"数字识别失败: {e}")
            return []
    
    def ocr_image(self, image: np.ndarray) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        使用多种OCR引擎识别，选择最佳结果
        
        Args:
            image: 输入图像
            
        Returns:
            识别结果列表
        """
        if image is None or image.size == 0:
            return []
        
        # 确保是numpy数组
        if not isinstance(image, np.ndarray):
            try:
                image = np.asarray(image)
            except Exception as e:
                logger.error(f"无法转换图像为numpy数组: {e}")
                return []
        
        # 确保图像有正确的形状和数据类型
        if len(image.shape) < 2:
            logger.warning("图像形状无效")
            return []
        
        # 确保数据类型是uint8
        if image.dtype != np.uint8:
            if image.dtype == np.float32 or image.dtype == np.float64:
                # 如果是浮点数，转换为0-255范围
                image = np.clip(image * 255, 0, 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
        
        # 预处理图像
        processed_image = self.preprocess_image(image)
        
        # 确保预处理后的图像有效
        if processed_image is None or processed_image.size == 0:
            logger.warning("图像预处理后无效")
            return []
        
        # 只使用Tesseract OCR（其他引擎已禁用）
        all_results = []
        
        # 只使用Tesseract
        if self.tesseract_available:
            results = self.ocr_with_tesseract(processed_image)
            if results:
                logger.debug(f"Tesseract识别到 {len(results)} 个文本")
                all_results.extend(results)
        
        # PaddleOCR和EasyOCR已禁用
        # if self.paddle_ocr:
        #     ...
        # if self.easyocr_reader:
        #     ...
        
        # 去重（相同位置的文本只保留置信度最高的）
        if all_results:
            unique_results = {}
            for text, pos, conf in all_results:
                key = f"{pos[0]}_{pos[1]}"
                if key not in unique_results or conf > unique_results[key][2]:
                    unique_results[key] = (text, pos, conf)
            return list(unique_results.values())
        
        return []
    
    def ocr_region(self, window_handle: int, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        对指定窗口的指定区域进行OCR识别
        
        Args:
            window_handle: 窗口句柄（VNC模式下不使用）
            x1, y1: 区域左上角坐标
            x2, y2: 区域右下角坐标
            
        Returns:
            识别结果列表
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
                        # 方法1: 如果 ManagedMemoryView 有 get_memoryview 方法（推荐方法）
                        if hasattr(region_image, 'get_memoryview'):
                            try:
                                mv = region_image.get_memoryview()
                                region_image = np.array(mv, copy=False)
                                logger.debug(f"✓ 使用get_memoryview()转换成功: shape={region_image.shape}")
                            except Exception as e1:
                                logger.debug(f"get_memoryview()转换失败: {e1}，尝试其他方法")
                                # 如果get_memoryview失败，尝试直接使用np.asarray
                                region_image = np.asarray(region_image, dtype=np.uint8)
                        
                        # 方法2: 直接使用 np.asarray（指定dtype）
                        else:
                            region_image = np.asarray(region_image, dtype=np.uint8)
                        
                        # 验证转换结果
                        if not isinstance(region_image, np.ndarray):
                            raise ValueError(f"无法转换为numpy数组，类型: {type(region_image)}")
                        
                        # 检查shape是否有效
                        if not hasattr(region_image, 'shape') or len(region_image.shape) == 0:
                            # 如果shape为空，尝试从原始对象获取信息
                            if hasattr(region_image, 'shape'):
                                original_shape = region_image.shape
                                logger.warning(f"转换后shape为空，原始shape: {original_shape}")
                                # 如果原始对象有shape，尝试重建
                                if len(original_shape) >= 2 and hasattr(region_image, 'tobytes'):
                                    try:
                                        bytes_data = region_image.tobytes()
                                        region_image = np.frombuffer(bytes_data, dtype=np.uint8).reshape(original_shape)
                                        logger.info(f"✓ 使用tobytes重建成功: shape={region_image.shape}")
                                    except Exception as e2:
                                        logger.error(f"使用tobytes重建失败: {e2}")
                                        raise ValueError(f"转换后的数组shape无效: {original_shape}")
                                else:
                                    raise ValueError(f"转换后的数组shape无效: {original_shape}")
                            
                    except Exception as e:
                        logger.error(f"转换图像格式失败: {e}, 类型: {type(region_image)}")
                        # 尝试获取更多调试信息
                        if hasattr(region_image, 'shape'):
                            logger.error(f"  图像shape: {region_image.shape}")
                        if hasattr(region_image, 'dtype'):
                            logger.error(f"  图像dtype: {region_image.dtype}")
                        # 最后尝试：使用get_memoryview
                        if hasattr(region_image, 'get_memoryview'):
                            try:
                                logger.info(f"  最后尝试：使用get_memoryview...")
                                mv = region_image.get_memoryview()
                                region_image = np.array(mv, copy=False)
                                logger.info(f"  ✓ 使用get_memoryview转换成功: shape={region_image.shape}")
                            except Exception as e2:
                                logger.error(f"  get_memoryview也失败: {e2}")
                                return []
                        else:
                            return []
                
                # 检查图像有效性
                if not hasattr(region_image, 'size') or region_image.size == 0:
                    logger.error(f"区域无效（图像大小为0）: ({x1}, {y1}, {x2}, {y2})")
                    return []
                
                # 检查图像形状
                if not hasattr(region_image, 'shape') or len(region_image.shape) < 2:
                    logger.error(f"图像形状无效: {getattr(region_image, 'shape', 'unknown')}, 类型: {getattr(region_image, 'dtype', 'unknown')}")
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
                
                logger.debug(f"图像格式: shape={region_image.shape}, dtype={region_image.dtype}, size={region_image.size}")
                
                # 保存调试图像
                debug_path = None
                try:
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary", "ocr_debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, f"ocr_region_{int(time.time())}.png")
                    cv2.imwrite(debug_path, region_image)
                    logger.debug(f"调试图像已保存: {debug_path}")
                except:
                    pass
                
                try:
                    # 执行OCR识别
                    results = self.ocr_image(region_image)
                    
                    # 将坐标转换为绝对坐标
                    absolute_results = []
                    for text, (cx, cy), confidence in results:
                        absolute_x = x1 + cx
                        absolute_y = y1 + cy
                        absolute_results.append((text, (absolute_x, absolute_y), confidence))
                    
                    # 保存带标注的图像用于调试（显示红框）
                    if absolute_results:
                        try:
                            self._save_annotated_image(region_image, results, x1, y1)
                        except Exception as e:
                            logger.debug(f"保存标注图像失败: {e}")
                    
                    return absolute_results
                finally:
                    # 清理调试图像
                    if debug_path and os.path.exists(debug_path):
                        try:
                            os.remove(debug_path)
                            logger.debug(f"已清理调试图像: {debug_path}")
                        except Exception as e:
                            logger.warning(f"清理调试图像失败: {e}")
            
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
                
                # 保存调试图像
                debug_path = None
                try:
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary", "ocr_debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, f"ocr_region_{int(time.time())}.png")
                    cv2.imwrite(debug_path, region_image)
                    logger.debug(f"调试图像已保存: {debug_path}")
                except:
                    pass
                
                try:
                    # 执行OCR识别
                    results = self.ocr_image(region_image)
                    
                    # 将坐标转换为绝对坐标
                    absolute_results = []
                    for text, (cx, cy), confidence in results:
                        absolute_x = x1 + cx
                        absolute_y = y1 + cy
                        absolute_results.append((text, (absolute_x, absolute_y), confidence))
                    
                    return absolute_results
                finally:
                    # 清理调试图像
                    if debug_path and os.path.exists(debug_path):
                        try:
                            os.remove(debug_path)
                            logger.debug(f"已清理调试图像: {debug_path}")
                        except Exception as e:
                            logger.warning(f"清理调试图像失败: {e}")
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
            target_text: 目标文本（可选）
            
        Returns:
            识别结果列表
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
    
    def _save_annotated_image(self, image: np.ndarray, results: List[Tuple[str, Tuple[int, int], float]], 
                              offset_x: int = 0, offset_y: int = 0):
        """
        保存带OCR标注的图像（红框标注识别结果）
        
        Args:
            image: 原始图像
            results: OCR识别结果列表（相对坐标）
            offset_x: X坐标偏移量
            offset_y: Y坐标偏移量
        """
        if image is None or image.size == 0 or not results:
            return
        
        try:
            # 创建图像副本用于绘制
            display_image = image.copy()
            
            # 确保是BGR格式
            if len(display_image.shape) == 2:
                display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2BGR)
            elif len(display_image.shape) == 3 and display_image.shape[2] == 4:
                display_image = cv2.cvtColor(display_image, cv2.COLOR_RGBA2BGR)
            
            h, w = display_image.shape[:2]
            
            # 绘制每个识别结果
            for i, (text, (cx, cy), confidence) in enumerate(results):
                # 估算文本边界框（根据文本长度）
                text_len = len(text)
                box_width = max(30, min(text_len * 12, w - cx))
                box_height = max(15, min(25, h - cy))
                
                # 计算边界框坐标
                x1_box = max(0, cx - box_width // 2)
                y1_box = max(0, cy - box_height // 2)
                x2_box = min(w, cx + box_width // 2)
                y2_box = min(h, cy + box_height // 2)
                
                # 绘制红色矩形框
                cv2.rectangle(display_image, (x1_box, y1_box), (x2_box, y2_box), (0, 0, 255), 2)
                
                # 绘制中心点（绿色）
                cv2.circle(display_image, (cx, cy), 3, (0, 255, 0), -1)
                
                # 绘制文本标签
                label = f"{i+1}:{text[:15]} ({confidence:.2f})"
                label_y = max(15, y1_box - 5)
                
                # 绘制文本背景（白色）
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    display_image,
                    (x1_box, label_y - text_height - 5),
                    (x1_box + text_width + 5, label_y + 5),
                    (255, 255, 255),
                    -1
                )
                
                # 绘制文本（红色）
                cv2.putText(
                    display_image,
                    label,
                    (x1_box + 2, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA
                )
            
            # 保存标注图像
            try:
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Temporary", "ocr_debug")
                os.makedirs(debug_dir, exist_ok=True)
                annotated_path = os.path.join(debug_dir, f"ocr_annotated_{int(time.time())}.png")
                cv2.imwrite(annotated_path, display_image)
                logger.info(f"✓ OCR标注图像已保存: {annotated_path}")
                
                # 尝试显示图像
                try:
                    from dxGame import MiniOpenCV
                    MiniOpenCV.imshow("OCR识别结果", display_image)
                    logger.info(f"已显示OCR识别结果，共识别到 {len(results)} 个文本")
                except ImportError:
                    logger.debug("MiniOpenCV不可用，跳过显示")
                except Exception as e:
                    logger.debug(f"显示图像失败: {e}")
                    
            except Exception as e:
                logger.warning(f"保存OCR标注图像失败: {e}")
                    
        except Exception as e:
            logger.error(f"绘制OCR结果失败: {e}")

