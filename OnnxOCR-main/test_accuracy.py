import cv2
import time
from onnxocr.onnx_paddleocr import ONNXPaddleOcr, sav2Img

def test_accuracy():
    """测试识别准确率"""
    print("=" * 80)
    print("OCR 识别准确率测试")
    print("=" * 80)
    
    # 选择几张不同类型的图片进行测试
    test_cases = [
        {
            'name': '英文场景',
            'path': './onnxocr/test_images/ger_1.jpg',
            'expected_keywords': ['德国', 'German']  # 期望包含的关键词
        },
        {
            'name': '中文界面',
            'path': './onnxocr/test_images/weixin_pay.jpg',
            'expected_keywords': ['微信', '支付', '金额']
        },
        {
            'name': '二维码',
            'path': './onnxocr/test_images/myQR.jpg',
            'expected_keywords': []  # 二维码可能没有明显文字
        }
    ]
    
    model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {case['name']}")
        print("-" * 80)
        
        img = cv2.imread(case['path'])
        if img is None:
            print(f"⚠ 无法读取图片：{case['path']}")
            continue
        
        h, w = img.shape[:2]
        print(f"图片尺寸：{w}x{h}")
        
        # 执行 OCR
        start = time.time()
        result = model.ocr(img)
        elapsed = time.time() - start
        
        print(f"识别耗时：{elapsed:.3f}秒")
        print(f"检测文本框数量：{len(result[0]) if result and result[0] else 0}")
        
        # 显示识别结果
        print("\n识别内容:")
        if result and result[0]:
            for j, box in enumerate(result[0], 1):
                text = box[1][0]
                confidence = box[1][1]
                print(f"  [{j}] {text}")
                print(f"      置信度：{confidence:.4f}")
                
                # 检查是否包含期望的关键词
                if case['expected_keywords']:
                    for keyword in case['expected_keywords']:
                        if keyword.lower() in text.lower():
                            print(f"      ✓ 包含期望关键词：'{keyword}'")
        else:
            print("  [未检测到文本]")
        
        # 保存带标注的结果图
        output_name = f"./result_img/test_accuracy_{i}_{int(time.time())}.jpg"
        try:
            sav2Img(img, result, name=output_name)
            print(f"\n✓ 结果图已保存：{output_name}")
        except Exception as e:
            print(f"⚠ 保存结果图失败：{e}")
    
    print("\n" + "=" * 80)

def test_batch_performance():
    """批量处理性能测试"""
    print("\n" + "=" * 80)
    print("批量处理性能模拟测试")
    print("=" * 80)
    
    # 模拟批量处理 10 张图片
    test_img_path = './onnxocr/test_images/00056221.jpg'
    batch_size = 10
    
    img = cv2.imread(test_img_path)
    if img is None:
        print("⚠ 无法读取测试图片")
        return
    
    model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)
    
    # 预热
    _ = model.ocr(img)
    
    print(f"\n批量处理模拟：{batch_size}张相同图片")
    print("-" * 80)
    
    total_start = time.time()
    results = []
    
    for i in range(batch_size):
        s = time.time()
        result = model.ocr(img)
        e = time.time()
        results.append(e - s)
        
        if (i + 1) % 5 == 0:
            print(f"已处理 {i+1}/{batch_size} 张，当前耗时：{results[-1]:.3f}秒")
    
    total_time = time.time() - total_start
    avg_time = sum(results) / len(results)
    
    print(f"\n批量处理统计:")
    print(f"  总耗时：{total_time:.2f}秒")
    print(f"  平均单张：{avg_time:.3f}秒")
    print(f"  最快：{min(results):.3f}秒")
    print(f"  最慢：{max(results):.3f}秒")
    print(f"  吞吐量：{batch_size/total_time:.2f}张/秒")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_accuracy()
    test_batch_performance()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
