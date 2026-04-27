# -*- coding: utf-8 -*-
"""
DXGI兼容的VNC截图类
使用方法：
    self.dx.screenshot = VNC("127.0.0.1", "5600", "")  # IP, 端口, 密码

截图性能（环境变量）：
    VNC_CAPTURE  不设或空：默认「内存 refreshScreen 优先」，失败再写临时 PNG（多开推荐）
                 file   ：始终临时 PNG（最稳、最慢，兼容差的服务端）
                 memory ：仅内存路径，失败直接抛错（调试用）
    VNC_MEMORY_DELAY_FULL      全量 refresh 后等待秒数，默认 0.42
    VNC_MEMORY_DELAY_INC       增量 refresh 后等待秒数（已稳定连接），默认 0.08
    VNC_MEMORY_DELAY_INC_COLD  首连阶段第二次尝试用增量时的等待秒数，默认 0.10
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

import threading
import time
import logging

import cv2
import numpy as np

from dxGame.dx_core import *
from dxGame import Window, dxpyd
from vncdotool import api

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING及以上级别的日志，屏蔽INFO和DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 单独设置vncdotool相关日志级别为WARNING，屏蔽其INFO级别的屏幕更新信息
vncdotool_logger = logging.getLogger('vncdotool')
vncdotool_logger.setLevel(logging.WARNING)
vncdotool_api_logger = logging.getLogger('vncdotool.api')
vncdotool_api_logger.setLevel(logging.WARNING)
vncdotool_client_logger = logging.getLogger('vncdotool.client')
vncdotool_client_logger.setLevel(logging.WARNING)


def _vnc_env_float(var_name: str, default: float) -> float:
    raw = os.environ.get(var_name, "").strip()
    if not raw:
        return default
    try:
        v = float(raw)
        if v < 0:
            raise ValueError("negative")
        return v
    except ValueError:
        logging.warning("忽略无效环境变量 %s=%r，使用默认值 %s", var_name, raw, default)
        return default


class VNC:
    """
    VNC截图类，兼容DXGI接口
    使用方法：self.dx.screenshot = VNC("127.0.0.1", "5600", "")
    """

    def __init__(
        self,
        ip,
        port,
        password="",
        hwnd=None,
        fps=5,
        memory_delay_full=None,
        memory_delay_inc=None,
        memory_delay_inc_cold=None,
    ):
        """
        初始化VNC连接

        Args:
            ip: VNC服务器IP地址
            port: VNC服务器端口（字符串或数字）
            password: VNC密码，默认空字符串
            hwnd: 窗口句柄（VNC不需要，但为了兼容DXGI接口保留）
            fps: 截图帧率限制，默认 5 帧/秒（避免过高频率导致崩溃）
            memory_delay_full: 内存截图全量 refresh 后 sleep 秒数；None 则用环境变量或默认 0.42
            memory_delay_inc: 已稳定后增量 refresh 后 sleep 秒数；None 则用环境变量或默认 0.08
            memory_delay_inc_cold: 首连阶段增量尝试的 sleep 秒数；None 则用环境变量或默认 0.10
        """
        # 🔍 引用计数监控：记录 VNC 对象创建
        import sys
        logging.info(f"🔧 VNC 对象创建: ID={id(self)}, IP:Port={ip}:{port}")
        logging.info(f"   - 引用计数: {sys.getrefcount(self)}")
        
        # 处理端口号
        if isinstance(port, int):
            port = str(port)
        
        # 处理密码
        if password == "":
            password = None
        
        self.ip = ip
        self.port = port
        self.password = password
        self.hwnd_desktop = user32.GetDesktopWindow()
        self.screen = 0  # VNC只有一个屏幕
        self._fps = fps
        self.error_max_refresh = 10  # 最大刷新错误次数
        self.consecutive_errors = 0  # 连续错误计数器
        self.total_screenshots = 0  # 总截图次数统计
        self.last_success_time = time.time()  # 上次成功截图时间
        self.max_idle_time = 300  # 最大空闲时间 5 分钟，超时尝试重连
        # 每实例一把锁：多开时各 VNC 互不阻塞（原类级 _lock 会导致所有账号串行截图）
        self._capture_lock = threading.Lock()
        self._reconnect_lock = threading.Lock()

        # 截图策略：默认内存优先（快），失败再写临时 PNG。环境变量 VNC_CAPTURE=file 强制仅文件。
        _cm = os.environ.get("VNC_CAPTURE", "").strip().lower()
        self._vnc_capture_file_only = _cm == "file"
        self._vnc_capture_memory_only = _cm == "memory"
        self._vnc_incremental_ready = False  # 是否已可用增量 refresh，首帧需全量

        df = _vnc_env_float("VNC_MEMORY_DELAY_FULL", 0.42)
        di = _vnc_env_float("VNC_MEMORY_DELAY_INC", 0.08)
        dic = _vnc_env_float("VNC_MEMORY_DELAY_INC_COLD", 0.10)
        self._mem_delay_full = float(memory_delay_full) if memory_delay_full is not None else df
        self._mem_delay_inc = float(memory_delay_inc) if memory_delay_inc is not None else di
        self._mem_delay_inc_cold = (
            float(memory_delay_inc_cold) if memory_delay_inc_cold is not None else dic
        )

        # 连接VNC服务器
        vnc_address = f"{ip}::{port}"
        print(f"正在连接到VNC服务器: {ip}:{port}...")
        try:
            self.client = api.connect(vnc_address, password, timeout=60)
            print("VNC连接成功！")
        except Exception as e:
            print(f"❌ VNC连接失败: {e}")
            raise
        
        # 等待连接稳定
        time.sleep(2)
        
        # 获取VNC屏幕分辨率
        try:
            # 首次截图获取分辨率（文件路径更稳）
            temp_image = self._capture_raw(initial=True)
            if temp_image is not None and temp_image.size > 0:
                self.height, self.width = temp_image.shape[:2]
            else:
                raise Exception("无法获取VNC屏幕分辨率")
        except Exception as e:
            print(f"❌ 获取VNC分辨率失败: {e}")
            # 使用默认分辨率
            self.width = 1024
            self.height = 768
            print(f"使用默认分辨率: {self.width}x{self.height}")
        
        # 设置hwnd（为了兼容，但VNC不使用hwnd）
        self.set_hwnd(hwnd)
        
        # 初始化后台截图线程
        self.t_for_capture = None
        self._t_for_capture = None
        self.image = None
        self.for_capture()
        
        # 等待第一帧截图完成
        while True:
            time.sleep(0.01)
            if not getattr(self, "image", None) is None:
                break

    def __del__(self):
        """清理VNC资源（析构函数，确保资源释放）"""
        import sys
        # 🔧 降低日志级别：只在 DEBUG 模式显示，避免刷屏
        logging.debug(f"VNC.__del__() 被调用！对象 ID={id(self)}, IP:Port={self.ip}:{self.port}")
        logging.debug(f"   - 引用计数: {sys.getrefcount(self)}")
        
        # 检查 client 状态
        if hasattr(self, 'client'):
            client_status = self.client
            logging.debug(f"   - client 当前值: {client_status}")
        else:
            logging.debug(f"   - client 属性不存在")
        
        try:
            # 调用stop方法进行清理
            self.stop()
        except Exception as e:
            # 析构函数中不应该抛出异常
            pass

    def set_hwnd(self, hwnd):
        """
        设置窗口句柄（VNC不需要，但为了兼容DXGI接口保留）
        
        Args:
            hwnd: 窗口句柄，VNC中会被忽略
        """
        if hwnd is None:
            self.hwnd = self.hwnd_desktop
        else:
            self.hwnd = hwnd
        # VNC使用自己的分辨率，不从窗口获取
        # self.width, self.height 已经在初始化时从VNC获取

    def _capture_raw_via_file(self):
        """
        通过 captureScreen 写临时 PNG 再 imread（最稳，但磁盘与解码开销大）。
        """
        import tempfile

        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_file = tmp.name

            try:
                self.client.captureScreen(temp_file)
            except Exception:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                raise

            max_wait_time = 3.0
            wait_interval = 0.1
            waited_time = 0.0
            file_size = -1
            stable_count = 0
            stable_threshold = 2

            while waited_time < max_wait_time:
                if os.path.exists(temp_file):
                    current_size = os.path.getsize(temp_file)
                    if current_size > 0:
                        if current_size == file_size:
                            stable_count += 1
                            if stable_count >= stable_threshold:
                                break
                        else:
                            stable_count = 0
                        file_size = current_size
                time.sleep(wait_interval)
                waited_time += wait_interval

            if not os.path.exists(temp_file):
                raise ValueError(f"临时文件不存在: {temp_file}")

            final_size = os.path.getsize(temp_file)
            if final_size == 0:
                raise ValueError(f"临时文件为空: {temp_file}")
            if final_size < 100:
                raise ValueError(f"临时文件大小异常: {temp_file}")

            image = cv2.imread(temp_file)
            try:
                os.remove(temp_file)
            except Exception:
                pass

            if image is not None and image.size > 0:
                return image
            raise ValueError("无法读取临时文件中的图像")

        except Exception:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise

    def _capture_raw_via_memory(self):
        """
        refreshScreen + 内存像素，无磁盘；稳定后优先增量刷新与短延迟，适合后台高频率抓帧。
        """
        last_exc = None
        # 已有成功帧时先尝试增量（快），失败再全量；首连先全量再增量
        if self._vnc_incremental_ready:
            orders = [(1, self._mem_delay_inc), (0, self._mem_delay_full)]
        else:
            orders = [(0, self._mem_delay_full), (1, self._mem_delay_inc_cold)]

        for inc, delay in orders:
            try:
                self.client.refreshScreen(inc)
                time.sleep(delay)
                if not hasattr(self.client, "screen") or self.client.screen is None:
                    raise ValueError("无法获取屏幕数据")
                screen_array = np.asarray(self.client.screen)
                if screen_array.size == 0:
                    raise ValueError("屏幕数据为空数组")
                h, w = screen_array.shape[:2] if screen_array.ndim >= 2 else (0, 0)
                if h == 0 or w == 0:
                    raise ValueError("屏幕尺寸无效")
                bgr = cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
                if bgr is None or bgr.size == 0:
                    raise ValueError("BGR 转换失败")
                self._vnc_incremental_ready = True
                return bgr
            except Exception as e:
                last_exc = e
                continue

        raise last_exc if last_exc else RuntimeError("内存截图失败")

    def _capture_raw(self, *, initial=False):
        """
        原始截图，返回 BGR numpy。

        - initial=True：初始化/重连后首帧，优先临时文件保证成功率。
        - 默认：优先内存路径；失败则回退文件（除非 VNC_CAPTURE=memory 禁止回退）。
        """
        if initial:
            try:
                return self._capture_raw_via_file()
            except Exception:
                return self._capture_raw_via_memory()

        if self._vnc_capture_file_only:
            return self._capture_raw_via_file()

        if self._vnc_capture_memory_only:
            return self._capture_raw_via_memory()

        try:
            return self._capture_raw_via_memory()
        except Exception as e:
            logging.debug("VNC 内存截图失败，回退临时文件: %s", e)
            self._vnc_incremental_ready = False
            return self._capture_raw_via_file()

    def _capture(self):
        """
        内部截图方法，返回numpy数组（BGR格式）
        
        Returns:
            numpy数组（BGR格式，shape: (height, width, 3)）
        """
        s = time.time()
        with self._capture_lock:
            frame = None
            try:
                frame = self._capture_raw()
            except Exception as e:
                if time.time() - s > self.error_max_refresh:
                    raise Exception(f"VNC截图超时: {e}")
                return None
            
            if frame is None:
                return None
            
            # frame是BGR格式的numpy数组 (height, width, 3)
            h, w = frame.shape[:2]
            if h == 0 or w == 0:
                raise Exception("VNC截图失败,截图为空")
            
            # 更新分辨率（如果变化）
            if self.height != h or self.width != w:
                self.height = h
                self.width = w
            
            return frame

    def for_capture(self):
        """
        启动后台截图线程（增强版：带健康检查和自动重连）
        """
        if self.t_for_capture is None:
            self.t_for_capture = threading.Thread(target=self._capture_loop, daemon=True)
            self.t_for_capture.start()

    def _capture_loop(self):
        """
        后台抓帧循环。
        🔧 稳定性优化：增加指数退避机制，防止 VNC 断开后持续重试导致资源耗尽
        
        健康检查失败或连续失败时，在独立线程中执行 _reconnect_impl，
        避免在原截图线程内 join 自身造成死锁；并避免 Thread(target=self.for_capture) 导致子线程无法进入内层循环的问题。
        """
        import gc  # 🔧 引入垃圾回收模块
        
        self._t_for_capture = True
        health_check_interval = 60
        last_health_check = time.time()
        
        # 🔧 关键修复：增加最大空闲时间检测（3分钟），防止长时间卡死后崩溃
        max_idle_time_before_crash = 180  # 3分钟
        
        # 🔧 稳定性优化：指数退避机制
        consecutive_failures = 0  # 连续失败次数
        max_retries = 100  # 最大重试次数
        base_wait_time = 0.5  # 基础等待时间（秒）
        max_wait_time = 30  # 最大等待时间（秒）
                        
        # 🔧 稳定性优化：定期垃圾回收
        last_gc_time = time.time()
        gc_interval = 300  # 每 5 分钟执行一次垃圾回收
                        
        # 🔧 性能监控：记录截图调用
        from app.stability_optimizer import vnc_performance_monitor

        while self._t_for_capture:
            s = time.time()

            current_time = time.time()
            
            # 🔧 关键修复：检测是否超过最大空闲时间，如果是则主动退出并触发重连
            if current_time - self.last_success_time > max_idle_time_before_crash:
                logging.error(f"⚠️ VNC 超过 {max_idle_time_before_crash} 秒未成功截图，主动退出以避免崩溃")
                self._t_for_capture = False
                threading.Thread(target=self._reconnect_impl, daemon=True).start()
                break
            
            if (self.total_screenshots > 0 and self.total_screenshots % 100 == 0) or \
               (current_time - self.last_success_time > self.max_idle_time) or \
               (current_time - last_health_check > health_check_interval):
                if not self._check_connection_health():
                    logging.warning("VNC 连接健康检查失败，尝试重连...")
                    self._t_for_capture = False
                    threading.Thread(target=self._reconnect_impl, daemon=True).start()
                    break
                last_health_check = current_time

            try:
                # 🔧 稳定性优化：在更新 image 前，先释放旧对象，避免内存累积
                old_image = self.image
                if old_image is not None:
                    # 显式删除旧的图像对象，释放内存
                    try:
                        del old_image
                    except:
                        pass
                
                self.image = self._capture()
                # 🔧 成功截图后重置失败计数
                consecutive_failures = 0
                self.consecutive_errors = 0
                self.total_screenshots += 1
                self.last_success_time = time.time()
                
                # 🔧 性能监控：记录成功截图
                vnc_performance_monitor.record_screenshot(success=True)
            except Exception as e:
                if self._t_for_capture:
                    consecutive_failures += 1
                    self.consecutive_errors += 1

                    # 🔧 稳定性优化：指数退避策略
                    if consecutive_failures > 10:
                        # 计算等待时间：指数增长，但不超过最大值
                        wait_time = min(max_wait_time, base_wait_time * (2 ** (consecutive_failures - 10)))
                        logging.warning(
                            f"⚠️ [VNC] 连续失败 {consecutive_failures} 次，"
                            f"等待 {wait_time:.1f} 秒后重试（避免资源耗尽）"
                        )
                        time.sleep(wait_time)
                        
                        # 检查是否达到最大重试次数
                        if consecutive_failures >= max_retries:
                            logging.error(
                                f"❌ [VNC] 连续失败 {max_retries} 次，停止截图并尝试重连..."
                            )
                            self._t_for_capture = False
                            threading.Thread(target=self._reconnect_impl, daemon=True).start()
                            break
                    else:
                        # 前 10 次失败，使用原有逻辑
                        if consecutive_failures <= 3 or consecutive_failures % 10 == 0:
                            logging.warning(
                                f"VNC 截图错误 ({self.consecutive_errors}/{self.error_max_refresh}): {e}"
                            )

                        error_msg = str(e).lower()
                        if "timeout" in error_msg or "refused" in error_msg or "closed" in error_msg:
                            if consecutive_failures == 1:
                                print(f"⚠️ VNC 连接中断！请检查：")
                                print(f"   1. 模拟器是否正在运行")
                                print(f"   2. VNC 服务是否启动（端口：{self.port}）")
                                print(f"   3. 防火墙是否阻止连接")
                                print(f"   4. 尝试重启模拟器")

                        if self.consecutive_errors >= self.error_max_refresh:
                            logging.error("VNC 连续截图失败过多，暂停 5 秒并尝试重连...")
                            time.sleep(5)
                            self.consecutive_errors = 0
                            self._t_for_capture = False
                            
                            # 🔧 性能监控：记录超时截图
                            vnc_performance_monitor.record_screenshot(success=False, is_timeout=True)
                            
                            threading.Thread(target=self._reconnect_impl, daemon=True).start()
                            break

                self.image = None
                
                # 🔧 性能监控：记录失败截图（非超时）
                if consecutive_failures > 0:
                    vnc_performance_monitor.record_screenshot(success=False)

            if not self._t_for_capture:
                break

            if self._fps and self._fps > 0:
                delay = 1 / self._fps - (time.time() - s)
                if delay > 0:
                    time.sleep(delay)
            else:
                time.sleep(0.01)
            
            # 🔧 稳定性优化：定期执行垃圾回收，防止内存泄漏
            current_time = time.time()
            if current_time - last_gc_time > gc_interval:
                try:
                    collected = gc.collect()
                    if collected > 0:
                        logging.debug(f"[VNC] 垃圾回收完成，释放 {collected} 个对象")
                    last_gc_time = current_time
                except Exception as gc_error:
                    logging.warning(f"[VNC] 垃圾回收失败: {gc_error}")

    def _check_connection_health(self):
        """
        检查 VNC 连接健康状态
            
        Returns:
            bool: 连接是否健康
        """
        try:
            # 检查客户端是否存在且有效
            if not hasattr(self, 'client') or self.client is None:
                return False
                
            # 简单测试：尝试获取屏幕数据
            if hasattr(self.client, 'screen') and self.client.screen is not None:
                return True
                
            return True  # 默认认为健康
        except Exception as e:
            logging.debug(f"VNC 健康检查失败：{e}")
            return False
        
    def _reconnect_impl(self):
        """
        在独立线程中执行：等待旧截图线程结束、断开并重连、再 for_capture。
        必须由 _capture_loop 在设置 _t_for_capture=False 并退出后通过新线程调用，不可在截图线程内同步 join 自身。
        """
        with self._reconnect_lock:
            self._reconnect_impl_locked()

    def _reconnect_impl_locked(self):
        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                logging.info(f"VNC 尝试重连 ({attempt + 1}/{max_retries})...")

                t = self.t_for_capture
                if t is not None and t.is_alive():
                    t.join(timeout=3.0)
                self.t_for_capture = None

                if hasattr(self, 'client') and self.client is not None:
                    try:
                        def disconnect_thread():
                            try:
                                self.client.disconnect()
                            except Exception:
                                pass

                        disconnect_t = threading.Thread(target=disconnect_thread, daemon=True)
                        disconnect_t.start()
                        disconnect_t.join(timeout=1.0)
                    except Exception:
                        pass

                time.sleep(1)

                vnc_address = f"{self.ip}::{self.port}"
                self.client = api.connect(vnc_address, self.password, timeout=60)
                print("VNC重连成功！")
                
                # 🔧 性能监控：记录 VNC 重连
                vnc_performance_monitor.record_vnc_reconnect(
                    row=None,  # VNC 内部不知道 Row，由外部调用时记录
                    reason="自动重连"
                )

                time.sleep(2)

                self._vnc_incremental_ready = False
                temp_image = self._capture_raw(initial=True)
                if temp_image is not None and temp_image.size > 0:
                    self.height, self.width = temp_image.shape[:2]

                self.for_capture()

                wait_start = time.time()
                while self.image is None and (time.time() - wait_start) < 10:
                    time.sleep(0.1)

                if self.image is not None:
                    logging.info("VNC 重连成功！")
                    return
                logging.warning("VNC 重连后截图仍为空")

            except Exception as e:
                logging.error(f"VNC 重连失败 ({attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        logging.error("VNC 重连彻底失败，需要手动干预")

    def Capture(self, x1: int = None, y1: int = None, x2: int = None, y2: int = None):
        """
        截图方法，兼容DXGI接口
        
        Args:
            x1: 左上角x坐标，None表示0
            y1: 左上角y坐标，None表示0
            x2: 右下角x坐标，None表示width
            y2: 右下角y坐标，None表示height
        
        Returns:
            dxpyd.ManagedMemoryView（BGR格式），如果指定了区域则返回裁剪后的图像
        """
        # 🔧 关键修复：检查是否正在停止或重连
        if not getattr(self, '_t_for_capture', True):
            raise Exception("VNC正在停止或重连中，拒绝截图")
        
        # 🔧 关键修复：在访问 self.image 前验证 VNC 连接状态
        if not hasattr(self, 'client') or self.client is None:
            raise Exception("VNC客户端未初始化或已断开")
        
        # 参数处理
        if x1 is None or x1 < 0:
            x1 = 0
        if y1 is None or y1 < 0:
            y1 = 0
        if x2 is None or x2 > self.width:
            x2 = self.width
        if y2 is None or y2 > self.height:
            y2 = self.height
        
        # 调试信息（仅在测试时打印）
        if __name__ == '__main__':
            print(f"  [DEBUG] 裁剪参数: x1={x1}, y1={y1}, x2={x2}, y2={y2}, 原始尺寸: {self.width}x{self.height}")
        
        # 获取当前截图
        image = self.image
        if image is None:
            raise Exception("VNC截图未就绪，请稍后再试")
        
        # 统一处理：先转换为numpy数组，然后裁剪，最后转换为ManagedMemoryView
        # 这样可以避免类型判断的复杂性，确保数据正确
        try:
            # 🔧 关键修复：使用 try-except 包裹所有可能触发访问违规的操作
            # 转换为numpy数组
            if isinstance(image, np.ndarray):
                image_np = image
            else:
                # 对于其他类型（如_memoryviewslice），转换为numpy数组
                # 🔧 这里可能触发 0xC0000005，需要异常保护
                try:
                    image_np = np.asarray(image)
                except (ValueError, TypeError, SystemError) as e:
                    logging.error(f"VNC 图像转换失败（可能已损坏）: {e}")
                    # 标记 image 为 None，触发重连
                    self.image = None
                    raise Exception(f"VNC图像数据损坏，需要重新连接: {e}")
            
            # 进行裁剪
            image_cropped = image_np[y1:y2, x1:x2]
            
            # 🔧 稳定性优化：显式释放原始图像引用，避免内存累积
            if image is not image_np:  # 如果创建了新的 numpy 数组
                del image
            if image_np is not image_cropped:  # 如果进行了裁剪
                del image_np
            
            # 调试信息
            if __name__ == '__main__':
                print(f"  [DEBUG] 裁剪后尺寸: {image_cropped.shape}")
                print(f"  [DEBUG] 裁剪后数据类型: {image_cropped.dtype}, 形状: {image_cropped.shape}")
            
            # 确保数组是连续的（C顺序）并且数据类型正确
            if not image_cropped.flags['C_CONTIGUOUS']:
                image_cropped = np.ascontiguousarray(image_cropped)
            
            # 确保数据类型是uint8
            if image_cropped.dtype != np.uint8:
                image_cropped = image_cropped.astype(np.uint8)
            
            # 获取图像尺寸
            h, w = image_cropped.shape[:2]
            
            # 验证数据有效性
            if h == 0 or w == 0:
                raise ValueError(f"裁剪后图像尺寸无效: {h}x{w}")
            
            # 将numpy数组转换为字节数据，然后创建ManagedMemoryView
            image_bytes = image_cropped.tobytes()
            expected_size = h * w * 3
            if len(image_bytes) != expected_size:
                raise ValueError(f"字节数据大小不匹配: 期望{expected_size}，实际{len(image_bytes)}")
            
            # 🔧 关键修复：使用 try-except 包裹 ManagedMemoryView 创建
            # 如果 image_bytes 是空指针或损坏的数据，这里会触发 0xC0000005
            try:
                # 使用ManagedMemoryView构造函数创建正确的类型（而不是bytes_to_arr3d）
                # dtype=0 表示 uint8
                image = dxpyd.ManagedMemoryView(shape=(h, w, 3), dtype=0, bytes_data=image_bytes)
            except (OSError, WindowsError, SystemError) as e:
                # 🔧 捕获 Windows API 访问违规（0xC0000005）
                logging.error(f"⚠️ VNC ManagedMemoryView 创建失败 (可能是访问违规): {e}")
                logging.error(f"   图像信息: shape=({h}, {w}, 3), bytes_size={len(image_bytes)}")
                # 标记 image 为 None，触发重连
                self.image = None
                raise Exception(f"VNC内存分配失败，可能连接已断开: {e}")
            
        except Exception as e:
            if __name__ == '__main__':
                print(f"  [DEBUG] 转换过程出错: {e}")
                import traceback
                traceback.print_exc()
            # 🔧 记录详细错误日志，帮助诊断
            logging.error(f"VNC Capture 失败: {type(e).__name__}: {e}")
            raise
        
        return image

    def stop(self):
        """
        停止VNC截图线程并断开连接
        确保资源正确释放，避免阻塞
        """
        # 🔧 关键修复：先设置停止标志，阻止新的 Capture 调用
        self._t_for_capture = False
        
        # 🔍 诊断日志：记录谁调用了 stop()（仅在 DEBUG 模式）
        import traceback
        caller_info = traceback.extract_stack()[-2]  # 获取调用者信息
        logging.debug(f"VNC.stop() 被调用！")
        logging.debug(f"   - 调用文件: {caller_info.filename}")
        logging.debug(f"   - 调用行号: {caller_info.lineno}")
        logging.debug(f"   - 调用函数: {caller_info.name}")
        logging.debug(f"   - 代码内容: {caller_info.line}")
        logging.debug(f"   - VNC 对象 ID: {id(self)}")
        logging.debug(f"   - IP:Port: {self.ip}:{self.port}")
        
        # 1. 停止截图线程
        if self._t_for_capture is not None:
            self._t_for_capture = False  # 设置标志位，让线程自然退出
            if self.t_for_capture is not None and self.t_for_capture.is_alive():
                # 等待线程结束，最多等待2秒
                self.t_for_capture.join(timeout=2.0)
                if self.t_for_capture.is_alive():
                    logging.warning("VNC截图线程未能在2秒内结束")
            self.t_for_capture = None
        
        # 2. 断开VNC连接（使用超时避免阻塞）
        if hasattr(self, 'client') and self.client is not None:
            try:
                # 在单独的线程中执行disconnect，避免阻塞
                def disconnect_thread():
                    try:
                        self.client.disconnect()
                    except Exception as e:
                        logging.debug(f"VNC断开连接时出错: {e}")
                
                disconnect_t = threading.Thread(target=disconnect_thread, daemon=True)
                disconnect_t.start()
                disconnect_t.join(timeout=1.0)  # 最多等待1秒
                if disconnect_t.is_alive():
                    logging.warning("VNC断开连接超时，但不会阻塞主线程")
            except Exception as e:
                logging.debug(f"断开VNC连接时出错: {e}")
        
        # 3. 清理引用
        self.image = None
        self.client = None
    
    def get_status(self) -> dict:
        """
        获取 VNC 状态信息
        
        Returns:
            dict: 包含 VNC 各项状态信息
            {
                'connected': bool,      # 是否已连接
                'has_image': bool,      # 是否有截图数据
                'resolution': str,      # 分辨率
                'total_screenshots': int,  # 总截图次数
                'consecutive_errors': int,  # 连续错误次数
                'status': str           # 状态描述：healthy/degraded/failed
            }
        """
        # 判断连接状态
        connected = hasattr(self, 'client') and self.client is not None
        
        # 判断是否有截图数据
        has_image = hasattr(self, 'image') and self.image is not None
        
        # 计算状态
        if not connected:
            status = 'failed'
        elif not has_image:
            status = 'degraded'
        elif self.consecutive_errors > 5:
            status = 'degraded'
        else:
            status = 'healthy'
        
        return {
            'connected': connected,
            'has_image': has_image,
            'resolution': f"{self.width}x{self.height}" if hasattr(self, 'width') else 'unknown',
            'total_screenshots': getattr(self, 'total_screenshots', 0),
            'consecutive_errors': getattr(self, 'consecutive_errors', 0),
            'status': status
        }
    
    def print_status(self):
        """打印 VNC 状态信息"""
        status = self.get_status()
        print("\n" + "="*60)
        print("VNC 状态信息")
        print("="*60)
        print(f"  连接状态：{'✓ 已连接' if status['connected'] else '❌ 未连接'}")
        print(f"  截图数据：{'✓ 正常' if status['has_image'] else '❌ 为空'}")
        print(f"  分辨率：{status['resolution']}")
        print(f"  总截图次数：{status['total_screenshots']}")
        print(f"  连续错误：{status['consecutive_errors']}")
        print(f"  整体状态：{status['status'].upper()}")
        print("="*60)


if __name__ == '__main__':
    # 测试代码
    try:
        print("=" * 60)
        print("VNC截图测试（兼容DXGI接口）")
        print("=" * 60)
        
        # 创建VNC截图对象
        vnc = VNC("127.0.0.1", "5600", "")
        
        print(f"VNC分辨率: {vnc.width}x{vnc.height}")
        
        # 测试全屏截图
        print("\n测试全屏截图...")
        
        # 首先验证原始截图数据（self.image）
        print("验证原始截图数据...")
        raw_image = vnc.image
        if raw_image is not None:
            print(f"  原始图像类型: {type(raw_image)}")
            if isinstance(raw_image, np.ndarray):
                print(f"  原始图像形状: {raw_image.shape}, dtype: {raw_image.dtype}")
                print(f"  原始图像数据范围: [{raw_image.min()}, {raw_image.max()}]")
            else:
                print(f"  原始图像不是numpy数组")
        else:
            print("  警告: 原始图像为None")
        
        image = vnc.capture()
        print(f"截图尺寸: {image.shape}")
        print(f"图像类型: {type(image)}")
        print(f"是否有get_memoryview方法: {hasattr(image, 'get_memoryview')}")
        if hasattr(image, 'dtype'):
            print(f"数据类型: {image.dtype}")
        
        # 测试区域截图
        print("\n测试区域截图...")
        region_x1, region_y1, region_x2, region_y2 = 100, 100, 500, 400
        print(f"区域参数: x1={region_x1}, y1={region_y1}, x2={region_x2}, y2={region_y2}")
        image_region = vnc.capture(region_x1, region_y1, region_x2, region_y2)
        print(f"区域截图尺寸: {image_region.shape}")
        print(f"区域图像类型: {type(image_region)}")
        
        # 显示截图（需要GUI环境和MiniOpenCV）
        try:
            from dxGame import MiniOpenCV
            print("\n显示截图窗口...")
            MiniOpenCV.imshow("VNC全屏截图", image)
            MiniOpenCV.imshow("VNC区域截图", image_region)
            print("按任意键退出...")
            MiniOpenCV.waitKey(0)
        except Exception as e:
            print(f"⚠ 无法显示图像窗口（这通常是正常的，可能是因为没有GUI环境）: {type(e).__name__}")
            # 尝试保存图像到文件作为替代
            try:
                # 将ManagedMemoryView/dxpyd._memoryviewslice转换为numpy数组
                print(f"\n转换图像类型: {type(image).__name__}")
                try:
                    # 方法1: 尝试直接使用np.array或np.asarray
                    img_np = np.asarray(image, dtype=np.uint8)
                    img_region_np = np.asarray(image_region, dtype=np.uint8)
                    print(f"✓ 使用np.asarray转换成功")
                    print(f"  转换后形状: {img_np.shape}, {img_region_np.shape}")
                    print(f"  转换后dtype: {img_np.dtype}, {img_region_np.dtype}")
                    # 验证数据是否有效
                    if img_np.size == 0 or img_region_np.size == 0:
                        raise ValueError("转换后的数组为空")
                    print(f"  转换后数据大小: {img_np.size}, {img_region_np.size}")
                except Exception as e1:
                    print(f"⚠ np.asarray转换失败: {e1}")
                    try:
                        # 方法2: 使用get_memoryview方法
                        if hasattr(image, 'get_memoryview'):
                            mv = image.get_memoryview()
                            img_np = np.array(mv)
                            mv_region = image_region.get_memoryview()
                            img_region_np = np.array(mv_region)
                            print(f"✓ 使用get_memoryview()转换成功")
                        else:
                            raise ValueError("对象没有get_memoryview方法")
                    except Exception as e2:
                        print(f"⚠ get_memoryview()转换失败: {e2}")
                        # 方法3: 尝试使用copy方法
                        try:
                            img_np = np.array(image, copy=True)
                            img_region_np = np.array(image_region, copy=True)
                            print(f"✓ 使用np.array(copy=True)转换成功")
                        except Exception as e3:
                            print(f"❌ 所有转换方法都失败: {e3}")
                            raise
                
                # 确保数组是可写的（copy if read-only）
                if not img_np.flags.writeable:
                    img_np = img_np.copy()
                if not img_region_np.flags.writeable:
                    img_region_np = img_region_np.copy()
                
                # 验证图像数据（简化验证，避免计算min/max时出错）
                print(f"\n保存前验证:")
                try:
                    print(f"  全屏图像 - 形状: {img_np.shape}, 数据类型: {img_np.dtype}, 大小: {img_np.size}, 可写: {img_np.flags.writeable}")
                    # 只检查第一个像素和最后一个像素，不计算全部min/max
                    if img_np.size > 0:
                        first_pixel = img_np.flat[0]
                        last_pixel = img_np.flat[-1]
                        print(f"    首像素: {first_pixel}, 末像素: {last_pixel}")
                except Exception as verify_err1:
                    print(f"⚠ 验证全屏图像数据时出错: {verify_err1}")
                    import traceback
                    traceback.print_exc()
                
                try:
                    print(f"  区域图像 - 形状: {img_region_np.shape}, 数据类型: {img_region_np.dtype}, 大小: {img_region_np.size}, 可写: {img_region_np.flags.writeable}")
                    # 只检查第一个像素和最后一个像素，不计算全部min/max
                    if img_region_np.size > 0:
                        first_pixel = img_region_np.flat[0]
                        last_pixel = img_region_np.flat[-1]
                        print(f"    首像素: {first_pixel}, 末像素: {last_pixel}")
                except Exception as verify_err2:
                    print(f"⚠ 验证区域图像数据时出错: {verify_err2}")
                    import traceback
                    traceback.print_exc()
                
                # 保存图像前，验证图像数据有效性
                print(f"\n保存图像前验证:")
                try:
                    # 检查图像数组是否是有效的numpy数组
                    assert isinstance(img_np, np.ndarray), f"全屏图像不是numpy数组: {type(img_np)}"
                    assert isinstance(img_region_np, np.ndarray), f"区域图像不是numpy数组: {type(img_region_np)}"
                    assert len(img_np.shape) == 3, f"全屏图像维度错误: {img_np.shape}"
                    assert len(img_region_np.shape) == 3, f"区域图像维度错误: {img_region_np.shape}"
                    assert img_np.shape[2] == 3, f"全屏图像通道数错误: {img_np.shape[2]}"
                    assert img_region_np.shape[2] == 3, f"区域图像通道数错误: {img_region_np.shape[2]}"
                    assert img_np.dtype == np.uint8, f"全屏图像数据类型错误: {img_np.dtype}"
                    assert img_region_np.dtype == np.uint8, f"区域图像数据类型错误: {img_region_np.dtype}"
                    print(f"  ✓ 图像数据格式验证通过")
                except AssertionError as e:
                    print(f"  ❌ 图像数据验证失败: {e}")
                    raise
                
                # 保存图像
                import os
                file1 = "vnc_fullscreen_test.png"
                file2 = "vnc_region_test.png"
                file3 = "vnc_raw_test.png"  # 直接保存原始截图
                
                # 先尝试直接保存原始截图（绕过capture方法的转换）
                print(f"\n【测试1】直接保存原始截图...")
                try:
                    raw_img = vnc.image
                    if raw_img is not None and isinstance(raw_img, np.ndarray):
                        raw_img_np = raw_img.copy()
                        if raw_img_np.dtype != np.uint8:
                            raw_img_np = raw_img_np.astype(np.uint8)
                        success_raw = cv2.imwrite(file3, raw_img_np)
                        if success_raw:
                            size_raw = os.path.getsize(file3) if os.path.exists(file3) else 0
                            print(f"  ✓ 原始截图保存成功，文件大小: {size_raw} 字节")
                            if size_raw < 1000:
                                print(f"  ⚠ 警告: 原始截图文件大小异常小")
                        else:
                            print(f"  ❌ 原始截图保存失败")
                    else:
                        print(f"  ⚠ 原始截图不是numpy数组，跳过")
                except Exception as e:
                    print(f"  ❌ 保存原始截图时出错: {e}")
                
                print(f"\n【测试2】保存通过capture方法获取的图像...")
                print(f"  保存全屏图像到: {file1}")
                success1 = False
                try:
                    # 确保图像数据是连续的内存布局
                    if not img_np.flags['C_CONTIGUOUS']:
                        print(f"    警告: 图像数据不连续，正在复制...")
                        img_np = np.ascontiguousarray(img_np)
                    
                    success1 = cv2.imwrite(file1, img_np)
                    if success1:
                        # 等待一下确保文件写入完成
                        import time
                        time.sleep(0.1)
                        size1 = os.path.getsize(file1) if os.path.exists(file1) else 0
                        print(f"    ✓ cv2.imwrite返回成功，文件大小: {size1} 字节")
                        if size1 < 1000:
                            print(f"    ❌ 警告: 文件大小异常小（只有{size1}字节），保存可能失败")
                            success1 = False
                    else:
                        print(f"    ❌ cv2.imwrite返回False，保存失败")
                except Exception as e:
                    print(f"    ❌ 保存时发生异常: {e}")
                    import traceback
                    traceback.print_exc()
                    success1 = False
                
                print(f"  保存区域图像到: {file2}")
                success2 = False
                try:
                    # 确保图像数据是连续的内存布局
                    if not img_region_np.flags['C_CONTIGUOUS']:
                        print(f"    警告: 图像数据不连续，正在复制...")
                        img_region_np = np.ascontiguousarray(img_region_np)
                    
                    success2 = cv2.imwrite(file2, img_region_np)
                    if success2:
                        # 等待一下确保文件写入完成
                        import time
                        time.sleep(0.1)
                        size2 = os.path.getsize(file2) if os.path.exists(file2) else 0
                        print(f"    ✓ cv2.imwrite返回成功，文件大小: {size2} 字节")
                        if size2 < 1000:
                            print(f"    ❌ 警告: 文件大小异常小（只有{size2}字节），保存可能失败")
                            success2 = False
                    else:
                        print(f"    ❌ cv2.imwrite返回False，保存失败")
                except Exception as e:
                    print(f"    ❌ 保存时发生异常: {e}")
                    import traceback
                    traceback.print_exc()
                    success2 = False
                
                if success1 and success2:
                    size1 = os.path.getsize(file1) if os.path.exists(file1) else 0
                    size2 = os.path.getsize(file2) if os.path.exists(file2) else 0
                    if size1 >= 1000 and size2 >= 1000:
                        print(f"\n✓ 已成功保存测试图像到文件")
                    else:
                        print(f"\n⚠ 文件已保存，但大小异常，请检查图像数据")
                else:
                    print(f"\n⚠ 部分图像保存失败")
                    if not success1:
                        print(f"  全屏图像保存失败，可能的原因: 图像数据异常、路径权限问题等")
                    if not success2:
                        print(f"  区域图像保存失败")
            except Exception as save_err:
                print(f"⚠ 保存图像也失败: {save_err}")
                import traceback
                traceback.print_exc()
        
        vnc.stop()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
