import cv2
import time
import os
from onnxocr.onnx_paddleocr import ONNXPaddleOcr, sav2Img
import psutil

def get_memory_usage():
    """获取当前内存使用量（MB）"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def benchmark_ocr_performance():
    print("=" * 80)
    print("OnnxOCR 性能基准测试")
    print("=" * 80)
    
    # 测试图片列表
    test_images = [
        ("简单 - 小尺寸", "./onnxocr/test_images/ger_1.jpg"),
        ("简单 - 中等尺寸", "./onnxocr/test_images/00059985.jpg"),
        ("中等 - 标准尺寸", "./onnxocr/test_images/00056221.jpg"),
        ("复杂 - 大尺寸", "./onnxocr/test_images/1.jpg"),
        ("中文场景", "./onnxocr/test_images/微信群.jpg"),
        ("支付界面", "./onnxocr/test_images/weixin_pay.jpg"),
    ]
    
    # 初始化模型（CPU 模式）
    print("\n[1/3] 加载 OCR 模型（CPU 模式）...")
    start_load = time.time()
    model_cpu = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)
    load_time = time.time() - start_load
    print(f"✓ 模型加载完成，用时：{load_time:.2f}秒")
    
    # 内存占用
    mem_usage = get_memory_usage()
    print(f"✓ 当前内存占用：{mem_usage:.2f} MB")
    
    print("\n" + "=" * 80)
    print("[2/3] CPU 模式性能测试")
    print("=" * 80)
    
    cpu_results = []
    
    for name, img_path in test_images:
        if not os.path.exists(img_path):
            print(f"⚠ 文件不存在：{img_path}")
            continue
            
        img = cv2.imread(img_path)
        if img is None:
            print(f"⚠ 无法读取图片：{img_path}")
            continue
        
        h, w = img.shape[:2]
        file_size = os.path.getsize(img_path) / 1024  # KB
        
        # 预热一次
        _ = model_cpu.ocr(img)
        
        # 正式测试 3 次取平均
        times = []
        for i in range(3):
            s = time.time()
            result = model_cpu.ocr(img)
            e = time.time()
            times.append(e - s)
        
        avg_time = sum(times) / len(times)
        text_count = len(result[0]) if result and result[0] else 0
        
        # 计算性能指标
        pixels = h * w
        speed_mps = (pixels / 1000000) / avg_time  # 百万像素/秒
        
        cpu_results.append({
            'name': name,
            'size': f"{w}x{h}",
            'file_size': file_size,
            'avg_time': avg_time,
            'text_count': text_count,
            'speed_mps': speed_mps
        })
        
        print(f"\n{name}:")
        print(f"  图片尺寸：{w}x{h} ({file_size:.1f} KB)")
        print(f"  平均耗时：{avg_time:.3f}秒")
        print(f"  识别文本数：{text_count}条")
        print(f"  处理速度：{speed_mps:.2f} MP/s")
    
    # 计算总体统计
    if cpu_results:
        avg_inference = sum(r['avg_time'] for r in cpu_results) / len(cpu_results)
        avg_speed = sum(r['speed_mps'] for r in cpu_results) / len(cpu_results)
        
        print("\n" + "=" * 80)
        print("CPU 模式性能汇总")
        print("=" * 80)
        print(f"平均推理时间：{avg_inference:.3f}秒")
        print(f"平均处理速度：{avg_speed:.2f}百万像素/秒")
        print(f"总内存占用：{get_memory_usage():.2f} MB")
    
    # 如果有 GPU，测试 GPU 模式
    try:
        print("\n" + "=" * 80)
        print("[3/3] GPU 模式性能测试（如果可用）")
        print("=" * 80)
        
        model_gpu = ONNXPaddleOcr(use_angle_cls=True, use_gpu=True)
        
        # 选一张图快速测试
        test_img = test_images[2][1]  # 中等难度
        if os.path.exists(test_img):
            img = cv2.imread(test_img)
            
            # 预热
            _ = model_gpu.ocr(img)
            
            # 测试 3 次
            gpu_times = []
            for i in range(3):
                s = time.time()
                result = model_gpu.ocr(img)
                e = time.time()
                gpu_times.append(e - s)
            
            gpu_avg = sum(gpu_times) / len(gpu_times)
            cpu_avg_same = cpu_results[2]['avg_time']  # 同一张图的 CPU 时间
            
            speedup = cpu_avg_same / gpu_avg if gpu_avg > 0 else 0
            
            print(f"\n测试图片：中等 - 标准尺寸")
            print(f"GPU 平均耗时：{gpu_avg:.3f}秒")
            print(f"CPU 平均耗时：{cpu_avg_same:.3f}秒")
            print(f"加速比：{speedup:.2f}x")
            
            if speedup > 1.5:
                print("✓ GPU 加速效果显著！")
            elif speedup > 1.0:
                print("✓ GPU 略有加速")
            else:
                print("⚠ GPU 加速不明显，可能是数据传输开销导致")
    except Exception as e:
        print(f"⚠ GPU 模式不可用或未正确配置")
        print(f"错误信息：{str(e)}")
    
    # 最终总结
    print("\n" + "=" * 80)
    print("性能评估总结")
    print("=" * 80)
    
    if cpu_results:
        # 评级标准
        if avg_inference < 0.3:
            rating = "优秀 ⭐⭐⭐⭐⭐"
        elif avg_inference < 0.5:
            rating = "良好 ⭐⭐⭐⭐"
        elif avg_inference < 1.0:
            rating = "中等 ⭐⭐⭐"
        else:
            rating = "较慢 ⭐⭐"
        
        print(f"整体性能评级：{rating}")
        print(f"适用场景：", end="")
        if avg_inference < 0.5:
            print("✓ 实时处理 ✓ 批量处理 ✓ 在线服务")
        elif avg_inference < 1.0:
            print("✓ 离线批处理 ✓ 准实时应用")
        else:
            print("✓ 离线批处理（大量图片建议增加硬件或优化）")
        
        print(f"\n推荐配置:")
        print(f"  • 内存需求：≥ {mem_usage * 1.5:.0f} MB")
        print(f"  • CPU 核心：≥ 4 核")
        print(f"  • GPU: 可选（如有 CUDA 环境可提升 1.5-3 倍性能）")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    benchmark_ocr_performance()
