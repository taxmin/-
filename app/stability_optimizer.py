# -*- coding: utf-8 -*-
"""
多开框架稳定性优化模块
实现多层并发保护机制，提升多开环境下的稳定性
"""
import threading
import time
import logging
from collections import deque
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class VNCPerformanceMonitor:
    """
    VNC 性能监控器（记录 VNC 重连、截图、键鼠操作等关键指标）
    
    特性：
    1. 记录 VNC 重连次数和时间
    2. 统计截图调用次数和失败率
    3. 统计键鼠操作次数
    4. 记录崩溃事件，便于分析
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # VNC 重连统计
        self.vnc_reconnect_count = 0
        self.vnc_reconnect_times = []  # 记录每次重连的时间戳
        self.last_reconnect_time = None
        
        # 截图统计
        self.screenshot_total = 0
        self.screenshot_success = 0
        self.screenshot_failed = 0
        self.screenshot_timeout = 0  # 超时次数
        
        # 键鼠操作统计
        self.km_move_count = 0  # 移动次数
        self.km_click_count = 0  # 点击次数
        self.km_keypress_count = 0  # 按键次数
        self.km_error_count = 0  # 错误次数
        
        # 崩溃记录
        self.crash_count = 0
        self.crash_details = []  # 记录崩溃详情
        self.last_crash_time = None
        self.last_crash_location = None  # 崩溃位置
        self.crash_locations = {}  # 记录每个位置的崩溃次数 {location: count}
        
        # 启动时间
        self.start_time = time.time()
    
    def record_vnc_reconnect(self, row=None, reason=""):
        """记录 VNC 重连事件"""
        with self._lock:
            self.vnc_reconnect_count += 1
            reconnect_info = {
                'time': time.time(),
                'row': row,
                'reason': reason,
                'uptime': time.time() - self.start_time
            }
            self.vnc_reconnect_times.append(reconnect_info)
            self.last_reconnect_time = time.time()
            logger.info(f"[VNC监控] Row:{row} VNC重连 #{self.vnc_reconnect_count} - {reason}")
    
    def record_screenshot(self, success=True, is_timeout=False):
        """记录截图事件"""
        with self._lock:
            self.screenshot_total += 1
            if is_timeout:
                self.screenshot_timeout += 1
            elif success:
                self.screenshot_success += 1
            else:
                self.screenshot_failed += 1
    
    def record_km_move(self):
        """记录 KM 移动操作"""
        with self._lock:
            self.km_move_count += 1
    
    def record_km_click(self):
        """记录 KM 点击操作"""
        with self._lock:
            self.km_click_count += 1
    
    def record_km_keypress(self):
        """记录 KM 按键操作"""
        with self._lock:
            self.km_keypress_count += 1
    
    def record_km_error(self):
        """记录 KM 错误"""
        with self._lock:
            self.km_error_count += 1
    
    def record_crash(self, location="", details=""):
        """记录崩溃事件"""
        with self._lock:
            self.crash_count += 1
            crash_info = {
                'time': time.time(),
                'location': location,
                'details': details,
                'uptime': time.time() - self.start_time,
                'vnc_reconnects': self.vnc_reconnect_count,
                'screenshots': self.screenshot_total,
                'km_operations': self.get_km_total()
            }
            self.crash_details.append(crash_info)
            self.last_crash_time = time.time()
            self.last_crash_location = location
            
            # 记录每个位置的崩溃次数
            if location not in self.crash_locations:
                self.crash_locations[location] = 0
            self.crash_locations[location] += 1
            
            logger.error(f"[VNC监控] ❌ 崩溃 #{self.crash_count} @ {location}: {details}")
    
    def get_km_total(self):
        """获取 KM 操作总数"""
        return self.km_move_count + self.km_click_count + self.km_keypress_count
    
    def get_stats(self):
        """获取完整的性能统计"""
        with self._lock:
            uptime = time.time() - self.start_time
            km_total = self.get_km_total()
            
            # 计算成功率
            screenshot_rate = (
                f"{self.screenshot_success / max(self.screenshot_total, 1) * 100:.1f}%"
                if self.screenshot_total > 0 else "N/A"
            )
            
            return {
                # 基础信息
                '运行时长': f"{int(uptime // 3600)}小时{int((uptime % 3600) // 60)}分{int(uptime % 60)}秒",
                '启动时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
                
                # VNC 重连统计
                'VNC重连次数': self.vnc_reconnect_count,
                '最后重连时间': time.strftime('%H:%M:%S', time.localtime(self.last_reconnect_time)) if self.last_reconnect_time else '无',
                '平均重连间隔': f"{uptime / max(self.vnc_reconnect_count, 1) / 60:.1f}分钟",
                
                # 截图统计
                '截图总次数': self.screenshot_total,
                '截图成功': self.screenshot_success,
                '截图失败': self.screenshot_failed,
                '截图超时': self.screenshot_timeout,
                '截图成功率': screenshot_rate,
                '每秒截图数': f"{self.screenshot_total / max(uptime, 1):.2f}",
                
                # 键鼠统计
                'KM操作总数': km_total,
                'KM移动次数': self.km_move_count,
                'KM点击次数': self.km_click_count,
                'KM按键次数': self.km_keypress_count,
                'KM错误次数': self.km_error_count,
                'KM错误率': f"{self.km_error_count / max(km_total, 1) * 100:.2f}%",
                
                # 崩溃统计
                '崩溃次数': self.crash_count,
                '最后崩溃时间': time.strftime('%H:%M:%S', time.localtime(self.last_crash_time)) if self.last_crash_time else '无',
                '最后崩溃位置': self.last_crash_location or '无',
                '崩溃位置分布': dict(self.crash_locations),  # 新增：崩溃位置分布
            }
    
    def print_stats(self):
        """打印性能统计信息"""
        stats = self.get_stats()
        print("\n" + "="*70)
        print("📊 VNC 性能监控统计")
        print("="*70)
        
        print(f"\n⏱️  运行时长: {stats['运行时长']}")
        print(f"🚀 启动时间: {stats['启动时间']}")
        
        print(f"\n🔄 VNC 重连统计:")
        print(f"   重连次数: {stats['VNC重连次数']}")
        print(f"   最后重连: {stats['最后重连时间']}")
        print(f"   平均间隔: {stats['平均重连间隔']}")
        
        print(f"\n📸 截图统计:")
        print(f"   总次数: {stats['截图总次数']}")
        print(f"   成功: {stats['截图成功']} | 失败: {stats['截图失败']} | 超时: {stats['截图超时']}")
        print(f"   成功率: {stats['截图成功率']}")
        print(f"   速度: {stats['每秒截图数']} 次/秒")
        
        print(f"\n🖱️  键鼠操作统计:")
        print(f"   总操作: {stats['KM操作总数']}")
        print(f"   移动: {stats['KM移动次数']} | 点击: {stats['KM点击次数']} | 按键: {stats['KM按键次数']}")
        print(f"   错误: {stats['KM错误次数']} (错误率: {stats['KM错误率']})")
        
        print(f"\n💥 崩溃统计:")
        print(f"   崩溃次数: {stats['崩溃次数']}")
        print(f"   最后崩溃: {stats['最后崩溃时间']}")
        print(f"   崩溃位置: {stats['最后崩溃位置']}")
        
        # 打印崩溃位置分布
        if stats.get('崩溃位置分布'):
            print(f"\n📍 崩溃位置分布:")
            for loc, count in sorted(stats['崩溃位置分布'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {loc}: {count}次")
        
        print("\n" + "="*70)
    
    def export_report(self, filepath="vnc_performance_report.txt"):
        """导出详细报告到文件"""
        stats = self.get_stats()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("VNC 性能监控详细报告\n")
            f.write("="*70 + "\n\n")
            
            for key, value in stats.items():
                f.write(f"{key}: {value}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("崩溃详细记录\n")
            f.write("="*70 + "\n\n")
            
            for i, crash in enumerate(self.crash_details, 1):
                f.write(f"\n崩溃 #{i}:\n")
                f.write(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(crash['time']))}\n")
                f.write(f"  位置: {crash['location']}\n")
                f.write(f"  详情: {crash['details']}\n")
                f.write(f"  运行时长: {crash['uptime']:.0f}秒\n")
                f.write(f"  当时VNC重连次数: {crash['vnc_reconnects']}\n")
                f.write(f"  当时截图次数: {crash['screenshots']}\n")
                f.write(f"  当时KM操作次数: {crash['km_operations']}\n")
            
            # 添加崩溃位置汇总
            f.write("\n" + "="*70 + "\n")
            f.write("崩溃位置汇总（按频率排序）\n")
            f.write("="*70 + "\n\n")
            for loc, count in sorted(self.crash_locations.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{loc}: {count}次\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("VNC 重连历史记录\n")
            f.write("="*70 + "\n\n")
            
            for i, recon in enumerate(self.vnc_reconnect_times[-20:], 1):  # 最近20次
                f.write(f"\n重连 #{i}:\n")
                f.write(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(recon['time']))}\n")
                f.write(f"  Row: {recon['row']}\n")
                f.write(f"  原因: {recon['reason']}\n")
                f.write(f"  运行时长: {recon['uptime']:.0f}秒\n")
        
        print(f"✅ 性能报告已导出到: {filepath}")


# 全局 VNC 性能监控实例
vnc_performance_monitor = VNCPerformanceMonitor()


class EnhancedKMLock:
    """
    增强的KM操作锁（带超时和重试机制）
    
    特性：
    1. 支持超时等待，避免无限阻塞
    2. 自动重试机制，提高成功率
    3. 统计信息收集，便于监控
    """
    
    def __init__(self, timeout=5.0, max_retries=3, retry_delay=0.1):
        self._lock = threading.Lock()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 统计信息
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_wait_time = 0
    
    @contextmanager
    def acquire(self, operation_name="KM操作"):
        """
        获取锁的上下文管理器
        
        Args:
            operation_name: 操作名称（用于日志）
            
        Yields:
            None
            
        Raises:
            TimeoutError: 超过最大重试次数仍未获取到锁
        """
        acquired = False
        wait_start = time.time()
        
        for attempt in range(self.max_retries):
            # 尝试获取锁（非阻塞）
            if self._lock.acquire(timeout=self.timeout):
                acquired = True
                break
            
            # 等待后重试
            logger.warning(f"[KM锁] {operation_name} 第{attempt+1}次尝试超时，{self.retry_delay}s后重试")
            time.sleep(self.retry_delay)
        
        if not acquired:
            self.failed_operations += 1
            raise TimeoutError(f"[KM锁] {operation_name} 在{self.max_retries}次尝试后仍未获取到锁")
        
        try:
            yield
            self.successful_operations += 1
        finally:
            self._lock.release()
            wait_end = time.time()
            self.total_operations += 1
            self.total_wait_time += (wait_end - wait_start)
    
    def get_stats(self):
        """获取锁使用统计信息"""
        return {
            "总操作数": self.total_operations,
            "成功操作": self.successful_operations,
            "失败操作": self.failed_operations,
            "平均等待时间": f"{(self.total_wait_time / max(self.total_operations, 1)):.3f}s"
        }


class WindowRecoveryQueue:
    """
    窗口恢复队列（确保同一时间只有一个窗口在恢复）
    
    特性：
    1. FIFO队列，按顺序处理窗口恢复
    2. 防止多个窗口同时恢复导致的资源竞争
    3. 支持取消特定窗口的恢复请求
    """
    
    def __init__(self, max_concurrent=1):
        self._queue = deque()
        self._processing = set()  # 正在处理的窗口
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.max_concurrent = max_concurrent
    
    def request_recovery(self, row, recovery_func):
        """
        请求窗口恢复
        
        Args:
            row: 行号
            recovery_func: 恢复函数
            
        Returns:
            bool: 是否成功加入队列
        """
        with self._lock:
            # 检查是否已在队列中
            for item in self._queue:
                if item[0] == row:
                    logger.warning(f"[Row:{row}] 窗口恢复请求已在队列中")
                    return False
            
            self._queue.append((row, recovery_func))
            logger.info(f"[Row:{row}] 📋 窗口恢复请求已加入队列（位置:{len(self._queue)}）")
            self._condition.notify_all()
            return True
    
    def process_queue(self):
        """
        处理恢复队列（应在独立线程中运行）
        """
        while True:
            with self._condition:
                # 等待队列中有任务且未达到并发上限
                while len(self._queue) == 0 or len(self._processing) >= self.max_concurrent:
                    self._condition.wait(timeout=1.0)
                
                # 取出队首任务
                row, recovery_func = self._queue.popleft()
                self._processing.add(row)
            
            # 执行恢复（在锁外执行，避免长时间占用锁）
            try:
                logger.info(f"[Row:{row}] 🔄 开始执行窗口恢复...")
                success = recovery_func()
                logger.info(f"[Row:{row}] {'✅' if success else '❌'} 窗口恢复{'完成' if success else '失败'}")
            except Exception as e:
                logger.error(f"[Row:{row}] ❌ 窗口恢复异常: {e}")
            finally:
                with self._lock:
                    self._processing.discard(row)
                    self._condition.notify_all()
    
    def cancel_recovery(self, row):
        """取消指定窗口的恢复请求"""
        with self._lock:
            original_len = len(self._queue)
            self._queue = deque([(r, f) for r, f in self._queue if r != row])
            removed = original_len - len(self._queue)
            if removed > 0:
                logger.info(f"[Row:{row}] ❌ 已取消{removed}个恢复请求")
            return removed > 0
    
    def is_processing(self, row):
        """检查指定窗口是否正在恢复"""
        with self._lock:
            return row in self._processing
    
    def queue_length(self):
        """获取队列长度"""
        with self._lock:
            return len(self._queue)


class VNCConnectionPool:
    """
    VNC连接池（复用VNC连接，减少频繁创建/销毁）
    
    特性：
    1. 连接复用，降低网络开销
    2. 健康检查，自动替换失效连接
    3. 超时清理，释放空闲连接
    """
    
    def __init__(self, max_connections=10, idle_timeout=300):
        self._pool = {}  # {port: connection}
        self._last_used = {}  # {port: timestamp}
        self._lock = threading.Lock()
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
    
    def get_connection(self, port, create_func):
        """
        获取VNC连接
        
        Args:
            port: VNC端口
            create_func: 创建连接的函数
            
        Returns:
            连接对象
        """
        with self._lock:
            # 检查是否有可用连接
            if port in self._pool:
                conn = self._pool[port]
                last_used = self._last_used[port]
                
                # 检查连接是否仍然有效（简单检查）
                if time.time() - last_used < self.idle_timeout:
                    self._last_used[port] = time.time()
                    logger.debug(f"[VNC池] 复用端口 {port} 的连接")
                    return conn
                else:
                    # 连接超时，移除
                    logger.info(f"[VNC池] 端口 {port} 的连接已超时，移除")
                    del self._pool[port]
                    del self._last_used[port]
            
            # 检查是否需要清理空闲连接
            if len(self._pool) >= self.max_connections:
                self._cleanup_idle_connections()
        
        # 创建新连接
        try:
            conn = create_func()
            with self._lock:
                self._pool[port] = conn
                self._last_used[port] = time.time()
                logger.info(f"[VNC池] 创建端口 {port} 的新连接")
            return conn
        except Exception as e:
            logger.error(f"[VNC池] 创建端口 {port} 的连接失败: {e}")
            raise
    
    def release_connection(self, port):
        """释放VNC连接（标记为空闲）"""
        with self._lock:
            if port in self._last_used:
                self._last_used[port] = time.time()
    
    def _cleanup_idle_connections(self):
        """清理空闲连接"""
        now = time.time()
        to_remove = []
        
        for port, last_used in self._last_used.items():
            if now - last_used > self.idle_timeout:
                to_remove.append(port)
        
        for port in to_remove:
            logger.info(f"[VNC池] 清理端口 {port} 的空闲连接")
            del self._pool[port]
            del self._last_used[port]
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for port, conn in self._pool.items():
                try:
                    if hasattr(conn, 'close'):
                        conn.close()
                except:
                    pass
            self._pool.clear()
            self._last_used.clear()
            logger.info("[VNC池] 已关闭所有连接")


# 全局实例
km_lock_enhanced = EnhancedKMLock(timeout=5.0, max_retries=3)
window_recovery_queue = WindowRecoveryQueue(max_concurrent=1)
vnc_pool = VNCConnectionPool(max_connections=10, idle_timeout=300)


def start_recovery_worker():
    """启动窗口恢复工作线程"""
    worker = threading.Thread(target=window_recovery_queue.process_queue, daemon=True, name="WindowRecoveryWorker")
    worker.start()
    logger.info("✅ 窗口恢复工作线程已启动")
    return worker


if __name__ == "__main__":
    # 测试代码
    print("=== 测试增强KM锁 ===")
    lock = EnhancedKMLock(timeout=1.0, max_retries=2)
    
    def test_operation():
        with lock.acquire("测试操作") :
            print("执行操作...")
            time.sleep(0.5)
    
    test_operation()
    print("统计:", lock.get_stats())
    
    print("\n=== 测试窗口恢复队列 ===")
    queue = WindowRecoveryQueue(max_concurrent=1)
    
    def mock_recovery():
        time.sleep(2)
        return True
    
    queue.request_recovery(0, mock_recovery)
    queue.request_recovery(1, mock_recovery)
    
    worker = start_recovery_worker()
    time.sleep(5)
    
    print(f"队列长度: {queue.queue_length()}")
    print(f"正在处理: {queue.is_processing(0)}")
