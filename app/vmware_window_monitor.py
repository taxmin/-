


# -*- coding: utf-8 -*-
"""
VMware 窗口监控守护线程
定期检测所有虚拟机窗口是否卡住，并自动激活恢复
"""
import threading
import time
import logging

from dxGame.dx_Window import Window
from dxGame.dx_model import gl_info, td_info
from public import MS

logger = logging.getLogger(__name__)

# 🔧 全局窗口恢复状态标记 {row: timestamp}
# 用于防止任务线程在窗口恢复期间执行 KM 操作
_window_recovering = {}

# 🔧 全局 KM 操作锁（默认兜底）
_km_operation_lock = threading.Lock()
# 🔧 按实例粒度的 KM 锁：key 一般用 row/编号；不同 key 可并行，降低多开互相阻塞
_km_operation_lock_by_key = {}
_km_operation_lock_guard = threading.Lock()

# 导出锁供其他模块使用
def get_km_lock(key=None):
    """
    获取 KM 操作锁。
    - key 为 None：返回全局锁（兼容旧调用）
    - key 非 None：返回该 key 对应的实例锁（不同 key 间可并行）
    """
    if key is None:
        return _km_operation_lock
    with _km_operation_lock_guard:
        lock = _km_operation_lock_by_key.get(key)
        if lock is None:
            lock = threading.Lock()
            _km_operation_lock_by_key[key] = lock
        return lock


def _physical_mouse_click(hwnd, x1=191, y1=229, x2=739, y2=561):
    """
    使用物理鼠标点击窗口指定区域（用于激活 VMware 虚拟机窗口）
    
    Args:
        hwnd: 窗口句柄
        x1, y1, x2, y2: 随机点击区域范围（默认 191,229,739,561）
        
    Returns:
        bool: 是否成功点击
    """
    try:
        import random
        import ctypes.wintypes
        
        # 🔧 检查窗口是否有效
        if not ctypes.windll.user32.IsWindow(hwnd):
            logger.warning(f"⚠️ 窗口句柄 {hwnd} 已失效，无法执行物理点击")
            return False
        
        # 获取窗口位置
        rect = ctypes.wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            logger.error(f"❌ 获取窗口位置失败: {ctypes.get_last_error()}")
            return False
        
        # 计算窗口左上角坐标
        window_left = rect.left
        window_top = rect.top
        
        # 生成随机点击坐标（相对于窗口客户区）
        click_x_relative = random.randint(x1, x2)
        click_y_relative = random.randint(y1, y2)
        
        # 转换为屏幕绝对坐标
        screen_x = window_left + click_x_relative
        screen_y = window_top + click_y_relative
        
        logger.info(f"🖱️ 准备物理点击: 窗口({window_left},{window_top}) + 相对({click_x_relative},{click_y_relative}) = 屏幕({screen_x},{screen_y})")
        
        # 🔧 保存当前鼠标位置
        current_pos = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(current_pos))
        original_x, original_y = current_pos.x, current_pos.y
        
        # 🔧 移动鼠标到目标位置
        if not ctypes.windll.user32.SetCursorPos(screen_x, screen_y):
            logger.error(f"❌ SetCursorPos 失败")
            return False
        
        # 短暂延迟，确保鼠标移动到位
        time.sleep(0.05)
        
        # 🔧 模拟鼠标左键点击（使用 mouse_event）
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)  # 按下延迟
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        logger.info(f"✓ 物理点击完成: ({screen_x}, {screen_y})")
        
        # 🔧 恢复鼠标原位置（可选，避免干扰用户操作）
        time.sleep(0.1)
        ctypes.windll.user32.SetCursorPos(original_x, original_y)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 物理鼠标点击异常: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def is_window_recovering(row):
    """
    检查指定行的窗口是否正在恢复中
    
    Args:
        row: 行号
    
    Returns:
        bool: True=正在恢复，False=未恢复
    """
    if row not in _window_recovering:
        return False
    
    # 如果超过 30 秒还在恢复标记中，认为异常，清除标记
    if time.time() - _window_recovering[row] > 30:
        _window_recovering.pop(row, None)
        logger.warning(f"[Row:{row}] ⚠️ 窗口恢复标记超时，已清除")
        return False
    
    return True


def _get_vmware_ports():
    """
    从配置中获取所有 VMware 端口号
    
    Returns:
        list: 端口号列表，如 ["5600", "5601"]
    """
    ports = []
    
    # 尝试从 controller 获取活动行信息
    controller = getattr(gl_info, "controller", None)
    if controller is None:
        return ports
    
    tc = getattr(controller, "线程控制器", None)
    if tc is None:
        return ports
    
    thread_dict = getattr(tc, "_thread_dict", None)
    if not isinstance(thread_dict, dict):
        return ports
    
    # 遍历所有活动的行
    for row in thread_dict.keys():
        th = thread_dict[row]
        if th is not None and th.is_alive():
            # 尝试从 td_info 获取端口号（通常是 row + 5600）
            try:
                port = str(5600 + row)
                ports.append((row, port))
            except Exception as e:
                logger.debug(f"获取行 {row} 的端口号失败: {e}")
    
    return ports


def _check_and_recover_window(row, port):
    """
    检查并恢复指定端口的窗口（使用真实游戏窗口句柄）
    
    Args:
        row: 行号
        port: 端口号字符串
        
    Returns:
        bool: 是否执行了恢复操作
    """
    try:
        # 1. 查找真实游戏窗口句柄（多层级查找）
        real_hwnd = Window.FindVMwareRealWindowByPort(port)
        
        if not real_hwnd:
            logger.warning(f"[Row:{row}] 未找到端口 {port} 的真实游戏窗口")
            return False
        
        # 2. 快速检查真实窗口是否卡住（使用较短的超时时间以避免阻塞）
        # 注意：这里使用 10 秒的快速检查，而不是完整的 300 秒
        logger.debug(f"[Row:{row}] 检查真实窗口 {real_hwnd} (端口:{port}) 状态...")
        
        # 严格确保 timeout_seconds 是标准 Python int，避免任何类型的溢出
        timeout_val = 10
        try:
            # 处理 numpy 类型或其他异常类型
            if hasattr(timeout_val, 'item'):
                timeout_val = int(timeout_val.item())
            elif hasattr(timeout_val, '__int__'):
                timeout_val = int(timeout_val)
            else:
                timeout_val = int(str(timeout_val))
            
            # 最终确保是纯 Python int
            timeout_val = int(timeout_val)
            
            # 限制合理范围
            if timeout_val < 1 or timeout_val > 600:
                logger.warning(f"timeout_val 超出范围 ({timeout_val})，使用默认值 10")
                timeout_val = 10
        except Exception as e:
            logger.error(f"timeout_val 类型转换失败: {e}，使用默认值 10")
            timeout_val = 10
        
        logger.debug(f"[Row:{row}] 调用 CheckWindowFrozen(hwnd={real_hwnd}, timeout={timeout_val}, type={type(timeout_val).__name__})")
        
        # 🔧 增加窗口句柄有效性检查，防止访问违规
        try:
            import ctypes.wintypes
            if not ctypes.windll.user32.IsWindow(real_hwnd):
                logger.warning(f"[Row:{row}] ⚠️ 窗口句柄 {real_hwnd} 已失效，跳过检查")
                return False
        except Exception as e:
            logger.debug(f"[Row:{row}] 窗口句柄检查异常: {e}")
        
        # 🔧 等待一小段时间，确保窗口状态稳定，避免与其他线程冲突
        time.sleep(0.5)
        
        try:
            is_frozen = Window.CheckWindowFrozen(real_hwnd, timeout_seconds=timeout_val)
        except OSError as e:
            # 捕获 Windows API 调用失败（如访问违规）
            logger.error(f"[Row:{row}] ❌ CheckWindowFrozen 调用失败: {e}")
            return False
        except Exception as e:
            logger.error(f"[Row:{row}] ❌ 窗口冻结检查异常: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
        
        if is_frozen:
            logger.warning(f"[Row:{row}] ⚠️ 检测到真实窗口 {real_hwnd} (端口:{port}) 已卡住，正在恢复...")
            
            # 🔧 标记窗口正在恢复中
            _window_recovering[row] = time.time()
            
            # 3. 激活真实窗口
            success = Window.ActivateWindow(real_hwnd)
            
            if success:
                logger.info(f"[Row:{row}] ✓ 真实窗口 {real_hwnd} (端口:{port}) 已激活恢复")
                
                # 🔧 关键修复：使用物理鼠标点击唤醒虚拟机窗口
                logger.info(f"[Row:{row}] 🖱️ 执行物理鼠标点击以唤醒虚拟机...")
                click_success = _physical_mouse_click(real_hwnd, x1=191, y1=229, x2=739, y2=561)
                
                if click_success:
                    logger.info(f"[Row:{row}] ✓ 物理点击成功，等待窗口完全激活...")
                else:
                    logger.warning(f"[Row:{row}] ⚠️ 物理点击失败，继续尝试后续恢复步骤")
                
                # 🔧 等待更长时间，确保其他线程的 KM 操作完成
                time.sleep(3)
                
                # 5. 尝试通过游戏界面检测并恢复（新增逻辑）
                recovery_success = False
                try:
                    from dxGame.dx import for_ms_row, wait_for_ms
                    
                    # 从 td_info 获取对应行的 dx 对象（使用顶部已导入的 td_info）
                    dx_obj = getattr(td_info[row], 'dx', None)
                    
                    if dx_obj is not None:
                        logger.info(f"[Row:{row}] 🔍 检查账号界面...")
                        
                        # 检查是否卡在账号界面
                        res, x, y = for_ms_row(row, [MS.账号界面])
                        if res:
                            logger.info(f"[Row:{row}] ✅ 检测到账号界面，尝试点击恢复...")
                            # 🔧 使用全局锁保护 KM 操作，防止与其他线程冲突
                            km_click_success = True
                            with _km_operation_lock:
                                try:
                                    if hasattr(dx_obj.KM, 'MoveTo') and hasattr(dx_obj.KM, 'LeftClick'):
                                        dx_obj.KM.MoveTo(419, 345)
                                        time.sleep(0.3)
                                        dx_obj.KM.LeftClick()
                                        time.sleep(1)
                                except OSError as e:
                                    logger.error(f"[Row:{row}] ❌ KM 点击操作失败（可能窗口已关闭）: {e}")
                                    km_click_success = False
                                except Exception as e:
                                    logger.error(f"[Row:{row}] ❌ KM 点击异常: {e}")
                                    import traceback
                                    logger.debug(traceback.format_exc())
                                    km_click_success = False
                            
                            # 如果点击成功，等待进入游戏界面
                            if km_click_success:
                                # 等待进入游戏界面
                                logger.info(f"[Row:{row}] ⏳ 等待进入游戏界面...")
                                res = wait_for_ms(row, [MS.进入游戏, MS.进入游戏1], for_num=6, delay=0.5)
                                
                                if res:
                                    logger.info(f"[Row:{row}] ✅ 窗口恢复成功 - 已进入游戏界面")
                                    recovery_success = True
                                else:
                                    logger.warning(f"[Row:{row}] ⚠️ 点击账号界面后未检测到进入游戏")
                            else:
                                logger.warning(f"[Row:{row}] ⚠️ KM 点击失败，跳过等待进入游戏")
                        else:
                            logger.debug(f"[Row:{row}] ℹ️ 未检测到账号界面，使用备用恢复方案")
                            # 🔧 未检测到账号界面，直接发送 ESC 尝试恢复
                            try:
                                dx_obj = getattr(td_info[row], 'dx', None)
                                if dx_obj is not None and hasattr(dx_obj, 'KM') and dx_obj.KM is not None:
                                    dx_obj.KM.PressKey('esc')
                                    logger.info(f"[Row:{row}] ✓ 已发送 ESC 键尝试恢复")
                                    time.sleep(0.5)
                            except Exception as e:
                                logger.error(f"[Row:{row}] ❌ 发送 ESC 失败: {e}")
                    else:
                        logger.warning(f"[Row:{row}] ⚠️ 未找到 Row {row} 的 DX 对象")
                        
                except Exception as e:
                    logger.error(f"[Row:{row}] ❌ 游戏界面恢复失败: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                # 6. 如果游戏界面恢复失败，使用原有的 ESC 方案
                if not recovery_success:
                    logger.info(f"[Row:{row}] 🔄 使用备用恢复方案（ESC键）...")
                    try:
                        # 从 td_info 获取对应行的 dx 对象
                        dx_obj = getattr(td_info[row], 'dx', None)
                        
                        if dx_obj is not None and hasattr(dx_obj, 'KM') and dx_obj.KM is not None:
                            # 优化策略：先尝试点击空白处关闭界面，减少 ESC 使用频率
                            # 🔧 使用全局锁保护 KM 操作
                            with _km_operation_lock:
                                try:
                                    if hasattr(dx_obj.KM, 'MoveTo') and hasattr(dx_obj.KM, 'LeftClick'):
                                        dx_obj.KM.MoveTo(100, 100)
                                        time.sleep(0.3)
                                        dx_obj.KM.LeftClick()
                                        time.sleep(0.5)
                                        
                                        logger.info(f"[Row:{row}] ✓ 已尝试点击空白处关闭界面")
                                except OSError as e:
                                    logger.error(f"[Row:{row}] ❌ KM 点击失败（窗口可能已关闭）: {e}")
                                except Exception as e:
                                    logger.error(f"[Row:{row}] ❌ KM 点击异常: {e}")
                            
                            # 备用方案：如果点击无效，再发送 ESC
                            # 注意：ESC 可能触发退出确认对话框，导致 VNC 断开
                            try:
                                dx_obj.KM.PressKey('esc')
                                logger.info(f"[Row:{row}] ✓ 已发送 ESC 键到窗口 {real_hwnd}")
                                time.sleep(0.5)  # 等待按键生效
                            except OSError as e:
                                logger.error(f"[Row:{row}] ❌ KM 按键失败（窗口可能已关闭）: {e}")
                            except Exception as e:
                                logger.error(f"[Row:{row}] ❌ KM 按键异常: {e}")
                        else:
                            logger.warning(f"[Row:{row}] ⚠️ 未找到 Row {row} 的 KM 对象，跳过发送 ESC 键")
                            
                    except Exception as e:
                        logger.error(f"[Row:{row}] ❌ 发送 ESC 键失败: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                
                # 7. 检查 VNC 连接状态（防止窗口恢复后 VNC 断开）
                try:
                    dx_obj = getattr(td_info[row], 'dx', None)
                    if dx_obj and hasattr(dx_obj, 'screenshot') and dx_obj.screenshot:
                        vnc_client = getattr(dx_obj.screenshot, 'client', None)
                        if vnc_client is None:
                            logger.warning(f"[Row:{row}] ⚠️ 窗口恢复后 VNC 已断开，将在下次任务时重连")
                        else:
                            logger.debug(f"[Row:{row}] ✓ VNC 连接正常")
                except Exception as e:
                    logger.debug(f"[Row:{row}] VNC 状态检查异常: {e}")
                
                # 🔧 清除窗口恢复标记
                _window_recovering.pop(row, None)
                logger.debug(f"[Row:{row}] ✅ 窗口恢夏完成，清除恢复标记")
                
                return True
            else:
                logger.error(f"[Row:{row}] ❌ 激活真实窗口 {real_hwnd} (端口:{port}) 失败")
                return False
        else:
            logger.debug(f"[Row:{row}] ✓ 真实窗口 {real_hwnd} (端口:{port}) 正常运行")
            return False
            
    except Exception as e:
        logger.error(f"[Row:{row}] 检查和恢复窗口失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def _tick(fired: set):
    """
    监控周期函数：检查所有活动窗口
    
    Args:
        fired: 已处理的 (row, timestamp) 集合，避免重复处理
    """
    # 获取所有活动的 VMware 端口
    vmware_ports = _get_vmware_ports()
    
    if not vmware_ports:
        return
    
    now_timestamp = int(time.time() / 60)  # 按分钟粒度去重
    
    for row, port in vmware_ports:
        # 生成唯一键，避免同一分钟内重复处理
        key = (row, now_timestamp)
        
        if key in fired:
            continue
        
        # 检查并恢复窗口
        recovered = _check_and_recover_window(row, port)
        
        if recovered:
            fired.add(key)
            logger.info(f"[Row:{row}] 窗口恢复完成")
    
    # 清理过期的 fired 记录（保留最近 10 分钟）
    stale_keys = [k for k in fired if k[1] < now_timestamp - 10]
    for k in stale_keys:
        fired.discard(k)


def start_vmware_window_monitor():
    """
    启动 VMware 窗口监控守护线程
    
    在 Controller.__init__ 末尾调用一次即可。
    """
    stop_flag = threading.Event()
    
    # 将 stop_flag 存储到 gl_info.controller
    controller = getattr(gl_info, "controller", None)
    if controller is not None:
        controller._vmware_monitor_stop = stop_flag
    
    fired = set()
    
    def loop():
        logger.info("[VMware 窗口监控] 守护线程已启动")
        
        while not stop_flag.is_set():
            try:
                _tick(fired)
            except Exception as e:
                logger.error(f"[VMware 窗口监控] 异常: {e}")
                import traceback
                logger.debug(traceback.format_exc())
            
            # 轮询间隔：每 300 秒检查一次（5分钟，大幅降低频率，减少系统负载）
            # 说明：游戏本身响应慢时频繁检测会导致误报，5分钟足够让游戏自行恢复
            poll_interval = 300
            stop_flag.wait(timeout=poll_interval)
        
        logger.info("[VMware 窗口监控] 守护线程已停止")
    
    t = threading.Thread(target=loop, daemon=True, name="VMwareWindowMonitor")
    t.start()
    
    if controller is not None:
        controller._vmware_monitor_thread = t
    
    logger.info("[VMware 窗口监控] 监控线程已创建")
    
    # 🔧 新增：启动线程存活监控（检测跨天重置后的自动重启）
    _start_thread_life_monitor()


def _start_thread_life_monitor():
    """
    启动线程存活监控（检测跨天重置后的自动重启）
    
    每 30 秒检查一次所有活动行的线程状态，如果发现线程退出但配置中仍存在，则自动重启
    """
    def monitor_thread_life():
        logger.info("[线程存活监控] 守护线程已启动")
        
        while True:
            try:
                time.sleep(30)  # 每 30 秒检查一次
                
                controller = getattr(gl_info, "controller", None)
                if controller is None:
                    continue
                
                tc = getattr(controller, "线程控制器", None)
                if tc is None:
                    continue
                
                thread_dict = getattr(tc, "_thread_dict", None)
                if not isinstance(thread_dict, dict):
                    continue
                
                # 检查每个活动的行
                for row in list(thread_dict.keys()):
                    th = thread_dict.get(row)
                    
                    # 如果线程不存在或已退出
                    if th is None or not th.is_alive():
                        logger.warning(f"[Row:{row}] ⚠️ 检测到线程已退出，准备自动重启...")
                        
                        # 等待一小段时间，确保线程完全退出
                        time.sleep(2)
                        
                        # 尝试重新启动线程
                        try:
                            logger.info(f"[Row:{row}] 🔄 正在重启线程...")
                            result = tc.start(row)
                            
                            if result == 2:  # 线程启动成功
                                logger.info(f"[Row:{row}] ✅ 线程重启成功")
                            elif result == 1:  # 线程已在运行
                                logger.info(f"[Row:{row}] ℹ️  线程已在运行，无需重启")
                            else:  # 无法启动（可能达到最大线程数）
                                logger.warning(f"[Row:{row}] ⚠️ 线程重启失败，返回码: {result}")
                        except Exception as e:
                            logger.error(f"[Row:{row}] ❌ 线程重启异常: {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                
            except Exception as e:
                logger.error(f"[线程存活监控] 异常: {e}")
                import traceback
                logger.debug(traceback.format_exc())
    
    monitor_t = threading.Thread(target=monitor_thread_life, daemon=True, name="ThreadLifeMonitor")
    monitor_t.start()
    logger.info("[线程存活监控] 监控线程已创建")


def stop_vmware_window_monitor():
    """
    停止 VMware 窗口监控守护线程
    """
    controller = getattr(gl_info, "controller", None)
    if controller is None:
        return
    
    ev = getattr(controller, "_vmware_monitor_stop", None)
    if ev is not None:
        ev.set()
        logger.info("[VMware 窗口监控] 已发送停止信号")
        
        # 等待线程结束（最多 5 秒）
        t = getattr(controller, "_vmware_monitor_thread", None)
        if t is not None and t.is_alive():
            t.join(timeout=5)
            if t.is_alive():
                logger.warning("[VMware 窗口监控] 线程未在 5 秒内停止")
            else:
                logger.info("[VMware 窗口监控] 线程已停止")
