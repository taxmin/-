# -*- coding: utf-8 -*-
"""
稳定版数字OCR识别 - 多重保障机制
结合图像预处理、多次识别、投票机制，确保每次都能稳定识别
"""
import sys
import os
import time
import cv2
import numpy as np
from typing import List, Tuple, Optional

# 添加项目路径
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

sys.path.insert(0, os.path.join(_current_dir, 'dxGame'))

from dxGame.dx_vnc import VNC
from dxGame.dx_ocr import VNC_OCR


class StableNumberOCR:
    """
    稳定版数字OCR识别器
    
    核心策略：
    1. 多次截图识别（默认3次）
    2. 多种预处理方法尝试
    3. 投票机制选择最可能的结果
    4. 智能重试和降级
    """
    
    def __init__(self, vnc_instance):
        """
        初始化稳定版OCR
        
        Args:
            vnc_instance: VNC实例
        """
        self.vnc = vnc_instance
        self.vnc_ocr = VNC_OCR(vnc_instance=vnc_instance)
        
        if self.vnc_ocr.ocr_engine is None:
            raise RuntimeError("VNC_OCR 引擎初始化失败")
        
        print("✓ 稳定版数字OCR初始化成功")
    
    def recognize_number(self, x1: int, y1: int, x2: int, y2: int, 
                        max_retries: int = 5,
                        confidence_min: float = 0.2) -> Optional[int]:
        """
        稳定识别数字（带重试和投票机制）
        
        Args:
            x1, y1, x2, y2: 识别区域
            max_retries: 最大重试次数
            confidence_min: 最小置信度阈值
            
        Returns:
            识别到的数字，失败返回 None
        """
        print(f"\n开始识别区域 ({x1}, {y1}, {x2}, {y2})...")
        
        # 收集所有识别结果
        all_results = []
        
        for attempt in range(max_retries):
            print(f"\n[第 {attempt + 1}/{max_retries} 次尝试]")
            
            # 方法1: OcrNumbers (专用数字识别)
            result1 = self._try_ocr_numbers(x1, y1, x2, y2, confidence_min)
            if result1:
                all_results.append(result1)
                print(f"  ✓ OcrNumbers 成功: {result1}")
            
            # 方法2: Ocr + 正则提取
            result2 = self._try_ocr_with_regex(x1, y1, x2, y2, confidence_min)
            if result2:
                all_results.append(result2)
                print(f"  ✓ Ocr+正则 成功: {result2}")
            
            # 如果已经有足够多的结果，提前结束
            if len(all_results) >= 3:
                print(f"  → 已收集 {len(all_results)} 个结果，停止重试")
                break
            
            # 短暂等待后重试
            if attempt < max_retries - 1:
                time.sleep(0.2)
        
        # 投票选择最终结果
        if not all_results:
            print(f"\n❌ 所有尝试均失败")
            return None
        
        final_result = self._vote_result(all_results)
        print(f"\n✅ 最终识别结果: {final_result} (从 {len(all_results)} 个结果中投票)")
        
        return final_result
    
    def _try_ocr_numbers(self, x1: int, y1: int, x2: int, y2: int, 
                         confidence_min: float) -> Optional[int]:
        """尝试使用 OcrNumbers 方法"""
        try:
            # 降低阈值以提高识别率
            results = self.vnc_ocr.OcrNumbers(
                x1, y1, x2, y2,
                confidence_threshold=confidence_min,
                min_confidence=confidence_min * 0.7
            )
            
            if results:
                text, pos, conf = results[0]
                try:
                    number = int(text)
                    return number
                except ValueError:
                    pass
        except Exception as e:
            print(f"  ⚠️ OcrNumbers 异常: {e}")
        
        return None
    
    def _try_ocr_with_regex(self, x1: int, y1: int, x2: int, y2: int,
                            confidence_min: float) -> Optional[int]:
        """尝试使用 Ocr + 正则提取"""
        try:
            import re
            
            results = self.vnc_ocr.Ocr(x1, y1, x2, y2, show_result=False)
            
            if results:
                for text, pos, conf in results:
                    if conf < confidence_min:
                        continue
                    
                    # 提取所有数字
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        # 取最长的数字串（更可能是目标）
                        best_number = max(numbers, key=len)
                        try:
                            return int(best_number)
                        except ValueError:
                            pass
        except Exception as e:
            print(f"  ⚠️ Ocr+正则 异常: {e}")
        
        return None
    
    def _vote_result(self, results: List[int]) -> int:
        """
        投票机制：选择出现次数最多的结果
        
        Args:
            results: 所有识别结果列表
            
        Returns:
            投票后的最终结果
        """
        from collections import Counter
        
        # 统计每个结果出现的次数
        counter = Counter(results)
        
        # 获取出现次数最多的结果
        most_common = counter.most_common(1)[0]
        number, count = most_common
        
        print(f"  投票结果: {number} (出现 {count}/{len(results)} 次)")
        
        # 如果有多数票（超过一半），直接返回
        if count > len(results) / 2:
            return number
        
        # 否则返回出现次数最多的
        return number
    
    def recognize_with_image_enhancement(self, x1: int, y1: int, x2: int, y2: int,
                                         max_retries: int = 5) -> Optional[int]:
        """
        带图像增强的识别（适合低质量图像）
        
        Args:
            x1, y1, x2, y2: 识别区域
            max_retries: 最大重试次数
            
        Returns:
            识别到的数字，失败返回 None
        """
        print(f"\n开始增强识别区域 ({x1}, {y1}, {x2}, {y2})...")
        
        # 获取原始图像
        original_image = self.vnc.Capture(x1, y1, x2, y2)
        
        if original_image is None:
            print("❌ 截图失败")
            return None
        
        # 转换为numpy数组
        if not isinstance(original_image, np.ndarray):
            if hasattr(original_image, 'get_memoryview'):
                mv = original_image.get_memoryview()
                original_image = np.array(mv, copy=False)
            else:
                original_image = np.asarray(original_image, dtype=np.uint8)
        
        # 尝试多种图像增强方法
        enhanced_images = self._enhance_image(original_image)
        
        all_results = []
        
        for i, enhanced_img in enumerate(enhanced_images):
            print(f"\n[增强方法 {i+1}/{len(enhanced_images)}]")
            
            # 临时保存增强后的图像
            temp_path = os.path.join(_parent_dir, "Temporary", f"enhanced_{i}.png")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            cv2.imwrite(temp_path, enhanced_img)
            
            # 读取并识别
            test_img = cv2.imread(temp_path)
            if test_img is not None:
                # 使用Tesseract直接识别增强后的图像
                result = self._recognize_from_image(test_img)
                if result is not None:
                    all_results.append(result)
                    print(f"  ✓ 识别成功: {result}")
            
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            if len(all_results) >= 3:
                break
        
        if not all_results:
            print(f"\n❌ 所有增强方法均失败")
            return None
        
        final_result = self._vote_result(all_results)
        print(f"\n✅ 最终识别结果: {final_result}")
        
        return final_result
    
    def _enhance_image(self, image: np.ndarray) -> List[np.ndarray]:
        """
        生成多种增强版本的图像
        
        Returns:
            增强后的图像列表
        """
        enhanced_list = []
        
        # 确保是BGR格式
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        h, w = image.shape[:2]
        
        # 方法1: 放大2倍 + CLAHE增强
        try:
            img1 = cv2.resize(image, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced1 = clahe.apply(gray1)
            enhanced_list.append(cv2.cvtColor(enhanced1, cv2.COLOR_GRAY2BGR))
        except Exception as e:
            print(f"  ⚠️ 增强方法1失败: {e}")
        
        # 方法2: 放大3倍 + 自适应二值化
        try:
            img2 = cv2.resize(image, (w*3, h*3), interpolation=cv2.INTER_CUBIC)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            binary2 = cv2.adaptiveThreshold(
                gray2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            enhanced_list.append(cv2.cvtColor(binary2, cv2.COLOR_GRAY2BGR))
        except Exception as e:
            print(f"  ⚠️ 增强方法2失败: {e}")
        
        # 方法3: 原始图像 + 锐化
        try:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            enhanced3 = cv2.filter2D(image, -1, kernel)
            enhanced_list.append(enhanced3)
        except Exception as e:
            print(f"  ⚠️ 增强方法3失败: {e}")
        
        # 方法4: 灰度 + OTSU二值化
        try:
            gray4 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary4 = cv2.threshold(gray4, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced_list.append(cv2.cvtColor(binary4, cv2.COLOR_GRAY2BGR))
        except Exception as e:
            print(f"  ⚠️ 增强方法4失败: {e}")
        
        return enhanced_list
    
    def _recognize_from_image(self, image: np.ndarray) -> Optional[int]:
        """直接从图像识别数字（使用Tesseract）"""
        try:
            import pytesseract
            from PIL import Image
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Tesseract数字识别配置
            config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
            
            # 识别
            text = pytesseract.image_to_string(gray, config=config).strip()
            
            # 提取数字
            import re
            numbers = re.findall(r'\d+', text)
            
            if numbers:
                return int(numbers[0])
            
        except Exception as e:
            print(f"  ⚠️ 图像识别失败: {e}")
        
        return None


def test_stable_ocr():
    """测试稳定版OCR"""
    print("=" * 80)
    print("测试稳定版数字OCR识别")
    print("=" * 80)
    
    # 配置
    IP = "127.0.0.1"
    PORT = "5600"
    PASSWORD = ""
    X1, Y1, X2, Y2 = 822, 75, 862, 96
    
    try:
        # 连接VNC
        print(f"\n正在连接 VNC: {IP}:{PORT}...")
        vnc = VNC(IP, PORT, PASSWORD, fps=5)
        print(f"✓ VNC 连接成功，分辨率: {vnc.width}x{vnc.height}")
        
        # 创建稳定版OCR
        stable_ocr = StableNumberOCR(vnc)
        
        # 测试1: 普通识别
        print("\n" + "=" * 80)
        print("测试1: 普通稳定识别")
        print("=" * 80)
        result1 = stable_ocr.recognize_number(X1, Y1, X2, Y2, max_retries=5)
        
        if result1 is not None:
            print(f"\n✅ 识别成功: {result1}")
        else:
            print(f"\n❌ 识别失败")
        
        # 测试2: 增强识别
        print("\n" + "=" * 80)
        print("测试2: 增强版识别（适合低质量图像）")
        print("=" * 80)
        result2 = stable_ocr.recognize_with_image_enhancement(X1, Y1, X2, Y2, max_retries=5)
        
        if result2 is not None:
            print(f"\n✅ 识别成功: {result2}")
        else:
            print(f"\n❌ 识别失败")
        
        # 总结
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        print(f"普通识别结果: {result1}")
        print(f"增强识别结果: {result2}")
        
        if result1 is not None or result2 is not None:
            print("\n✅ 至少有一种方法识别成功！")
        else:
            print("\n❌ 所有方法均失败，建议:")
            print("   1. 检查识别区域是否正确")
            print("   2. 查看游戏内字体是否清晰")
            print("   3. 尝试扩大识别区域")
        
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            if 'vnc' in locals():
                vnc.stop()
            print("\n✓ 资源已释放")
        except:
            pass


if __name__ == '__main__':
    test_stable_ocr()
