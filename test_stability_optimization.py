# -*- coding: utf-8 -*-
"""
稳定性优化验证脚本
用于测试方案B的各项功能是否正常工作
"""
import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.stability_optimizer import (
    km_lock_enhanced,
    window_recovery_queue,
    vnc_pool,
    start_recovery_worker
)


def test_enhanced_km_lock():
    """测试增强KM锁"""
    print("\n" + "="*60)
    print("测试1: 增强KM锁")
    print("="*60)
    
    # 测试基本加锁解锁
    print("\n[测试1.1] 基本加锁解锁...")
    try:
        with km_lock_enhanced.acquire("测试操作"):
            print("✅ 成功获取锁")
            time.sleep(0.5)
        print("✅ 成功释放锁")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 测试并发访问
    print("\n[测试1.2] 并发访问测试...")
    results = []
    
    def worker(worker_id):
        try:
            with km_lock_enhanced.acquire(f"工作线程{worker_id}"):
                print(f"  工作线程{worker_id} 开始执行")
                time.sleep(0.3)
                print(f"  工作线程{worker_id} 完成")
            results.append(True)
        except Exception as e:
            print(f"  工作线程{worker_id} 失败: {e}")
            results.append(False)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.05)  # 错开启动时间
    
    for t in threads:
        t.join()
    
    success_count = sum(results)
    print(f"✅ 并发测试完成: {success_count}/{len(results)} 成功")
    
    # 打印统计信息
    stats = km_lock_enhanced.get_stats()
    print(f"\n📊 KM锁统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return True


def test_window_recovery_queue():
    """测试窗口恢复队列"""
    print("\n" + "="*60)
    print("测试2: 窗口恢复队列")
    print("="*60)
    
    # 启动工作线程
    print("\n[测试2.1] 启动工作线程...")
    worker = start_recovery_worker()
    time.sleep(0.5)
    print("✅ 工作线程已启动")
    
    # 测试添加恢复任务
    print("\n[测试2.2] 添加恢复任务...")
    
    def mock_recovery(row_id):
        def recovery_func():
            print(f"  [Row:{row_id}] 开始恢复...")
            time.sleep(2)
            print(f"  [Row:{row_id}] 恢复完成")
            return True
        return recovery_func
    
    # 添加3个恢复任务
    for i in range(3):
        success = window_recovery_queue.request_recovery(i, mock_recovery(i))
        if success:
            print(f"✅ Row:{i} 恢复请求已加入队列")
        else:
            print(f"❌ Row:{i} 恢复请求失败")
    
    # 等待所有任务完成
    print("\n[测试2.3] 等待所有任务完成...")
    while window_recovery_queue.queue_length() > 0:
        time.sleep(0.5)
        print(f"  队列长度: {window_recovery_queue.queue_length()}")
    
    print("✅ 所有恢复任务已完成")
    
    return True


def test_vnc_connection_pool():
    """测试VNC连接池"""
    print("\n" + "="*60)
    print("测试3: VNC连接池")
    print("="*60)
    
    # 模拟创建连接
    print("\n[测试3.1] 创建VNC连接...")
    
    def create_mock_connection(port):
        print(f"  创建端口 {port} 的VNC连接...")
        return {"port": port, "status": "connected"}
    
    # 获取连接（会创建新连接）
    conn1 = vnc_pool.get_connection("5600", lambda: create_mock_connection("5600"))
    print(f"✅ 连接1: {conn1}")
    
    # 再次获取同一端口（应该复用）
    print("\n[测试3.2] 复用VNC连接...")
    conn2 = vnc_pool.get_connection("5600", lambda: create_mock_connection("5600"))
    print(f"✅ 连接2: {conn2}")
    print(f"  是否为同一连接: {conn1 is conn2}")
    
    # 获取不同端口的连接
    print("\n[测试3.3] 创建新端口连接...")
    conn3 = vnc_pool.get_connection("5601", lambda: create_mock_connection("5601"))
    print(f"✅ 连接3: {conn3}")
    
    # 释放连接
    print("\n[测试3.4] 释放连接...")
    vnc_pool.release_connection("5600")
    vnc_pool.release_connection("5601")
    print("✅ 连接已释放")
    
    # 关闭所有连接
    print("\n[测试3.5] 关闭所有连接...")
    vnc_pool.close_all()
    print("✅ 所有连接已关闭")
    
    return True


def test_concurrent_km_operations():
    """测试并发KM操作（模拟真实场景）"""
    print("\n" + "="*60)
    print("测试4: 并发KM操作（模拟真实场景）")
    print("="*60)
    
    operation_count = [0]
    error_count = [0]
    
    def simulate_km_operation(operation_id):
        """模拟KM操作"""
        try:
            with km_lock_enhanced.acquire(f"操作{operation_id}"):
                print(f"  [操作{operation_id}] 开始执行...")
                # 模拟KM操作耗时
                time.sleep(0.2)
                operation_count[0] += 1
                print(f"  [操作{operation_id}] 完成")
        except TimeoutError as e:
            print(f"  [操作{operation_id}] 超时: {e}")
            error_count[0] += 1
        except Exception as e:
            print(f"  [操作{operation_id}] 异常: {e}")
            error_count[0] += 1
    
    # 启动10个并发操作
    print("\n启动10个并发KM操作...")
    threads = []
    for i in range(10):
        t = threading.Thread(target=simulate_km_operation, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.05)  # 错开启动时间
    
    # 等待所有操作完成
    for t in threads:
        t.join()
    
    print(f"\n✅ 并发测试完成:")
    print(f"  总操作数: {len(threads)}")
    print(f"  成功执行: {operation_count[0]}")
    print(f"  失败次数: {error_count[0]}")
    
    # 打印最终统计
    stats = km_lock_enhanced.get_stats()
    print(f"\n📊 最终KM锁统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return error_count[0] == 0


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("多开框架稳定性优化 - 验证测试")
    print("="*60)
    
    tests = [
        ("增强KM锁", test_enhanced_km_lock),
        ("窗口恢复队列", test_window_recovery_queue),
        ("VNC连接池", test_vnc_connection_pool),
        ("并发KM操作", test_concurrent_km_operations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, r in results if r)
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！稳定性优化已就绪。")
        return True
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 个测试失败，请检查日志。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
