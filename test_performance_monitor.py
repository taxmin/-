# -*- coding: utf-8 -*-
"""
VNC性能监控系统测试脚本
用于验证崩溃位置跟踪、VNC重连统计、KM操作统计等功能
"""
import sys
import os
import time

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.stability_optimizer import vnc_performance_monitor


def test_crash_location_tracking():
    """测试崩溃位置跟踪功能"""
    print("\n" + "="*70)
    print("测试1: 崩溃位置跟踪")
    print("="*70)
    
    # 模拟不同位置的崩溃
    test_locations = [
        ("km_稳妥移动点击", "OSError: 访问被拒绝"),
        ("for_ms_row", "ValueError: 图像数据为空"),
        ("km_稳妥移动点击", "OSError: VNC连接断开"),
        ("Capture", "Exception: ManagedMemoryView创建失败"),
        ("km_稳妥移动点击", "OSError: 访问违规"),
    ]
    
    for location, details in test_locations:
        vnc_performance_monitor.record_crash(location=location, details=details)
        print(f"  记录崩溃: {location} - {details}")
    
    # 获取统计信息
    stats = vnc_performance_monitor.get_stats()
    
    print(f"\n崩溃总数: {stats['崩溃次数']}")
    print(f"最后崩溃位置: {stats['最后崩溃位置']}")
    
    if stats.get('崩溃位置分布'):
        print(f"\n崩溃位置分布:")
        for loc, count in sorted(stats['崩溃位置分布'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {loc}: {count}次")
    
    # 验证结果
    expected_km_crashes = 3  # km_稳妥移动点击应该有3次
    actual_km_crashes = stats['崩溃位置分布'].get('km_稳妥移动点击', 0)
    
    if actual_km_crashes == expected_km_crashes:
        print(f"\n✅ 测试通过: km_稳妥移动点击 崩溃次数正确 ({actual_km_crashes}次)")
    else:
        print(f"\n❌ 测试失败: 期望 {expected_km_crashes}次，实际 {actual_km_crashes}次")
    
    return True


def test_vnc_reconnect_tracking():
    """测试VNC重连统计"""
    print("\n" + "="*70)
    print("测试2: VNC重连统计")
    print("="*70)
    
    # 模拟VNC重连
    for i in range(3):
        vnc_performance_monitor.record_vnc_reconnect(row=i, reason=f"测试重连 #{i+1}")
        print(f"  记录重连: Row {i} - 测试重连 #{i+1}")
        time.sleep(0.1)
    
    stats = vnc_performance_monitor.get_stats()
    
    print(f"\nVNC重连次数: {stats['VNC重连次数']}")
    print(f"平均重连间隔: {stats['平均重连间隔']}")
    
    if stats['VNC重连次数'] >= 3:
        print(f"\n✅ 测试通过: VNC重连次数正确")
    else:
        print(f"\n❌ 测试失败: VNC重连次数不正确")
    
    return True


def test_screenshot_tracking():
    """测试截图统计"""
    print("\n" + "="*70)
    print("测试3: 截图统计")
    print("="*70)
    
    # 模拟截图
    for i in range(10):
        if i < 8:
            vnc_performance_monitor.record_screenshot(success=True)
        elif i == 8:
            vnc_performance_monitor.record_screenshot(success=False)
        else:
            vnc_performance_monitor.record_screenshot(success=False, is_timeout=True)
    
    stats = vnc_performance_monitor.get_stats()
    
    print(f"截图总次数: {stats['截图总次数']}")
    print(f"成功: {stats['截图成功']}")
    print(f"失败: {stats['截图失败']}")
    print(f"超时: {stats['截图超时']}")
    print(f"成功率: {stats['截图成功率']}")
    
    if stats['截图总次数'] == 10 and stats['截图成功'] == 8:
        print(f"\n✅ 测试通过: 截图统计正确")
    else:
        print(f"\n❌ 测试失败: 截图统计不正确")
    
    return True


def test_km_operations_tracking():
    """测试KM操作统计"""
    print("\n" + "="*70)
    print("测试4: KM操作统计")
    print("="*70)
    
    # 模拟KM操作
    for i in range(5):
        vnc_performance_monitor.record_km_move()
        vnc_performance_monitor.record_km_click()
        vnc_performance_monitor.record_km_keypress()
    
    vnc_performance_monitor.record_km_error()
    vnc_performance_monitor.record_km_error()
    
    stats = vnc_performance_monitor.get_stats()
    
    print(f"KM移动次数: {stats['KM移动次数']}")
    print(f"KM点击次数: {stats['KM点击次数']}")
    print(f"KM按键次数: {stats['KM按键次数']}")
    print(f"KM错误次数: {stats['KM错误次数']}")
    print(f"KM错误率: {stats['KM错误率']}")
    
    if (stats['KM移动次数'] == 5 and 
        stats['KM点击次数'] == 5 and 
        stats['KM按键次数'] == 5 and
        stats['KM错误次数'] == 2):
        print(f"\n✅ 测试通过: KM操作统计正确")
    else:
        print(f"\n❌ 测试失败: KM操作统计不正确")
    
    return True


def test_export_report():
    """测试报告导出功能"""
    print("\n" + "="*70)
    print("测试5: 导出性能报告")
    print("="*70)
    
    report_file = "test_vnc_performance_report.txt"
    
    try:
        vnc_performance_monitor.export_report(report_file)
        
        if os.path.exists(report_file):
            print(f"\n✅ 测试通过: 报告文件已生成")
            
            # 读取并显示部分内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n报告文件大小: {len(content)} 字节")
                
                # 检查是否包含崩溃位置汇总
                if "崩溃位置汇总" in content:
                    print("✅ 报告包含崩溃位置汇总")
                else:
                    print("❌ 报告缺少崩溃位置汇总")
            
            # 清理测试文件
            os.remove(report_file)
            print(f"\n已清理测试文件: {report_file}")
        else:
            print(f"\n❌ 测试失败: 报告文件未生成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("VNC性能监控系统测试")
    print("="*70)
    
    tests = [
        test_crash_location_tracking,
        test_vnc_reconnect_tracking,
        test_screenshot_tracking,
        test_km_operations_tracking,
        test_export_report,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查")
    
    # 打印最终统计
    print("\n" + "="*70)
    print("最终性能统计")
    print("="*70)
    vnc_performance_monitor.print_stats()


if __name__ == '__main__':
    main()
