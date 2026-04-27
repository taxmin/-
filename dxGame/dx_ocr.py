# -*- coding: utf-8 -*-
"""
VNC OCR识别类 - 兼容DX OCR接口
使用方法：
    self.dx.Ocr = VNC_OCR("127.0.0.1", "5600", "")  # IP, 端口, 密码
"""
# 处理直接运行时的路径问题
import sys
import os
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
_parent_dir = os.path.dirname(_current_dir)  # dx多开框架 目录
# 如果父目录不在路径中，尝试添加（用于直接运行此文件）
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import time
import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional

# OCR模块延迟导入（避免启动时加载失败）
ENHANCED_OCR_AVAILABLE = False
OCR_AVAILABLE = False
EnhancedOCR = None
OCR = None

def _import_ocr_modules():
    """延迟导入OCR模块，避免启动时因依赖问题导致程序无法启动"""
    global ENHANCED_OCR_AVAILABLE, OCR_AVAILABLE, EnhancedOCR, OCR
    
    if EnhancedOCR is not None or OCR is not None:
        return  # 已经导入过了
    
    # 确保当前目录（dxGame）在Python路径中
    if _current_dir not in sys.path:
        sys.path.insert(0, _current_dir)
    
    # 优先从当前目录（dxGame）导入增强版OCR
    # 注意：即使模块内部有PyTorch DLL错误，模块本身也应该能导入
    try:
        # 先尝试相对导入（同目录）
        try:
            from ocr_enhanced import EnhancedOCR  # type: ignore
            ENHANCED_OCR_AVAILABLE = True
            logging.info("✓ 成功从本地目录导入增强版OCR模块")
            # 检查是否有可用的OCR引擎
            if hasattr(EnhancedOCR, 'TESSERACT_AVAILABLE'):
                from ocr_enhanced import TESSERACT_AVAILABLE  # type: ignore
                if TESSERACT_AVAILABLE:
                    logging.info("  → Tesseract OCR可用（不依赖PyTorch）")
            return
        except ImportError as ie:
            # 如果失败，尝试绝对导入
            try:
                from dxGame.ocr_enhanced import EnhancedOCR  # type: ignore
                ENHANCED_OCR_AVAILABLE = True
                logging.info("✓ 成功从dxGame目录导入增强版OCR模块")
                # 检查是否有可用的OCR引擎
                try:
                    from dxGame.ocr_enhanced import TESSERACT_AVAILABLE  # type: ignore
                    if TESSERACT_AVAILABLE:
                        logging.info("  → Tesseract OCR可用（不依赖PyTorch）")
                except:
                    pass
                return
            except ImportError:
                pass
    except Exception as e:
        error_msg = str(e)
        # 即使有错误，也尝试继续导入（模块可能已经部分加载）
        logging.debug(f"导入增强版OCR模块时遇到问题: {error_msg[:100]}...")
        # 不直接返回，继续尝试导入基础OCR
    
    # 如果增强版不可用，尝试从本地目录导入基础OCR
    try:
        # 先尝试相对导入（同目录）
        try:
            from ocr import OCR  # type: ignore
            OCR_AVAILABLE = True
            logging.info("成功从本地目录导入基础OCR模块")
            return
        except ImportError:
            # 如果失败，尝试绝对导入
            try:
                from dxGame.ocr import OCR  # type: ignore
                OCR_AVAILABLE = True
                logging.info("成功从dxGame目录导入基础OCR模块")
                return
            except ImportError:
                pass
    except Exception as e:
        error_msg = str(e)
        logging.debug(f"导入基础OCR模块时出错: {error_msg[:100]}...")
    
    # 如果两个模块都导入失败，记录警告
    if not ENHANCED_OCR_AVAILABLE and not OCR_AVAILABLE:
        logging.warning("⚠️ 所有OCR模块导入失败，OCR功能将不可用")
        logging.info("💡 提示: 即使PyTorch有问题，Tesseract OCR也应该可用")

from dxGame.dx_vnc import VNC
from dxGame.dx_core import *
from dxGame import MiniOpenCV
from dxGame import dxpyd

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class VNC_OCR:
    """
    VNC OCR识别类，兼容DX OCR接口
    使用方法：self.dx.Ocr = VNC_OCR("127.0.0.1", "5600", "")
    """
    
    def __init__(self, ip=None, port=None, password="", hwnd=None, vnc_instance=None):
        """
        初始化VNC OCR连接
        
        Args:
            ip: VNC服务器IP地址（如果提供了vnc_instance则不需要）
            port: VNC服务器端口（字符串或数字，如果提供了vnc_instance则不需要）
            password: VNC密码，默认空字符串（如果提供了vnc_instance则不需要）
            hwnd: 窗口句柄（VNC不需要，但为了兼容DX接口保留）
            vnc_instance: 已有的VNC实例，如果提供则复用，避免重复连接
        """
        # 如果提供了已有的VNC实例，直接复用
        if vnc_instance is not None:
            if not isinstance(vnc_instance, VNC):
                raise ValueError("vnc_instance必须是VNC类的实例")
            self.vnc_screenshot = vnc_instance
            self.ip = getattr(vnc_instance, 'ip', None)
            self.port = getattr(vnc_instance, 'port', None)
            self.password = getattr(vnc_instance, 'password', None)
            self.hwnd = hwnd
            self._is_reused_instance = True  # 标记为复用实例
            logging.info(f"VNC OCR复用已有截图连接: {self.ip}:{self.port}")
        else:
            # 如果没有提供实例，创建新的连接
            if ip is None or port is None:
                raise ValueError("如果未提供vnc_instance，则必须提供ip和port参数")
            
            # 处理端口号
            if isinstance(port, int):
                port = str(port)
            
            # 处理密码
            if password == "":
                password = None
            
            self.ip = ip
            self.port = port
            self.password = password
            self.hwnd = hwnd  # VNC不使用hwnd，但保留用于兼容
            
            # 创建VNC截图实例用于OCR
            try:
                self.vnc_screenshot = VNC(ip, port, password, hwnd)
                self._is_reused_instance = False  # 标记为新建实例
                logging.info(f"VNC OCR截图连接成功: {ip}:{port}")
            except Exception as e:
                logging.error(f"VNC OCR截图连接失败: {e}")
                raise
        
        # 延迟导入OCR模块（避免启动时失败）
        _import_ocr_modules()
        
        # 初始化OCR引擎
        self.ocr_engine = None
        
        # 只使用Tesseract OCR（最稳定，适合数字识别）
        if ENHANCED_OCR_AVAILABLE and EnhancedOCR is not None:
            try:
                self.ocr_engine = EnhancedOCR(
                    vnc_instance=self.vnc_screenshot,  # 直接使用VNC实例
                    languages=['eng'],  # 只使用英文（数字识别不需要中文）
                    gpu=False,
                    confidence_threshold=0.3,
                    preferred_engine='tesseract'  # 强制只使用Tesseract
                )
                # 检查Tesseract是否真正可用
                if hasattr(self.ocr_engine, 'tesseract_available') and self.ocr_engine.tesseract_available:
                    logging.info("✓ Tesseract OCR引擎初始化成功（已禁用PaddleOCR和EasyOCR）")
                else:
                    logging.error("⚠️ EnhancedOCR初始化成功，但Tesseract不可用")
                    logging.error("   请确保Tesseract已安装在: C:\\Program Files\\Tesseract-OCR\\")
                    logging.error("   并确保已安装pytesseract: pip install pytesseract")
                    self.ocr_engine = None
            except Exception as e:
                logging.error(f"⚠️ Tesseract OCR引擎初始化失败: {e}")
                import traceback
                logging.error(traceback.format_exc())
                self.ocr_engine = None
        
        # 不再使用基础OCR（EasyOCR），因为已强制使用Tesseract
        # 如果Tesseract不可用，程序会报错（这是预期的行为）
        
        if self.ocr_engine is None:
            logging.warning("⚠️ OCR引擎初始化失败，OCR功能将不可用")
            logging.info("💡 提示: 程序可继续运行，只是无法使用OCR识别功能")
            logging.info("💡 如需使用OCR功能，请确保:")
            logging.info("   1. Tesseract已安装在: C:\\Program Files\\Tesseract-OCR\\")
            logging.info("   2. 已安装pytesseract: pip install pytesseract")
    
    def __del__(self):
        """清理VNC资源"""
        try:
            self.stop()
        except:
            pass
    
    def stop(self):
        """
        断开VNC连接
        注意：如果VNC实例是复用的，不会关闭连接（由原实例管理）
        """
        try:
            # 如果是复用实例，不关闭连接（由原实例管理）
            if hasattr(self, '_is_reused_instance') and self._is_reused_instance:
                logging.debug("VNC OCR使用复用实例，不关闭连接")
                return
            
            # 如果是自己创建的实例，才关闭连接
            if hasattr(self, 'vnc_screenshot') and self.vnc_screenshot is not None:
                self.vnc_screenshot.stop()
        except Exception as e:
            logging.warning(f"清理VNC OCR资源失败: {e}")
    
    @staticmethod
    def _parse_color(color_str: str) -> Optional[Tuple[Tuple[int, int, int], Optional[Tuple[int, int, int]]]]:
        """
        解析颜色字符串，支持大漠工具的颜色-偏色格式
        
        Args:
            color_str: 颜色字符串，支持格式：
                - 'eee81d' (十六进制RGB，不带#)
                - '#eee81d' (十六进制RGB，带#)
                - 'eee81d-505050' (颜色-偏色格式，类似大漠工具)
                - 'rgb(238,232,29)' (RGB格式)
                - (238, 232, 29) (BGR元组，直接返回)
        
        Returns:
            如果只有颜色：(BGR颜色, None)
            如果有偏色：(BGR颜色, BGR偏色)
            如果解析失败返回None
        """
        if color_str is None:
            return None
        
        # 如果是元组，假设已经是BGR格式
        if isinstance(color_str, (tuple, list)):
            if len(color_str) == 3:
                return (tuple(int(c) for c in color_str), None)
            return None
        
        color_str = str(color_str).strip().lower()
        
        # 检查是否有偏色（格式：颜色-偏色）
        if '-' in color_str:
            parts = color_str.split('-', 1)
            if len(parts) == 2:
                main_color_str = parts[0].strip()
                offset_color_str = parts[1].strip()
                
                # 解析主颜色
                main_color = VNC_OCR._parse_single_color(main_color_str)
                if main_color is None:
                    return None
                
                # 解析偏色
                offset_color = VNC_OCR._parse_single_color(offset_color_str)
                if offset_color is None:
                    return None
                
                return (main_color, offset_color)
        
        # 移除#号
        if color_str.startswith('#'):
            color_str = color_str[1:]
        
        # 解析单个颜色
        single_color = VNC_OCR._parse_single_color(color_str)
        if single_color is not None:
            return (single_color, None)
        
        return None
    
    @staticmethod
    def _parse_single_color(color_str: str) -> Optional[Tuple[int, int, int]]:
        """
        解析单个颜色字符串，转换为BGR格式
        
        Args:
            color_str: 颜色字符串
        
        Returns:
            BGR格式的颜色元组 (B, G, R)，如果解析失败返回None
        """
        if color_str is None:
            return None
        
        color_str = str(color_str).strip().lower()
        
        # 移除#号
        if color_str.startswith('#'):
            color_str = color_str[1:]
        
        # 尝试解析十六进制格式 (如 'eee81d')
        if len(color_str) == 6 and all(c in '0123456789abcdef' for c in color_str):
            try:
                r = int(color_str[0:2], 16)
                g = int(color_str[2:4], 16)
                b = int(color_str[4:6], 16)
                # 转换为BGR格式
                return (b, g, r)
            except ValueError:
                return None
        
        # 尝试解析RGB格式 (如 'rgb(238,232,29)')
        if color_str.startswith('rgb(') and color_str.endswith(')'):
            try:
                values = color_str[4:-1].split(',')
                if len(values) == 3:
                    r = int(values[0].strip())
                    g = int(values[1].strip())
                    b = int(values[2].strip())
                    # 转换为BGR格式
                    return (b, g, r)
            except (ValueError, IndexError):
                return None
        
        return None
    
    def _filter_by_color(self, image: np.ndarray, results: List[Tuple[str, Tuple[int, int], float]], 
                        target_color: Tuple[int, int, int], offset_color: Optional[Tuple[int, int, int]] = None,
                        color_tolerance: int = 30) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        根据颜色过滤OCR识别结果（支持大漠工具的颜色-偏色格式）
        
        Args:
            image: 原始图像（BGR格式）
            results: OCR识别结果列表
            target_color: 目标颜色 (B, G, R)
            offset_color: 偏色 (B, G, R)，如果提供则使用颜色范围匹配（类似大漠工具）
            color_tolerance: 颜色容差，默认30（仅在无偏色时使用）
        
        Returns:
            过滤后的识别结果列表
        """
        if target_color is None or image is None or len(results) == 0:
            return results
        
        # 如果有偏色，计算颜色范围（类似大漠工具的RGB范围匹配）
        if offset_color is not None:
            # 计算颜色范围：主颜色 ± 偏色
            color_min = tuple(max(0, target_color[i] - offset_color[i]) for i in range(3))
            color_max = tuple(min(255, target_color[i] + offset_color[i]) for i in range(3))
        else:
            # 没有偏色，使用容差计算范围
            color_min = tuple(max(0, target_color[i] - color_tolerance) for i in range(3))
            color_max = tuple(min(255, target_color[i] + color_tolerance) for i in range(3))
        
        # 确保image是numpy数组格式
        try:
            if not isinstance(image, np.ndarray):
                # 尝试转换为numpy数组
                if hasattr(image, 'get_memoryview'):
                    mv = image.get_memoryview()
                    image = np.array(mv, copy=False)
                else:
                    image = np.asarray(image)
            
            # 检查图像格式
            if image.size == 0 or len(image.shape) < 2:
                logging.warning("图像格式无效，跳过颜色过滤")
                return results
            
            # 确保是BGR格式（3通道）
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            elif len(image.shape) == 3 and image.shape[2] != 3:
                logging.warning(f"图像通道数异常: {image.shape}，跳过颜色过滤")
                return results
        except Exception as e:
            logging.warning(f"图像格式转换失败: {e}，跳过颜色过滤")
            return results
        
        filtered_results = []
        h, w = image.shape[:2]
        
        for text, (cx, cy), confidence in results:
            # 将绝对坐标转换为相对坐标（相对于图像）
            rel_x = int(cx)
            rel_y = int(cy)
            
            # 确保坐标在图像范围内
            if rel_x < 0 or rel_x >= w or rel_y < 0 or rel_y >= h:
                continue
            
            # 估算文本区域（根据文本长度）
            # 假设每个字符大约 10-15 像素宽，高度约 20 像素
            text_len = len(text)
            estimated_width = text_len * 12  # 估算文本宽度
            estimated_height = 25  # 估算文本高度
            
            # 计算文本区域的边界框（以文本中心为基准）
            half_width = max(10, estimated_width // 2)
            half_height = max(7, estimated_height // 2)
            
            x1_box = max(0, rel_x - half_width)
            y1_box = max(0, rel_y - half_height)
            x2_box = min(w, rel_x + half_width)
            y2_box = min(h, rel_y + half_height)
            
            # 提取文本区域的像素
            text_region = image[y1_box:y2_box, x1_box:x2_box]
            
            if text_region.size == 0:
                continue
            
            # 计算文本区域的平均颜色
            # 使用中位数而不是平均值，更抗干扰
            avg_b = np.median(text_region[:, :, 0])
            avg_g = np.median(text_region[:, :, 1])
            avg_r = np.median(text_region[:, :, 2])
            
            avg_color = (int(avg_b), int(avg_g), int(avg_r))
            
            # 将BGR转换为RGB用于显示（十六进制格式）
            rgb_color = (avg_color[2], avg_color[1], avg_color[0])  # BGR转RGB
            hex_color = f"{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"
            
            # 颜色范围匹配（类似大漠工具）
            # 检查每个通道是否在范围内
            color_match = True
            for i in range(3):
                if not (color_min[i] <= avg_color[i] <= color_max[i]):
                    color_match = False
                    break
            
            # 计算颜色差异（用于调试显示）
            color_diff = np.sqrt(
                (avg_color[0] - target_color[0]) ** 2 +
                (avg_color[1] - target_color[1]) ** 2 +
                (avg_color[2] - target_color[2]) ** 2
            )
            
            # 记录颜色信息（用于调试）
            if offset_color is not None:
                offset_rgb = (offset_color[2], offset_color[1], offset_color[0])
                logging.info(f"文本 '{text}': 平均颜色RGB={rgb_color}, 十六进制=#{hex_color}, "
                           f"目标颜色=#{target_color[2]:02x}{target_color[1]:02x}{target_color[0]:02x}, "
                           f"偏色={offset_rgb}, 颜色范围=[{color_min} ~ {color_max}], 匹配={color_match}")
            else:
                logging.info(f"文本 '{text}': 平均颜色RGB={rgb_color}, 十六进制=#{hex_color}, "
                           f"目标颜色=#{target_color[2]:02x}{target_color[1]:02x}{target_color[0]:02x}, "
                           f"颜色差异={color_diff:.2f}, 容差={color_tolerance}, 匹配={color_match}")
            
            # 如果颜色在范围内，保留该结果
            if color_match:
                filtered_results.append((text, (cx, cy), confidence))
                logging.debug(f"✓ 颜色匹配: 文本='{text}', 平均颜色={avg_color}, 颜色范围=[{color_min} ~ {color_max}]")
            else:
                logging.debug(f"✗ 颜色不匹配: 文本='{text}', 平均颜色RGB={rgb_color} (#{hex_color}), 不在范围[{color_min} ~ {color_max}]内")
        
        return filtered_results
    
    def _get_region_image(self, x1: int, y1: int, x2: int, y2: int) -> Optional[np.ndarray]:
        """
        获取区域截图并转换为numpy数组
        
        Args:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
        
        Returns:
            区域图像（BGR格式），如果失败返回None
        """
        try:
            region_image = self.vnc_screenshot.Capture(x1, y1, x2, y2)
            # 转换为numpy数组
            if not isinstance(region_image, np.ndarray):
                if hasattr(region_image, 'get_memoryview'):
                    mv = region_image.get_memoryview()
                    region_image = np.array(mv, copy=False)
                else:
                    region_image = np.asarray(region_image)
            
            # 确保是BGR格式（OpenCV格式）
            if region_image.size > 0:
                if len(region_image.shape) == 2:
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_GRAY2BGR)
                elif len(region_image.shape) == 3 and region_image.shape[2] == 4:
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_RGBA2BGR)
                return region_image
            else:
                logging.error(f"区域截图为空: ({x1}, {y1}, {x2}, {y2})")
                return None
        except Exception as e:
            logging.error(f"获取截图失败: {e}")
            return None
    
    def _perform_ocr(self, region_image: np.ndarray, x1: int, y1: int, x2: int, y2: int, numbers_only: bool = False) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        执行OCR识别
        
        Args:
            region_image: 区域图像（BGR格式）
            x1: 左上角x坐标（用于坐标转换）
            y1: 左上角y坐标（用于坐标转换）
            x2: 右下角x坐标
            y2: 右下角y坐标
            numbers_only: 是否只识别数字
        
        Returns:
            OCR识别结果列表，坐标是绝对坐标
        """
        # 如果只识别数字，优先使用ocr_numbers方法
        if numbers_only and hasattr(self.ocr_engine, 'ocr_numbers'):
            results = self.ocr_engine.ocr_numbers(region_image)
            # results中的坐标是相对于region_image的相对坐标，转换为绝对坐标
            adjusted_results = []
            for text, (cx, cy), confidence in results:
                absolute_x = x1 + cx
                absolute_y = y1 + cy
                adjusted_results.append((text, (absolute_x, absolute_y), confidence))
            return adjusted_results
        
        # 优先使用ocr_image方法
        if hasattr(self.ocr_engine, 'ocr_image'):
            results = self.ocr_engine.ocr_image(region_image)
            # results中的坐标是相对于region_image的相对坐标，转换为绝对坐标
            adjusted_results = []
            for text, (cx, cy), confidence in results:
                absolute_x = x1 + cx
                absolute_y = y1 + cy
                adjusted_results.append((text, (absolute_x, absolute_y), confidence))
            return adjusted_results
        
        # 如果OCR引擎不支持ocr_image，使用ocr_region
        elif hasattr(self.ocr_engine, 'ocr_region'):
            # ocr_region方法会自动使用vnc_instance进行截图和识别，返回绝对坐标
            results = self.ocr_engine.ocr_region(None, x1, y1, x2, y2)
            return results
        
        else:
            logging.error("OCR引擎不支持ocr_image或ocr_region方法")
            return []
    
    def Ocr(self, x1: int, y1: int, x2: int, y2: int, target_color: Optional[str] = None, 
            color_tolerance: int = 30, confidence_threshold: float = 0.0, 
            show_result: bool = True) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        OCR识别指定区域，支持颜色过滤和置信度过滤
        
        Args:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
            target_color: 目标颜色（可选），用于过滤识别结果
                支持格式：
                - 'eee81d' (十六进制RGB，不带#)
                - '#eee81d' (十六进制RGB，带#)
                - 'eee81d-505050' (颜色-偏色格式，类似大漠工具)
                - 'rgb(238,232,29)' (RGB格式)
            color_tolerance: 颜色容差，默认30（0-255范围，仅在无偏色时使用）
            confidence_threshold: 置信度阈值，默认0.8（0-1范围），只返回置信度>=此值的结果
            show_result: 是否显示识别结果图像（默认True）
        
        Returns:
            识别结果列表，每个元素为(文本, 中心坐标(x, y), 置信度)
            如果识别失败或未找到文本，返回空列表
        """
        if self.ocr_engine is None:
            logging.error("OCR引擎未初始化")
            return []
        
        # 验证置信度阈值
        if confidence_threshold < 0 or confidence_threshold > 1:
            logging.warning(f"置信度阈值 {confidence_threshold} 超出范围 [0, 1]，使用默认值 0.8")
            confidence_threshold = 0.8
        
        # 解析目标颜色
        parsed_color_info = None
        parsed_color = None
        offset_color = None
        
        if target_color:
            parsed_color_info = self._parse_color(target_color)
            if parsed_color_info is None:
                logging.warning(f"无法解析颜色参数: {target_color}，将进行普通OCR识别")
            else:
                parsed_color, offset_color = parsed_color_info
                if offset_color is not None:
                    logging.info(f"启用颜色过滤（颜色-偏色）: 目标颜色={target_color}, "
                               f"主颜色BGR={parsed_color}, 偏色BGR={offset_color}, "
                               f"置信度阈值={confidence_threshold}")
                else:
                    logging.info(f"启用颜色过滤: 目标颜色={target_color}, "
                               f"BGR={parsed_color}, 容差={color_tolerance}, "
                               f"置信度阈值={confidence_threshold}")
        
        try:
            # 获取区域截图（用于OCR识别和颜色过滤）
            region_image = self._get_region_image(x1, y1, x2, y2)
            if region_image is None:
                return []
            
            # 执行OCR识别
            results = self._perform_ocr(region_image, x1, y1, x2, y2, numbers_only=False)
            if not results:
                # logging.warning(f"OCR识别未返回任何结果，区域: ({x1}, {y1}, {x2}, {y2})")
                return []
            
            logging.info(f"OCR识别到{len(results)}个结果（未过滤前）")
            
            # 进行置信度过滤（如果设置了阈值）
            if confidence_threshold > 0:
                original_count = len(results)
                results = [(text, pos, conf) for text, pos, conf in results if conf >= confidence_threshold]
                if original_count != len(results):
                    logging.info(f"置信度过滤: 原始结果{original_count}个，过滤后{len(results)}个（阈值={confidence_threshold}）")
            else:
                # 如果没有设置置信度阈值，记录所有结果
                logging.debug(f"未设置置信度阈值，返回所有{len(results)}个识别结果")
            
            # 如果提供了颜色参数，进行颜色过滤
            if parsed_color is not None and results:
                original_count = len(results)
                # 将绝对坐标转换为相对坐标（相对于region_image）
                relative_results = []
                for text, (cx, cy), confidence in results:
                    rel_cx = cx - x1
                    rel_cy = cy - y1
                    relative_results.append((text, (rel_cx, rel_cy), confidence))
                
                # 使用相对坐标进行颜色过滤
                filtered_relative = self._filter_by_color(
                    region_image, relative_results, parsed_color, offset_color, color_tolerance
                )
                
                # 将过滤后的相对坐标转换回绝对坐标
                results = []
                for text, (rel_cx, rel_cy), confidence in filtered_relative:
                    abs_cx = rel_cx + x1
                    abs_cy = rel_cy + y1
                    results.append((text, (abs_cx, abs_cy), confidence))
                
                filtered_count = len(results)
                logging.info(f"颜色过滤: 原始结果{original_count}个，过滤后{filtered_count}个")
            
            # 显示识别结果（如果启用了显示）
            if show_result and results:
                self._show_ocr_results(region_image, results, x1, y1)
            
            return results
            
        except Exception as e:
            logging.error(f"OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def OcrNumbers(self, x1: int, y1: int, x2: int, y2: int, confidence_threshold: float = 0.75, min_confidence: float = 0.7) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        专门用于数字识别的方法，使用数字优化的OCR配置（高精度模式）
        
        Args:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
            confidence_threshold: 主置信度阈值（0-1），默认0.75（高精度）
            min_confidence: 最小置信度阈值（0-1），默认0.7（低于此值直接拒绝）
        
        Returns:
            识别结果列表，只包含数字字符，每个元素为(文本, 中心坐标(x, y), 置信度)
        """
        if self.ocr_engine is None:
            logging.error("OCR引擎未初始化")
            return []
        
        try:
            # 获取区域截图
            region_image = self._get_region_image(x1, y1, x2, y2)
            if region_image is None:
                return []
            
            # 检查图像是否有足够的内容（避免识别空白区域）
            import cv2
            import numpy as np
            gray_check = cv2.cvtColor(region_image, cv2.COLOR_BGR2GRAY) if len(region_image.shape) == 3 else region_image
            # 计算图像的标准差（如果太均匀，可能是空白）
            std_dev = np.std(gray_check.astype(np.float32))
            if std_dev < 10:  # 标准差太小，可能是空白或纯色区域
                logging.debug(f"图像区域可能为空或纯色（标准差={std_dev:.2f}），跳过OCR识别")
                return []
            
            # 执行数字OCR识别
            results = self._perform_ocr(region_image, x1, y1, x2, y2, numbers_only=True)
            if not results:
                logging.debug(f"数字OCR识别未返回任何结果，区域: ({x1}, {y1}, {x2}, {y2})")
                return []
            
            logging.info(f"数字OCR识别到{len(results)}个结果（未过滤前）")
            
            # 第一轮：严格置信度过滤（移除低置信度结果）
            if min_confidence > 0:
                original_count = len(results)
                results = [(text, pos, conf) for text, pos, conf in results if conf >= min_confidence]
                if original_count != len(results):
                    logging.debug(f"最小置信度过滤: 原始结果{original_count}个，过滤后{len(results)}个（阈值={min_confidence}）")
                    # 如果过滤后没有结果，直接返回
                    if not results:
                        logging.debug("所有结果都被最小置信度阈值过滤，返回空列表")
                        return []
            
            # 最终过滤：确保结果只包含数字
            final_results = []
            for text, pos, conf in results:
                # 移除非数字字符
                cleaned_text = ''.join(c for c in text if c.isdigit())
                if cleaned_text:
                    # 再次检查置信度（主阈值）
                    if conf >= confidence_threshold:
                        final_results.append((cleaned_text, pos, conf))
                    else:
                        logging.debug(f"结果 '{cleaned_text}' 置信度 {conf:.2f} 低于主阈值 {confidence_threshold}，已过滤")
            
            if len(final_results) != len(results):
                logging.debug(f"数字过滤: {len(results)}个结果，过滤后{len(final_results)}个纯数字结果（主阈值={confidence_threshold}）")
            
            # 如果有多人结果，按置信度排序，只返回置信度最高的
            if len(final_results) > 1:
                final_results.sort(key=lambda x: x[2], reverse=True)  # 按置信度降序排序
                logging.debug(f"多个识别结果，保留置信度最高的: {final_results[0][0]} (置信度={final_results[0][2]:.2f})")
                # 只返回置信度最高的结果
                return [final_results[0]]
            
            return final_results
            
        except Exception as e:
            logging.error(f"数字OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _show_ocr_results(self, image: np.ndarray, results: List[Tuple[str, Tuple[int, int], float]], 
                         offset_x: int = 0, offset_y: int = 0):
        """
        在图像上绘制OCR识别结果（红框标注）
        
        Args:
            image: 原始图像
            results: OCR识别结果列表
            offset_x: X坐标偏移量（用于显示绝对坐标）
            offset_y: Y坐标偏移量（用于显示绝对坐标）
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
                # 将绝对坐标转换为相对坐标（相对于图像）
                rel_x = cx - offset_x
                rel_y = cy - offset_y
                
                # 估算文本边界框（根据文本长度）
                # 假设每个字符大约 10-15 像素宽，高度约 20 像素
                text_len = len(text)
                box_width = max(30, min(text_len * 12, w - rel_x))
                box_height = max(15, min(25, h - rel_y))
                
                # 计算边界框坐标
                x1_box = max(0, rel_x - box_width // 2)
                y1_box = max(0, rel_y - box_height // 2)
                x2_box = min(w, rel_x + box_width // 2)
                y2_box = min(h, rel_y + box_height // 2)
                
                # 绘制红色矩形框
                cv2.rectangle(display_image, (x1_box, y1_box), (x2_box, y2_box), (0, 0, 255), 2)
                
                # 绘制中心点
                cv2.circle(display_image, (rel_x, rel_y), 3, (0, 255, 0), -1)
                
                # 绘制文本标签（在框的上方）
                label = f"{i+1}:{text[:10]} ({confidence:.2f})"
                label_y = max(15, y1_box - 5)
                
                # 绘制文本背景（白色半透明）
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
                
                # 绘制文本
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
            
            # 显示图像
            try:
                # 将numpy数组转换为ManagedMemoryView（MiniOpenCV.imshow需要此类型）
                h, w = display_image.shape[:2]
                image_bytes = display_image.tobytes()
                display_image_mv = dxpyd.ManagedMemoryView(shape=(h, w, 3), dtype=0, bytes_data=image_bytes)
                # MiniOpenCV.imshow("OCR识别结果", display_image_mv)
                logging.info(f"已显示OCR识别结果，共识别到 {len(results)} 个文本")
            except Exception as e:
                logging.warning(f"显示OCR结果失败: {e}")
                # 如果显示失败，保存到文件
                try:
                    debug_dir = os.path.join(_parent_dir, "Temporary", "ocr_debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, f"ocr_result_{int(time.time())}.png")
                    cv2.imwrite(debug_path, display_image)
                    logging.info(f"OCR结果已保存到: {debug_path}")
                except Exception as save_error:
                    logging.error(f"保存OCR结果失败: {save_error}")
                    
        except Exception as e:
            logging.error(f"绘制OCR结果失败: {e}")
            import traceback
            traceback.print_exc()
    
    def OcrText(self, x1: int, y1: int, x2: int, y2: int, target_text: Optional[str] = None) -> List[str]:
        """
        OCR识别指定区域，返回文本列表（简化接口）
        
        Args:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
            target_text: 目标文本（可选），如果提供则只返回包含此文本的结果
        
        Returns:
            文本列表
        """
        results = self.Ocr(x1, y1, x2, y2)
        
        if target_text is None:
            return [text for text, _, _ in results]
        
        # 过滤包含目标文本的结果
        target_text_lower = target_text.lower()
        filtered_texts = []
        for text, _, _ in results:
            if target_text_lower in text.lower():
                filtered_texts.append(text)
        
        return filtered_texts
    
    def FindText(self, x1: int, y1: int, x2: int, y2: int, target_text: str) -> List[Tuple[str, Tuple[int, int], float]]:
        """
        在指定区域查找文本
        
        Args:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
            target_text: 目标文本
        
        Returns:
            识别结果列表，只返回包含目标文本的结果
        """
        results = self.Ocr(x1, y1, x2, y2)
        
        # 过滤包含目标文本的结果
        filtered_results = []
        target_text_lower = target_text.lower()
        for text, pos, confidence in results:
            if target_text_lower in text.lower():
                filtered_results.append((text, pos, confidence))
        
        return filtered_results
