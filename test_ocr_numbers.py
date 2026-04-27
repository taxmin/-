# -*- coding: utf-8 -*-
"""
测试 VNC_OCR.OcrNumbers() 数字识别效果
对比 Ocr() 和 OcrNumbers() 在角色等级区域的识别效果
"""
import sys
import os
import time

# 添加项目路径
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# 直接导入需要的模块，避免通过 __init__.py 导入所有模块
import sys
sys.path.insert(0, os.path.join(_current_dir, 'dxGame'))

from dx_vnc import VNC
from dx_ocr import VNC_OCR
try:
    from dx_OnnxOCR import ONNX_OCR
    ONNX_AVAILABLE = True
except Exception as e:
    print(f"⚠️ ONNX_OCR 导入失败: {e}")
    ONNX_AVAILABLE = False
    ONNX_OCR = None


def test_ocr_numbers():
    """测试 OcrNumbers() 方法"""
    print("=" * 80)
    print("测试 VNC_OCR.OcrNumbers() 数字识别")
    print("=" * 80)
    
    # 配置参数
    IP = "127.0.0.1"
    PORT = "5600"
    PASSWORD = ""
    
    # 测试区域（角色等级）
    X1, Y1, X2, Y2 = 822, 75, 862, 96
    
    try:
        # 创建 VNC 连接
        print(f"\n正在连接 VNC: {IP}:{PORT}...")
        vnc = VNC(IP, PORT, PASSWORD, fps=5)
        print(f"✓ VNC 连接成功，分辨率: {vnc.width}x{vnc.height}")
        
        # 创建 VNC_OCR 实例（使用 Tesseract，适合数字识别）
        print("\n初始化 VNC_OCR (Tesseract)...")
        vnc_ocr = VNC_OCR(vnc_instance=vnc)
        
        if vnc_ocr.ocr_engine is None:
            print("❌ VNC_OCR 引擎初始化失败")
            print("   请确保 Tesseract 已安装并正确配置")
            vnc.stop()
            return
        
        print("✓ VNC_OCR 初始化成功")
        
        # 创建 ONNX_OCR 实例（用于对比）
        if ONNX_AVAILABLE and ONNX_OCR is not None:
            print("\n初始化 ONNX_OCR (PaddleOCR)...")
            onnx_ocr = ONNX_OCR(vnc_instance=vnc, use_gpu=False, drop_score=0.5)
            
            if onnx_ocr.ocr_engine is None:
                print("⚠️ ONNX_OCR 引擎初始化失败，将只测试 VNC_OCR")
                onnx_ocr = None
            else:
                print("✓ ONNX_OCR 初始化成功")
        else:
            print("\n⚠️ ONNX_OCR 不可用，将只测试 VNC_OCR")
            onnx_ocr = None
        
        print("\n" + "=" * 80)
        print(f"开始测试区域: ({X1}, {Y1}, {X2}, {Y2})")
        print("=" * 80)
        
        # 测试次数
        test_count = 5
        
        for i in range(test_count):
            print(f"\n{'='*80}")
            print(f"第 {i+1}/{test_count} 次测试")
            print(f"{'='*80}")
            
            # 方法1: 使用 VNC_OCR.OcrNumbers() - 专门针对数字优化
            print("\n[方法1] VNC_OCR.OcrNumbers() - Tesseract 数字专用")
            start_time = time.time()
            results_numbers = vnc_ocr.OcrNumbers(X1, Y1, X2, Y2, 
                                                  confidence_threshold=0.75, 
                                                  min_confidence=0.7)
            elapsed_numbers = time.time() - start_time
            
            if results_numbers:
                print(f"  ✓ 识别耗时: {elapsed_numbers:.3f}秒")
                for j, (text, pos, confidence) in enumerate(results_numbers):
                    print(f"    结果{j+1}: '{text}' | 位置: {pos} | 置信度: {confidence:.3f}")
                    try:
                        level = int(text)
                        print(f"    → 解析为数字: {level}")
                    except ValueError:
                        print(f"    → ⚠️ 无法转换为数字")
            else:
                print(f"  ❌ 未识别到任何内容 (耗时: {elapsed_numbers:.3f}秒)")
            
            # 方法2: 使用 VNC_OCR.Ocr() - 通用OCR
            print("\n[方法2] VNC_OCR.Ocr() - Tesseract 通用识别")
            start_time = time.time()
            results_ocr = vnc_ocr.Ocr(X1, Y1, X2, Y2, show_result=False)
            elapsed_ocr = time.time() - start_time
            
            if results_ocr:
                print(f"  ✓ 识别耗时: {elapsed_ocr:.3f}秒")
                for j, (text, pos, confidence) in enumerate(results_ocr):
                    print(f"    结果{j+1}: '{text}' | 位置: {pos} | 置信度: {confidence:.3f}")
                    try:
                        level = int(text)
                        print(f"    → 解析为数字: {level}")
                    except ValueError:
                        print(f"    → ⚠️ 无法转换为数字")
            else:
                print(f"  ❌ 未识别到任何内容 (耗时: {elapsed_ocr:.3f}秒)")
            
            # 方法3: 使用 ONNX_OCR.Ocr() - PaddleOCR（如果可用）
            if onnx_ocr is not None:
                print("\n[方法3] ONNX_OCR.Ocr() - PaddleOCR 通用识别")
                start_time = time.time()
                results_onnx = onnx_ocr.Ocr(X1, Y1, X2, Y2)
                elapsed_onnx = time.time() - start_time
                
                if results_onnx:
                    print(f"  ✓ 识别耗时: {elapsed_onnx:.3f}秒")
                    for j, (text, pos, confidence) in enumerate(results_onnx):
                        print(f"    结果{j+1}: '{text}' | 位置: {pos} | 置信度: {confidence:.3f}")
                        try:
                            level = int(text)
                            print(f"    → 解析为数字: {level}")
                        except ValueError:
                            print(f"    → ⚠️ 无法转换为数字")
                else:
                    print(f"  ❌ 未识别到任何内容 (耗时: {elapsed_onnx:.3f}秒)")
            
            # 等待一下，避免请求过快
            if i < test_count - 1:
                time.sleep(1)
        
        # 打印统计信息
        print("\n" + "=" * 80)
        print("测试完成！统计信息:")
        print("=" * 80)
        
        if hasattr(vnc_ocr, 'get_stats'):
            stats = vnc_ocr.get_stats() if hasattr(vnc_ocr, 'get_stats') else None
            if stats:
                print(f"\nVNC_OCR 统计:")
                print(f"  总调用次数: {stats.get('total_calls', 'N/A')}")
                print(f"  成功次数: {stats.get('success_count', 'N/A')}")
                print(f"  错误次数: {stats.get('error_count', 'N/A')}")
                print(f"  成功率: {stats.get('success_rate', 'N/A')}")
        
        if onnx_ocr is not None and hasattr(onnx_ocr, 'get_stats'):
            stats = onnx_ocr.get_stats()
            print(f"\nONNX_OCR 统计:")
            print(f"  总调用次数: {stats['total_calls']}")
            print(f"  成功次数: {stats['success_count']}")
            print(f"  错误次数: {stats['error_count']}")
            print(f"  成功率: {stats['success_rate']}")
            print(f"  引擎状态: {stats['engine_status']}")
        
        print("\n" + "=" * 80)
        print("建议:")
        print("=" * 80)
        print("1. 纯数字识别推荐使用: VNC_OCR.OcrNumbers()")
        print("   - 优势: 专门针对数字优化，精度高，稳定性好")
        print("   - 适用: 等级、价格、数量等纯数字场景")
        print("\n2. 混合文本识别推荐使用: ONNX_OCR.Ocr()")
        print("   - 优势: 支持中英文混合，通用性强")
        print("   - 适用: 包含中文+数字的复杂场景")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n正在清理资源...")
        try:
            if 'vnc_ocr' in locals():
                vnc_ocr.stop()
            if 'onnx_ocr' in locals() and onnx_ocr is not None:
                onnx_ocr.stop()
            if 'vnc' in locals():
                vnc.stop()
            print("✓ 资源已释放")
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {e}")


if __name__ == '__main__':
    test_ocr_numbers()
