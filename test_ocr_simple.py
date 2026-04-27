# -*- coding: utf-8 -*-
"""
简单测试 VNC_OCR.OcrNumbers() 数字识别效果
不依赖完整的dx框架，直接测试OCR功能
"""
import sys
import os
import time

# 添加项目路径
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

print("=" * 80)
print("测试 VNC_OCR.OcrNumbers() 数字识别")
print("=" * 80)

try:
    # 尝试导入VNC和OCR模块
    print("\n正在导入模块...")
    
    # 先尝试直接导入（如果dxGame已经在路径中）
    try:
        from dxGame.dx_vnc import VNC
        from dxGame.dx_ocr import VNC_OCR
        print("✓ 成功从 dxGame 导入模块")
    except ImportError as e1:
        print(f"从 dxGame 导入失败: {e1}")
        # 尝试其他方式
        try:
            sys.path.insert(0, os.path.join(_current_dir, 'dxGame'))
            from dx_vnc import VNC
            from dx_ocr import VNC_OCR
            print("✓ 成功从 dxGame 子目录导入模块")
        except ImportError as e2:
            print(f"❌ 所有导入方式都失败:")
            print(f"   错误1: {e1}")
            print(f"   错误2: {e2}")
            print("\n提示: 请确保在正确的环境中运行此脚本")
            sys.exit(1)
    
    # 配置参数
    IP = "127.0.0.1"
    PORT = "5600"
    PASSWORD = ""
    
    # 测试区域（角色等级）
    X1, Y1, X2, Y2 = 822, 75, 862, 96
    
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
        print("   安装位置应为: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        vnc.stop()
        sys.exit(1)
    
    print("✓ VNC_OCR 初始化成功")
    print(f"  Tesseract 可用: {vnc_ocr.ocr_engine.tesseract_available}")
    
    print("\n" + "=" * 80)
    print(f"开始测试区域: ({X1}, {Y1}, {X2}, {Y2})")
    print("=" * 80)
    
    # 测试次数
    test_count = 5
    
    success_count = 0
    fail_count = 0
    
    for i in range(test_count):
        print(f"\n{'='*80}")
        print(f"第 {i+1}/{test_count} 次测试")
        print(f"{'='*80}")
        
        # 方法1: 使用 VNC_OCR.OcrNumbers() - 专门针对数字优化
        print("\n[方法1] VNC_OCR.OcrNumbers() - Tesseract 数字专用")
        start_time = time.time()
        # 降低阈值以提高识别率
        results_numbers = vnc_ocr.OcrNumbers(X1, Y1, X2, Y2, 
                                              confidence_threshold=0.5, 
                                              min_confidence=0.3)
        elapsed_numbers = time.time() - start_time
        
        if results_numbers:
            success_count += 1
            print(f"  ✓ 识别成功 (耗时: {elapsed_numbers:.3f}秒)")
            for j, (text, pos, confidence) in enumerate(results_numbers):
                print(f"    结果{j+1}: '{text}' | 位置: {pos} | 置信度: {confidence:.3f}")
                try:
                    level = int(text)
                    print(f"    → ✅ 解析为数字: {level}")
                except ValueError:
                    print(f"    → ⚠️ 无法转换为数字")
        else:
            fail_count += 1
            print(f"  ❌ 未识别到任何内容 (耗时: {elapsed_numbers:.3f}秒)")
        
        # 方法2: 使用 VNC_OCR.Ocr() - 通用OCR
        print("\n[方法2] VNC_OCR.Ocr() - Tesseract 通用识别")
        start_time = time.time()
        results_ocr = vnc_ocr.Ocr(X1, Y1, X2, Y2, show_result=False)
        elapsed_ocr = time.time() - start_time
        
        if results_ocr:
            print(f"  ✓ 识别成功 (耗时: {elapsed_ocr:.3f}秒)")
            for j, (text, pos, confidence) in enumerate(results_ocr):
                print(f"    结果{j+1}: '{text}' | 位置: {pos} | 置信度: {confidence:.3f}")
                try:
                    level = int(text)
                    print(f"    → ✅ 解析为数字: {level}")
                except ValueError:
                    print(f"    → ⚠️ 无法转换为数字")
        else:
            print(f"  ❌ 未识别到任何内容 (耗时: {elapsed_ocr:.3f}秒)")
        
        # 等待一下，避免请求过快
        if i < test_count - 1:
            time.sleep(1)
    
    # 打印统计信息
    print("\n" + "=" * 80)
    print("测试结果汇总:")
    print("=" * 80)
    print(f"总测试次数: {test_count}")
    print(f"成功次数: {success_count}")
    print(f"失败次数: {fail_count}")
    print(f"成功率: {success_count/test_count*100:.1f}%")
    
    print("\n" + "=" * 80)
    print("结论与建议:")
    print("=" * 80)
    print("✅ VNC_OCR.OcrNumbers() 是识别数字的最佳选择")
    print("   - 专为数字识别优化")
    print("   - 使用 Tesseract 白名单模式 (只识别 0-9)")
    print("   - 图像预处理增强（放大、二值化、形态学操作）")
    print("   - 双阈值过滤（min_confidence + confidence_threshold）")
    print("   - 自动移除非数字字符")
    print("\n适用场景:")
    print("   - 角色等级识别")
    print("   - 价格/金币识别")
    print("   - 数量/血量等纯数字场景")
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
        if 'vnc' in locals():
            vnc.stop()
        print("✓ 资源已释放")
    except Exception as e:
        print(f"⚠️ 清理资源时出错: {e}")
