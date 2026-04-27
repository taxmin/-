# -*- coding: utf-8 -*-
from ast import Pass
from math import e
import builtins
import inspect
import time
import random
import cv2
import numpy as np
from dxGame.dx_model import gl_info, td_info


def _resolve_row_for_print():
    """从调用栈解析当前线程对应的表格行号，供统一 print 前缀使用。"""
    frame = inspect.currentframe()
    if frame is None:
        return None
    f = frame.f_back
    while f is not None:
        try:
            loc = f.f_locals
            inst = loc.get("self")
            if inst is not None and type(inst).__name__ == "Task" and hasattr(inst, "row"):
                return getattr(inst, "row")
            ti = loc.get("task_instance")
            if ti is not None and type(ti).__name__ == "Task" and hasattr(ti, "row"):
                return getattr(ti, "row")
        except Exception:
            pass
        f = f.f_back
    return None


def print(*args, **kwargs):
    row = _resolve_row_for_print()
    if row is None:
        return builtins.print(*args, **kwargs)
    return builtins.print(f"[Row:{row}]", *args, **kwargs)


# region 缓存优化类
class 简单缓存:
    """简单的结果缓存，用于避免重复找图和 OCR 识别"""
    def __init__(self, timeout=2.0):
        self._cache = {}  # 存储结果的字典 {key: (result, timestamp)}
        self._timeout = timeout  # 缓存有效期（秒）
    
    def get(self, key):
        """从缓存获取，如果过期则返回 None"""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._timeout:
                return result  # 缓存有效
            else:
                del self._cache[key]  # 删除过期的缓存
        return None
    
    def set(self, key, result):
        """保存到缓存"""
        self._cache[key] = (result, time.time())
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()

# endregion

# region 动态等待辅助函数
def 轮询等待 (条件函数,max_wait=2.0, interval=0.2):
    """
    轮询等待直到条件满足或超时
    
    Args:
        条件函数：返回 True/False 的函数
        max_wait: 最大等待时间（秒）
        interval: 轮询间隔（秒）
    
    Returns:
        bool: 条件是否满足
    """
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if 条件函数 ():
            return True
        time.sleep(interval)
    return False

# endregion

# region 统一退避重试器
def 退避重试(操作名, fn, *, 重试次数=3, 初始等待=0.15, 最大等待=1.5, 指数=2.0, 捕获异常=(Exception,), on_retry=None):
    """
    通用退避重试器：减少 scattered sleep/except，统一重试策略与日志噪音。
    """
    wait = float(初始等待)
    last_err = None
    for i in range(int(重试次数)):
        try:
            return fn()
        except 捕获异常 as e:
            last_err = e
            is_last = i >= int(重试次数) - 1
            if is_last:
                break
            if on_retry:
                try:
                    on_retry(i + 1, e, wait)
                except Exception:
                    pass
            else:
                print(f"[重试] {操作名} 第{i + 1}/{重试次数}次失败: {e}，{wait:.2f}s后重试")
            time.sleep(wait)
            wait = min(float(最大等待), max(0.01, wait * float(指数)))
    if last_err is not None:
        raise last_err
    return None

# endregion

# region VNC 心跳检测与自动重连
def VNC健康检查(vnc_instance, detailed: bool = False):
    """
    检查 VNC 连接是否健康（增强版：兼容 ManagedMemoryView）
    
    Args:
        vnc_instance: VNC 对象
        detailed: 是否打印详细诊断信息
    
    Returns:
        bool: 连接是否健康
    """
    try:
        # 检查基本属性
        if not hasattr(vnc_instance, 'image'):
            if detailed:
                print("  [VNC 检查] image 属性不存在")
            return False
        
        if vnc_instance.image is None:
            if detailed:
                print("  [VNC 检查] image 为 None")
            return False
        
        # 检查是否有 client 连接
        if not hasattr(vnc_instance, 'client') or vnc_instance.client is None:
            if detailed:
                print("  [VNC 检查] client 未连接")
            return False
        
        # 尝试截图验证（小区域，快速）
        try:
            test_img = vnc_instance.Capture(0, 0, 10, 10)
        except OSError as e:
            # 🔧 捕获 Windows API 访问违规（0xC0000005）
            if detailed:
                print(f"  [VNC 检查] Capture 调用失败 (OSError): {e}")
            return False
        except Exception as capture_error:
            if detailed:
                print(f"  [VNC 检查] Capture 异常: {capture_error}")
                import traceback
                traceback.print_exc()
            return False
        
        if test_img is None:
            if detailed:
                print("  [VNC 检查] Capture 返回 None")
            return False
        
        # 兼容多种数据类型：numpy.ndarray, ManagedMemoryView, memoryview
        # 检查是否有 shape 或 size 属性
        has_shape = hasattr(test_img, 'shape')
        has_size = hasattr(test_img, 'size')
        
        if not has_shape and not has_size:
            if detailed:
                print(f"  [VNC 检查] 截图数据类型异常: {type(test_img)}，既无 shape 也无 size")
            return False
        
        # 如果有 shape，检查维度
        if has_shape:
            if isinstance(test_img.shape, tuple) and len(test_img.shape) >= 2:
                h, w = test_img.shape[0], test_img.shape[1]
                if h == 0 or w == 0:
                    if detailed:
                        print(f"  [VNC 检查] 截图尺寸无效: {w}x{h}")
                    return False
            else:
                if detailed:
                    print(f"  [VNC 检查] shape 格式异常: {test_img.shape}")
                return False
        
        # 如果有 size，检查大小
        if has_size:
            try:
                size_val = test_img.size
                if isinstance(size_val, (int, float)) and size_val == 0:
                    if detailed:
                        print("  [VNC 检查] 截图数据大小为 0")
                    return False
            except:
                # size 可能是 property，访问失败也认为有问题
                pass
        
        # 额外检查：尝试转换为 numpy 数组验证
        try:
            import numpy as np
            if not isinstance(test_img, np.ndarray):
                # 尝试转换
                test_array = np.asarray(test_img)
                if test_array.size == 0:
                    if detailed:
                        print("  [VNC 检查] 转换为 numpy 后大小为 0")
                    return False
        except Exception as convert_err:
            if detailed:
                print(f"  [VNC 检查] 转换为 numpy 数组失败: {convert_err}")
            # 不直接返回 False，因为有些类型无法转换但仍然有效
        
        if detailed:
            print(f"  [VNC 检查] ✅ 通过 (类型: {type(test_img).__name__})")
        return True
    except Exception as e:
        if detailed:
            print(f"VNC 健康检查失败：{e}")
            import traceback
            traceback.print_exc()
        return False

def VNC自动重连(task_instance, 编号):
    """
    自动重连 VNC（增强版：增加等待时间和重试机制）
    
    Args:
        task_instance: Task 对象
        编号：模拟器编号
    
    Returns:
        bool: 重连是否成功
    """
    try:
        # 🔧 导入全局 KM 锁，防止 VNC 重连时与其他线程的 KM 操作冲突
        from app.vmware_window_monitor import get_km_lock
        km_lock = get_km_lock(getattr(task_instance, "row", None))
        task_instance._vnc_reconnecting = True
        if hasattr(task_instance, "dx"):
            setattr(task_instance.dx, "_vnc_reconnecting", True)
        
        print(f"[VNC 重连] 开始尝试重新连接...")
        
        # 🔧 使用全局锁保护 VNC 重连过程，防止与 KM 操作并发
        with km_lock:
            # 停止旧连接
            if hasattr(task_instance.dx.screenshot, 'stop'):
                try:
                    task_instance.dx.screenshot.stop()
                except:
                    pass
                time.sleep(1.0)  # 增加等待时间，确保资源释放
            
            # 🔧 性能监控：记录 VNC 重连
            from app.stability_optimizer import vnc_performance_monitor
            vnc_performance_monitor.record_vnc_reconnect(
                row=getattr(task_instance, 'row', None),
                reason="VNC自动重连"
            )
            
            # 重新初始化 VNC
            print(f"[VNC 重连] 创建新的 VNC 连接 (127.0.0.1:{编号})...")
            task_instance.dx.screenshot = VNC("127.0.0.1", 编号, "", fps=2)  # 🔧 稳定性优化：降低 FPS 至 2，回合制游戏足够，减少 CPU/内存占用
            
            # 等待后台截图线程启动
            print("[VNC 重连] 等待截图线程启动...")
            time.sleep(2.0)
        
        # 轮询等待第一帧截图（最多等待 15 秒）
        print("[VNC 重连] 等待第一帧截图...")
        success = 轮询等待(
            lambda: hasattr(task_instance.dx.screenshot, 'image') and 
                    task_instance.dx.screenshot.image is not None,
            max_wait=15.0,  # 增加等待时间到15秒
            interval=0.5
        )
        
        if not success:
            print("[VNC 重连] ❌ 超时：未获取到截图数据")
            return False
        
        # 增加额外等待，确保截图稳定
        print("[VNC 重连] 等待截图稳定...")
        time.sleep(2.0)  # 增加到2秒
        
        # 🔧 新增：进行多次连续截图测试，确保连接真正稳定
        print("[VNC 重连] 进行连续截图测试...")
        test_success_count = 0
        for i in range(3):
            try:
                test_img = task_instance.dx.screenshot.Capture(0, 0, 100, 100)
                if test_img is not None and hasattr(test_img, 'shape'):
                    test_success_count += 1
                    print(f"[VNC 重连] 测试截图 {i+1}/3 成功")
                    time.sleep(0.5)
                else:
                    print(f"[VNC 重连] 测试截图 {i+1}/3 失败：图像无效")
            except Exception as e:
                print(f"[VNC 重连] 测试截图 {i+1}/3 异常: {e}")
        
        if test_success_count < 2:
            print(f"[VNC 重连] ❌ 连续截图测试失败（成功{test_success_count}/3次）")
            return False
        
        # 验证连接（带重试）
        print("[VNC 重连] 验证连接...")
        for attempt in range(5):  # 增加到5次重试
            if VNC健康检查(task_instance.dx.screenshot, detailed=True):  # 使用详细模式
                task_instance._vnc_reconnect_attempts = 0  # 重置重连次数
                print(f"[VNC 重连] ✅ 成功！（连续截图测试: {test_success_count}/3）")
                return True
            else:
                if attempt < 4:
                    print(f"[VNC 重连] 验证失败，重试 {attempt + 1}/5...")
                    time.sleep(2.0)  # 增加重试间隔
                else:
                    print("[VNC 重连] ❌ 验证失败（已重试 5 次）")
                    return False

    except Exception as e:
        print(f"[VNC 重连] ❌ 异常：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        task_instance._vnc_reconnecting = False
        if hasattr(task_instance, "dx"):
            setattr(task_instance.dx, "_vnc_reconnecting", False)

# endregion
import os
import sys
from PIL import Image
from difflib import SequenceMatcher
import re
import pyperclip
import datetime
import time
from app.public_function import show_log
from public import 表格_收益
try:
    import win32clipboard
    import win32con

    WIN32CLIPBOARD_AVAILABLE = True
except ImportError:
    WIN32CLIPBOARD_AVAILABLE = False

# 添加父目录到 Python 路径，以便导入 app、dxGame 和 public 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from app.public_function import *
from dxGame import MiniOpenCV
from dxGame.dx_a_start import 取直线的最远一个坐标, 直线优化路径, 获取下一个坐标位置, 获取骨干网A星轨迹
from dxGame.dx_km_class import DXKM
from dxGame.dx_ldmnq import ld_read_json
from dxGame.dx_OnnxOCR import ONNX_OCR
from dxGame.dx_vnc import VNC
from dxGame.dx_vnckm import VNC_KM
from dxGame.phone_verify import verify_phone_number
from public import *


# region 保存进度（v2：支持日常任务细粒度断点）
PROGRESS_VERSION = 2

# 日常流水线步骤 id（与 主界面 编排一致，勿随意改名以免断点失效）
DAILY_STEP_IDENTIFY_GOLD = "identify_gold"  # 识别金币
DAILY_STEP_CLEAR_BAG_H = "clear_bag_h"  # 清理背包（高活跃）
DAILY_STEP_STALL_H = "stall_h"  # 摆摊（高活跃）
DAILY_STEP_DAILY_SANJIE = "daily_sanjie"  # 日常三界
DAILY_STEP_DAILY_KEJU = "daily_keju"  # 日常科举
DAILY_STEP_GUILD_TASK = "guild_task"  # 帮派任务
DAILY_STEP_GHOST_AFK = "ghost_afk"
DAILY_STEP_PARTNER = "partner"  # 伙伴助战
DAILY_STEP_CLEAR_BAG_L = "clear_bag_l"  # 清理背包（低活跃）
DAILY_STEP_STALL_L = "stall_l"  # 摆摊（低活跃）
DAILY_STEP_RANDOM_PREFIX = "daily_random_"  # + 师门|宝图|趣闻|秘境
DAILY_STEP_DIG_TREASURE = "dig_treasure"  # 挖宝
DAILY_STEP_ESCORT = "escort"  # 运镖
DAILY_STEP_WORK = "work"  # 打工
DAILY_STEP_CLEAR_BAG_L2 = "clear_bag_l2"  # 清理背包（低活跃）
DAILY_STEP_STALL_L2 = "stall_l2"  # 摆摊（低活跃）
DAILY_STEP_PRAYER = "prayer"  # 祈福
DAILY_STEP_SCRATCH_CARD = "scratch_card"  # 刮刮乐

# 日常断点按「任务日」切换：每天 0:15 起算新一天，0:00–0:14 仍属上一任务日
DAILY_PROGRESS_RESET_HOUR = 0
DAILY_PROGRESS_RESET_MINUTE = 15


def daily_progress_cycle_date_iso(now=None):
    """
    当前所属任务日的日期字符串（YYYY-MM-DD），用于 daily.calendar_date。
    在本地 0:15 整点起进入「当天」任务周期；此前仍计为前一自然日对应的任务日。
    """
    if now is None:
        now = datetime.datetime.now()
    reset = datetime.time(DAILY_PROGRESS_RESET_HOUR, DAILY_PROGRESS_RESET_MINUTE, 0)
    if now.time() < reset:
        return (now.date() - datetime.timedelta(days=1)).isoformat()
    return now.date().isoformat()


def _default_daily_state():
    return {
        "calendar_date": "",
        "account_index": 0,
        "branch": None,
        "completed_steps": [],
        "random_order": [],
    }


def _default_progress_state():
    return {
        "version": PROGRESS_VERSION,
        "now_user_id": 0,
        "now_server_id": 0,
        "now_task_id": 0,
        "now_fuben_id": 0,
        "daily": _default_daily_state(),
        # 🔧 新增：标记是否为意外退出（崩溃/断线）后的重新登录
        "crash_recovery": False,
    }


def migrate_progress_raw(raw):
    """将进度配置转为 v2 dict；兼容旧版四元 list。"""
    if isinstance(raw, dict) and raw.get("version") == PROGRESS_VERSION:
        out = dict(raw)
        out["daily"] = dict(_default_daily_state(), **(raw.get("daily") or {}))
        for k in _default_daily_state():
            if k not in out["daily"]:
                out["daily"][k] = _default_daily_state()[k]
        # 🔧 新增：确保 crash_recovery 字段存在
        if "crash_recovery" not in out:
            out["crash_recovery"] = False
        return out
    if isinstance(raw, (list, tuple)) and len(raw) >= 4:
        b = _default_progress_state()
        b["now_user_id"] = int(raw[0])
        b["now_server_id"] = int(raw[1])
        b["now_task_id"] = int(raw[2])
        b["now_fuben_id"] = int(raw[3])
        return b
    return _default_progress_state()


def _sync_progress_attrs(self, blob):
    self.now_user_id = int(blob["now_user_id"])
    self.now_server_id = int(blob["now_server_id"])
    self.now_task_id = int(blob["now_task_id"])
    self.now_fuben_id = int(blob["now_fuben_id"])


def 保存进度(self, now_user_id, now_server_id, now_task_id, now_fube_id):
    """更新顶层四元组并写入本地；全 0 表示任务整表完成，清空含日常断点。"""
    cfg = gl_info.配置.setdefault("进度配置", {})
    if now_user_id == 0 and now_server_id == 0 and now_task_id == 0 and now_fube_id == 0:
        # 🔧 关键修复：任务完成时，清除 crash_recovery 标记
        blob = _default_progress_state()
        blob["crash_recovery"] = False  # 确保为 False
        cfg[self.名称] = blob
        _sync_progress_attrs(self, cfg[self.名称])
        gl_info.配置.写入本地配置文件()
        print(f"[Row:{self.row}] ✅ [任务完成] 已清除 crash_recovery 标记")
        return
    blob = migrate_progress_raw(cfg.get(self.名称))
    blob["now_user_id"] = int(now_user_id)
    blob["now_server_id"] = int(now_server_id)
    blob["now_task_id"] = int(now_task_id)
    blob["now_fuben_id"] = int(now_fube_id)
    cfg[self.名称] = blob
    _sync_progress_attrs(self, blob)
    gl_info.配置.写入本地配置文件()


# 排队界面 OCR 区域与轮询间隔（秒）
_QUEUE_ETA_OCR_XY = (387, 362, 605, 386)
_QUEUE_POLL_NO_OCR_SEC = 5.0
_QUEUE_POLL_MINUTE_LEVEL_SEC = 60.0
_QUEUE_POLL_HOUR_LEVEL_SEC = 1800.0


def _parse_queue_eta_hours_minutes(text):
    """解析「预计等待：0小时5分」类文案；未出现「数字+小时/分」则 ok=False。"""
    if not text or not isinstance(text, str):
        return 0, 0, False
    h_m = re.search(r'(\d+)\s*小时', text)
    m_m = re.search(r'(\d+)\s*(?:分钟|分)', text)
    if not h_m and not m_m:
        return 0, 0, False
    h = int(h_m.group(1)) if h_m else 0
    m = int(m_m.group(1)) if m_m else 0
    return h, m, True


def _env_float(name, default):
    try:
        v = os.environ.get(name, "").strip()
        if v == "":
            return float(default)
        return float(v)
    except ValueError:
        return float(default)


def _env_int(name, default):
    try:
        v = os.environ.get(name, "").strip()
        if v == "":
            return int(default)
        return int(v)
    except ValueError:
        return int(default)


_RATE_LIMIT_STATE = {}


def _rate_limited_print(key, interval_sec, *args, **kwargs):
    """简单日志限流：同一 key 在 interval_sec 内仅打印一次。"""
    now = time.time()
    last = _RATE_LIMIT_STATE.get(key, 0.0)
    if now - last >= float(interval_sec):
        _RATE_LIMIT_STATE[key] = now
        print(*args, **kwargs)


def _safe_capture_dx(dx, *capture_args):
    """
    安全截图门禁：
    - VNC 重连窗口期直接跳过，避免竞争
    - 统一捕获底层 OSError，返回 None
    - 🔧 关键修复：检测 VNC 长时间未响应，主动抛出异常终止任务
    """
    if dx is None:
        return None
    if getattr(dx, "_vnc_reconnecting", False):
        return None
    sc = getattr(dx, "screenshot", None)
    if sc is None:
        return None
    
    # 🔧 关键修复：检查 VNC 是否超过 1 分钟未成功截图
    if hasattr(sc, 'last_success_time'):
        idle_time = time.time() - sc.last_success_time
        if idle_time > 60:
            # 超过 1 分钟未截图，说明 VNC 已失效，不应继续访问
            print(f"⚠️ [安全截图] VNC 已超过 {int(idle_time)} 秒未响应，拒绝截图以避免崩溃")
            raise RuntimeError(f"VNC 超时 {int(idle_time)} 秒，任务应中止")
    
    try:
        if capture_args:
            return sc.Capture(*capture_args)
        return sc.Capture()
    except OSError as e:
        _rate_limited_print("safe_capture_oserror", 3.0, f"⚠️ 安全截图失败 (OSError): {e}")
        return None
    except RuntimeError:
        # 重新抛出我们主动抛出的超时异常
        raise
    except Exception:
        return None


def _km_img_to_bgr_np(img):
    if img is None:
        return None
    if isinstance(img, np.ndarray):
        a = img
    elif hasattr(img, "get_memoryview"):
        a = np.array(img.get_memoryview(), copy=False)
    else:
        a = np.asarray(img)
    if a is None or a.size == 0:
        return None
    if len(a.shape) == 2:
        a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    elif len(a.shape) == 3 and a.shape[2] == 4:
        a = cv2.cvtColor(a, cv2.COLOR_RGBA2BGR)
    if a.dtype != np.uint8:
        a = a.astype(np.uint8)
    return np.ascontiguousarray(a)


def _km_clip_roi(x, y, pad, w, h):
    x1 = max(0, int(x) - pad)
    y1 = max(0, int(y) - pad)
    x2 = min(int(w), int(x) + pad + 1)
    y2 = min(int(h), int(y) + pad + 1)
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _km_roi_mean_abs_diff(a, b):
    if a is None or b is None or a.size == 0 or b.size == 0:
        return 0.0
    if a.shape != b.shape:
        return 999.0
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def _km_pixel_verify_use(dx, pixel_verify):
    if pixel_verify is False:
        return False
    if pixel_verify is True:
        return dx is not None and getattr(dx, "screenshot", None) is not None
    if dx is None or getattr(dx, "screenshot", None) is None:
        return False
    v = os.environ.get("KM_CLICK_VERIFY_PIXEL", "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _km_do_click_sequence(km, x, y, 时间间隔, settle, post_floor, repeats, gap, second):
    km.MoveTo(int(x), int(y))
    time.sleep(max(时间间隔 * 0.5, settle))
    for i in range(repeats):
        km.LeftClick()
        if i < repeats - 1:
            time.sleep(gap)
    if second:
        time.sleep(gap)
        km.LeftClick()
    time.sleep(max(时间间隔 * 0.5, post_floor))


def km_稳妥移动点击(
    km,
    x,
    y,
    时间间隔=0.5,
    *,
    dx=None,
    verify=None,
    verify_retries=None,
    verify_interval=None,
    pixel_verify=None,
):
    """
    缓解画面卡顿、VNC 帧未跟上时的「点空 / 点偏」：MoveTo 后多停一帧再点；并带**点击后校验**，不通过则重试。

    校验策略（满足任一即视为本尝试成功）：
      1) 传入 verify 且 verify() 为 True（无参可调用，如 lambda: for_ms_row(row, [...])[0]）
      2) 开启像素邻域校验：点击前后截取 (x,y) 附近 ROI，平均绝对差 >= KM_CLICK_VERIFY_DIFF 视为画面有反馈

    传入 dx 且未显式 pixel_verify=False、且环境变量未关闭 KM_CLICK_VERIFY_PIXEL 时，**默认开启**像素邻域校验。

    可选环境变量：
      KM_MOVE_SETTLE_SEC / KM_CLICK_POST_DELAY_SEC / KM_CLICK_REPEAT / KM_CLICK_REPEAT_GAP_SEC / KM_CLICK_SECOND
      VNC_MOUSE_DELAY / VNC_KEY_DELAY
      KM_CLICK_VERIFY_RETRIES     最大尝试次数（每尝试含一整次移动+点击），默认 4
      KM_CLICK_VERIFY_INTERVAL    每次点击后等待再校验的秒数，默认 0.22
      KM_CLICK_VERIFY_PIXEL       0/false 关闭像素邻域校验（仍可用 verify 回调）
      KM_CLICK_VERIFY_ROI_PAD     邻域半宽像素，默认 10
      KM_CLICK_VERIFY_DIFF        邻域均值绝对差阈值，默认 2.5
    """
    settle = _env_float("KM_MOVE_SETTLE_SEC", 0.12)
    post_floor = _env_float("KM_CLICK_POST_DELAY_SEC", 0.06)
    repeats = max(1, _env_int("KM_CLICK_REPEAT", 1))
    gap = _env_float("KM_CLICK_REPEAT_GAP_SEC", 0.06)
    second = os.environ.get("KM_CLICK_SECOND", "").strip().lower() in ("1", "true", "yes", "on")

    retries = max(1, int(verify_retries if verify_retries is not None else _env_int("KM_CLICK_VERIFY_RETRIES", 4)))
    interval = float(verify_interval if verify_interval is not None else _env_float("KM_CLICK_VERIFY_INTERVAL", 0.22))
    use_pixel = _km_pixel_verify_use(dx, pixel_verify)
    # VNC 重连窗口期内禁用像素校验，避免重连期间 Capture 竞争导致误判/异常
    if dx is not None and getattr(dx, "_vnc_reconnecting", False):
        use_pixel = False
    need_retry_loop = (verify is not None) or use_pixel
    
    # 🔧 关键修复：当 pixel_verify=False 且无 verify 回调时，强制单击模式（禁用重复点击）
    if pixel_verify is False and verify is None:
        repeats = 1
        second = False

    if not need_retry_loop:
        try:
            _km_do_click_sequence(km, x, y, 时间间隔, settle, post_floor, repeats, gap, second)
        except OSError as e:
            print(f"⚠️ KM 点击操作失败 (OSError): {e}")
            return
        except Exception as e:
            print(f"⚠️ KM 点击序列异常: {e}")
            import traceback
            traceback.print_exc()
            return

    pad = max(2, _env_int("KM_CLICK_VERIFY_ROI_PAD", 10))
    diff_th = _env_float("KM_CLICK_VERIFY_DIFF", 2.5)
    
    # 🔧 性能监控：记录 KM 点击操作
    from app.stability_optimizer import vnc_performance_monitor
    vnc_performance_monitor.record_km_click()

    for _attempt in range(retries):
        ref_np = None
        if use_pixel:
            try:
                sc = dx.screenshot
                w, h = int(sc.width), int(sc.height)
                box = _km_clip_roi(x, y, pad, w, h)
                if box:
                    ref_np = _km_img_to_bgr_np(_safe_capture_dx(dx, *box))
            except OSError as e:
                # 🔧 捕获 Windows API 访问违规（0xC0000005）
                print(f"⚠️ KM 像素验证截图失败 (OSError): {e}")
                ref_np = None
            except Exception:
                ref_np = None

        try:
            _km_do_click_sequence(km, x, y, 时间间隔, settle, post_floor, repeats, gap, second)
        except OSError as e:
            # 🔧 捕获底层 API 访问违规（0xC0000005）
            print(f"⚠️ KM 点击操作失败 (OSError): {e}")
            
            # 🔧 性能监控：记录崩溃
            from app.stability_optimizer import vnc_performance_monitor
            vnc_performance_monitor.record_crash(
                location="km_稳妥移动点击",
                details=f"OSError: {e}"
            )
            
            return  # 直接返回，避免继续重试导致崩溃
        except Exception as e:
            print(f"⚠️ KM 点击序列异常: {e}")
            import traceback
            traceback.print_exc()
            return
        time.sleep(interval)

        if verify is not None:
            try:
                if verify():
                    return
            except Exception:
                pass

        if use_pixel and ref_np is not None:
            try:
                sc = dx.screenshot
                w, h = int(sc.width), int(sc.height)
                box = _km_clip_roi(x, y, pad, w, h)
                if box:
                    cur_np = _km_img_to_bgr_np(_safe_capture_dx(dx, *box))
                    if _km_roi_mean_abs_diff(ref_np, cur_np) >= diff_th:
                        return
            except OSError as e:
                # 🔧 捕获 Windows API 访问违规（0xC0000005）
                print(f"⚠️ KM 像素验证截图失败 (OSError): {e}")
                return
            except Exception:
                return


# endregion


class Task:
    """
    表格一行的「单开脚本」载体：由 ThreadController 在线程里构造并跑 初始化任务。

    生命周期简述
    ------------
    - __init__：启动延迟 → 初始化插件（DX/VNC/缓存/VNC 监控）→ 读存档进度 → 初始化任务。
    - 初始化任务：按表格第 4 列「逗号分隔的任务方法名」依次 getattr(self, 名称) 调用；
      常见入口是「日常任务」；方法必须定义为 Task 的本类方法，与 日常任务 内部的嵌套函数不是一层。
    - 日常任务：用 td_info[self.row].process 做状态机（登陆 → 进游戏初始化 → 主界面），
      「主界面」里再展开具体日常（活跃值分支、随机日常、运镖/挖宝/打工/捉鬼等）。

    进度与配置
    ----------
    - 进度配置[self.名称] → v2 dict：含 now_* 四元组与 daily（account_index、branch、completed_steps、random_order、calendar_date，任务日每日 0:15 切换）。
    - 账号配置[编号] → 多条「账号|密码|区服|角色」；编号通常对应模拟器 VNC 端口等。
    """

    # region 初始化
    # region 初始化类
    def __init__(self, row):
        self.名称 = get_row_content(row)[1]
        self.row = row
        self._移动开始时间 = None  # 记录开始移动的时间
        self._是否在移动 = False  # 标记是否正在移动
        self._vnc_reconnecting = False  # VNC 重连窗口期保护标记
        self.启动延迟()
        self.初始化插件()
        self.初始化加载进度()
        self.初始化任务()

    # endregion
    # region 启动延迟
    def 启动延迟(self):
        """多开错峰：秒数来自 全局配置「启动延迟」，避免同时打 VNC/磁盘。"""
        for i in range(gl_info.配置["全局配置"]["启动延迟"]):
            time.sleep(1)
            show_log(self.row, f"启动等待{i}s")

    # endregion

    # region 初始化插件
    def 初始化插件 (self):
        """创建 DX、挂 VNC 监控线程、找图/OCR 短缓存；此时尚未连具体模拟器 VNC（在 login 里按编号连接）。"""
        self.dx: DX = DX()
        self.dx.UseDict(0)
        self.dx.SetPath(IMAGE_DIR)
        self.dx.SetPicPwd("@123")
        self.dx._vnc_reconnecting = False
        td_info[self.row].dx = self.dx
            
        # 添加 VNC 状态监控变量
        self._vnc_monitor_enabled = True
        self._vnc_last_heartbeat = time.time()  # 最后心跳时间
        self._vnc_reconnect_attempts = 0  # 重连次数
        self._vnc_fault_flag = False  # 由监控线程写入，主任务循环统一消费
        self._vnc_fault_reason = ""
        self._vnc_fault_lock = threading.Lock()
        self._loop_watchdog_state = {}
        self._loop_watchdog_log_state = {}
        self._start_vnc_monitor()
        
        # 添加缓存优化（避免重复找图和 OCR）
        self.find_cache = 简单缓存 (timeout=1.5)  # 找图缓存，有效期 1.5 秒
        self.ocr_cache = 简单缓存 (timeout=3.0)   # OCR 缓存，有效期 3 秒
        
        # 🔧 新增：金币截图存储
        self._gold_screenshot_data = None  # 存储金币截图数据
        # endregion
        # self.test_mem_capture ()

    def _rate_limited_show_log(self, key, interval_sec, content, table=None):
        """实例级日志限流，减少多开高频重复日志对 IO/调度的影响。"""
        full_key = f"{self.row}:{key}"
        now = time.time()
        if not hasattr(self, "_log_rl_state"):
            self._log_rl_state = {}
        last = self._log_rl_state.get(full_key, 0.0)
        if now - last >= float(interval_sec):
            self._log_rl_state[full_key] = now
            if table is None:
                show_log(self.row, content)
            else:
                show_log(self.row, content, table)

    def _set_vnc_fault(self, reason):
        """由 VNC 监控线程写入故障标志，主任务循环统一处理（单一出口）。"""
        with self._vnc_fault_lock:
            self._vnc_fault_flag = True
            self._vnc_fault_reason = str(reason)

    def _consume_vnc_fault(self):
        """主任务循环读取并清空故障标志。"""
        with self._vnc_fault_lock:
            if not self._vnc_fault_flag:
                return None
            reason = self._vnc_fault_reason or "未知 VNC 监控故障"
            self._vnc_fault_flag = False
            self._vnc_fault_reason = ""
            return reason

    def _watchdog_tick(self, loop_key, max_loop_seconds=600, log_interval_seconds=30):
        """
        统一循环 watchdog：用于 while True 防隐性死循环。
        超时抛出 RuntimeError，由主流程统一出口处理。
        """
        now = time.time()
        start = self._loop_watchdog_state.get(loop_key)
        if start is None:
            self._loop_watchdog_state[loop_key] = now
            self._loop_watchdog_log_state[loop_key] = now
            return
        elapsed = now - start
        last_log = self._loop_watchdog_log_state.get(loop_key, start)
        if now - last_log >= float(log_interval_seconds):
            self._loop_watchdog_log_state[loop_key] = now
            process = getattr(td_info[self.row], "process", "未知")
            self._rate_limited_show_log(
                f"watchdog:{loop_key}",
                float(log_interval_seconds),
                f"⏱️ 循环监控: {loop_key} 已运行 {int(elapsed)}s, process={process}",
                表格_状态,
            )
        if elapsed > float(max_loop_seconds):
            process = getattr(td_info[self.row], "process", "未知")
            raise RuntimeError(
                f"watchdog 超时: {loop_key} 运行 {int(elapsed)}s, process={process}, 已触发统一退出"
            )

    # endregion
    # region 初始化加载进度
    def 初始化加载进度(self):
        """从「进度配置」恢复 v2 进度；跨任务日（每日 0:15）清空 daily；兼容旧版四元 list。"""
        cfg = gl_info.配置.setdefault("进度配置", {})
        raw = cfg.get(self.名称)
        blob = migrate_progress_raw(raw)
        daily = blob["daily"]
        cycle_day = daily_progress_cycle_date_iso()
        need_save = False
        if daily.get("calendar_date") != cycle_day:
            daily["calendar_date"] = cycle_day
            daily["account_index"] = 0
            daily["branch"] = None
            daily["completed_steps"] = []
            daily["random_order"] = []
            need_save = True
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        if need_save:
            gl_info.配置.写入本地配置文件()

    def _read_progress_blob(self):
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        # 🔧 调试：打印读取到的配置
        print(f"[Row:{self.row}] 📖 [读取配置] blob keys: {list(blob.keys())}")
        if "daily" in blob:
            print(f"[Row:{self.row}] 📖 [读取配置] daily.calendar_date: {blob['daily'].get('calendar_date', 'N/A')}")
            print(f"[Row:{self.row}] 📖 [读取配置] daily.completed_steps: {blob['daily'].get('completed_steps', [])}")
        return blob

    def _write_progress_blob(self, blob):
        gl_info.配置.setdefault("进度配置", {})[self.名称] = blob
        _sync_progress_attrs(self, blob)
        # 🔧 调试：打印写入的配置
        print(f"[Row:{self.row}] 💾 [写入配置] blob keys: {list(blob.keys())}")
        if "daily" in blob:
            print(f"[Row:{self.row}] 💾 [写入配置] daily.calendar_date: {blob['daily'].get('calendar_date', 'N/A')}")
            print(f"[Row:{self.row}] 💾 [写入配置] daily.completed_steps: {blob['daily'].get('completed_steps', [])}")
        gl_info.配置.写入本地配置文件()
        print(f"[Row:{self.row}] ✅ [写入配置] 配置文件已保存")

    def _daily_ensure_today(self, blob):
        """若 blob.daily 与当前任务日（每日 0:15 切换）不一致则重置日常子状态；返回 (blob, changed)。"""
        daily = blob["daily"]
        cycle_day = daily_progress_cycle_date_iso()
        if daily.get("calendar_date") == cycle_day:
            return blob, False
        daily["calendar_date"] = cycle_day
        daily["account_index"] = 0
        daily["branch"] = None
        daily["completed_steps"] = []
        daily["random_order"] = []
        return blob, True

    def _daily_should_skip(self, step_id):
        """
        检查是否应该跳过指定的日常步骤
        
        Args:
            step_id: 步骤 ID
            
        Returns:
            bool: True=应该跳过（已完成）, False=不应该跳过（未完成）
        """
        blob = self._read_progress_blob()
        blob, changed = self._daily_ensure_today(blob)
        if changed:
            gl_info.配置.setdefault("进度配置", {})[self.名称] = blob
            _sync_progress_attrs(self, blob)
            gl_info.配置.写入本地配置文件()
        
        should_skip = step_id in blob["daily"].get("completed_steps", [])
        if should_skip:
            print(f"[Row:{self.row}] ⏭️ [跳过步骤] {step_id} 已完成，将自动跳过")
        else:
            print(f"[Row:{self.row}] ▶️ [执行步骤] {step_id} 未完成，开始执行")
        
        return should_skip

    def _daily_mark_step_done(self, step_id):
        print(f"\n{'='*80}")
        print(f"[Row:{self.row}] 🏷️ [标记步骤] 开始标记: {step_id}")
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._daily_ensure_today(blob)
        daily = blob["daily"]
        
        print(f"[Row:{self.row}] 🏷️ [标记步骤] 标记前 completed_steps: {daily.get('completed_steps', [])}")
        if step_id not in daily["completed_steps"]:
            daily["completed_steps"].append(step_id)
            print(f"[Row:{self.row}] 💾 [日常断点] 已标记步骤完成: {step_id} | 当前已完成: {daily['completed_steps']}")
        else:
            print(f"[Row:{self.row}] ⚠️ [日常断点] 步骤已存在，无需重复标记: {step_id}")
        
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()
        print(f"[Row:{self.row}] ✅ [标记步骤] 配置文件已保存")
        print(f"{'='*80}\n")

    def _daily_set_branch(self, branch):
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._daily_ensure_today(blob)
        blob["daily"]["branch"] = branch
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()

    def _daily_set_random_order(self, order_ids):
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._daily_ensure_today(blob)
        blob["daily"]["random_order"] = list(order_ids)
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()

    def _daily_finish_account(self):
        """当前账号日常整段跑完：前进 account_index，清空步骤与分支以便下一账号。"""
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._daily_ensure_today(blob)
        daily = blob["daily"]
        old_index = int(daily.get("account_index", 0))
        daily["account_index"] = old_index + 1
        print(f"[Row:{self.row}] 📊 [日常断点] 账号完成: account_index {old_index} -> {daily['account_index']}")
        daily["branch"] = None
        daily["completed_steps"] = []
        daily["random_order"] = []
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()

    def _daily_reset_for_next_run(self):
        """一轮所有账号处理完后，重置日常游标，便于当日再次执行整轮（或下次进入 主界面）。"""
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._daily_ensure_today(blob)
        daily = blob["daily"]
        daily["account_index"] = 0
        daily["branch"] = None
        daily["completed_steps"] = []
        daily["random_order"] = []
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()

    # region 周常任务状态管理
    def _get_weekly_blob(self):
        """
        获取周常任务进度数据
        
        Returns:
            dict: 周常任务进度数据
        """
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        
        # 确保有 weekly 字段
        if "weekly" not in blob:
            blob["weekly"] = {
                "week_start_date": "",  # 本周开始日期（周一）
                "completed_tasks": [],  # 已完成的任务列表
            }
        
        return blob
    
    def _ensure_current_week(self, blob):
        """
        检查是否为新的周，如果是则重置周常任务状态
        
        Args:
            blob: 进度数据
            
        Returns:
            tuple: (blob, changed) - 数据和是否发生变化
        """
        weekly = blob["weekly"]
        
        # 计算本周一的日期
        now = datetime.datetime.now()
        monday = now - datetime.timedelta(days=now.weekday())
        current_week_start = monday.date().isoformat()
        
        # 检查是否需要重置
        if weekly.get("week_start_date") != current_week_start:
            # 新的一周，重置周常任务
            weekly["week_start_date"] = current_week_start
            weekly["completed_tasks"] = []
            return blob, True
        
        return blob, False
    
    def _检查周常任务是否已完成(self, task_name):
        """
        检查指定周常任务是否已完成
        
        Args:
            task_name: 任务名称
            
        Returns:
            bool: 是否已完成
        """
        blob = self._get_weekly_blob()
        blob, changed = self._ensure_current_week(blob)
        
        if changed:
            self._write_progress_blob(blob)
        
        return task_name in blob["weekly"].get("completed_tasks", [])
    
    def _标记周常任务完成(self, task_name):
        """
        标记周常任务为已完成
        
        Args:
            task_name: 任务名称
        """
        cfg = gl_info.配置.setdefault("进度配置", {})
        blob = migrate_progress_raw(cfg.get(self.名称))
        blob, _ = self._ensure_current_week(blob)
        
        weekly = blob["weekly"]
        if task_name not in weekly.get("completed_tasks", []):
            weekly.setdefault("completed_tasks", []).append(task_name)
        
        cfg[self.名称] = blob
        _sync_progress_attrs(self, blob)
        gl_info.配置.写入本地配置文件()
        print(f"✓ [Row:{self.row}] 已标记周常任务完成: {task_name}")
    
    def _获取本周未完成的周常任务(self):
        """
        获取本周未完成的周常任务列表
        
        Returns:
            list: 未完成的任务名称列表
        """
        all_weekly_tasks = [
            "剑会",
            # TODO: 在这里添加所有周常任务名称
            # "帮派竞赛",
            # "比武大会",
            # "秘境降妖",
        ]
        
        blob = self._get_weekly_blob()
        blob, _ = self._ensure_current_week(blob)
        
        completed = blob["weekly"].get("completed_tasks", [])
        return [task for task in all_weekly_tasks if task not in completed]
    # endregion

    # region 通用辅助方法（供周常任务和日常任务共用）
    def 关闭窗口(self):
        """
        处理意外弹窗、剧情、界面关闭等
        
        Returns:
            bool: 是否找到并关闭了窗口
        """
        # 处理意外报错框遮住的问题
        res, x, y = for_ms_row(self.row, [MS.意外报错])
        if res:
            print("找到意外报错")
            self.移动点击(x - 47, y - 93)
            # 优化：轮询等待响应
            self.轮询等待(lambda: False, max_wait=1.0, interval=0.2)
            self.滑动屏幕(x - 47, y - 93, 461, 733)
            self.轮询等待(lambda: False, max_wait=1.0, interval=0.2)
        
        res, x, y = for_ms_row(self.row, [MS.剧情中])
        if res:
            while True:
                print("剧情中....")
                # 优化：轮询等待界面变化（最多 1 秒）
                self.轮询等待(lambda: for_ms_row(self.row, [MS.剧情确定])[0] or 
                                         for_ms_row(self.row, [MS.是否跳过本段剧情])[0] or
                                         for_ms_row(self.row, [MS.快进,MS.快进1])[0] or
                                         not for_ms_row(self.row, [MS.剧情中])[0], 
                                  max_wait=1.0, interval=0.2)
                res, x, y = for_ms_row(self.row, [MS.剧情确定])
                if res:
                    print("点击剧情确定")
                    self.移动点击(x + 5, y + 5)
                    continue
                res, x, y = for_ms_row(self.row, [MS.是否跳过本段剧情])
                if res:
                    print("点击是否跳过本段剧情")
                    self.移动点击(x + 215, y + 50)
                    continue
                res, x, y = for_ms_row(self.row, [MS.快进, MS.快进1])
                if res:
                    print("跳过剧情！")
                    self.移动点击(x + 5, y + 5)
                    continue
                res, x, y = for_ms_row(self.row, [MS.剧情中])
                if not res:
                    break
            return True
        
        res, x, y = for_ms_row(self.row, [MS.是否跳过本段剧情])
        if res:
            print("点击是否跳过本段剧情")
            self.移动点击(x + 215, y + 50)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.打造关闭])
        if res:
            print("点击打造关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.加入帮派关闭])
        if res:
            print("点击加入帮派关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.帮战关闭])
        if res:
            print("点击帮战关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.快进, MS.快进1])
        if res:
            print("跳过剧情！")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.点击任意地方继续])
        if res:
            # 随机点击x,y坐标（285,231,632,384）范围
            print("点击任意地方继续")
            xx = random.randint(285, 632)
            yy = random.randint(231, 384)
            self.移动点击(xx, yy)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.师门任务完成确定])
        if res:
            print("点击师门任务完成确定")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.人物属性关闭])
        if res:
            print("点击人物属性关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.包裹界面关闭按钮])
        if res:
            print("关闭包裹界面")
            self.移动点击(x + 10, y + 10)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.点击空白区域关闭窗口])
        if res:
            print("点击空白区域关闭窗口")
            self.移动点击(71, 630)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.手动])
        if res:
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.活动面板关闭])
        if res:
            print("活动面板关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.个人空间关闭])
        if res:
            print("个人空间关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.确定1])
        if res:
            print("点击确定")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.算了])
        if res:
            print("点击确定")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.师门任务关闭])
        if res:
            print("师门任务关闭")
            self.移动点击(x + 5, y + 5)
            return True
        
        res, x, y = for_ms_row(self.row, [MS.知道了])
        if res:
            print("点击知道了")
            self.移动点击(x + 5, y + 5)
            return True
        else:
            return False
    
    def 组合按键(self, 按键1, 按键2):
        """
        执行组合按键操作
        
        Args:
            按键1: 第一个按键
            按键2: 第二个按键
        """
        try:
            self.dx.KM.hot_key([按键1, 按键2])
            print(f"组合按键: {按键1}, {按键2}")
        except OSError as e:
            print(f"⚠️ [Row:{self.row}] KM 组合按键操作失败 (OSError): {e}")
            return False
        except Exception as e:
            print(f"⚠️ [Row:{self.row}] 组合按键异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def 移动点击(self, x, y, 时间间隔=0.5, verify=None, verify_retries=None, verify_interval=None, pixel_verify=None):
        """
        稳妥移动并点击（带校验和重试机制）
        
        Args:
            x: 目标 x 坐标
            y: 目标 y 坐标
            时间间隔: 移动后等待时间（秒）
            verify: 校验函数（可选）
            verify_retries: 校验重试次数（可选）
            verify_interval: 校验间隔（可选）
            pixel_verify: 像素校验开关（可选）
        """
        km_稳妥移动点击(
            self.dx.KM,
            x,
            y,
            时间间隔,
            dx=self.dx,
            verify=verify,
            verify_retries=verify_retries,
            verify_interval=verify_interval,
            pixel_verify=pixel_verify,
        )
    # endregion

    def _daily_run_step(self, step_id, fn):
        """
        执行一步日常任务；已完成则跳过。若 fn 返回 False 则不标记完成（便于超时后重试）。
        
        Args:
            step_id: 步骤 ID
            fn: 任务函数
        """
        # 检查周常任务优先
        self._周常优先检查并执行()
        
        # 检查是否已跳过
        if self._daily_should_skip(step_id):
            print(f"[Row:{self.row}] [日常断点] ⏭️ 跳过已完成步骤: {step_id}")
            show_log(self.row, f"跳过: {step_id} (已完成)", 表格_进度)
            return
        
        # 记录开始时间
        start_time = time.time()
        task_name = getattr(fn, '__name__', str(step_id))
        
        # 输出开始日志
        print(f"\n{'='*60}")
        print(f"[Row:{self.row}] ▶ 开始任务: {task_name} (ID: {step_id})")
        print(f"{'='*60}")
        show_log(self.row, f"开始: {task_name}", 表格_进度)
        
        try:
            # 执行任务
            ret = fn()
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
            
            # 输出结果日志
            if ret is not False:
                print(f"[Row:{self.row}] ✓ 任务完成: {task_name} | 耗时: {time_str}")
                show_log(self.row, f"完成: {task_name} ({time_str})", 表格_进度)
                # 标记步骤完成
                self._daily_mark_step_done(step_id)
            else:
                print(f"[Row:{self.row}] ⚠ 任务返回 False (可能超时/失败): {task_name} | 耗时: {time_str}")
                show_log(self.row, f"未完成: {task_name} ({time_str})", 表格_状态)
            
            print(f"{'='*60}\n")
            
        except Exception as e:
            # 异常处理
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
            
            import traceback
            error_msg = f"❌ 任务异常: {task_name} | 耗时: {time_str} | 错误: {e}"
            print(f"[Row:{self.row}] {error_msg}")
            print(traceback.format_exc())
            show_log(self.row, f"异常: {task_name} ({time_str}): {e}", 表格_状态)

    def _周常优先检查并执行(self):
        """协作式周常：由调度线程写入 td_info 队列，本线程在检查点取出并执行（优先于日常）。"""
        row = self.row
        if not getattr(td_info[row], "weekly_pending", False):
            return
        try:
            sec = gl_info.配置.data.get("周常调度") or {}
        except Exception:
            sec = {}
        if sec.get("仅主界面触发", True):
            if td_info[row].process != "主界面":
                return
        from app.weekly_scheduler import snapshot_weekly_batch
        batch = snapshot_weekly_batch(row)
        if not batch:
            return
        for name in batch:
            func = getattr(self, name, None)
            if func is None or not callable(func):
                show_log(self.row, f"周常方法不存在: {name}", 表格_状态)
                continue
            try:
                show_log(self.row, f"周常优先: {name}", 表格_进度)
                func()
            except Exception as e:
                show_log(self.row, f"周常执行异常 {name}: {e}", 表格_状态)

    def 剑会(self):
        """
        剑会天下：周一周三周五20:00-23:00开放，周六周日12:00-20:00开放
        周任务，以周为记录，完成就不做了，刷新时间周一凌晨0:15
        """
        show_log(self.row, "剑会", 表格_进度)
        
        # ========== 前置检查 ==========
        if not self._检查周常任务是否已完成("剑会"):
            show_log(self.row, "✓ 剑会本周已完成，跳过")
            return True
        
        if not self._检查剑会开放时间():
            show_log(self.row, "⏰ 剑会未开放，跳过")
            return False
        
        # ========== 主流程 ==========
        try:
            print(f"[Row:{self.row}] 开始执行剑会任务")
            
            # TODO: 在这里添加具体的剑会任务逻辑
            while True:
                print(f"[Row:{self.row}] 剑会任务进行中...")
                res, x, y = for_ms_row(self.row, [MS.报名])
                if res:
                    print(f"[Row:{self.row}] 剑会报名")
                    self.移动点击(x + 5, y + 5)
                    time.sleep(1)
                    res, x, y = for_ms_row(self.row, [MS.本角色])
                    if res:
                        print(f"[Row:{self.row}] 本角色上架藏宝阁，无法报名剑会活动")
                        return True
                res, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                if res :
                    print(f"[Row:{self.row}] 活动界面已打开")
                    res, x, y = for_ms_row(self.row, [MS.竞技休闲])
                    if res:
                        self.移动点击(x + 15, y + 15)
                        time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.剑会群雄])
                        if res:
                            print(f"[Row:{self.row}] 剑会群雄已找到")
                            xx = x + 140
                            yy = y + 2
                            res, x, y = for_ms_row(self.row,
                                                   [[xx, yy, xx + 100, yy + 50, f"Common\\完成.bmp", "", 0.7, 5],
                                                    [xx, yy, xx + 100, yy + 50, f"Common\\参加.bmp", "", 0.7, 5],
                                                    [xx, yy, xx + 100, yy + 50, f"Common\\完成1.bmp", "", 0.7, 5]])
                            if res == 1 or res == 3:
                                print("剑会群雄已完成")
                                return True
                            if res == 2:
                                self.移动点击(x + 20, y + 10)
                                time.sleep(1)
                                continue
                        else:
                            print("剑会群雄未找到")
                            return False
                    continue
                else:
                    res, x, y = for_ms_row(self.row, [MS.右侧任务栏标记,MS.主角红蓝,MS.宠物红蓝])
                    if res:
                        self.组合按键('alt', 'c')
                        time.sleep(1)
                    else:
                        if self.关闭窗口():
                            continue
                        else:
                            res, x, y = for_ms_row(self.row, [MS.离开])
                            if res:
                                self.移动点击(x + 15, y + 15)
                                time.sleep(1)
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)
                            if self.关闭窗口():
                                continue
                            else:
                                # 打开活动界面
                                self.组合按键('alt', 'c')
                                time.sleep(1)
            # 标记任务完成
            self._标记周常任务完成("剑会")
            show_log(self.row, "✓ 剑会任务完成")
            return True
            
        except Exception as e:
            import traceback
            error_msg = f"❌ 剑会任务异常: {e}\n{traceback.format_exc()}"
            print(error_msg)
            show_log(self.row, f"剑会任务异常: {e}", 表格_状态)
            return False
    
    def _检查剑会开放时间(self):
        """
        检查当前时间是否在剑会开放时间内
        
        Returns:
            bool: 是否开放
        """
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=周一, 6=周日
        hour = now.hour
        
        # 周一、三、五: 20:00-23:00
        if weekday in [0, 2, 4]:  # 周一、三、五
            return 20 <= hour < 23
        
        # 周六、日: 12:00-20:00
        if weekday in [5, 6]:  # 周六、日
            return 12 <= hour < 20
        
        # 周二、四: 不开放
        return False
    
    def 周常任务(self):
        """
        周常任务总调度器
        在 [周常调度] 规则列表的 task 字段中填写「周常任务」即可被调度调用
        """
        show_log(self.row, "周常任务（总调度）", 表格_进度)
        print(f"[Row:{self.row}] 开始执行周常任务")
        
        # ========== 周常任务列表 ==========
        weekly_tasks = [
            {"name": "剑会", "func": self.剑会},
            # TODO: 在这里添加更多周常任务
            # {"name": "帮派竞赛", "func": self.帮派竞赛},
            # {"name": "比武大会", "func": self.比武大会},
            # {"name": "秘境降妖", "func": self.秘境降妖},
        ]
        
        # ========== 执行所有周常任务 ==========
        completed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for task in weekly_tasks:
            task_name = task["name"]
            task_func = task["func"]
            
            try:
                print(f"\n{'='*50}")
                print(f"[Row:{self.row}] 执行周常任务: {task_name}")
                print(f"{'='*50}")
                
                result = task_func()
                
                if result:
                    completed_count += 1
                    print(f"✓ {task_name} 完成")
                else:
                    skipped_count += 1
                    print(f"⏭ {task_name} 跳过")
                
                # 🔧 稳定性优化：周常任务之间随机休息 1-3 秒
                import random
                rest_time = random.uniform(1.0, 3.0)
                print(f"\n{'='*50}")
                print(f"[Row:{self.row}] ☕ [周常间隔] {task_name} 已完成，休息 {rest_time:.1f} 秒...")
                print(f"{'='*50}\n")
                time.sleep(rest_time)
                    
            except Exception as e:
                import traceback
                error_msg = f"❌ {task_name} 执行异常: {e}\n{traceback.format_exc()}"
                print(error_msg)
                show_log(self.row, f"{task_name} 异常: {e}", 表格_状态)
                failed_count += 1
        
        # ========== 总结 ==========
        print(f"\n{'='*50}")
        print(f"[Row:{self.row}] 周常任务执行完毕")
        print(f"  完成: {completed_count}")
        print(f"  跳过: {skipped_count}")
        print(f"  失败: {failed_count}")
        print(f"{'='*50}\n")
        
        show_log(self.row, f"周常任务完成 (完成:{completed_count}, 跳过:{skipped_count}, 失败:{failed_count})")
        
        # 如果全部完成或跳过，标记周常任务整体完成
        if failed_count == 0:
            self._标记周常任务完成("周常任务总调度")
        
        return failed_count == 0  # 没有失败则返回 True

    def 等待排队结束(self, interval=None):
        """
        识别到「退出排队」即仍在排队。根据 OCR 预计等待文案调整下次检测间隔：
        - 含「X小时」且 X>=1：约 30 分钟后再识别；
        - 仅分钟级（0 小时但 Y>0 分，或能解析到分且无小时）：约 1 分钟；
        - OCR 无结果或解析不到小时/分：interval 秒（默认 5）。
        
        修复：增加连续检测次数，避免误判
        """
        show_log(self.row, "等待排队结束")
        if interval is None:
            interval = _QUEUE_POLL_NO_OCR_SEC
        x1, y1, x2, y2 = _QUEUE_ETA_OCR_XY
        
        # 连续检测到"不在排队"的次数，确保真的不在排队了
        not_in_queue_count = 0
        required_not_in_queue = 3  # 需要连续3次检测不到"退出排队"才认为排队结束
        
        while True:
            res, x, y = for_ms_row(self.row, [MS.退出排队])
            if res:
                # 找到"退出排队"按钮 → 确实在排队中
                print("排队中...")
                not_in_queue_count = 0  # 重置计数器
                next_sleep = interval
                ocr = getattr(getattr(self, 'dx', None), 'Ocr', None)
                if ocr:
                    try:
                        ocr_results = ocr.Ocr(x1, y1, x2, y2)
                        if ocr_results:
                            full = "".join((item[0] or "") for item in ocr_results)
                            print(f"预计等待时间: {ocr_results}")
                            h, m, ok = _parse_queue_eta_hours_minutes(full)
                            if ok:
                                if h >= 1:
                                    next_sleep = _QUEUE_POLL_HOUR_LEVEL_SEC
                                    print(f"检测到长时间排队: {h}小时{m}分，{next_sleep}秒后再次检查")
                                elif m > 0:
                                    next_sleep = _QUEUE_POLL_MINUTE_LEVEL_SEC
                                    print(f"检测到短时间排队: {h}小时{m}分，{next_sleep}秒后再次检查")
                    except Exception as e:
                        print(f"OCR识别排队时间失败: {e}")
                time.sleep(next_sleep)
            else:
                # 未找到"退出排队"按钮 → 可能不在排队了
                not_in_queue_count += 1
                print(f"未检测到排队状态 ({not_in_queue_count}/{required_not_in_queue})")
                
                if not_in_queue_count >= required_not_in_queue:
                    # 连续3次都检测不到，确认排队已结束
                    print("✅ 排队已结束，开始执行任务")
                    break
                else:
                    # 还未达到连续次数，继续检测
                    time.sleep(2)  # 短暂等待后再次检测

    # endregion
    # region 获取账号信息
    def 获取账号信息(self):
        """
        获取当前账号信息
        返回: dict 包含 {编号, 账号, 密码, 区服, 角色}
        """
        try:
            # 获取当前行的编号（从表格中获取）
            row_values = get_row_content(self.row)
            编号 = str(row_values[1])  # 获取编号，如 "5600"（索引1是编号）

            # 从配置中获取该编号对应的账号列表
            账号配置 = gl_info.配置.get("账号配置", {})
            if 编号 not in 账号配置:
                # show_log(self.row, f"未找到编号 {编号} 的账号配置")
                return None

            账号列表 = 账号配置[编号]

            # 如果账号列表是字符串，尝试解析为列表
            if isinstance(账号列表, str):
                import ast
                try:
                    账号列表 = ast.literal_eval(账号列表)
                except:
                    # show_log(self.row, f"编号 {编号} 的账号列表格式无法解析")
                    return None

            # 如果账号列表为空或不是列表格式，返回None
            if not 账号列表 or not isinstance(账号列表, list):
                # show_log(self.row, f"编号 {编号} 的账号列表为空或格式错误")
                return None

            # 使用 now_user_id 作为索引选择当前账号（默认为0）
            账号索引 = self.now_user_id if hasattr(self, 'now_user_id') else 0

            # 确保索引在有效范围内
            if 账号索引 >= len(账号列表):
                # show_log(self.row, f"账号索引 {账号索引} 超出范围，使用索引 0")
                账号索引 = 0

            # 获取当前账号的字符串信息
            账号信息字符串 = 账号列表[账号索引]

            # 解析账号信息：格式为 "账号|密码|区服|角色"
            账号信息列表 = 账号信息字符串.split('|')

            if len(账号信息列表) != 4:
                # show_log(self.row, f"账号信息格式错误: {账号信息字符串}")
                return None

            账号, 密码, 区服, 角色 = 账号信息列表

            # 返回账号信息字典
            账号信息 = {
                '编号': 编号,
                '账号': 账号.strip(),
                '密码': 密码.strip(),
                '区服': 区服.strip(),
                '角色': 角色.strip()
            }

            # show_log(self.row, f"获取账号信息成功: 编号={编号}, 账号={账号}, 区服={区服}, 角色={角色}")
            return 账号信息

        except Exception as e:
            # show_log(self.row, f"获取账号信息异常: {str(e)}")
            return None

    def 获取所有账号信息(self):
        """
        获取当前编号对应的所有账号信息
        返回: list 包含多个账号信息字典 [{编号, 账号, 密码, 区服, 角色}, ...]
        """
        try:
            # 获取当前行的编号（从表格中获取）
            row_values = get_row_content(self.row)
            编号 = str(row_values[1])  # 获取编号，如 "5600"（索引1是编号）

            # 从配置中获取该编号对应的账号列表
            账号配置 = gl_info.配置.get("账号配置", {})
            if 编号 not in 账号配置:
                # show_log(self.row, f"未找到编号 {编号} 的账号配置")
                return []

            账号列表 = 账号配置[编号]

            # 如果账号列表是字符串，尝试解析为列表
            if isinstance(账号列表, str):
                import ast
                try:
                    账号列表 = ast.literal_eval(账号列表)
                except:
                    # show_log(self.row, f"编号 {编号} 的账号列表格式无法解析")
                    return []

            # 如果账号列表为空或不是列表格式，返回空列表
            if not 账号列表 or not isinstance(账号列表, list):
                # show_log(self.row, f"编号 {编号} 的账号列表为空或格式错误")
                return []

            所有账号信息 = []

            # 循环遍历所有账号
            for 账号索引, 账号信息字符串 in enumerate(账号列表):
                try:
                    # 解析账号信息：格式为 "账号|密码|区服|角色"
                    账号信息列表 = 账号信息字符串.split('|')

                    if len(账号信息列表) != 4:
                        # show_log(self.row, f"账号索引 {账号索引} 格式错误: {账号信息字符串}")
                        continue

                    账号, 密码, 区服, 角色 = 账号信息列表

                    # 添加到结果列表
                    账号信息 = {
                        '编号': 编号,
                        '账号': 账号.strip(),
                        '密码': 密码.strip(),
                        '区服': 区服.strip(),
                        '角色': 角色.strip(),
                        '索引': 账号索引
                    }
                    所有账号信息.append(账号信息)

                except Exception as e:
                    # show_log(self.row, f"解析账号索引 {账号索引} 时出错: {str(e)}")
                    continue

            return 所有账号信息

        except Exception as e:
            # show_log(self.row, f"获取所有账号信息异常: {str(e)}")
            return []

    # endregion
    # region 登陆
    def login(self):
        """
        按当前行的「编号」建立 VNC 截图 + VNC 键鼠 + ONNX OCR（复用同一条截图连接）。
        内部含大量闭包（打开游戏、更新确认等），主体流程见末尾：取账号信息 → 设置截图/键鼠/OCR。
        """
        def 移动点击(x, y, 时间间隔=0.5, verify=None, verify_retries=None, verify_interval=None, pixel_verify=None):
            km_稳妥移动点击(
                self.dx.KM,
                x,
                y,
                时间间隔,
                dx=self.dx,
                verify=verify,
                verify_retries=verify_retries,
                verify_interval=verify_interval,
                pixel_verify=pixel_verify,
            )

        def 双击左键():
            self.dx.KM.LeftClick()
            time.sleep(0.1)
            self.dx.KM.LeftClick()

        def 游戏更新完成 ():
            res, x, y = for_ms_row(self.row, [MS.游戏更新完成])
            if res:
                show_log(self.row, "游戏更新完成")
                while True:
                    res, x, y = for_ms_row(self.row, [MS.游戏更新完成])
                    if res:
                        print("游戏更新完成，点击确定")
                        移动点击 (x + 170, y + 105)
                        # 优化：轮询等待按钮响应（最多 1 秒）
                        轮询等待 (lambda: not for_ms_row(self.row, [MS.游戏更新完成])[0], max_wait=1.0, interval=0.2)
                    else:
                        break
                    # 优化：轮询等待界面变化（最多 1 秒）
                    轮询等待 (lambda: for_ms_row(self.row, [MS.游戏更新完成])[0], max_wait=1.0, interval=0.2)

        def 打开游戏 ():
            res, x, y = for_ms_row(self.row, [MS.梦幻西游图标])
            if res:
                print("找到梦幻西游图标")
                # 优化：轮询等待界面稳定（最多 1 秒）
                轮询等待 (lambda: True, max_wait=1.0, interval=0.2)
                移动点击 (x + 10, y + 10)
                time.sleep(0.5)
                双击左键 ()
                # 优化：轮询等待启动（最多 1 秒）
                轮询等待 (lambda: False, max_wait=1.0, interval=0.2)  # 简单延迟替代
                return True

        # 获取

        

        # 检测分辨率

        # 设置截图模式
        def 设置截图模式 (编号):
            # self.dx.screenshot = DXGI(self.hwnd)
            # 启用 DirectML GPU 加速后，提高 VNC FPS 到 8（原 3），提升响应速度
            print(f"[Row:{self.row}] 📡 正在创建 VNC 连接: 127.0.0.1:{编号}...")
            
            try:
                vnc_obj = VNC("127.0.0.1", 编号,"", fps=2)  # 🔧 稳定性优化：降低 FPS 至 2，回合制游戏足够，减少资源占用
                print(f"[Row:{self.row}] ✅ VNC 对象创建成功: ID={id(vnc_obj)}")
                
                # 验证 client 是否正常
                if not hasattr(vnc_obj, 'client') or vnc_obj.client is None:
                    print(f"[Row:{self.row}] ❌ VNC 对象创建后 client 为 None！")
                    raise RuntimeError("VNC 初始化失败：client 为 None")
                
                # 赋值给 self.dx.screenshot
                self.dx.screenshot = vnc_obj
                print(f"[Row:{self.row}] ✅ VNC 已赋值给 self.dx.screenshot")
                
                # 启动后台截图线程
                self.dx.screenshot.for_capture()
                
                # 优化：使用轮询等待 VNC 连接稳定（最多 3 秒，提前就绪则立即继续）
                print("等待 VNC 截图就绪...")
                轮询等待 (lambda: hasattr(self.dx.screenshot, 'image') and self.dx.screenshot.image is not None, max_wait=3.0, interval=0.2)
                print("VNC 截图已就绪")
                
                # 最后验证
                if self.dx.screenshot.client is None:
                    print(f"[Row:{self.row}] ❌ VNC 初始化完成后 client 变为 None！")
                    raise RuntimeError("VNC client 在初始化后被清空")
                    
            except Exception as e:
                print(f"[Row:{self.row}] ❌ 设置截图模式失败: {e}")
                import traceback
                traceback.print_exc()
                raise

        # 测试截图
        def 测试截图():
            image = self.dx.screenshot.Capture()
            MiniOpenCV.imshow("截图", image)
            MiniOpenCV.waitKey(0)
            show_log(self.row, "截图完成")

        # 设置键鼠模式
        def 设置键鼠模式(编号):
            # self.hwnd = 6690340
            # self.dx.KM = DXKM(self.hwnd)
            self.dx.KM = VNC_KM("127.0.0.1", 编号, "")
            md = _env_float("VNC_MOUSE_DELAY", 0.05)
            kd = _env_float("VNC_KEY_DELAY", 0.01)
            if md > 0 and kd >= 0:
                self.dx.KM.set_delay(key_delay=kd, mouse_delay=md)

        # 测试键鼠
        def 测试键鼠():
            self.dx.KM.MoveTo(34,145)
            time.sleep(0.1)
            for i in range(2):
                self.dx.KM.LeftClick()

        def 设置_OCR_识别模式 ():
            # ⚠️ 关键配置：多开时必须禁用共享模式，否则会导致锁竞争和识别失败
            import os
            
            # 🔧 强制 CPU 模式（避免 GPU 并发冲突）
            os.environ['ONNX_OCR_SHARED'] = '0'  # 每个窗口独立加载模型
            os.environ['ONNX_USE_GPU'] = '0'     # 强制 CPU 模式
            
            # 更新配置类
            try:
                from app.onnx_config import ONNXRuntimeConfig
                ONNXRuntimeConfig.use_cpu()
                logging.info(f"✓ 已强制切换到 CPU 模式 (Row:{self.row})")
            except Exception as e:
                logging.warning(f"⚠️ 无法切换 CPU 模式: {e}")
            
            # 复用已有的截图连接，避免重复连接 VNC 服务器
            # 使用企业级 ONNX OCR，精度更高，支持中文、英文、日文等多种语言
            self.dx.Ocr = ONNX_OCR(vnc_instance=self.dx.screenshot, use_gpu=False, drop_score=0.5)
            logging.info(f"✓ ONNX OCR 引擎已初始化（CPU 模式，独立实例 - Row:{self.row}）")
            
            # 预热模型（避免首次调用慢）
            try:
                print(f"[Row:{self.row}] 正在预热 OCR 模型...")
                import numpy as np
                test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                _ = self.dx.Ocr._ocr_infer(test_img)
                print(f"[Row:{self.row}] ✓ OCR 模型预热完成")
            except Exception as e:
                print(f"[Row:{self.row}] ❌ OCR 模型预热失败：{e}")
                import traceback
                traceback.print_exc()
                raise

        def 测试OCR识别():
            # OCR识别区域 (x1, y1, x2, y2) - 左上角和右下角坐标
            x1, y1, x2, y2 =428,122,532,151

            # 验证坐标
            if x1 >= x2 or y1 >= y2:
                show_log(self.row, f"OCR坐标错误: ({x1}, {y1}, {x2}, {y2}) - 左上角坐标必须小于右下角坐标")
                return

            show_log(self.row, f"开始OCR识别区域: ({x1}, {y1}) -> ({x2}, {y2}), 尺寸: {x2 - x1}x{y2 - y1}")

            # 执行OCR识别
            results = self.dx.Ocr.Ocr(x1, y1, x2, y2)
            show_log(self.row, f"OCR识别结果数量: {len(results)}")

            if results:
                for i, (text, pos, confidence) in enumerate(results):
                    show_log(self.row, f"结果{i + 1}: {text} | 位置: {pos} | 置信度: {confidence:.2f}")
            else:
                show_log(self.row, "未识别到任何文本")

        def 账号登录 ():
            pass

        # ---------- 登录主流程：编号决定 VNC 端口；账号信息来自配置里该编号下的列表 ----------
        账号信息 = self.获取账号信息()
        if not 账号信息:
            show_log(self.row, "获取账号信息失败，无法继续")
            return
        编号 = 账号信息 ['编号']
        账号 = 账号信息 ['账号']
        密码 = 账号信息 ['密码']
        区服 = 账号信息 ['区服']
        角色 = 账号信息 ['角色']
        # 优化：使用轮询等待界面加载（最多 10 秒，提前就绪则立即继续）
        print("等待游戏界面加载...")
        轮询等待 (lambda: False, max_wait=10.0, interval=0.5)  # 简单延迟替代
        设置截图模式 (编号)
        # 测试截图()
        设置键鼠模式(编号)
        # 测试键鼠()
        设置_OCR_识别模式()

        # 测试OCR识别()
        # show_log(self.row, "测试OCR识别完成")
        # time.sleep(180)
        # if 游戏更新完成():
        #     time.sleep(2)
        #     if 打开游戏():
        #         return True
        # else:
        #     if 打开游戏():
        #         return True

    # endregion
    # region 初始化任务
    def 初始化任务(self):
        """
        调度器：遍历表格第 4 列配置的任务方法名，按 now_task_id 断点续跑。
        每步更新「进度配置」、表格进度列；异常时依赖 td_info[self.row].process 标记；结束 clear_resource。
        """

        def 读取所有耗时(task_list_id):
            task_delays = []
            for i in task_list_id:
                task_delays.append(int(gl_info.配置.get("耗时配置", {}).get(str(i), 0)))
            return task_delays

        def 保存耗时(task_id, delay_time):
            gl_info.配置.添加("耗时配置", str(task_id), str(int(delay_time / 60)))
            gl_info.配置.写入本地配置文件()

        show_log(self.row, "运行中", 表格_状态)
        result = gl_info.result
        # 🔧 调试：打印当前进度配置
        print(f"\n{'='*80}")
        print(f"[Row:{self.row}] 📊 [任务调度] 开始执行任务")
        print(f"[Row:{self.row}] 📊 当前 now_task_id: {self.now_task_id}")
        cfg_debug = gl_info.配置.get("进度配置", {}).get(self.名称, {})
        if isinstance(cfg_debug, dict):
            daily_debug = cfg_debug.get("daily", {})
            print(f"[Row:{self.row}] 📊 日常进度 - calendar_date: {daily_debug.get('calendar_date', 'N/A')}")
            print(f"[Row:{self.row}] 📊 日常进度 - account_index: {daily_debug.get('account_index', 0)}")
            print(f"[Row:{self.row}] 📊 日常进度 - completed_steps: {daily_debug.get('completed_steps', [])}")
            print(f"[Row:{self.row}] 📊 日常进度 - branch: {daily_debug.get('branch', None)}")
            print(f"[Row:{self.row}] 📊 日常进度 - random_order: {daily_debug.get('random_order', [])}")
        print(f"{'='*80}\n")
        
        # 任务名与界面/配置联动：result 来自控制器注入；真正执行顺序以本行第 4 列 task_id_list 为准
        all_task_list = result.get("message", {}).get("所有任务")
        if not all_task_list or not isinstance(all_task_list, dict):
            show_log(self.row, "异常:所有任务")
            return
        task_id_list = get_row_content(self.row)[3].split(",")
        task_delays = 读取所有耗时(task_id_list)
        
        # 🔧 获取已完成的日常步骤列表
        cfg_steps = gl_info.配置.get("进度配置", {}).get(self.名称, {})
        completed_daily_steps = []
        if isinstance(cfg_steps, dict) and "daily" in cfg_steps:
            completed_daily_steps = cfg_steps["daily"].get("completed_steps", [])
        
        for i, task_name in enumerate(task_id_list):
            if not task_name:
                continue

            if i < self.now_task_id:
                continue
            
            # 🔧 检查是否是日常任务，如果是则检查内部步骤是否已完成
            if task_name == "日常任务" and completed_daily_steps:
                print(f"\n{'='*80}")
                print(f"[Row:{self.row}] ⏭️ [跳过检查] 检测到日常任务")
                print(f"[Row:{self.row}] ⏭️ [跳过检查] 已完成步骤: {completed_daily_steps}")
                print(f"[Row:{self.row}] ⏭️ [跳过检查] 将自动跳过已完成的子步骤")
                print(f"{'='*80}\n")
            
            # 保存进度
            self.now_task_id = i
            保存进度(self, self.now_user_id, self.now_server_id, self.now_task_id, self.now_fuben_id)

            show_log(self.row, task_name, 表格_进度)
            func = getattr(self, task_name, None)
            if func is None:
                show_log(self.row, "异常:任务不存在 %s" % task_name)
                return
            td_info[self.row].process = func.__name__
            show_log(self.row, f"{func.__name__} 开始")

            func()
            if td_info[self.row].process == "任务异常":
                break
            show_log(self.row, f"{func.__name__} 完成")
            
            # 🔧 稳定性优化：任务完成后随机休息 1-3 秒，给 VNC 缓冲时间
            import random
            rest_time = random.uniform(1.0, 3.0)
            print(f"\n{'='*80}")
            print(f"[Row:{self.row}] ☕ [任务间隔] {func.__name__} 已完成，休息 {rest_time:.1f} 秒...")
            print(f"{'='*80}\n")
            time.sleep(rest_time)
            
            # 🔧 调试：任务完成后打印进度状态
            print(f"\n{'='*80}")
            print(f"[Row:{self.row}] ✅ [任务完成] {func.__name__}")
            cfg_after = gl_info.配置.get("进度配置", {}).get(self.名称, {})
            if isinstance(cfg_after, dict):
                daily_after = cfg_after.get("daily", {})
                print(f"[Row:{self.row}] 📊 完成后进度 - completed_steps: {daily_after.get('completed_steps', [])}")
                print(f"[Row:{self.row}] 📊 完成后进度 - account_index: {daily_after.get('account_index', 0)}")
            print(f"{'='*80}\n")
        
        # 🔧 检查是否是因为跨天重置而退出，如果是则标记需要重启
        if hasattr(self, '_daily_restart_triggered') and self._daily_restart_triggered:
            today_str = datetime.datetime.now().date().isoformat()
            if today_str in self._daily_restart_triggered:
                print(f"\n{'='*60}")
                print(f"[Row:{self.row}] 🔄 检测到跨天重置标记")
                print(f"[Row:{self.row}] 🔄 当前线程将退出，请外部监控线程自动重启")
                print(f"{'='*60}\n")
                
                # 🔧 关键修复：不在此处停止线程，而是直接返回
                # 让当前线程自然退出，由外部监控线程（或 ThreadController）检测到退出后自动重启
                show_log(self.row, f"🔄 跨天重置，线程即将退出...", 表格_状态)
                return  # 直接返回，不执行 clear_resource，让线程自然结束

        # 最后一个任务如果是完成，则清理进度
        if td_info[self.row].process == "任务完成":
            保存进度(self, 0, 0, 0, 0)
        # if td_info[self.row].process == "任务完成":
        #     gl_info.show_message_async("任务完成","OK","green")
        # else:
        #     gl_info.show_message_async("任务异常", "ERR","red")
        # 清理资源
        clear_resource(self.row)
        show_log(self.row, "完成", 表格_状态)
        show_log(self.row, "所有完成")

    # endregion
    # region 初始化游戏界面
    def game_init(self):
        """状态机中的「进游戏初始化」占位；当前为空，后续可放分辨率/首次弹窗等一次性逻辑。"""
        pass

    # endregion
    # region VNC 心跳检测
    def 检查VNC状态 (self):
        """
        检查 VNC 状态，如果异常则自动重连
        每 30 秒检查一次心跳
        """
        if getattr(self, "_vnc_reconnecting", False):
            return
        current_time = time.time()
        # 如果距离上次心跳超过 30 秒，进行检查
        if current_time - self._vnc_last_heartbeat >= 30:
            self._vnc_last_heartbeat = current_time
                        
            # 健康检查（统一退避重试，降低瞬时抖动误判）
            healthy = 退避重试(
                "VNC健康检查",
                lambda: VNC健康检查(self.dx.screenshot),
                重试次数=2,
                初始等待=0.2,
                最大等待=0.5,
            )
            if not healthy:
                print("[VNC 心跳] 检测到连接异常！")
                show_log(self.row, "VNC 连接异常，尝试重连...")
                            
                # 获取编号进行重连
                账号信息 = self.获取账号信息 ()
                if 账号信息:
                    编号 = 账号信息 ['编号']
                    if VNC自动重连 (self, 编号):
                        show_log(self.row, "VNC 重连成功")
                    else:
                        show_log(self.row, "VNC 重连失败", 表格_状态)
                        raise Exception("VNC 重连失败")
            else:
                # VNC 正常，更新心跳
                pass  # 已在上面更新时间
    
    def _保存金币截图(self, x1, y1, x2, y2, 金币数值):
        """
        截取金币区域并保存到临时目录
        
        Args:
            x1, y1, x2, y2: 截图区域坐标
            金币数值: OCR识别的金币数量（用于文件名）
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        import os
        import time
        from PIL import Image
        import cv2
        import numpy as np
        
        try:
            # 🔧 检查 VNC 连接状态
            if not hasattr(self.dx, 'screenshot') or self.dx.screenshot is None:
                print(f"[Row:{self.row}] ⚠️ [金币截图] VNC 对象不存在")
                return False
            
            # 验证并修正坐标
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            if x1 == x2 or y1 == y2:
                print(f"[Row:{self.row}] ⚠️ [金币截图] 截图坐标无效: ({x1},{y1})-({x2},{y2})")
                return False
            
            # 截图
            screenshot = self.dx.screenshot.Capture(x1, y1, x2, y2)
            
            if screenshot is None:
                print(f"[Row:{self.row}] ⚠️ [金币截图] 截图失败：图像数据为空")
                return False
            
            # 🔧 关键修复：确保 screenshot 是 numpy 数组
            if not isinstance(screenshot, np.ndarray):
                # 如果是 PIL Image，转换为 numpy
                if hasattr(screenshot, 'convert'):
                    screenshot = np.array(screenshot.convert('RGB'))
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                # 如果是 bytes，尝试转换
                elif isinstance(screenshot, bytes):
                    print(f"[Row:{self.row}] ⚠️ [金币截图] 截图为bytes类型，尝试转换...")
                    # 这里需要根据实际格式处理
                    return False
                else:
                    print(f"[Row:{self.row}] ⚠️ [金币截图] 未知的截图类型: {type(screenshot)}")
                    return False
            
            # 验证 numpy 数组的有效性
            if screenshot.ndim != 3 or screenshot.shape[2] != 3:
                print(f"[Row:{self.row}] ⚠️ [金币截图] 图像格式不正确: shape={screenshot.shape}")
                return False
            
            # 转换为PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # 创建缩略图（用于UI提示框）
            thumbnail = pil_image.copy()
            thumbnail.thumbnail((200, 60))  # 缩略图尺寸
            
            # 存储到实例变量
            timestamp = time.time()
            self._gold_screenshot_data = {
                'image': pil_image,
                'thumbnail': thumbnail,
                'timestamp': timestamp,
                'gold_text': str(金币数值),
                'region': (x1, y1, x2, y2)
            }
            
            # 🔧 保存到文件（可选，用于调试）
            try:
                save_dir = os.path.join("Temporary", "gold_screenshots")
                os.makedirs(save_dir, exist_ok=True)
                
                filename = f"row{self.row}_{int(timestamp)}_{金币数值}.png"
                filepath = os.path.join(save_dir, filename)
                pil_image.save(filepath)
                print(f"[Row:{self.row}] ✅ [金币截图] 已保存: {filepath}")
            except Exception as e:
                print(f"[Row:{self.row}] ⚠️ [金币截图] 保存文件失败: {e}")
            
            print(f"[Row:{self.row}] ✅ [金币截图] 成功 - 金币: {金币数值}")
            return True
            
        except Exception as e:
            print(f"[Row:{self.row}] ❌ [金币截图] 异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _更新金币UI显示(self, 金币数值):
        """
        更新UI表格中的金币列显示
        
        Args:
            金币数值: OCR识别的金币数量
        """
        try:
            # 🔧 通过全局控制器更新UI
            from app.public_function import gl_info
            
            if hasattr(gl_info, 'controller') and gl_info.controller:
                # 调用controller的更新方法
                gl_info.controller.update_gold_display(self.row, 金币数值)
                print(f"[Row:{self.row}] ✅ [金币UI] 已更新显示: {金币数值}")
            else:
                print(f"[Row:{self.row}] ⚠️ [金币UI] Controller未初始化，跳过UI更新")
                
        except Exception as e:
            print(f"[Row:{self.row}] ❌ [金币UI] 更新失败: {e}")
            import traceback
            traceback.print_exc()
        
    # endregion

    # endregion 初始化

    # region 任务
    # region 任务1
    def 日常任务(self):
        """
        游戏内主流程容器：
        - 前半：定义 主界面 及其内部闭包（通用操作 + 各「日常_xxx」子块）。
        - 末尾 while True：读 td_info[self.row].process，驱动 登陆 → game_init → 主界面 状态迁移。
        """
        # ---------- 主界面：进入游戏后的日常编排（活跃值分支、随机/固定任务链、摆摊捉鬼等）----------
        def 主界面(row):

            def 识别金币 ():
                """
                获取 金币信息（增强版：支持截图保存和UI显示）
                
                Returns:
                    bool: 获取金币成功返回True，失败返回False
                    
                实现思路：
                1. 判断是否进入了包裹界面
                2. OCR识别金币数量
                3. 🔧 新增：截取金币区域图片并保存
                4. 🔧 新增：更新UI表格显示
                """
                show_log(row, "识别金币")
                #初始时间
                start_time = time.time()
                # 获取金币
                while True:
                    if time.time() - start_time > 60:
                        print("⚠️ 识别金币超时")
                        return False
                                
                    # 每次循环前检查 VNC 状态（每 30 秒一次）
                    try:
                        self.检查VNC状态 ()
                    except Exception as e:
                        print(f"VNC 检查失败：{e}")
                        continue
                                
                    res, x, y = for_ms_row(self.row, [MS.包裹界面关闭按钮,MS.包裹界面])
                    if res:
                        print("开始获取金币")
                        # 使用 OCR 缓存，避免重复识别同一区域
                        cache_key = ('金币', 105, 606, 233, 628)
                        results = self.ocr_cache.get(cache_key)
                        if results is None:
                            results = 退避重试(
                                "OCR识别金币",
                                lambda: self.dx.Ocr.Ocr(105, 606, 233, 628),
                                重试次数=3,
                                初始等待=0.15,
                                最大等待=0.6,
                            )
                            self.ocr_cache.set(cache_key, results)
                        
                        if results:
                            金币数值 = results[0][0]
                            识别率 = results[0][2]
                            
                            # 🔧 关键修复：排除金币数值中的逗号
                            金币数值_清理 = str(金币数值).replace(',', '').replace('，', '')
                            
                            show_log(row, f"金币:{金币数值_清理}  识别率:{识别率:.2f}", 表格_收益)
                            
                            # 🔧 新增：截取金币区域截图并保存
                            try:
                                self._保存金币截图(105, 606, 233, 628, 金币数值_清理)
                            except Exception as e:
                                print(f"⚠️ 保存金币截图失败: {e}")
                            
                            # 🔧 新增：更新UI显示（使用清理后的数值）
                            try:
                                self._更新金币UI显示(金币数值_清理)
                            except Exception as e:
                                print(f"⚠️ 更新金币UI显示失败: {e}")
                            
                            time.sleep(1)
                            return True
                        else:
                            print("OCR识别金币失败")
                            return False
                        time.sleep(1)
                    else:
                        if 关闭窗口():
                            pass
                        else:
                            ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                            if 识别角色等级() != -1 or ress or 识别宠物等级()!= -1:
                                组合按键('alt', 'e')
                                time.sleep(1)
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)
            def 验证账号是否正确图片版本(账号):
                print(f"  🔍 验证账号 - 图片识别: '{账号}'")
                # 判断账号类型并预处理
                if '@' in 账号:
                    # 邮箱账号：保留@符号及之前的内容
                    账号 = 账号.split('@')[0] + '@'
                    print(f"  📧 邮箱账号处理完成: {账号}")
                else:
                    # 电话号码：不做处理，直接使用
                    print(f"  📱 电话号码，无需处理: {账号}")

                while True:
                    # 用户中心图标
                    res, x, y = for_ms_row(self.row, [MS.用户图标,MS.用户图标1])
                    if res:
                        移动点击(x+5, y+5)
                        time.sleep(1)
                        continue
                    # 用户中心图标
                    res,x,y = for_ms_row(self.row, [MS.用户图标1, MS.用户中心])
                    if res:
                        移动点击(385,381)
                        time.sleep(1)
                        continue
                    res,x,y = for_ms_row(self.row, [MS.账号界面])
                    if not res:
                        print("未找到账号界面")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.账号登录界面特征])
                    if res:
                        #优先识别一次，识别到账号就退出，没识别到就正常流程走
                        res, x, y = for_ms_row(self.row, [[319, 385, 630, 519, f"账号\\{账号}.bmp", "", 0.9, 5]])
                        if res:
                            print(f"  ✅ 账号识别成功,{账号}")
                            移动点击(x + 70, y + 10)
                            time.sleep(3)
                            ress = wait_for_ms(self.row, [MS.进入游戏, MS.进入游戏1])
                            if ress:
                                移动点击(471, 435)
                                print("  ✅ 进入游戏成功")
                                time.sleep(1)
                                return True
                        # 重置账号选择界面（向上滑动到顶部）
                        for i in range(10):
                            res, x, y = for_ms_row(self.row, [MS.账号界面])
                            if not res:
                                break
                            检查画面是否变化_前置截图(324,386,493,423)
                            滑动屏幕(619, 449,618, 404)
                            time.sleep(1)
                            # 画面如果没变化就退出
                            if not 检查画面是否变化_验证截图(324,386,493,423):
                                break
                        # 循环查找账号
                        for i in range(10):
                            res, x, y = for_ms_row(self.row, [MS.账号界面])
                            if not res:
                                return False
                            res, x, y = for_ms_row(self.row,[[319,385,630,519, f"账号\\{账号}.bmp", "", 0.9, 5]] )
                            if res:
                                print(f"  ✅ 账号识别成功,{账号}")
                                移动点击(x+70, y+10)
                                time.sleep(3)
                                ress = wait_for_ms(self.row, [MS.进入游戏,MS.进入游戏1])
                                if ress:
                                    移动点击(471,435)
                                    print("  ✅ 进入游戏成功")
                                    time.sleep(5)
                                    return True
                            else:
                                检查画面是否变化_前置截图(323,444,456,513)
                                滑动屏幕(618,404,619,449)
                                time.sleep(1)
                                # 画面如果没变化就退出
                                if not 检查画面是否变化_验证截图(323,444,456,513):
                                    break
                        return  False
                    else:
                        # 点击账号选择，进入到账号界面特征
                        移动点击(438,346,pixel_verify=False)
                        time.sleep(1)
                    time.sleep(1)
            def 去完成():
                # 自动选择没日任务
                res, x, y = for_ms_row(self.row, [MS.未勾选自动选择每日任务])
                if res:
                    print("勾选自动选择每日任务")
                    移动点击(x + 10, y + 10)
                res, x, y = for_ms_row(self.row, [MS.未勾选自动完成任务])
                if res:
                    print("勾选自动完成任务")
                    移动点击(x + 10, y + 10)
                # 去完成
                res, x, y = for_ms_row(self.row, [MS.去完成, MS.继续任务, MS.继续任务1, MS.选择])
                if res:
                    if res == 1:
                        print('去完成')
                    if res == 2:
                        print('继续任务')
                    if res == 3:
                        print('选择人物')
                    移动点击(x + 10, y + 5)
                    return True
                else:
                    return False

            def 检查画面是否变化_前置截图(x1, y1, x2, y2):
                """
                区域截图并保存到临时目录（每个row独立文件）
                
                Args:
                    x1, y1, x2, y2: 截图区域坐标
                
                Returns:
                    bool: 保存成功返回True，失败返回False
                """
                import numpy as np  # 🔧 修复作用域问题：在函数内部显式导入
                try:
                    # 🔧 检查 VNC 连接状态，避免在 VNC 异常时截图导致崩溃
                    if not hasattr(self.dx, 'screenshot') or self.dx.screenshot is None:
                        print(f"⚠️ [画面变化] VNC 对象不存在")
                        return False
                    
                    # 验证并修正坐标（确保 x1 < x2 且 y1 < y2）
                    if x1 > x2:
                        x1, x2 = x2, x1  # 交换x坐标
                    if y1 > y2:
                        y1, y2 = y2, y1  # 交换y坐标

                    # 验证坐标有效性
                    if x1 == x2 or y1 == y2:
                        print(f"截图坐标无效: ({x1},{y1})-({x2},{y2})，区域尺寸为0")
                        return False

                    # 🔧 截图 - 增强异常保护，捕获 OSError（访问违规）
                    try:
                        image = self.dx.screenshot.Capture(x1, y1, x2, y2)
                    except OSError as e:
                        # 🔧 捕获 Windows API 访问违规（0xC0000005）
                        print(f"⚠️ [画面变化] 截图API调用失败 (OSError): {e}")
                        print(f"   可能原因: VNC连接已断开、窗口已关闭")
                        return False
                    except Exception as e:
                        print(f"⚠️ 截图API调用异常: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
                    
                    if image is None:
                        print(f"⚠️ 截图失败: 返回值为None ({x1},{y1})-({x2},{y2})")
                        print(f"   可能原因: VNC连接断开、窗口未激活、截图区域超出屏幕")
                        return False

                    # 确保临时目录存在
                    os.makedirs(TEMP_DIR, exist_ok=True)
                    # 每个row使用独立的临时文件，避免冲突
                    image_path = os.path.join(TEMP_DIR, f"临时图片_Row{self.row}.bmp")

                    # 将 dxpyd.ManagedMemoryView 转换为 numpy 数组
                    if hasattr(image, 'get_memoryview'):
                        mv = image.get_memoryview()
                        image_np = np.array(mv, copy=False)
                    else:
                        image_np = np.asarray(image)

                    # 检查图像数据有效性
                    if image_np is None or image_np.size == 0:
                        print(f"图像数据无效: size={image_np.size if image_np is not None else 'None'}")
                        return False

                    # 确保是BGR格式（OpenCV默认）
                    if len(image_np.shape) == 2:
                        # 灰度图转BGR
                        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
                        # RGBA转BGR
                        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)

                    # 确保数据类型是uint8
                    if image_np.dtype != np.uint8:
                        image_np = image_np.astype(np.uint8)

                    # 确保数组是连续的
                    if not image_np.flags['C_CONTIGUOUS']:
                        image_np = np.ascontiguousarray(image_np)

                    # 方法1: 优先使用PIL/Pillow保存（更可靠）
                    try:
                        # 确保是3通道BGR格式
                        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                            # BGR转RGB（PIL使用RGB格式）
                            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                        elif len(image_np.shape) == 2:
                            # 灰度图转RGB
                            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
                        else:
                            image_rgb = image_np

                        # 转换为PIL Image并保存
                        pil_image = Image.fromarray(image_rgb)
                        pil_image.save(image_path, 'BMP')

                        # 验证文件
                        time.sleep(0.1)
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 100:
                            return True
                        else:
                            pass
                    except Exception as e:
                        print(f"PIL保存失败: {e}，尝试OpenCV...")
                        import traceback
                        traceback.print_exc()

                    # 方法2: 备用方案 - 使用OpenCV保存
                    try:
                        success = cv2.imwrite(image_path, image_np)
                        if success:
                            time.sleep(0.2)
                            if os.path.exists(image_path) and os.path.getsize(image_path) > 100:
                                return True
                            else:
                                pass
                        else:
                            print(f"cv2.imwrite返回False: {image_path}")
                    except Exception as e:
                        print(f"OpenCV保存异常: {e}")
                        import traceback
                        traceback.print_exc()

                    # 方法3: 最后备用 - 保存为PNG格式
                    try:
                        png_path = image_path.replace('.bmp', '.png')
                        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                        else:
                            image_rgb = image_np
                        pil_image = Image.fromarray(image_rgb)
                        pil_image.save(png_path, 'PNG')
                        if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
                            # 尝试将PNG转换为BMP
                            try:
                                pil_image.save(image_path, 'BMP')
                                if os.path.exists(image_path):
                                    os.remove(png_path)
                                    return True
                            except:
                                pass
                    except Exception as e:
                        print(f"PNG保存也失败: {e}")

                    return False
                except Exception as e:
                    print(f"截图保存异常: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

            def 角色移动检测_前置截图(x1, y1, x2, y2):
                """
                角色移动检测专用截图（独立文件，与其他截图隔离）
                
                Args:
                    x1, y1, x2, y2: 截图区域坐标
                
                Returns:
                    bool: 保存成功返回True，失败返回False
                """
                import numpy as np  # 🔧 修复作用域问题：在函数内部显式导入
                try:
                    # 🔧 检查 VNC 连接状态，避免在 VNC 异常时截图导致崩溃
                    if not hasattr(self.dx, 'screenshot') or self.dx.screenshot is None:
                        print(f"⚠️ [角色移动] VNC 对象不存在")
                        return False
                    
                    # 验证并修正坐标
                    if x1 > x2:
                        x1, x2 = x2, x1
                    if y1 > y2:
                        y1, y2 = y2, y1

                    if x1 == x2 or y1 == y2:
                        print(f"⚠️ [角色移动] 截图坐标无效: ({x1},{y1})-({x2},{y2})")
                        return False

                    # 🔧 截图 - 增强异常保护，捕获 OSError（访问违规）
                    try:
                        image = self.dx.screenshot.Capture(x1, y1, x2, y2)
                    except OSError as e:
                        # 🔧 捕获 Windows API 访问违规（0xC0000005）
                        print(f"⚠️ [角色移动] 截图API调用失败 (OSError): {e}")
                        print(f"   可能原因: VNC连接已断开、窗口已关闭")
                        return False
                    except Exception as e:
                        print(f"⚠️ [角色移动] 截图API调用异常: {e}")
                        return False
                    
                    if image is None:
                        print(f"⚠️ [角色移动] 截图失败: 返回值为None ({x1},{y1})-({x2},{y2})")
                        return False

                    # 确保临时目录存在
                    os.makedirs(TEMP_DIR, exist_ok=True)
                    # 使用独立的文件名，与其他截图完全隔离
                    image_path = os.path.join(TEMP_DIR, f"角色移动检测_Row{self.row}.bmp")

                    # 转换为 numpy 数组
                    if hasattr(image, 'get_memoryview'):
                        mv = image.get_memoryview()
                        image_np = np.array(mv, copy=False)
                    else:
                        image_np = np.asarray(image)

                    if image_np is None or image_np.size == 0:
                        print(f"⚠️ [角色移动] 图像数据无效")
                        return False

                    # 确保是BGR格式
                    if len(image_np.shape) == 2:
                        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
                        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)

                    if image_np.dtype != np.uint8:
                        image_np = image_np.astype(np.uint8)

                    if not image_np.flags['C_CONTIGUOUS']:
                        image_np = np.ascontiguousarray(image_np)

                    # 保存截图（优先使用PIL）
                    try:
                        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                        elif len(image_np.shape) == 2:
                            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
                        else:
                            image_rgb = image_np

                        pil_image = Image.fromarray(image_rgb)
                        pil_image.save(image_path, 'BMP')

                        time.sleep(0.1)
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 100:
                            return True
                    except Exception as e:
                        print(f"⚠️ [角色移动] PIL保存失败: {e}，尝试OpenCV...")

                    # 备用方案：OpenCV保存
                    try:
                        success = cv2.imwrite(image_path, image_np)
                        if success and os.path.exists(image_path) and os.path.getsize(image_path) > 100:
                            return True
                    except Exception as e:
                        print(f"⚠️ [角色移动] OpenCV保存失败: {e}")

                    return False
                except Exception as e:
                    print(f"⚠️ [角色移动] 截图异常: {e}")
                    return False

            def 角色移动检测_验证截图(x1, y1, x2, y2):
                """
                角色移动检测专用验证（使用 for_ms_row 模板匹配）
                
                原理：
                1. 前置截图保存为临时文件
                2. 验证时在当前画面中查找该临时文件
                3. 如果找到（相似度>=0.9）→ 画面未变化 → 角色静止
                4. 如果找不到 → 画面已变化 → 角色移动中
                
                Args:
                    x1, y1, x2, y2: 截图区域坐标
                
                Returns:
                    bool: True=画面有变化(移动中), False=画面无变化(静止)
                """
                # 验证并修正坐标
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1

                # 使用独立的文件名
                image_path = os.path.join(TEMP_DIR, f"角色移动检测_Row{self.row}.bmp")
                if not os.path.exists(image_path):
                    print(f"⚠️ [角色移动] 截图文件不存在: {image_path}")
                    return False
                
                # 检查文件大小
                try:
                    file_size = os.path.getsize(image_path)
                    if file_size == 0:
                        print(f"⚠️ [角色移动] 截图文件为空 (0字节)")
                        return False
                    elif file_size < 100:
                        print(f"⚠️ [角色移动] 截图文件过小 ({file_size}字节)")
                        return False
                except Exception as e:
                    print(f"⚠️ [角色移动] 检查文件大小失败: {e}")
                    return False
                
                try:
                    # 使用 for_ms_row 在当前画面中查找第一次截图
                    # 参数说明：[x1, y1, x2, y2, 模板路径, "", 相似度阈值, 重试次数]
                    res, x, y = for_ms_row(self.row, [[x1, y1, x2, y2, image_path, "", 0.95, 5]])
                    
                    if res:
                        # 找到了模板 → 画面未变化 → 角色静止
                        print(f"[DEBUG] [角色移动] 找到模板 (x={x}, y={y}) → 画面未变化")
                        return False
                    else:
                        # 没找到模板 → 画面已变化 → 角色移动中
                        print(f"[DEBUG] [角色移动] 未找到模板 → 画面有变化")
                        return True
                        
                except ValueError as e:
                    if "文件为空" in str(e):
                        print(f"⚠️ [角色移动] 找图时检测到文件为空: {e}")
                        return False
                    else:
                        raise
                except Exception as e:
                    print(f"⚠️ [角色移动] 验证截图异常: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

            def 检查画面是否变化_验证截图(x1, y1, x2, y2):
                """
                验证画面是否变化：使用 for_ms_row 模板匹配
                
                原理：
                1. 前置截图保存为临时文件（临时图片_Row{row}.bmp）
                2. 验证时在当前画面中查找该临时文件
                3. 如果找到（相似度>=0.9）→ 画面未变化
                4. 如果找不到 → 画面已变化
                
                Args:
                    x1, y1, x2, y2: 截图区域坐标
                
                Returns:
                    bool: True=画面有变化, False=画面无变化
                """
                # 验证并修正坐标（确保 x1 < x2 且 y1 < y2）
                if x1 > x2:
                    x1, x2 = x2, x1  # 交换x坐标
                if y1 > y2:
                    y1, y2 = y2, y1  # 交换y坐标

                # 检查之前的截图文件是否存在（使用row独立的文件）
                image_path = os.path.join(TEMP_DIR, f"临时图片_Row{self.row}.bmp")
                if not os.path.exists(image_path):
                    print(f"⚠️ 截图文件不存在: {image_path}")
                    return False
                
                # 检查文件大小，避免读取空文件
                try:
                    file_size = os.path.getsize(image_path)
                    if file_size == 0:
                        print(f"⚠️ 截图文件为空 (0字节): {image_path}")
                        return False
                    elif file_size < 100:
                        print(f"⚠️ 截图文件过小 ({file_size}字节): {image_path}")
                        return False
                except Exception as e:
                    print(f"⚠️ 检查文件大小失败: {e}")
                    return False
                
                try:
                    # 使用 for_ms_row 在当前画面中查找第一次截图
                    # 参数说明：[x1, y1, x2, y2, 模板路径, "", 相似度阈值, 重试次数]
                    res, x, y = for_ms_row(self.row, [[x1, y1, x2, y2, image_path, "", 0.9, 5]])
                    
                    if res:
                        # 找到了模板 → 画面未变化
                        print(f"[DEBUG] [画面变化] 找到模板 (x={x}, y={y}) → 画面未变化")
                        return False
                    else:
                        # 没找到模板 → 画面已变化
                        print(f"[DEBUG] [画面变化] 未找到模板 → 画面有变化")
                        return True
                        
                except ValueError as e:
                    if "文件为空" in str(e):
                        print(f"⚠️ 验证截图时检测到文件为空: {e}")
                        return False
                    else:
                        raise
                except Exception as e:
                    print(f"⚠️ 验证截图异常: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

            def 移动点击(x, y, 时间间隔=0.25, verify=None, verify_retries=None, verify_interval=None, pixel_verify=None):
                # 🔧 导入全局 KM 锁，防止多线程并发访问导致崩溃
                from app.vmware_window_monitor import get_km_lock
                km_lock = get_km_lock(self.row)
                
                # 调试：打印调用栈，确认是哪个线程在调用
                import threading
                _rate_limited_print(
                    f"move_click_debug:{self.row}",
                    2.0,
                    f"[Row:{self.row}] 🖱️ 移动点击: ({x}, {y}) - 线程={threading.current_thread().name}",
                )
                if pixel_verify == False:
                    # 🔧 修复 0xC0000005 崩溃：使用全局锁 + 异常保护
                    with km_lock:
                        try:
                            self.dx.KM.MoveTo(x, y)
                            time.sleep(1)
                            self.dx.KM.LeftClick()
                            print(f"[Row:{self.row}] 移动点击完成: {x}, {y}")
                        except OSError as e:
                            print(f"⚠️ [Row:{self.row}] KM 点击操作失败 (OSError): {e}")
                            return
                        except Exception as e:
                            print(f"⚠️ [Row:{self.row}] 移动点击异常: {e}")
                            import traceback
                            traceback.print_exc()
                            return
                else:
                    km_稳妥移动点击(
                        self.dx.KM,
                        x,
                        y,
                        时间间隔,
                        dx=self.dx,
                        verify=verify,
                        verify_retries=verify_retries,
                        verify_interval=verify_interval,
                        pixel_verify=pixel_verify,
                    )
                    print(f"[Row:{self.row}] 移动点击完成: {x}, {y}")

            def 滑动屏幕(x1, y1, x2, y2, 时间间隔=1):
                # 🔧 导入全局 KM 锁，防止多线程并发访问导致崩溃
                from app.vmware_window_monitor import get_km_lock
                km_lock = get_km_lock(self.row)
                
                # 🔧 修复 0xC0000005 崩溃：使用全局锁 + 异常保护
                with km_lock:
                    try:
                        self.dx.KM.MoveTo(x1, y1)
                        time.sleep(0.1)
                        self.dx.KM.LeftDown()
                        time.sleep(时间间隔)
                        self.dx.KM.MoveTo(x2, y2)
                        time.sleep(0.1)
                        self.dx.KM.LeftUp()
                        time.sleep(0.1)
                    except OSError as e:
                        print(f"⚠️ [Row:{self.row}] KM 滑动操作失败 (OSError): {e}")
                        return False
                    except Exception as e:
                        print(f"⚠️ [Row:{self.row}] 滑动屏幕异常: {e}")
                        import traceback
                        traceback.print_exc()
                        return False

            def 游戏窗口位置检查():
                res, x, y = for_ms_row(self.row, [MS.游戏左上角图标, MS.游戏左上角图标1])
                if res:
                    target_x = 10 + 100
                    target_y = 8 + 5
                    # 检查是否已经在目标位置（允许1像素误差）
                    if abs(x - 10) <= 1 and abs(y - 8) <= 1:
                        return True
                    else:
                        print(f"找到游戏窗口位置: {x}, {y}")
                        print(f"拖动到标准位置: {target_x}, {target_y}")
                        滑动屏幕(x + 100, y + 5, target_x, target_y, 1)
                        return True
                else:
                    res, x, y = for_ms_row(self.row, [MS.游戏运行图标])
                    if res:
                        print(f"找到游戏运行图标: {x}, {y}")
                        移动点击(x+15, y+15)
                        time.sleep(1)
                    else:
                        print("未找到游戏窗口位置,请检查游戏是否开启")
                        return False

            def 滑屏查任务(需要查询的任务名称):
                print(f"开始滑屏查任务: {需要查询的任务名称}")
                start_time = time.time()
                while True:
                    res,x,y = for_ms_row(self.row, [MS.创建, MS.邀请入队1])
                    if res:
                        移动点击(769,145)
                        time.sleep(1)
                        continue
                    # 超时3分钟
                    if time.time() - start_time > 180:
                        print(f"滑屏查任务超时: {需要查询的任务名称}")
                        return False
                    if 需要查询的任务名称 == "帮派":
                        res, x, y = for_ms_row(self.row, [[722, 170, 919, 455, "Common\青龙.bmp", "", 0.7, 5],
                                                          [722, 170, 919, 455, "Common\玄武.bmp", "", 0.7, 5]])
                        if res:
                            移动点击(x + 90, y + 15,pixel_verify=False)
                            print(f"找到任务: {需要查询的任务名称}")
                            time.sleep(1)
                            return True
                        else:
                            print("检查环境是否正常")
                            # 检查任务栏是否打开
                            res, x, y = for_ms_row(self.row, [MS.右三角])
                            if res:
                                移动点击(x + 5, y + 5,pixel_verify=False)
                            res, x, y = for_ms_row(self.row, [MS.创建, MS.邀请入队])
                            if res:
                                # 从右侧队伍分页中切换到任务分页
                                移动点击(749, 142,pixel_verify=False)
                            # 开始循环检查任务
                            res, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                            if res:
                                print("检查环境是否正常,开始滑动查找任务")
                                for i in range(10):
                                    检查画面是否变化_前置截图(763, 145, 839, 200)
                                    滑动屏幕(818, 194, 817, 314)
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(763, 145, 839, 200):
                                        # 画面未变化 → 已滑到底 → 停止
                                        print("已滑到最底层")
                                        break
                                time.sleep(0.5)
                                for i in range(10):
                                    res, x, y = for_ms_row(self.row,
                                                           [[722, 170, 919, 455, "Common\青龙.bmp", "", 0.7,
                                                             5]])
                                    if res:
                                        移动点击(x + 90, y + 15,pixel_verify=False)
                                        print(f"找到任务: {需要查询的任务名称}")
                                        time.sleep(1)
                                        return True
                                    else:
                                        检查画面是否变化_前置截图(764, 367, 879, 425)
                                        滑动屏幕(817, 314, 818, 194)
                                        time.sleep(1)
                                        if not 检查画面是否变化_验证截图(764, 367, 879, 425):
                                            # 画面未变化 → 已滑到顶 → 停止
                                            print("已滑到最顶层")
                                            break
                                print("未找到任务,返回False")
                                return False
                            else:
                                print("检查环境是否正常,未找到右侧任务栏标记")
                                if 关闭窗口():
                                    continue
                                time.sleep(1)
                                return False
                    else:
                        res, x, y = for_ms_row(self.row, [[722, 170, 919, 455, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5]])
                        if res:
                            移动点击(x + 90, y + 15,pixel_verify=False)
                            print(f"找到任务: {需要查询的任务名称}")
                            time.sleep(1)
                            # 第一次开启师门
                            res, x, y = for_ms_row(self.row, [MS.参加1])
                            if res:
                                print("第一次开启师门, 点击参加,等待20秒")
                                time.sleep(20)
                                移动点击(494, 205,pixel_verify=False)
                            return True
                        else:
                            print("检查环境是否正常")
                            # 检查任务栏是否打开
                            res, x, y = for_ms_row(self.row, [MS.右三角])
                            if res:
                                移动点击(x + 5, y + 5,pixel_verify=False)
                            res, x, y = for_ms_row(self.row, [MS.创建, MS.邀请入队])
                            if res:
                                # 从右侧队伍分页中切换到任务分页
                                移动点击(749, 142,pixel_verify=False)
                            # 开始循环检查任务
                            res, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                            if res:
                                print("检查环境是否正常,开始滑动查找任务")
                                for i in range(10):
                                    检查画面是否变化_前置截图(763, 145, 839, 200)
                                    滑动屏幕(818, 194, 817, 314)
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(763, 145, 839, 200):
                                        # 画面未变化 → 已滑到底 → 停止
                                        print("已滑到最底层")
                                        break
                                time.sleep(0.5)
                                for i in range(10):
                                    res, x, y = for_ms_row(self.row,
                                                           [[722, 170, 919, 455, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5]])
                                    if res:
                                        移动点击(x + 90, y + 15,pixel_verify=False)
                                        print(f"找到任务: {需要查询的任务名称}")
                                        time.sleep(1)
                                        return True
                                    else:
                                        检查画面是否变化_前置截图(764, 367, 879, 425)
                                        滑动屏幕(817, 314, 818, 194)
                                        time.sleep(1)
                                        if not 检查画面是否变化_验证截图(764, 367, 879, 425):
                                            # 画面未变化 → 已滑到顶 → 停止
                                            print("已滑到最顶层")
                                            break
                                print("未找到任务,返回False")
                                return False
                            else:
                                print("检查环境是否正常,未找到右侧任务栏标记")
                                if 关闭窗口():
                                    continue
                                time.sleep(1)
                                return False

            def 人物是否移动中():
                """
                检测人物是否正在移动（使用独立的截图文件）
                
                Returns:
                    bool: True=正在移动, False=已停止
                """
                # 整体检测超时时间（防止死循环）
                start_time = time.time()
                max_detect_time = 60  # 最多检测60秒
                
                while True:
                    # 检查整体检测是否超时
                    if time.time() - start_time > max_detect_time:
                        print(f"⚠️ [角色移动] 检测超时 ({max_detect_time}秒)，假设人物未移动")
                        # 重置移动状态
                        if self._是否在移动:
                            self._是否在移动 = False
                            self._移动开始时间 = None
                        return False
                    # 先执行截图（使用专用函数和文件名）
                    screenshot_success = 角色移动检测_前置截图(69, 34, 111, 49)
                    if not screenshot_success:
                        print("⚠️ [角色移动] 截图失败，假设人物未移动")
                        # 重置移动状态
                        if self._是否在移动:
                            self._是否在移动 = False
                            self._移动开始时间 = None
                        return False

                    time.sleep(1)

                    # 验证画面是否变化（使用专用函数）
                    try:
                        is_changed = 角色移动检测_验证截图(69, 34, 111, 49)
                    except Exception as e:
                        print(f"⚠️ [角色移动] 验证截图异常: {e}，假设人物未移动")
                        if self._是否在移动:
                            self._是否在移动 = False
                            self._移动开始时间 = None
                        return False

                    if is_changed:
                        # 画面有变化 → 角色正在移动
                        if not self._是否在移动:
                            # 刚开始移动，打印一次并记录时间
                            print("人物移动中...")
                            self._是否在移动 = True
                            self._移动开始时间 = time.time()
                        else:
                            # 持续移动中，计算并打印时间
                            elapsed_time = int(time.time() - self._移动开始时间)
                            print(f"角色移动中,已持续: {elapsed_time}秒")

                            # 超过 30 秒强制认为移动结束，避免死循环
                            if elapsed_time > 30:
                                print(f"⚠️ [角色移动] 移动超时 ({elapsed_time}秒)，强制重置状态")
                                self._是否在移动 = False
                                self._移动开始时间 = None
                                return False

                            time.sleep(0.5)
                            # 人物移动中的时候检查是否有使用需要点击
                            res, x, y = for_ms_row(self.row, [MS.使用, MS.使用1, MS.使用活力, MS.藏宝图使用, MS.批量使用])
                            if res:
                                try:
                                    移动点击(x + 5, y + 5, pixel_verify=False)
                                    time.sleep(0.5)
                                except OSError as e:
                                    print(f"⚠️ [角色移动] KM 点击失败: {e}")
                                except Exception as e:
                                    print(f"⚠️ [角色移动] 点击异常: {e}")
                        return True
                    else:
                        # 画面未变化 → 角色已停止，重置状态
                        if self._是否在移动:
                            print("[DEBUG] [角色移动] 角色已停止移动")
                            self._是否在移动 = False
                            self._移动开始时间 = None
                        return False
                    if 关闭窗口():
                        return  False
            def 识别角色等级():
                if 关闭窗口():
                    pass
                else:
                    res, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                    if res:
                        return -1
                res, x, y = for_ms_row(self.row, [MS.主角红蓝])
                if res:
                    return 0
                else:
                    # print("未识别到角色等级,返回-1")
                    return -1

            def 识别宠物等级 ():
                if 关闭窗口():
                    pass
                else:
                    res, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                    if res:
                        return -1
                res, x, y = for_ms_row(self.row, [MS.宠物红蓝])
                if res:
                    return 0
                else:
                    # print("未识别到角色等级,返回-1")
                    return -1

            # ✅ 截图缓存机制：减少VNC截图次数
            self._screenshot_cache_lock = False  # 标记是否已锁定屏幕
            
            def _cache_find_ms(ms_list, debug=False):
                """
                ✅ 带缓存的找图函数（仅在关闭窗口等特定场景使用）
                
                原理：利用大漠的 keep_screen 机制，在多次识别间复用同一张截图
                
                用法：
                  1. 调用 _cache_start() 开始缓存
                  2. 多次调用 _cache_find_ms() 进行识别（都使用同一张截图）
                  3. 调用 _cache_end() 释放缓存
                
                参数:
                    ms_list: 模板列表
                    debug: 是否打印调试信息
                
                返回:
                    (res, x, y) - 与 for_ms_row 相同的返回值
                """
                try:
                    from dxGame.dx import for_ms_row as original_for_ms_row
                    # 直接调用原始函数，但此时 dx.keep_screen(True) 已经生效
                    # for_ms 内部会复用缓存的截图，不会重新截图
                    return original_for_ms_row(self.row, ms_list, debug=debug)
                except Exception as e:
                    print(f"❌ _cache_find_ms 异常: {e}")
                    return 0, 0, 0
            
            def _cache_start():
                """
                ✅ 开始截图缓存（在进入稳定界面时调用）
                
                注意：必须在 _cache_find_ms 之前调用
                """
                try:
                    from dxGame.dx import td_info
                    dx = td_info[self.row].dx
                    dx.keep_screen(True)  # 锁定屏幕，只截图一次
                    self._screenshot_cache_lock = True
                    print("✅ 截图缓存已启动（后续识别将复用此截图）")
                    return True
                except Exception as e:
                    print(f"❌ _cache_start 失败: {e}")
                    return False
            
            def _cache_end():
                """
                ✅ 结束截图缓存（在退出界面或界面变化时调用）
                
                注意：必须与 _cache_start 配对使用
                """
                try:
                    if self._screenshot_cache_lock:
                        from dxGame.dx import td_info
                        dx = td_info[self.row].dx
                        dx.keep_screen(False)  # 释放缓存
                        self._screenshot_cache_lock = False
                        print("🗑️ 截图缓存已释放")
                except Exception as e:
                    print(f"❌ _cache_end 异常: {e}")
                    # 即使失败也要重置标记
                    self._screenshot_cache_lock = False
            
            def 关闭窗口 (use_cache=True):
                """
                关闭各种弹窗
                
                参数:
                    use_cache: 是否使用截图缓存（默认True）
                              - True:  复用同一张截图（适合静态界面，如账号列表）
                              - False: 每次识别都重新截图（适合动态界面，如战斗）
                """
                # 这里检测游戏画面异常情况
                res, x, y = for_ms_row(self.row, [MS.游戏左上角图标, MS.游戏左上角图标1])
                if not res:
                    print("游戏画面异常")
                    res, x1, y1 = for_ms_row(self.row, [MS.游戏运行图标])
                    if res:
                        print("找到游戏运行图标")
                        移动点击(x1 + 15, y1 + 10, pixel_verify=False)
                        time.sleep(1)
                        移动点击(x1 + 15, y1 + 10)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.游戏左上角图标], for_num=5, delay=0.5)
                        if ress:
                            print("找到游戏左上角图标")
                            return True
                        else:
                            移动点击(x1 + 15, y1 + 10, pixel_verify=False)
                else:
                    if use_cache:
                        # ✅ 启用缓存模式：只截图一次，所有识别复用
                        _cache_start()
                        try:
                            return _关闭窗口_内部()
                        finally:
                            _cache_end()
                    else:
                        # ⚠️ 不使用缓存：每次识别都重新截图（适合战斗等动态场景）
                        return _关闭窗口_内部()
            
            def _关闭窗口_内部():
                """内部实现：实际的窗口关闭逻辑"""
                res, x, y = for_ms_row(self.row, [MS.小地图关闭])
                if res:
                    移动点击 (x+5, y+5)
                    time.sleep(1)
                    return True
                res, x, y = for_ms_row(self.row, [MS.对话关闭按钮])
                if res:
                    移动点击 (x+5, y+5)
                    time.sleep(1)
                    return True
                res, x, y = for_ms_row(self.row, [MS.您的账号已经在其他设备登录])
                if res:
                    start_time = time.time()
                    while True:
                        if time.time() - start_time > 60:
                            print("已等待10秒,未找到关闭窗口按钮")
                            return True
                        print("您的账号已经在其他设备登录")
                        移动点击 (x +100, y +50)
                        time.sleep(1)
                        ress = wait_for_ms([MS.进入游戏,MS.进入游戏1])
                        if ress:
                            print("已进入游戏")
                            res, x, y = for_ms_row(self.row, [MS.进入游戏,MS.进入游戏1])
                            if ress:
                                print("已进入游戏")
                                移动点击 (x +10, y +5)
                                time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.登录游戏,MS.登录游戏1])
                        if res:
                            检查画面是否变化_前置截图(279,361,414,397)
                            print("已登录游戏")
                            移动点击 (x +10, y +5)
                            time.sleep(3)
                            if not 检查画面是否变化_验证截图(279,361,414,397):
                                return True
                    # 优化：轮询等待响应
                # 处理意外报错框遮住的问题
                res, x, y = for_ms_row(self.row, [MS.意外报错])
                if res:
                    print("找到意外报错")
                    移动点击 (x - 47, y - 93,pixel_verify=False)
                    # 优化：轮询等待响应
                    轮询等待 (lambda: False, max_wait=1.0, interval=0.2)
                    滑动屏幕 (x - 47, y - 93, 461, 733)
                    轮询等待 (lambda: False, max_wait=1.0, interval=0.2)
                # print("关闭窗口")
                res, x, y = for_ms_row(self.row, [MS.剧情中])
                if res:
                    while True:
                        print("剧情中....")
                        # 优化：轮询等待界面变化（最多 1 秒）
                        轮询等待 (lambda: for_ms_row(self.row, [MS.剧情确定])[0] or 
                                         for_ms_row(self.row, [MS.是否跳过本段剧情])[0] or
                                         for_ms_row(self.row, [MS.快进,MS.快进1])[0] or
                                         not for_ms_row(self.row, [MS.剧情中])[0], 
                                  max_wait=1.0, interval=0.2)
                        res, x, y = for_ms_row(self.row, [MS.剧情确定])
                        if res:
                            print("点击剧情确定")
                            移动点击(x + 5, y + 5)
                            continue
                        res, x, y = for_ms_row(self.row, [MS.是否跳过本段剧情])
                        if res:
                            print("点击是否跳过本段剧情")
                            移动点击(x + 215, y + 50)
                            continue
                        res, x, y = for_ms_row(self.row, [MS.快进, MS.快进1])
                        if res:
                            print("跳过剧情！")
                            移动点击(x + 5, y + 5)
                            continue
                        res, x, y = for_ms_row(self.row, [MS.剧情中])
                        if not res:
                            break
                    return True
                res, x, y = for_ms_row(self.row, [MS.是否跳过本段剧情])
                if res:
                    print("点击是否跳过本段剧情")
                    移动点击(x + 215, y + 50)
                    return True
                res, x, y = for_ms_row(self.row, [MS.重连失败])
                if res:
                    print("点击重连失败")
                    移动点击(x + 140, y + 75,pixel_verify=False)
                    time.sleep(1)
                    ress = wait_for_ms(self.row, [MS.登录游戏1, MS.登录游戏])
                    if ress:
                        print("点击登录游戏")
                        移动点击(463,510,pixel_verify=False)
                    time.sleep(1)
                    return True
                res, x, y = for_ms_row(self.row, [MS.打造关闭])
                if res:
                    print("点击打造关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.加入帮派关闭])
                if res:
                    print("点击加入帮派关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.限时折扣关闭])
                if res:
                    print("点击限时折扣关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.帮战关闭])
                if res:
                    print("点击帮战关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.快进, MS.快进1])
                if res:
                    print("跳过剧情！")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.点击任意地方继续])
                if res:
                    # 随机点击x,y坐标（285,231,632,384）范围
                    print("点击任意地方继续")
                    xx = random.randint(285, 632)
                    yy = random.randint(231, 384)
                    移动点击(xx, yy)
                    return True
                res, x, y = for_ms_row(self.row, [MS.师门任务完成确定])
                if res:
                    print("点击师门任务完成确定")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.祈福关闭])
                if res:
                    print("点击祈福关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.人物属性关闭])
                if res:
                    print("点击人物属性关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.包裹界面关闭按钮])
                if res:
                    print("关闭包裹界面")
                    移动点击(x + 10, y + 10,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.点击空白区域关闭窗口])
                if res:
                    print("点击空白区域关闭窗口")
                    移动点击(71, 630,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.手动])
                if res:
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.活动面板关闭])
                if res:
                    print("活动面板关闭")
                    移动点击(x + 5, y + 5)
                    return True
                res, x, y = for_ms_row(self.row, [MS.个人空间关闭])
                if res:
                    print("个人空间关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.确定1])
                if res:
                    print("点击确定")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.算了])
                if res:
                    print("点击确定")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.师门任务关闭])
                if res:
                    print("师门任务关闭")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                res, x, y = for_ms_row(self.row, [MS.知道了])
                if res:
                    print("点击知道了")
                    移动点击(x + 5, y + 5,pixel_verify=False)
                    return True
                else:
                    # print("退出关闭窗口")
                    return False

            def 上交():
                res, x, y = for_ms_row(self.row, [MS.上交, MS.上交1, MS.召唤灵上交])
                if res:
                    print("上交")
                    移动点击(x + 25, y + 10,pixel_verify=False)
                    return True
                else:
                    return False

            def 组合按键(按键1, 按键2):
                self.dx.KM.hot_key([按键1, 按键2])
                print(f"组合按键: {按键1}, {按键2}")

            def 请选择 ():
                while True:
                    res, x, y = for_ms_row(self.row, [MS.请选择,MS.请选择1])
                    if res:
                        print("请选择")
                        移动点击 (x + 125, y + 75,pixel_verify=False)
                        time.sleep(1)
                        # 优化：轮询等待界面响应（最多 1 秒）
                        # 轮询等待 (lambda: False, max_wait=1.0, interval=0.2)
                        return True
                    else:
                        return False


            def 购买():
                res, x, y = for_ms_row(self.row, [MS.药店购买, MS.兵器购买, MS.摆摊购买, MS.召唤灵购买,MS.购买1, MS.购买2, MS.购买3, MS.购买4])
                if res:
                    print("购买")
                    移动点击(x + 40, y + 15,pixel_verify=False)
                    time.sleep(0.5)
                    res, x, y = for_ms_row(self.row, [MS.请选择要购买的商品])
                    if res:
                        print("请选择要购买的商品")
                        移动点击(404, 242,pixel_verify=False)
                        time.sleep(0.5)
                        return True
                    else:
                        return False
                else:
                    return False

            def 师门任务完成():
                res, x, y = for_ms_row(self.row, [MS.师门任务完成])
                if res:
                    print("师门任务完成")
                    移动点击(462, 522,pixel_verify=False)
                    time.sleep(0.5)
                    return True
                else:
                    return False

            def 物品识别并操作():
                while True:
                    res, x, y = for_ms_row(self.row, [MS.打造关闭])
                    if res:
                        print("关闭打造界面")
                        移动点击(x + 5, y + 5,pixel_verify=False)
                        time.sleep(0.5)
                    res, x, y = for_ms_row(self.row, [MS.包裹界面])
                    if res:
                        res, x, y = for_ms_row(self.row, [MS.装备提升])
                        if res:
                            print("装备提升")
                            time.sleep(0.5)
                            res, x, y = for_ms_row(self.row, [MS.装备])
                            if res:
                                print("点击装备")
                                移动点击(x + 5, y + 5,pixel_verify=False)
                                time.sleep(0.5)
                                return True
                            else:
                                return False
                        else:
                            res, x, y = for_ms_row(self.row, [MS.商会出售, MS.商会出售1])
                            if res:
                                print("商会出售")
                                移动点击(x + 10, y + 10,pixel_verify=False)
                                time.sleep(1)
                                continue
                            else:
                                res, x, y = for_ms_row(self.row, [MS.出售])
                                if res:
                                    print("点击出售")
                                    移动点击(x + 10, y + 10,pixel_verify=False)
                                    time.sleep(1)
                                    continue
                                else:
                                    res, x, y = for_ms_row(self.row, [MS.阵法残卷])
                                    if res:
                                        print("点击合成阵法残卷")
                                        移动点击(x + 128, y + 156,pixel_verify=False)
                                        time.sleep(1)
                                        return True
                                    else:
                                        res, x, y = for_ms_row(self.row, [MS.批量使用])
                                        if res:
                                            print("批量使用")
                                            移动点击(x + 10, y + 10,pixel_verify=False)
                                            time.sleep(1)
                                            continue
                                        else:
                                            res, x, y = for_ms_row(self.row, [MS.红罗羹, MS.绿芦羹])
                                            if res:
                                                print("点击红罗羹或绿芦羹")
                                                while True:
                                                    移动点击(x + 210, y + 180,pixel_verify=False)
                                                    time.sleep(0.5)
                                                    if not 使用():
                                                        break
                                                continue
                                            else:
                                                res, x, y = for_ms_row(self.row, [MS.升级大礼包])
                                                if res:
                                                    print("升级大礼包")
                                                    移动点击(x + 115, y + 150,pixel_verify=False)
                                                    time.sleep(1)
                                                    start_time = time.time()
                                                    while True:
                                                        res, x, y = for_ms_row(self.row, [MS.福利界面])
                                                        if res:
                                                            res, x, y = for_ms_row(self.row, [MS.领取])
                                                            if res:
                                                                while True:
                                                                    res, x, y = for_ms_row(self.row, [MS.领取])
                                                                    if res:
                                                                        print("点击领取")
                                                                        移动点击(x + 10, y + 10,pixel_verify=False)
                                                                        time.sleep(1)
                                                                    else:
                                                                        break
                                                            else:
                                                                self.dx.KM.PressKey('esc')
                                                                time.sleep(1)
                                                        else:
                                                            break
                                                        if time.time() - start_time > 60:
                                                            self.dx.KM.PressKey('esc')
                                                            break
                                                    continue
                                                else:
                                                    res, x, y = for_ms_row(self.row, [MS.福利界面])
                                                    if res:
                                                        res, x, y = for_ms_row(self.row, [MS.领取])
                                                        if res:
                                                            while True:
                                                                res, x, y = for_ms_row(self.row, [MS.领取])
                                                                if res:
                                                                    print("点击领取")
                                                                    移动点击(x + 10, y + 10,pixel_verify=False)
                                                                    time.sleep(1)
                                                                else:
                                                                    break
                                                        else:
                                                            # 按键esc退出
                                                            self.dx.KM.PressKey('esc')
                                                            time.sleep(1)
                                                            return True
                                                    else:
                                                        res, x, y = for_ms_row(self.row, [MS.宝石])
                                                        if res:
                                                            time.sleep(0.5)
                                                            res, x, y = for_ms_row(self.row, [MS.更多])
                                                            if res:
                                                                print("点击更多")
                                                                移动点击(x + 10, y + 10,pixel_verify=False)
                                                                time.sleep(1)
                                                                # 高级石头直接跳过
                                                                res, x, y = for_ms_row(self.row, [MS.七级])
                                                                if res:
                                                                    break
                                                        else:
                                                            return False
                    else:
                        res, x, y = for_ms_row(self.row, [MS.新手礼包])
                        if res:
                            print("新手礼包")
                            移动点击(x + 130, y + 155)
                            # 第一次指引福利 控时
                            time.sleep(5)
                            res, x, y = for_ms_row(self.row, [MS.福利指引])
                            if res:
                                print("福利指引")
                                移动点击(34, 150)
                                time.sleep(0.5)
                            else:
                                res, x, y = for_ms_row(self.row, [MS.福利界面])
                                if res:
                                    print("福利界面")
                                    time.sleep(1)
                                    while True:
                                        res, x, y = for_ms_row(self.row, [MS.领取])
                                        if res:
                                            print("领取")
                                            移动点击(x + 10, y + 10)
                                            time.sleep(1)
                                        else:
                                            # 按键esc退出
                                            self.dx.KM.PressKey('esc')
                                            time.sleep(1)
                                            return True
                                        time.sleep(1)
                                continue
                            continue
                        else:
                            res, x, y = for_ms_row(self.row, [MS.福利界面])
                            if res:
                                # 按键esc退出
                                self.dx.KM.PressKey('esc')
                            else:
                                组合按键('alt', 'e')
                                time.sleep(1)

            def 背包物品识别():
                # 起始坐标
                start_x = 510
                start_y = 250
                # 格子间距
                step_x = 75  # 从左往右，X坐标增加75
                step_y = 75  # 从上往下，Y坐标增加75
                # 5x5格子
                rows = 5
                cols = 5
                # 遍历所有格子，从上往下，从左往右
                for row in range(rows):
                    for col in range(cols):
                        # 异常退出
                        res, x, y = for_ms_row(self.row, [MS.包裹界面, MS.仓库界面])
                        if not res:
                            return False
                        # 计算当前格子的坐标
                        xx = start_x + col * step_x
                        yy = start_y + row * step_y
                        print(f"点击背包物品格子: 第{row + 1}行, 第{col + 1}列, 坐标({xx}, {yy})")
                        # 空包裹格子或未解锁包裹格子
                        res, x, y = for_ms_row(self.row,
                                               [[xx - 70, yy - 70, xx + 70, yy + 70, "Common\空包裹格子.bmp", "", 0.95, 5],
                                                [xx - 70, yy - 70, xx + 70, yy + 70, "Common\未解锁包裹格子.bmp", "", 0.95, 5],
                                                [xx - 70, yy - 70, xx + 70, yy + 70, "Common\空包裹格子1.bmp", "", 0.95, 5]
                                                ])
                        if res:
                            print("空包裹格子或未解锁包裹格子")
                            return False
                        移动点击(xx, yy, pixel_verify=False)
                        time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.打造关闭])
                        if res:
                            print("关闭打造界面")
                            移动点击(x + 5, y + 5)
                            time.sleep(0.5)
                        # 物品识别并操作
                        if not 物品识别并操作():
                            print("未识别到包裹内容，点击上方空白处")
                            移动点击(457, 110)
                            time.sleep(0.5)
                        time.sleep(1)  # 每个格子点击后稍作延迟
                return True

            def 清理背包():
                show_log(self.row, "开始清理背包")
                print("开始清理背包")
                start_time = time.time()
                while True:

                    # 超时5分钟
                    if time.time() - start_time > 300:
                        print("清理背包超时")
                        return True
                    res, x, y = for_ms_row(self.row, [MS.包裹界面, MS.仓库界面])
                    if res:
                        print("进入背包界面")
                        if res == 2:
                            移动点击(868, 228)
                            time.sleep(1)

                        # 整理背包
                        res, x, y = for_ms_row(self.row, [MS.整理])
                        if res:
                            print("整理背包")
                            移动点击(x + 10, y + 10)
                            time.sleep(1)

                        # 滑动至最底层
                        for i in range(10):
                            print("滑动至最顶层")
                            检查画面是否变化_前置截图(501, 152, 674, 262)
                            time.sleep(1)
                            滑动屏幕(693, 221, 693, 432, 1)
                            time.sleep(1)
                            if not 检查画面是否变化_验证截图(501, 152, 674, 262):
                                # 画面未变化 → 已滑到底 → 停止
                                print("已滑到最底层")
                                break
                            # 异常退出
                            res, x, y = for_ms_row(self.row, [MS.包裹界面, MS.仓库界面])
                            if not res:
                                break

                        # 循环清理背包物品
                        for i in range(10):
                            print(f"循环清理背包物品: {i}次")
                            print("循环清理背包物品")
                            # 循环点击背包物品
                            if 背包物品识别():
                                滑动屏幕(693, 503, 694, 131, 1)
                                time.sleep(1)
                            else:
                                return True
                            # 异常退出
                            res, x, y = for_ms_row(self.row, [MS.包裹界面, MS.仓库界面])
                            if not res:
                                break
                        return True
                        continue
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 'e')
                            time.sleep(1)
                            continue
                        else:
                            if 关闭窗口():
                                continue
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)

            def 日常_师门():
                show_log(self.row, "开始日常_师门")
                print("开始日常_师门")
                start_time = time.time()
                while True:
                    res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                    if res:
                        print("仙玉不足")
                        移动点击(653, 180, pixel_verify=False)
                        time.sleep(0.5)
                        return True
                    # 超时30分钟
                    if time.time() - start_time > 1800:
                        print(f"日常_师门超时，退出，用时{int((time.time() - start_time) / 60)}分钟")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.背包空间不足])
                    if res:
                        print("背包空间不足")
                        移动点击(x - 50, y + 25)
                        time.sleep(1)
                        清理背包()
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.自动购买确定])
                            if res:
                                移动点击(x + 10, y + 10, pixel_verify=False)
                                time.sleep(1)
                            if 请选择():
                                continue
                            if 购买():
                                res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                                if res:
                                    print("仙玉不足")
                                    移动点击(653, 180, pixel_verify=False)
                                    time.sleep(1)
                                    self.dx.KM.PressKey('esc')
                                    time.sleep(1)
                                    return True
                                continue
                            if 上交():
                                continue
                            if 使用():
                                continue
                            if 去完成():
                                continue
                            if 滑屏查任务("师门"):
                                time.sleep(1)
                                continue
                            if 师门任务完成():
                                print(f"师门任务完成，用时{int((time.time() - start_time) / 60)}分钟")
                                return True
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if 识别角色等级() != -1 or ress != 0:
                                    if 查任务是否完成('师门任务'):
                                        # 师门任务完成，用时多少时间
                                        print(f"师门任务完成，用时{int((time.time() - start_time) / 60)}分钟")
                                        return True
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    else:
                                        print("环境异常,按键(ESC)退出")
                                        self.dx.KM.PressKey('esc')  # ESC
                                        time.sleep(1)
                                        if 关闭窗口():
                                            continue
                                        else:
                                            # 打开活动界面
                                            组合按键('alt', 'c')
                                            time.sleep(1)

            def 查任务是否完成(需要查询的任务名称):
                print(f"开始查任务是否完成: {需要查询的任务名称}")
                start_time = time.time()
                while True:
                    if 自动战斗():
                        break
                    # 超时1分钟
                    if time.time() - start_time > 60:
                        print(f"查任务是否完成超时: {需要查询的任务名称}")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.活动界面])
                    if res:
                        print("活动界面已打开,继续查询任务是否完成")
                        time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.日常活动1, MS.日常活动2])
                        if res:
                            移动点击(x+15, y+15,pixel_verify=False)
                            time.sleep(1)
                        # 异常状态
                        res, x, y = for_ms_row(self.row, [MS.异常状态])
                        if res:
                            # 异常状态，关闭窗口
                            print("异常状态，点击(327, 56)")
                            移动点击(327, 56,pixel_verify=False)
                            time.sleep(0.5)
                            continue
                        # 快速反应，检查任务是否完成
                        res, x, y = for_ms_row(self.row, [[280, 144, 403, 478, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5],
                                                          [618, 142, 751, 479, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5]])
                        if res:
                            print(f"找到任务: {需要查询的任务名称}")
                            xx = x + 140
                            yy = y + 2
                            res, x, y = for_ms_row(self.row,
                                                   [[xx, yy, xx + 100, yy + 50, f"Common\\完成.bmp", "", 0.7, 5],
                                                    [xx, yy, xx + 100, yy + 50, f"Common\\参加.bmp", "", 0.7, 5],
                                                    [xx, yy, xx + 100, yy + 50, f"Common\\完成1.bmp", "", 0.7, 5]])
                            if res == 1 or res == 3:
                                print(f"任务{需要查询的任务名称}已完成")
                                return True
                            if res == 2:
                                移动点击(x + 20, y + 10, pixel_verify=False)
                                time.sleep(3)
                                return False
                            else:
                                print(f"任务{需要查询的任务名称}异常,向下滑动屏幕")
                                res, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if res:
                                    滑动屏幕(435, 447, 444, 257)
                                    time.sleep(1)
                        else:
                            print(f"未找{需要查询的任务名称},重置活动界面到最顶层")
                            for i in range(10):
                                检查画面是否变化_前置截图(390, 114, 535, 166)
                                time.sleep(1)
                                滑动屏幕(537, 209, 538, 490)
                                time.sleep(1)
                                if not 检查画面是否变化_验证截图(390, 114, 535, 166):
                                    # 画面未变化 → 已滑到顶 → 停止
                                    print("已滑到最顶层")
                                    break
                                # 异常退出
                                res, x, y = for_ms_row(self.row, [MS.活动界面])
                                if not res:
                                    print("活动界面已关闭,异常退出")
                                    return False
                                time.sleep(1)
                            time.sleep(0.5)
                            # 循环查找任务是否完成 
                            for i in range(10):
                                res, x, y = for_ms_row(self.row,
                                                       [[280, 144, 403, 478, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5],
                                                        [618, 142, 751, 479, f"Common\\{需要查询的任务名称}.bmp", "", 0.7, 5]])
                                if res:
                                    print(f"找到任务: {需要查询的任务名称}")
                                    xx = x + 140
                                    yy = y + 2
                                    res, x, y = for_ms_row(self.row,
                                                           [[xx, yy, xx + 100, yy + 50, f"Common\\完成.bmp", "", 0.7, 5],
                                                            [xx, yy, xx + 100, yy + 50, f"Common\\参加.bmp", "", 0.7, 5]])
                                    if res == 1:
                                        print(f"任务{需要查询的任务名称}已完成")
                                        return True
                                    if res == 2:
                                        移动点击(x + 20, y + 10, pixel_verify=False)
                                        time.sleep(3)
                                        return False
                                else:
                                    检查画面是否变化_前置截图(242, 429, 381, 491)
                                    滑动屏幕(538, 342, 537, 161)
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(242, 429, 381, 491):
                                        # 画面未变化 → 已滑到顶 → 停止
                                        print("已滑到最顶层")
                                        break
                                # 异常退出
                                res, x, y = for_ms_row(self.row, [MS.活动界面])
                                if not res:
                                    print("活动界面已关闭,异常退出")
                                    return False
                                time.sleep(0.5)
                            print(f"未找到{需要查询的任务名称},返回False")
                            return False
                        continue
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 'c')
                            time.sleep(1)
                        else:
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)

            def 自动战斗():
                """
                战斗内挂机：识别战斗 UI 后循环点击自动/防御等，直到脱战或超时。
                返回值：True = 超时视为结束；False = 未进战斗或已确认不在战斗中。
                """
                try:
                    # 左三角：战斗场景特征，用于判断是否处于战斗界面
                    res, x, y = for_ms_row(self.row, [MS.左三角1, MS.左三角2])
                    if res:
                        print("进入战斗场景...")
                        battle_start_time = time.time()
                        max_battle_time = 120  # 防止死循环卡死，超时强制结束本段逻辑
                        while True:
                            try:
                                关闭窗口(use_cache=False)  # 战斗中禁用缓存，每次重新截图

                                elapsed_time = int(time.time() - battle_start_time)
                                print(f"自动战斗中,已持续: {elapsed_time}秒")

                                if elapsed_time > max_battle_time:
                                    print(f"战斗超时{max_battle_time}秒，强制退出")
                                    # 🔧 防止崩溃：退出前等待，确保 KM 操作队列清空
                                    time.sleep(1.0)
                                    return True  # 与上层约定：超时也算「处理完毕」

                                # ---------- 指引弹层 ----------
                                res, x, y = for_ms_row(self.row, [MS.指引左上])
                                if res:
                                    print("点击指引左上")
                                    移动点击(x + 30, y + 30)
                                    time.sleep(1)
                                    continue

                                # ---------- 秦琼关卡：角色防御 + 宠物保护 ----------
                                res, x, y = for_ms_row(self.row, [MS.秦琼])
                                if res:
                                    print("进入秦琼界面，角色防御，宠物保护")
                                    res, x, y = for_ms_row(self.row, [MS.保护])
                                    if res:
                                        print("点击保护")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(1)
                                        移动点击(723, 425)  # 选保护目标等固定点位
                                        time.sleep(0.3)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.防御])
                                    if res:
                                        print("点击防御")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(0.3)
                                    continue
                                else:
                                    # ---------- 常规战斗条：开自动、切技能 ----------
                                    res, x, y = for_ms_row(self.row, [MS.选择人物自动技能])
                                    if res:
                                        print("点击选择人物自动技能")
                                        移动点击(x - 15, y + 70)
                                        time.sleep(0.3)
                                        continue

                                    res, x, y = for_ms_row(self.row, [MS.自动战斗])
                                    if res:
                                        print("点击自动战斗")
                                        移动点击(x + 15, y - 25)
                                        time.sleep(0.3)
                                        continue

                                    res, x, y = for_ms_row(self.row, [MS.防御转攻击])
                                    if res:
                                        print("防御改攻击")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(1)
                                        移动点击(698, 437)
                                        time.sleep(1)
                                        continue

                                    # 无上述按钮时再辨认是否仍在战斗（先排除运镖界面，避免误判）
                                    time.sleep(0.5)
                                    res, x, y = for_ms_row(self.row, [MS.距离运镖])
                                    if res:
                                        return False
                                    res, x, y = for_ms_row(self.row, [MS.左三角1, MS.左三角2])
                                    if res:
                                        continue  # 仍在战斗，下一轮继续处理弹窗/技能条
                                    print("不在战斗中，退出自动战斗")
                                    return False
                            except (OSError, WindowsError, SystemError) as e:
                                # 🔧 关键修复：捕获战斗过程中的访问违规
                                print(f"⚠️ 自动战斗异常 (可能 VNC 断开): {e}")
                                time.sleep(1)
                                return False
                            except Exception as e:
                                print(f"⚠️ 自动战斗未知异常: {type(e).__name__}: {e}")
                                import traceback
                                traceback.print_exc()
                                time.sleep(1)
                                return False
                    else:
                        return False  # 入口即未检测到战斗特征
                except (OSError, WindowsError, SystemError) as e:
                    # 🔧 捕获入口处的访问违规
                    print(f"⚠️ 自动战斗入口异常 (可能 VNC 断开): {e}")
                    return False
                except Exception as e:
                    print(f"⚠️ 自动战斗入口未知异常: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

            def 日常_宝图():
                show_log(self.row, f"开始日常_宝图")
                print("开始日常_宝图")
                start_time = time.time()
                while True:
                    # 超时30分钟
                    if time.time() - start_time > 1800:
                        print(f"开始日常_宝图超时，退出，用时{int((time.time() - start_time) / 60)}分钟")
                        return False
                    if not 自动战斗():
                        time.sleep(1)
                        if not 人物是否移动中():
                            time.sleep(1)
                            if 请选择():
                                continue
                            if 滑屏查任务("宝图"):
                                continue
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if 识别角色等级() != -1 or ress != 0:
                                    if 查任务是否完成('宝图任务'):
                                        print(f"开始日常_宝图完成，用时{int((time.time() - start_time) / 60)}分钟")
                                        return True
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    else:
                                        print("环境异常,按键(ESC)退出")
                                        self.dx.KM.PressKey('esc')  # ESC
                                        time.sleep(1)
                                        if 关闭窗口():
                                            continue
                                        else:
                                            组合按键('alt', 'c')
                                            time.sleep(1)

            def 伙伴助战():
                res, x, y = for_ms_row(self.row, [MS.伙伴助战])
                if res:
                    show_log(self.row, f"开始伙伴助战")
                    start_time = time.time()
                    if res:
                        while True:
                            # 超时3分钟
                            if time.time() - start_time > 180:
                                print("伙伴助战超时")
                                return False
                            print("开始伙伴助战")
                            # 消费确认 
                            res, x, y = for_ms_row(self.row, [MS.消费确认])
                            if res:
                                # 按键esc退出
                                self.dx.KM.PressKey('esc')  # ESC
                                time.sleep(1)
                                return True
                            res, x, y = for_ms_row(self.row, [MS.伙伴助战])
                            if res:
                                res, x, y = for_ms_row(self.row, [MS.勾选助战第一队伍])
                                if not res:
                                    移动点击(838, 178)
                                    time.sleep(1)
                                    continue
                                res, x, y = for_ms_row(self.row, [MS.上阵助战])
                                if res:
                                    print("点击上阵助战")
                                    移动点击(x + 15, y + 15)
                                    time.sleep(1)
                                    continue
                                res, x, y = for_ms_row(self.row, [MS.添加助战])
                                if res:
                                    print("点击添加助战")
                                    移动点击(x + 20, y + 20)
                                    time.sleep(1)
                                    continue
                                # 阵法确定
                                res, x, y = for_ms_row(self.row, [MS.确定2])
                                if res:
                                    print("点击确定2")
                                    移动点击(x + 20, y + 10)
                                    time.sleep(1)
                                    continue
                                res, x, y = for_ms_row(self.row, [MS.无阵])
                                if res:
                                    print("点击无阵")
                                    移动点击(x + 20, y + 10)
                                    time.sleep(1)
                                    continue
                            else:
                                res, x, y = for_ms_row(self.row, [MS.阵法界面])
                                if res:
                                    print("进入阵法界面")
                                    # 购买阵法
                                    res, x, y = for_ms_row(self.row, [MS.购买1])
                                    if res:
                                        print("点击购买1")
                                        移动点击(x + 20, y + 10)
                                        time.sleep(1)
                                        continue
                                    # 确认购买
                                    res, x, y = for_ms_row(self.row, [MS.确认2])
                                    if res:
                                        print("点击确认2")
                                        移动点击(x + 20, y + 10)
                                        time.sleep(2)
                                        res, x, y = for_ms_row(self.row, [MS.消费确认])
                                        if res:
                                            self.dx.KM.PressKey('esc')  # ESC
                                            time.sleep(1)
                                            return True
                                        else:
                                            self.dx.KM.PressKey('esc')  # ESC
                                            time.sleep(1)
                                            return False
                                        continue
                                    # 学习阵法
                                    res, x, y = for_ms_row(self.row, [MS.学习])
                                    if res:
                                        print("点击学习")
                                        移动点击(x + 20, y + 15)
                                        time.sleep(1)
                                        continue
                                    continue
                                else:
                                    return False

            def 使用():
                res, x, y = for_ms_row(self.row, [MS.使用, MS.使用1, MS.藏宝图使用])
                if res:
                    print("点击使用")
                    移动点击(x + 30, y + 10)
                    return True
                else:
                    return False

            def 日常_三界():
                show_log(self.row, f"开始日常_三界奇缘")
                print("开始日常_三界奇缘")
                start_time = time.time()
                
                # 🔧 时间限制检查：11:00-24:00
                current_hour = time.localtime().tm_hour
                if current_hour < 11 or current_hour >= 24:
                    print(f"⏰ 当前时间{current_hour:02d}:00，不在允许时间段(11:00-24:00)，退出日常_三界奇缘")
                    show_log(self.row, f"⏰ 三界奇缘时间未到或已过期", 表格_状态)
                    return False
                
                while True:
                    # 超时10分钟
                    if time.time() - start_time > 600:
                        print("日常_三界奇缘超时")
                        self.dx.KM.PressKey('esc')  # ESC
                        time.sleep(1)
                        return False
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(0.5)
                            res, x, y = for_ms_row(self.row, [MS.求助])
                            if res:
                                # 随机点击3个坐标 （413,269），（578,269），（754,271）
                                random_pos = random.choice([(413, 269), (578, 269), (754, 271)])
                                移动点击(random_pos[0], random_pos[1])
                                time.sleep(0.5)
                                print(f"随机点击: {random_pos[0]}, {random_pos[1]}")
                                continue
                            res, x, y = for_ms_row(self.row, [MS.恭喜少侠])
                            if res:
                                print("三界奇缘任务完成，执行退出")
                                time.sleep(1)
                                # 按键(ESC)退出
                                self.dx.KM.PressKey('esc')
                                return True
                            else:
                                # 这里再次查找活动面板，避免人物等级未识别成功后从活动面板进入
                                ress, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if 识别角色等级() != -1 or ress != 0:
                                    if 查任务是否完成('三界奇缘'):
                                        print("三界奇缘任务完成，执行退出")
                                        # 按键(ESC)退出
                                        self.dx.KM.PressKey('esc')
                                        return True
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    else:
                                        print("环境异常,按键(ESC)退出")
                                        self.dx.KM.PressKey('esc')  # ESC
                                        if 关闭窗口():
                                            continue
                                        else:
                                            组合按键('alt', 'c')
                                            print("打开活动面板")

                                    time.sleep(1)

            def 日常_科举():
                show_log(self.row, f"开始科举乡试")
                print("开始科举乡试")
                start_time = time.time()
                
                # 🔧 时间限制检查：周一至周五 17:00-24:00
                now = datetime.datetime.now()
                weekday = now.weekday()  # 0=周一, 4=周五, 5=周六, 6=周日
                current_hour = now.hour
                
                # 检查是否是周一至周五
                if weekday >= 5:  # 周六或周日
                    print(f"⏰ 今天是周{weekday+1}，科举只在周一至周五开放，退出科举乡试")
                    show_log(self.row, f"⏰ 科举周末不开放", 表格_状态)
                    return False
                
                # 检查时间是否在 17:00-24:00
                if current_hour < 17 or current_hour >= 24:
                    print(f"⏰ 当前时间{current_hour:02d}:00，不在允许时间段(17:00-24:00)，退出科举乡试")
                    show_log(self.row, f"⏰ 科举时间未到或已过期", 表格_状态)
                    return False
                
                while True:
                    # 超时10分钟
                    if time.time() - start_time > 600:
                        print("科举乡试超时")
                        return False
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(0.5)
                            res, x, y = for_ms_row(self.row, [MS.科举求助])
                            if res:
                                # 随机点击4个坐标 （472,356），（722,355），（465,436），（712,433）
                                random_pos = random.choice([(472, 356), (722, 355), (465, 436), (712, 433)])
                                移动点击(random_pos[0], random_pos[1])
                                time.sleep(0.5)
                                print(f"随机点击: {random_pos[0]}, {random_pos[1]}")
                                # 完成退出
                                res, x, y = for_ms_row(self.row, [MS.学海无涯])
                                if res:
                                    self.dx.KM.PressKey('esc')  # ESC
                                    print("科举乡试完成,退出(ESC)")
                                    time.sleep(1)
                                    return True
                                continue
                            else:
                                # 这里再次查找活动面板，避免人物等级未识别成功后从活动面板进入
                                ress, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if 识别角色等级() != -1 or ress != 0:
                                    if 查任务是否完成('科举乡试'):
                                        return True
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    else:
                                        print("环境异常,按键(ESC)退出")
                                        self.dx.KM.PressKey('esc')  # ESC
                                        time.sleep(1)
                                        if 关闭窗口():
                                            continue
                                        else:
                                            组合按键('alt', 'c')
                                            print("打开活动面板")

            def 日常_趣闻():
                show_log(self.row, f"开始日常_趣闻")
                print("开始日常_趣闻")
                start_time = time.time()
                滑动次数 = 0
                while True:
                    # 超时3分钟
                    if time.time() - start_time > 180:
                        print("日常_趣闻超时")
                        return False
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(0.5)
                            res, x, y = for_ms_row(self.row, [MS.外置聊天关闭按钮, MS.对话关闭按钮])
                            if res:
                                print("进入对话框")
                                if res == 1:
                                    # 外置聊天关闭按钮
                                    移动点击(x + 5, y + 5)
                                res, x, y = for_ms_row(self.row, [MS.红心, MS.图文选中, MS.红心1])
                                if res:
                                    print("找到红心或图文选中")
                                    for i in range(5):
                                        res, x, y = for_ms_row(self.row, [MS.红心, MS.红心1])
                                        if res:
                                            移动点击(x + 15, y + 10)
                                            time.sleep(1)
                                        else:
                                            滑动屏幕(292, 397, 291, 145)
                                            time.sleep(1)
                                    print("完成5次趣闻")
                                    # 完成退出
                                    self.dx.KM.PressKey('esc')  # ESC
                                    time.sleep(1)
                                else:
                                    滑动屏幕(292, 397, 291, 145)
                                    time.sleep(1)
                                    滑动次数 += 1
                                    if 滑动次数 > 3:
                                        print("趣闻鉴赏完成")
                                        return True
                                continue
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                                if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                    if 查任务是否完成('趣闻鉴赏'):
                                        return True
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    print("环境异常,按键(ESC)退出")
                                    self.dx.KM.PressKey('esc')  # ESC
                                    time.sleep(1)

            def 日常_秘境():
                show_log(self.row, f"开始日常_秘境")
                print("开始日常_秘境")
                start_time = time.time()
                last_progress_log = start_time  # 🔧 新增：记录上次进度日志时间
                while True:
                    # 🔧 新增：每5分钟打印一次进度日志
                    current_time = time.time()
                    if current_time - last_progress_log > 300:  # 5分钟
                        elapsed = int(current_time - start_time)
                        print(f"⏱️ [秘境] 已运行 {elapsed//60}分{elapsed%60}秒")
                        show_log(self.row, f"⏱️ 秘境运行中: {elapsed//60}分{elapsed%60}秒", 表格_状态)
                        last_progress_log = current_time
                    
                    # 超时30分钟   （每天只能做一次）
                    if time.time() - start_time > 1800:
                        elapsed = int(time.time() - start_time)
                        print(f"❌ 日常_秘境超时（{elapsed//60}分{elapsed%60}秒）")
                        show_log(self.row, f"❌ 秘境超时: {elapsed//60}分{elapsed%60}秒", 表格_状态)
                        return False
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(0.5)
                            if 请选择():
                                continue
                            res, x, y = for_ms_row(self.row, [MS.确定, MS.确定1, MS.确定2,MS.确定3])
                            if res:
                                print("点击确定")
                                移动点击(x + 5, y + 5,pixel_verify=False)
                                time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.进入秘境])
                            if res:
                                print("进入秘境")
                                移动点击(x + 30, y + 15,pixel_verify=False)
                                time.sleep(1)
                                continue
                            if 使用():
                                continue
                            res, x, y = for_ms_row(self.row, [MS.秘境降妖任务])
                            if res:
                                print("进入秘境降妖任务")
                                移动点击(x + 85, y + 35,pixel_verify=False)
                                res, x, y = for_ms_row(self.row, [MS.通关])
                                if res:
                                    print("通关")
                                    show_log(self.row, "通关")
                                    移动点击(880,366)
                                    time.sleep(1)
                                    return True
                                time.sleep(1)
                                continue
                            res, x, y = for_ms_row(self.row, [MS.点击空白])
                            if res:
                                print("点击空白")
                                移动点击(434, 565,pixel_verify=False)
                                time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.离开])
                                if res:
                                    print("离开")
                                    移动点击(x + 20, y + 15)
                                    time.sleep(1)
                                continue
                            res, x, y = for_ms_row(self.row, [MS.东海秘境界面, MS.秘境降妖界面])
                            if res:
                                print("进入秘境降妖界面")
                                if res == 1:
                                    移动点击(871, 214,pixel_verify=False)
                                    time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.进入])
                                if res:
                                    print("进入")
                                    移动点击(x + 15, y + 15)
                                    time.sleep(1)
                                else:
                                    res, x, y = for_ms_row(self.row, [MS.继续挑战])
                                    if res:
                                        print("继续挑战")
                                        移动点击(x + 25, y + 25)
                                        time.sleep(1)
                                    else:
                                        print("没有找到入口")
                                        res, x, y = for_ms_row(self.row, [MS.二十四])
                                        if res:
                                            return  True
                                continue
                            # 卡界面
                            res, x, y = for_ms_row(self.row, [MS.守护者, MS.新技能])
                            if res:
                                continue
                            if 查任务是否完成('秘境降妖'):
                                time.sleep(1)
                                return True
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                                if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                    if 查任务是否完成('秘境降妖'):
                                        time.sleep(1)
                                        return True
                                    else:
                                        res = wait_for_ms(self.row, [MS.请选择, MS.请选择1],for_num=8, delay=0.5)
                                        if res:
                                            if 请选择():
                                                continue
                                    time.sleep(1)
                                else:
                                    if 关闭窗口():
                                        continue
                                    print("环境异常,按键(ESC)退出")
                                    self.dx.KM.PressKey('esc')  # ESC
                                    time.sleep(1)

            def 日常_运镖():
                show_log(self.row, f"开始日常_运镖")
                print("开始日常_运镖")
                start_time = time.time()
                if 识别活跃值() < 50:
                    return True
                while True:
                    # 超时15分钟
                    if time.time() - start_time > 900:
                        print("日常_运镖超时")
                        return False
                        # 检查是否在运镖中
                    res, x, y = for_ms_row(self.row, [MS.距离运镖])
                    if res:
                        transport_start_time = time.time()  # 记录开始运镖的时间
                        while True:
                            res, x, y = for_ms_row(self.row, [MS.距离运镖])
                            if res:
                                # 计算运镖持续时间
                                elapsed_time = int(time.time() - transport_start_time)
                                print(f"运镖中,已持续: {elapsed_time}秒")
                                time.sleep(1)  # 避免打印过于频繁
                            else:
                                break
                        time.sleep(1)
                        continue
                    if not 自动战斗():
                        # 🔧 关键修复：在调用后续函数前添加异常保护
                        try:
                            if not 人物是否移动中():
                                time.sleep(0.5)
                                if 请选择():
                                    continue
                                # 这里是助战不够的情况下触发的
                                res, x, y = for_ms_row(self.row, [MS.我很强大])
                                if res:
                                    print("我很强大")
                                    移动点击(x + 10, y + 10)
                                    time.sleep(0.5)
                                    continue
                                res, x, y = for_ms_row(self.row, [MS.确定])
                                if res:
                                    print("确定")
                                    移动点击(x + 20, y + 15)
                                    time.sleep(0.5)
                                    continue
                                ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                                if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                    if 查任务是否完成('运镖'):
                                        return True
                                    res, x, y = for_ms_row(self.row, [MS.活跃度不够])
                                    if res:
                                        print("活跃度不够,结束任务")
                                        return True
                                    else:
                                        res = wait_for_ms(self.row, [MS.请选择, MS.请选择1], for_num=8, delay=0.5)
                                        if res:
                                            print("请选择")
                                            移动点击(x + 15, y + 15)
                                            time.sleep(1)
                                            continue
                                else:
                                    if 关闭窗口():
                                        continue
                                    print("环境异常,按键(ESC)退出")
                                    self.dx.KM.PressKey('esc')  # ESC
                                    time.sleep(1)
                        except (OSError, WindowsError, SystemError) as e:
                            # 🔧 捕获访问违规，避免崩溃
                            print(f"⚠️ 日常_运镖 异常 (可能 VNC 断开): {e}")
                            time.sleep(2)
                            continue
                        except Exception as e:
                            print(f"⚠️ 日常_运镖 未知异常: {type(e).__name__}: {e}")
                            import traceback
                            traceback.print_exc()
                            time.sleep(2)
                            continue

            def 双击左键():
                self.dx.KM.LeftClick()
                time.sleep(0.1)
                self.dx.KM.LeftClick()

            def 日常_挖宝():
                show_log(self.row, f"开始日常_挖宝")
                print("开始日常_挖宝")
                start_time = time.time()
                while True:
                    # 超时15分钟
                    if time.time() - start_time > 900:
                        print("日常_挖宝超时")
                        return True
                    if not 自动战斗():
                        # 🔧 关键修复：添加异常保护
                        try:
                            if not 人物是否移动中():
                                time.sleep(0.5)
                                if 使用():
                                    time.sleep(5)
                                    continue
                                else:
                                    res, x, y = for_ms_row(self.row, [MS.包裹界面, MS.仓库界面])
                                    if res:
                                        print("进入背包界面")
                                        if res == 2:
                                            移动点击(868, 228,pixel_verify=False)
                                            time.sleep(1)
                                        # 快速查找是否有藏宝图
                                        res, x, y = for_ms_row(self.row, [MS.藏宝图])
                                        if res:
                                            print("找到藏宝图")
                                            移动点击(x + 10, y + 10,pixel_verify=False)
                                            time.sleep(1)
                                            continue
                                        # 进入背包点击整理
                                        res, x, y = for_ms_row(self.row, [MS.整理])
                                        if res:
                                            print("找到整理")
                                            移动点击(x + 10, y + 10)
                                            time.sleep(1)
                                        # 重置背包到最顶层
                                        for i in range(10):
                                            print("重置背包到最顶层")
                                            检查画面是否变化_前置截图(619, 177, 692, 256)
                                            time.sleep(0.3)
                                            滑动屏幕(692, 234, 693, 447, 1)
                                            time.sleep(0.3)
                                            if not 检查画面是否变化_验证截图(619, 177, 692, 256):
                                                # 画面未变化 → 已滑到顶 → 停止
                                                print("已重置到最顶层")
                                                time.sleep(1)
                                                break
                                        # 循环查找藏宝图
                                        time.sleep(1)
                                        for i in range(10):
                                            print(f"第{i}次 循环查找藏宝图")
                                            res, x, y = for_ms_row(self.row, [MS.藏宝图])
                                            if res:
                                                print("找到藏宝图")
                                                移动点击(x + 10, y + 10,pixel_verify=False)
                                                break
                                            else:
                                                检查画面是否变化_前置截图(598, 535, 723, 611)
                                                time.sleep(0.3)
                                                滑动屏幕(693, 504, 693, 285, 1)
                                                time.sleep(0.3)
                                                if not 检查画面是否变化_验证截图(598, 535, 723, 611):
                                                    # 画面未变化 → 已滑到底 → 停止
                                                    print("已划到到最底层")
                                                    time.sleep(1)
                                                    res, x, y = for_ms_row(self.row, [MS.藏宝图])
                                                    if not res:
                                                        print("没有找到藏宝图,挖宝结束")
                                                        return True
                                                time.sleep(1)
                                        continue
                                    else:
                                        res, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                        if res:
                                            self.dx.KM.PressKey('esc')  # ESC
                                            time.sleep(1)
                                        else:
                                            ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                                            if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                                # alt +e 打开背包界面
                                                组合按键('alt', 'e')
                                                time.sleep(1)
                                            else:
                                                if 关闭窗口():
                                                    continue
                                                else:
                                                    print("环境异常,按键(ESC)退出")
                                                    self.dx.KM.PressKey('esc')  # ESC
                                                    time.sleep(1)
                                                    if 关闭窗口():
                                                        continue
                                                    else:
                                                        print("环境异常,按键(ESC)退出")
                                                        self.dx.KM.PressKey('esc')  # ESC
                                                        time.sleep(1)
                                                        if 关闭窗口():
                                                            continue
                                                        else:
                                                            组合按键('alt', 'e')
                        except (OSError, WindowsError, SystemError) as e:
                            # 🔧 捕获访问违规，避免崩溃
                            print(f"⚠️ 日常_挖宝 异常 (可能 VNC 断开): {e}")
                            time.sleep(2)
                            continue
                        except Exception as e:
                            print(f"⚠️ 日常_挖宝 未知异常: {type(e).__name__}: {e}")
                            import traceback
                            traceback.print_exc()
                            time.sleep(2)
                            continue

            def 活力产金():
                show_log(self.row, f"开始活力产金")
                print("开始活力产金")
                start_time = time.time()
                while True:
                    # 超时3分钟
                    if time.time() - start_time > 180:
                        print("活力产金-超时退出")
                        return False

                    # 打工赚钱
                    res, x, y = for_ms_row(self.row, [MS.活力界面])
                    if res:
                        print("进入活力界面1")
                        time.sleep(0.5)
                        res, x, y = for_ms_row(self.row, [MS.打工赚钱])
                        if res:
                            xx = x
                            yy = y
                            print("打工赚钱")
                            time.sleep(1)
                            for i in range(20):
                                print(f"第{i + 1}次打工赚钱")
                                移动点击(xx + 20, yy + 15)
                                time.sleep(0.5)
                                # 您的活跃值不够
                                res, x, y = for_ms_row(self.row, [MS.您的活跃值不够])
                                if res:
                                    print("打工赚钱完成")
                                    time.sleep(1)
                                    return True
                            else:
                                滑动屏幕(628, 269, 614, 473)
                                time.sleep(0.5)
                                continue
                        else:
                            continue

                    res, x, y = for_ms_row(self.row, [MS.人物属性页面, MS.人物信息页面, MS.人物加点页面])
                    if res:
                        if res != 1:
                            移动点击(871, 221)
                            time.sleep(1)
                        print("进入人物属性页面2")
                        res, x, y = for_ms_row(self.row, [MS.使用活力])
                        if res:
                            移动点击(x + 15, y + 10)
                        time.sleep(1)
                        continue
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 'w')
                            time.sleep(0.5)
                            continue
                        else:
                            if 关闭窗口():
                                continue
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)

            def 日常_打工():
                show_log(self.row, f"开始日常_打工")
                print("开始日常_打工")
                start_time = time.time()
                开始打工 = False
                while True:
                    # 超时5分钟
                    if time.time() - start_time > 300:
                        print("日常_打工超时")
                        return False
                    else:
                        # 帮派技能炼药
                        res, x, y = for_ms_row(self.row, [MS.人物技能页面, MS.修炼技能页面, MS.辅助技能页面, MS.帮派技能页面])
                        if res:
                            if res != 4:
                                移动点击(889, 342)
                                time.sleep(1)
                            while True:
                                res, x, y = for_ms_row(self.row, [MS.中医药理副页])
                                if res:
                                    print("医药正确界面")
                                    res, x, y = for_ms_row(self.row, [MS.学习技能])
                                    if res:
                                        xx = x
                                        yy = y
                                        start_time1 = time.time()
                                        while True:
                                            if time.time() - start_time1 > 180:
                                                print("技能学习-超时退出")
                                                return False
                                            res, x, y = for_ms_row(self.row, [MS.帮派申请确定, MS.稍后再试])
                                            if res:
                                                if res == 2:
                                                    print("退出")
                                                else:
                                                    print("点击确定")
                                                    移动点击(x + 5, y + 5, pixel_verify=False)
                                                    time.sleep(1)
                                                self.dx.KM.PressKey('esc')
                                                time.sleep(2)
                                                print("开始打工")
                                                res, x, y = for_ms_row(self.row, [MS.打开炼药界面])
                                                if res:
                                                    移动点击(x + 15, y + 15)
                                                    time.sleep(1)
                                                    while True:
                                                        # 使用活力
                                                        res, x, y = for_ms_row(self.row, [MS.炼药点击])
                                                        if res:
                                                            移动点击(x + 15, y + 15)
                                                            time.sleep(0.3)
                                                            res, x, y = for_ms_row(self.row, [MS.您的活力不够])
                                                            if res:
                                                                print("活力不够,退出！")
                                                                time.sleep(2)
                                                                return True
                                                            continue
                                                        res, x, y = for_ms_row(self.row, [MS.炼药])
                                                        if res:
                                                            print("开始炼药")
                                                            continue
                                                        else:
                                                            return True


                                            res, x, y = for_ms_row(self.row, [MS.发送申请])
                                            if res:
                                                print("点击发送申请")
                                                移动点击(x + 15, y + 15)
                                                time.sleep(1)
                                                continue
                                            res, x, y = for_ms_row(self.row, [MS.批量申请])
                                            if res:
                                                print("点击批量申请")
                                                移动点击(x + 15, y + 15)
                                                time.sleep(1)
                                                continue
                                            移动点击(xx + 15, yy + 15)
                                            print("点击学习技能")
                                            time.sleep(0.5)
                                            # 消费确认
                                            res, x, y = for_ms_row(self.row, [MS.消费确认])
                                            if res:
                                                # 按键esc退出
                                                self.dx.KM.PressKey('esc')  # ESC
                                                time.sleep(1)
                                                res, x, y = for_ms_row(self.row, [MS.打开炼药界面])
                                                if res:
                                                    移动点击(x + 15, y + 15)
                                                    time.sleep(1)
                                                    开始打工 = True
                                                    break
                                            res, x, y = for_ms_row(self.row, [MS.您的帮贡不够])
                                            if res:
                                                print("帮贡不够,退出！")
                                                time.sleep(2)
                                                res, x, y = for_ms_row(self.row, [MS.打开炼药界面])
                                                if res:
                                                    移动点击(x + 15, y + 15)
                                                    time.sleep(1)
                                                    开始打工 = True
                                                    break

                                    if 开始打工:
                                        while True:
                                            # 使用活力
                                            res, x, y = for_ms_row(self.row, [MS.炼药点击])
                                            if res:
                                                移动点击(x + 15, y + 15)
                                                time.sleep(0.3)
                                                res, x, y = for_ms_row(self.row, [MS.您的活力不够])
                                                if res:
                                                    print("活力不够,退出！")
                                                    time.sleep(2)
                                                    for i in range(2):
                                                        self.dx.KM.PressKey('esc')
                                                    return True
                                                continue
                                            res, x, y = for_ms_row(self.row, [MS.炼药])
                                            if res:
                                                print("开始炼药")
                                                continue
                                            else:
                                                return True
                                else:
                                    res, x, y = for_ms_row(self.row, [MS.中医药理])
                                    if res:
                                        移动点击(x + 25, y - 45)
                                        print("点击中医药理")
                                        time.sleep(1)
                                time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.人物技能页面, MS.修炼技能页面, MS.辅助技能页面, MS.帮派技能页面])
                                if not res:
                                    print("环境异常，退出")
                                    break
                            continue
                        else:
                            ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                            if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                if 关闭窗口():
                                    continue
                                else:
                                    print("环境异常,按键(ESC)退出")
                                    self.dx.KM.PressKey('esc')  # ESC
                                    time.sleep(1)
                                    组合按键('alt', 's')
                                    time.sleep(1)

            def 日常_祈福():
                """
                日常任务 - 祈福
                TODO: 在这里实现具体的祈福逻辑
                """
                show_log(self.row, "开始日常_祈福")
                print(f"[Row:{self.row}] 开始执行日常_祈福任务")
                start_time = time.time()
                try:
                    while True:
                        res, x, y = for_ms_row(self.row, [MS.内丹等级不够])
                        if res:
                            print("内丹等级不够,退出！")
                            time.sleep(2)
                            return True
                        # 超时1分钟退出
                        if time.time() - start_time > 60:
                            return True
                        if not 自动战斗():
                            if not 人物是否移动中():
                                if 请选择():
                                    print("请选择")
                                else:
                                    res, x, y = for_ms_row(self.row, [MS.凤凰记忆])
                                    if res:
                                        print("进入凤凰记忆")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.领取内丹])
                                    if res:
                                        print("点击开始")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.点击开始])
                                    if res:
                                        print("点击开始")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.传闻])
                                    if res:
                                        print("点击传闻")
                                        移动点击(x + 60, y + 15)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.剧情])
                                    if res:
                                        print("剧情继续")
                                        移动点击(489, 404)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.前往祈福])
                                    if res:
                                        print("前往祈福")
                                        移动点击(x + 15, y + 5)
                                        time.sleep(1)
                                        continue
                                    res, x, y = for_ms_row(self.row, [MS.祈福确定])
                                    if res:
                                        print("祈福确定")
                                        移动点击(x + 5, y + 5)
                                        time.sleep(5)
                                        # 关闭界面
                                        for i in range(5):
                                            self.dx.KM.PressKey('esc')
                                            time.sleep
                                            return True
                                    res, x, y = for_ms_row(self.row, [MS.明日再来])
                                    if res:
                                        print("明日再来")
                                        return True
                                    res, x, y = for_ms_row(self.row, [MS.右侧任务栏标记, MS.主角红蓝, MS.宠物红蓝])
                                    if res:
                                        print("环境正确")
                                        self.组合按键('alt', 'q')
                                    else:
                                        if 关闭窗口():
                                            continue
                                        else:
                                            print("环境异常,按键(ESC)退出")
                                            self.dx.KM.PressKey('esc')  # ESC
                                            time.sleep(1)
                                            continue
                                    time.sleep(1)

                except Exception as e:
                    import traceback
                    error_msg = f"❌ 日常_祈福任务异常: {e}\n{traceback.format_exc()}"
                    print(error_msg)
                    show_log(self.row, f"日常_祈福任务异常: {e}", 表格_状态)
                    return False
            
            def 日常_刮刮乐():
                """
                日常任务 - 刮刮乐
                TODO: 在这里实现具体的刮刮乐逻辑
                """
                show_log(self.row, "开始日常_刮刮乐")
                print(f"[Row:{self.row}] 开始执行日常_刮刮乐任务")
                start_time = time.time()
                while True:
                    if time.time() - start_time > 180:
                        return True
                    res, x, y = for_ms_row(self.row, [MS.滑动刮奖])
                    if res:
                        print("点击滑动刮奖")
                        a = 0
                        for i in range(10):
                            滑动屏幕(491, 388 + a, 787, 388 + a, 1)
                            a += 20
                            if i == 8:
                                return True
                        continue
                    res, x, y = for_ms_row(self.row, [MS.福利界面])
                    if res:
                        print("点击福利")
                        res, x, y = for_ms_row(self.row, [MS.梦幻刮刮乐])
                        if res:
                            print("点击梦幻刮刮乐")
                            移动点击(762, 601)
                            time.sleep(1)
                            continue
                        else:
                            show_log(self.row, "✓ 日常_刮刮乐任务完成")
                            return True
                        time.sleep(1)
                        continue
                    else:
                        if 关闭窗口():
                            continue
                        else:
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)
                            if 关闭窗口():
                                continue
                            else:
                                # 打开活动界面
                                组合按键('alt', 'd')
                                time.sleep(1)
                    time.sleep(1)
            def 技能提升():
                show_log(self.row, f"开始技能提升")
                print("开始技能提升")
                start_time = time.time()
                while True:
                    # 超时1分钟
                    if time.time() - start_time > 60:
                        print("技能提升超时")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.前往])
                    if res:
                        print("前往")
                        移动点击(x + 5, y + 5)
                        time.sleep(1)
                        continue
                    res, x, y = for_ms_row(self.row, [MS.技能提升])
                    if res:
                        print("技能提升")
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        continue
                    res, x, y = for_ms_row(self.row, [MS.一键升级])
                    if res:
                        print("一键升级")
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        # 按键esc退出
                        self.dx.KM.PressKey('esc')
                        time.sleep(1)
                        return True
                    res, x, y = for_ms_row(self.row, [MS.消费确认])
                    if res:
                        print("消费确认")
                        # 按ESC键
                        self.dx.KM.PressKey('esc')
                        time.sleep(1)
                        self.dx.KM.PressKey('esc')
                        time.sleep(1)
                        #  清理背包 
                        if 清理背包():
                            return True
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 's')
                            time.sleep(1)
                            continue
                        else:
                            if 关闭窗口():
                                continue
                            print("环境异常,按键(ESC)退出")
                            self.dx.KM.PressKey('esc')  # ESC
                            time.sleep(1)

            def Ocr数字识别(x1, y1, x2, y2):
                results = self.dx.Ocr.Ocr(x1, y1, x2, y2)
                if results:
                    for i, (text, pos, confidence) in enumerate(results):
                        try:
                            # 尝试转换为数字
                            角色等级 = int(text)
                            print(f"识别到角色等级: {角色等级}")
                            return 角色等级
                        except (ValueError, TypeError):
                            return -1
                        time.sleep(1)
                    return -1
                else:
                    return -1

            def Ocr文字识别并返回坐标(需要识别的文字, x1, y1, x2, y2):
                results = self.dx.Ocr.Ocr(x1, y1, x2, y2)
                if results and len(results) > 0:
                    # 遍历所有结果，寻找匹配的文字
                    for text, pos, confidence in results:
                        if text == 需要识别的文字:
                            print(f"OCR文字识别成功: '{需要识别的文字}' 坐标: {pos}")
                            return pos
                    # 如果没有匹配，打印所有识别到的文字
                    all_texts = [text for text, _, _ in results]
                    print(f"OCR文字识别失败: 识别到的文字 {all_texts}，不匹配需要识别的文字: '{需要识别的文字}'")
                    return -1
                else:
                    print(f"OCR文字识别失败: 未识别到任何文本（查找: '{需要识别的文字}'）")
                    return -1

            def 主线任务():
                show_log(self.row, f"开始主线任务")
                print("开始主线任务")
                start_time = time.time()
                while True:
                    res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                    if res:
                        print("仙玉不足")
                        移动点击(653,180, pixel_verify=False)
                        time.sleep(0.5)
                        return True
                    # 超时60分钟

                    if time.time() - start_time > 3600:
                        print("主线任务超时，退出")
                        return False
                    if not 自动战斗():
                        if not 人物是否移动中():

                            if 请选择():
                                continue
                            if 购买():
                                res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                                if res:
                                    print("仙玉不足")
                                    移动点击(653, 180, pixel_verify=False)
                                    time.sleep(0.5)
                                    return True
                                continue
                            if 上交():
                                continue
                            if 使用():
                                continue
                            if 去完成():
                                continue
                            if 伙伴助战():
                                continue
                            # res, x, y = for_ms_row(self.row, [MS.技能提升])
                            # if res:
                            #     技能提升()
                            res, x, y = for_ms_row(self.row, [MS.角色升级, MS.地府还魂])
                            if res:
                                print("角色升级(地府还魂), 暂停主线任务")
                                if 查任务是否完成('师门任务'):
                                    return True
                                while True:
                                    if 日常_师门():
                                        break
                                    time.sleep(0.5)
                                    print("主线任务暂停中, 继续日常_师门")
                                time.sleep(1)
                                continue

                            if 滑屏查任务("主线"):
                                time.sleep(0.5)
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                                if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                                    if 关闭窗口():
                                        continue
                                    else:
                                        print("环境异常,按键(ESC)退出")
                                        self.dx.KM.PressKey('esc')  # ESC
                                        time.sleep(1)
                                else:
                                    print("点击屏幕中间")
                                    移动点击(476, 329)
                                    time.sleep(1)

            def 验证账号是否正确(账号):
                result = self.dx.Ocr.Ocr(328, 268, 629, 332)
                if not result or len(result) == 0:
                    return False
                # 将result从列表格式转换为字符串（取第一个元素）
                result_str = result[0][0] if isinstance(result, list) and len(result) > 0 and len(result[0]) > 0 else str(result)
                print(f"  🔍 验证账号 - OCR识别: '{result_str}', 目标账号: '{账号}'")
                
                # 判断账号类型：包含@的是邮箱，否则是手机号
                if '@' in 账号:
                    # 邮箱账号的判断：如果不空，就判断result是否和账号一致，一致就返回True，不一致就返回False
                    return result_str == 账号
                else:
                    # 手机账号的判断：处理带 **** 的情况
                    import re
                    
                    # 尝试用 **** 分割OCR结果
                    if '****' in result_str:
                        parts = result_str.split('****')
                        ocr_prefix = parts[0].strip()  # 前三位
                        ocr_suffix = parts[1].strip() if len(parts) > 1 else ''  # 后缀(可能3-4位)
                    else:
                        # 没有分隔符，直接提取纯数字
                        digits = re.sub(r'[^0-9]', '', result_str)
                        if len(digits) >= 7:
                            ocr_prefix = digits[:3]
                            ocr_suffix = digits[3:]  # 剩余所有数字作为后缀
                        else:
                            print(f"    ⚠️ OCR结果格式异常: '{result_str}'")
                            return False
                    
                    # 账号的后4位
                    account_digits = re.sub(r'[^0-9]', '', 账号)
                    if len(account_digits) < 7:
                        print(f"    ⚠️ 账号格式异常: '{账号}'")
                        return False
                    
                    account_prefix = account_digits[:3]
                    account_suffix = account_digits[-4:]  # 固定取后4位
                    
                    print(f"    📱 OCR前缀: '{ocr_prefix}', OCR后缀: '{ocr_suffix}'")
                    print(f"    📱 账号前缀: '{account_prefix}', 账号后缀: '{account_suffix}'")
                    
                    # 验证前缀（必须精确匹配）
                    if ocr_prefix != account_prefix:
                        print(f"    ❌ 前缀不匹配")
                        return False
                    
                    # 验证后缀（模糊匹配：OCR后缀的每个数字都能在账号后缀中找到）
                    if not ocr_suffix:
                        # 没有后缀，只要前缀匹配就算成功
                        print(f"    ✅ 前缀匹配成功（无后缀）")
                        return True
                    
                    # 检查OCR后缀的每个数字是否都在账号后缀中
                    suffix_match_count = sum(1 for digit in ocr_suffix if digit in account_suffix)
                    suffix_match_rate = suffix_match_count / len(ocr_suffix) if len(ocr_suffix) > 0 else 0
                    
                    print(f"    📱 后缀匹配: {suffix_match_count}/{len(ocr_suffix)} 个数字匹配, 匹配率: {suffix_match_rate:.0%}")
                    
                    # 允许少1-2位数字（容错）
                    # 如果OCR后缀有3-4位，至少需要匹配 len(ocr_suffix)-1 个数字
                    min_match_count = max(len(ocr_suffix) - 1, 2)  # 至少匹配2个数字
                    
                    if suffix_match_count >= min_match_count and suffix_match_rate >= 0.6:
                        print(f"    ✅ 后缀模糊匹配成功")
                        return True
                    else:
                        print(f"    ❌ 后缀匹配不足 (需要至少{min_match_count}个)")
                        return False

            def 切换账号(账号):
                """
                切换账号功能：OCR识别账号列表，比对并点击匹配的账号
                返回: 是否找到
                """
                # 添加 VNC 连接检查
                try:
                    if not hasattr(self.dx, 'screenshot') or self.dx.screenshot is None:
                        print("错误：截图对象不存在")
                        return False
                except Exception as e:
                    print(f"检查截图对象异常：{e}")
                    return False
                # 快捷点「进入游戏」若无效（分辨率/布局不同），勿死循环，改走 OCR 选账户
                _进入游戏快捷可用 = True
                while True:
                    res, x, y = for_ms_row(self.row, [MS.账号界面])
                    if res:
                        print("找到账号界面")
                        time.sleep(1)
                        res_eg, x_eg, y_eg = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                        if res_eg :
                            print("找到进入游戏")
                            移动点击(596,347, pixel_verify=False)
                            time.sleep(1)
                            # 处理意外报错框遮住的问题
                            res, x, y = for_ms_row(self.row, [MS.意外报错])
                            if res:
                                print("找到意外报错")
                                移动点击(x - 47, y - 93)
                                time.sleep(1)
                                滑动屏幕(x - 47, y - 93, 461, 733)
                                time.sleep(1)
                                continue
                            # OCR识别账户
                            for i in range(3):
                                try:
                                    print(f"[Row:{self.row}] 第{i + 1}次OCR识别" )
                                    
                                    # 🔧 关键修复：每次 OCR 前验证 VNC 连接状态
                                    if not hasattr(self.dx, 'screenshot') or self.dx.screenshot is None:
                                        print(f"[Row:{self.row}] ❌ VNC 截图对象不存在，尝试重新连接...")
                                        设置截图模式(编号)
                                        time.sleep(2)
                                    
                                    if not hasattr(self.dx.screenshot, 'client') or self.dx.screenshot.client is None:
                                        print(f"[Row:{self.row}] ❌ VNC 客户端未连接，尝试重新连接...")
                                        设置截图模式(编号)
                                        time.sleep(2)
                                    
                                    # 🔍 检查后台截图线程是否正常
                                    if not hasattr(self.dx.screenshot, 'image') or self.dx.screenshot.image is None:
                                        print(f"[Row:{self.row}] ⚠️ 后台截图线程未就绪，等待 2 秒...")
                                        time.sleep(2)
                                        # 再次检查
                                        if self.dx.screenshot.image is None:
                                            print(f"[Row:{self.row}] ❌ 后台截图线程仍未就绪，重启 VNC...")
                                            设置截图模式(编号)
                                            time.sleep(2)
                                    
                                    # 测试截图
                                    try:
                                        test_img = self.dx.screenshot.Capture()
                                        if test_img is None:
                                            print(f"[Row:{self.row}] ⚠️ 第{i + 1}次 OCR 前截图失败，VNC 连接可能已断开")
                                            print("   尝试重新连接 VNC...")
                                            设置截图模式(编号)
                                            time.sleep(2)
                                            continue
                                    except Exception as e:
                                        print(f"[Row:{self.row}] ⚠️ 第{i + 1}次 OCR 前 VNC 检查失败：{e}")
                                        print("   尝试重新连接 VNC...")
                                        设置截图模式(编号)
                                        time.sleep(2)
                                        continue
                                    
                                    # ✅ VNC 正常，执行 OCR
                                    result = None
                                    if i == 0:
                                        result=self.dx.Ocr.Ocr(367,323,577,370)
                                    elif i == 1:
                                        result=self.dx.Ocr.Ocr(368,429,582,466)
                                    elif i == 2:
                                        result=self.dx.Ocr.Ocr(367,470,586,509)
                                    print(f"[Row:{self.row}] OCR 结果:{result}")
                                    # 添加结果有效性检查
                                    if not result or len(result) == 0:
                                        print(f"[Row:{self.row}] 第{i + 1}次 OCR 识别结果为空，继续下一次")
                                        time.sleep(2)
                                        continue
                                except (IndexError, TypeError, ValueError) as e:
                                    print(f"坐标访问异常：{e}, ocr_coords={ocr_coords}")
                                # 将结果和账号进行比对验证，如果是邮箱就直接验证，如果是手机号就判断前三位和后四位是否一致
                                if result and len(result) > 0:
                                    print(f"  📋 当前待匹配账号: {账号}")
                                    print(f"  📋 账号类型: {'邮箱' if '@' in 账号 else '手机号'}")
                                    # 遍历OCR结果，查找匹配的账号
                                    for item in result:
                                        if len(item) >= 2:
                                            ocr_text = item[0]  # 识别的文本
                                            ocr_coords = item[1]  # 坐标 (x, y)
                                            print(f"    🔍 正在检查 OCR 结果: '{ocr_text}'")

                                            # 判断账号类型并比对
                                            if '@' in 账号:
                                                # 邮箱账号：提取@前的字符串，检查OCR结果是否包含该字符串（支持模糊匹配）
                                                try:
                                                    print(f"    📧 开始邮箱账号匹配验证...")
                                                    # 提取账号中@前的部分（用户名）
                                                    account_username = 账号.split('@')[0].strip()

                                                    # 提取OCR结果中@前的部分（如果包含@）
                                                    ocr_text_lower = ocr_text.lower()
                                                    account_username_lower = account_username.lower()

                                                    # 如果OCR结果包含@，提取@前的部分
                                                    if '@' in ocr_text_lower:
                                                        ocr_username = ocr_text_lower.split('@')[0].strip()
                                                    else:
                                                        ocr_username = ocr_text_lower

                                                    print(f'      账号@前缀: {account_username_lower}')
                                                    print(f'      OCR结果前缀: {ocr_username}')

                                                    # 方法1: 精确匹配
                                                    if account_username_lower in ocr_text_lower:
                                                        print(
                                                            f"找到匹配的邮箱账号（精确匹配）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                        start_time = time.time()
                                                        while True:
                                                            if time.time() - start_time > 10:
                                                                print(f"  - 匹配超时，请手动处理")
                                                                break
                                                            res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                            if res:
                                                                移动点击(x + 10, y + 10)
                                                                time.sleep(5)
                                                                return True
                                                            else:
                                                                移动点击(int(ocr_coords[0]), int(ocr_coords[1]) - 20)
                                                                time.sleep(2)
                                                                移动点击(94, 286,pixel_verify=False)
                                                                time.sleep(2)

                                                    # 方法2: 子序列匹配（OCR结果按顺序在账号中能找到，允许缺失）
                                                    def is_subsequence(ocr_text, account_text):
                                                        """
                                                        检查 ocr_text 是否是 account_text 的子序列
                                                        即：ocr_text 的每个字符按顺序都能在 account_text 中找到
                                                        示例：'taxn' 是 'taxmin18802051824' 的子序列 → True
                                                        """
                                                        ocr_idx = 0
                                                        for char in account_text:
                                                            if ocr_idx < len(ocr_text) and char == ocr_text[ocr_idx]:
                                                                ocr_idx += 1
                                                        return ocr_idx == len(ocr_text)
                                                    
                                                    def normalize_ocr_text(text):
                                                        """标准化OCR文本，修正常见识别错误"""
                                                        # 常见OCR混淆字符替换
                                                        corrections = {
                                                            '.col': '.com',      # l -> m（最常见）
                                                            '.con': '.com',      # n -> m
                                                            '.coi': '.com',      # i -> m
                                                            '.c0m': '.com',      # 0 -> o
                                                            '.c0l': '.com',      # 0->o, l->m
                                                        }
                                                        normalized = text.lower()
                                                        original = normalized
                                                        for wrong, correct in corrections.items():
                                                            if wrong in normalized:
                                                                normalized = normalized.replace(wrong, correct)
                                                                if normalized != original:
                                                                    print(f"    📝 OCR文本修正: '{wrong}' -> '{correct}'")
                                                                    original = normalized
                                                        return normalized
                                                    
                                                    # 先尝试标准化OCR文本后再匹配
                                                    normalized_ocr_username = normalize_ocr_text(ocr_username)
                                                    
                                                    print(f'      标准化后OCR前缀: {normalized_ocr_username}')
                                                    
                                                    # 如果标准化后能精确匹配，优先使用
                                                    if account_username_lower == normalized_ocr_username or account_username_lower in normalized_ocr_username:
                                                        print(
                                                            f"找到匹配的邮箱账号（标准化后精确匹配）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                        start_time = time.time()
                                                        while True:
                                                            if time.time() - start_time > 10:
                                                                print(f"  - 匹配超时，请手动处理")
                                                                break
                                                            res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                            if res:
                                                                移动点击(x + 10, y + 10)
                                                                time.sleep(5)
                                                                return True
                                                            else:
                                                                移动点击(int(ocr_coords[0]), int(ocr_coords[1]) - 20)
                                                                time.sleep(2)
                                                                移动点击(94, 286)
                                                                time.sleep(2)

                                                    # 子序列匹配：OCR结果按顺序在账号中能找到（允许缺失）
                                                    if is_subsequence(normalized_ocr_username, account_username_lower):
                                                        print(
                                                            f"找到匹配的邮箱账号（子序列匹配）: OCR结果='{ocr_text}', 账号='{账号}', 坐标: {ocr_coords}")
                                                        print(f"    ✅ OCR '{normalized_ocr_username}' 是账号 '{account_username_lower}' 的子序列")
                                                        start_time = time.time()
                                                        while True:
                                                            if time.time() - start_time > 10:
                                                                print(f"  - 匹配超时，请手动处理")
                                                                break
                                                            res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                            if res:
                                                                移动点击(x + 10, y + 10)
                                                                time.sleep(5)
                                                                return True
                                                            else:
                                                                移动点击(int(ocr_coords[0]), int(ocr_coords[1]) - 20)
                                                                time.sleep(2)
                                                                移动点击(94, 286)
                                                                time.sleep(2)
                                                    else:
                                                        print(f"    ❌ 子序列匹配失败: OCR '{normalized_ocr_username}' 不是账号 '{account_username_lower}' 的子序列")

                                                except Exception as e:
                                                    # 如果提取过程中出错，跳过当前结果
                                                    print(f"邮箱账号匹配出错: {e}, OCR文本={ocr_text}")
                                                    import traceback
                                                    traceback.print_exc()
                                                    continue
                                            else:
                                                # 使用新的手机号验证函数（支持 **** 分隔符）
                                                print(f"    📱 开始手机号匹配验证...")
                                                匹配成功,前缀,后缀 = verify_phone_number(ocr_text, 账号)
                                                print(f"    📱 匹配结果: 成功={匹配成功}, 前缀='{前缀}', 后缀='{后缀}'")
                                                if 匹配成功:
                                                    print(f"找到匹配的手机号账号：{ocr_text}, 坐标：{ocr_coords}")
                                                    print(f"  - OCR 识别：{ocr_text}")
                                                    print(f"  - 完整账号：{账号}")
                                                    print(f"  - 提取前缀：{前缀}, 提取后缀：{后缀}")
                                                    # 转整数，防止有空格什么的
                                                    start_time = time.time()
                                                    while True:
                                                        if time.time() - start_time > 10:
                                                            print(f"  - 匹配超时，请手动处理")
                                                            break
                                                        res, x, y = for_ms_row(self.row, [MS.进入游戏,MS.进入游戏1])
                                                        if res:
                                                            移动点击(x + 10, y + 10)
                                                            time.sleep(5)
                                                            return True
                                                        else:
                                                            移动点击(int(ocr_coords[0]), int(ocr_coords[1]) - 20)
                                                            time.sleep(2)
                                                            移动点击(94, 286)
                                                            time.sleep(2)

                                i = i + 1
                                time.sleep(2)
                            else:
                                # 循环正常结束，说明没找到匹配的账号
                                print("未找到匹配的账号")
                                return False
                        else:
                            # OCR识别账户
                            for i in range(3):
                                try:
                                    print(f"第{i + 1}次OCR识别")
                                    # 每次 OCR 前检查 VNC 连接
                                    try:
                                        test_img = self.dx.screenshot.Capture()
                                        if test_img is None:
                                            print(f"⚠️ 第{i + 1}次 OCR 前截图失败，VNC 连接可能已断开")
                                            print("   请检查：")
                                            print("   1. 模拟器是否正在运行")
                                            print("   2. VNC 服务是否正常")
                                            print("   3. 尝试重启模拟器")
                                            time.sleep(2)
                                            continue
                                    except Exception as e:
                                        print(f"⚠️ 第{i + 1}次 OCR 前 VNC 检查失败：{e}")
                                        print("   VNC 连接已断开，请检查模拟器状态！")
                                        time.sleep(2)
                                        continue
                                    result = None

                                    if i == 0:
                                        result = self.dx.Ocr.Ocr(367, 323, 577, 370)
                                    elif i == 1:
                                        result = self.dx.Ocr.Ocr(368, 429, 582, 466)
                                    elif i == 2:
                                        result = self.dx.Ocr.Ocr(367, 470, 586, 509)
                                    print(f"OCR 结果:{result}")
                                    # 添加结果有效性检查
                                    if not result or len(result) == 0:
                                        print(f"第{i + 1}次 OCR 识别结果为空，继续下一次")
                                        time.sleep(2)
                                        continue
                                except (IndexError, TypeError, ValueError) as e:
                                    print(f"坐标访问异常：{e}, ocr_coords={ocr_coords}")
                                # 将结果和账号进行比对验证，如果是邮箱就直接验证，如果是手机号就判断前三位和后四位是否一致
                                if result and len(result) > 0:
                                    print(f"  📋 当前待匹配账号: {账号}")
                                    print(f"  📋 账号类型: {'邮箱' if '@' in 账号 else '手机号'}")
                                    # 遍历OCR结果，查找匹配的账号
                                    for item in result:
                                        if len(item) >= 2:
                                            ocr_text = item[0]  # 识别的文本
                                            ocr_coords = item[1]  # 坐标 (x, y)
                                            print(f"    🔍 正在检查 OCR 结果: '{ocr_text}'")

                                            # 判断账号类型并比对
                                            if '@' in 账号:
                                                # 邮箱账号：提取@前的字符串，检查OCR结果是否包含该字符串（支持模糊匹配）
                                                try:
                                                    print(f"    📧 开始邮箱账号匹配验证...")
                                                    # 提取账号中@前的部分（用户名）
                                                    account_username = 账号.split('@')[0].strip()

                                                    # 提取OCR结果中@前的部分（如果包含@）
                                                    ocr_text_lower = ocr_text.lower()
                                                    account_username_lower = account_username.lower()

                                                    # 如果OCR结果包含@，提取@前的部分
                                                    if '@' in ocr_text_lower:
                                                        ocr_username = ocr_text_lower.split('@')[0].strip()
                                                    else:
                                                        ocr_username = ocr_text_lower

                                                    print(f'      账号@前缀: {account_username_lower}')
                                                    print(f'      OCR结果前缀: {ocr_username}')

                                                    # 方法1: 精确匹配
                                                    if account_username_lower in ocr_text_lower:
                                                        print(
                                                            f"找到匹配的邮箱账号（精确匹配）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                        移动点击(ocr_coords[0], ocr_coords[1])
                                                        time.sleep(2)
                                                        res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                        if res:
                                                            移动点击(x + 10, y + 10,pixel_verify=False)
                                                            time.sleep(2)
                                                        return True

                                                    # 方法2: 模糊匹配（字母80%，数字100%）
                                                    # 分离字母和数字部分
                                                    def extract_letters_and_digits(text):
                                                        """提取文本中的字母部分和数字部分"""
                                                        letters = re.sub(r'[^a-zA-Z]', '', text)
                                                        digits = re.sub(r'[^0-9]', '', text)
                                                        return letters, digits

                                                    def normalize_ocr_text(text):
                                                        """标准化OCR文本，修正常见识别错误"""
                                                        # 常见OCR混淆字符替换
                                                        corrections = {
                                                            '.col': '.com',  # l -> m（最常见）
                                                            '.con': '.com',  # n -> m
                                                            '.coi': '.com',  # i -> m
                                                            '.c0m': '.com',  # 0 -> o
                                                            '.c0l': '.com',  # 0->o, l->m
                                                        }
                                                        normalized = text.lower()
                                                        original = normalized
                                                        for wrong, correct in corrections.items():
                                                            if wrong in normalized:
                                                                normalized = normalized.replace(wrong, correct)
                                                                if normalized != original:
                                                                    print(f"    📝 OCR文本修正: '{wrong}' -> '{correct}'")
                                                                    original = normalized
                                                        return normalized

                                                    account_letters, account_digits = extract_letters_and_digits(
                                                        account_username_lower)
                                                    ocr_letters, ocr_digits = extract_letters_and_digits(ocr_username)

                                                    # 先尝试标准化OCR文本后再匹配
                                                    normalized_ocr_username = normalize_ocr_text(ocr_username)
                                                    normalized_ocr_letters, normalized_ocr_digits = extract_letters_and_digits(
                                                        normalized_ocr_username)

                                                    print(f'      标准化后OCR前缀: {normalized_ocr_username}')

                                                    # 如果标准化后能精确匹配，优先使用
                                                    if account_username_lower == normalized_ocr_username or account_username_lower in normalized_ocr_username:
                                                        print(
                                                            f"找到匹配的邮箱账号（标准化后精确匹配）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                        移动点击(ocr_coords[0], ocr_coords[1])
                                                        time.sleep(2)
                                                        res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                        if res:
                                                            移动点击(x + 10, y + 10,pixel_verify=False)
                                                            time.sleep(2)
                                                        return True

                                                    # 检查数字部分：必须100%匹配（如果账号中有数字）
                                                    if account_digits:
                                                        if not normalized_ocr_digits:
                                                            print(f"账号有数字但OCR没有数字: 账号数字={account_digits}")
                                                            continue
                                                        if account_digits != normalized_ocr_digits:
                                                            print(
                                                                f"数字部分不匹配: 账号数字={account_digits}, OCR数字={normalized_ocr_digits}")
                                                            continue
                                                        print(f"数字部分匹配: {account_digits}")

                                                    # 检查字母部分：相似度>=80%（如果账号中有字母）
                                                    if account_letters:
                                                        if not normalized_ocr_letters:
                                                            print(f"账号有字母但OCR没有字母: 账号字母={account_letters}")
                                                            continue
                                                        # 计算字母部分的相似度
                                                        letter_similarity = SequenceMatcher(None, account_letters,
                                                                                            normalized_ocr_letters).ratio()
                                                        print(
                                                            f"字母部分相似度: {letter_similarity:.2f} (账号字母={account_letters}, OCR字母={normalized_ocr_letters})")

                                                        if letter_similarity >= 0.80:
                                                            print(
                                                                f"找到匹配的邮箱账号（模糊匹配，字母相似度={letter_similarity:.2f}）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                            移动点击(ocr_coords[0], ocr_coords[1])
                                                            time.sleep(1)
                                                            移动点击(94, 286, pixel_verify=False)
                                                            time.sleep(2)
                                                            res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                            if res:
                                                                移动点击(x + 10, y + 10, pixel_verify=False)
                                                                time.sleep(2)
                                                            return True
                                                        else:
                                                            print(f"字母部分相似度不足80%: {letter_similarity:.2f}")
                                                    elif account_digits:
                                                        # 如果账号只有数字（没有字母），且数字已匹配，则通过
                                                        print(
                                                            f"找到匹配的邮箱账号（纯数字匹配）: OCR结果={ocr_text}, 匹配用户名={account_username}, 坐标: {ocr_coords}")
                                                        移动点击(ocr_coords[0], ocr_coords[1])
                                                        time.sleep(1)
                                                        移动点击(94, 286, pixel_verify=False)
                                                        time.sleep(2)
                                                        res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                        if res:
                                                            移动点击(x + 10, y + 10, pixel_verify=False)
                                                            time.sleep(2)
                                                        return True

                                                except Exception as e:
                                                    # 如果提取过程中出错，跳过当前结果
                                                    print(f"邮箱账号匹配出错: {e}, OCR文本={ocr_text}")
                                                    import traceback
                                                    traceback.print_exc()
                                                    continue
                                            else:
                                                # 使用新的手机号验证函数（支持 **** 分隔符）
                                                print(f"    📱 开始手机号匹配验证...")
                                                匹配成功, 前缀, 后缀 = verify_phone_number(ocr_text, 账号)
                                                print(f"    📱 匹配结果: 成功={匹配成功}, 前缀='{前缀}', 后缀='{后缀}'")
                                                if 匹配成功:
                                                    print(f"找到匹配的手机号账号：{ocr_text}, 坐标：{ocr_coords}")
                                                    print(f"  - OCR 识别：{ocr_text}")
                                                    print(f"  - 完整账号：{账号}")
                                                    print(f"  - 提取前缀：{前缀}, 提取后缀：{后缀}")
                                                    # 转整数，防止有空格什么的
                                                    移动点击(int(ocr_coords[0]), int(ocr_coords[1]) - 20)
                                                    time.sleep(2)
                                                    移动点击(94, 286)
                                                    time.sleep(2)
                                                    res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                                    if res:
                                                        移动点击(x + 10, y + 10)
                                                        time.sleep(5)
                                                    return True
                                i = i + 1
                                time.sleep(2)
                            else:
                                # 循环正常结束，说明没找到匹配的账号
                                print("未找到匹配的账号")
                                return False

                        continue

            def 识别活跃值 ():
                # 优化 1：使用缓存避免重复找图（有效期 5 秒）
                if hasattr(self, '_活跃值缓存'):
                    缓存时间,缓存值 = self._活跃值缓存
                    if time.time() - 缓存时间 < 5.0:  # 5 秒内直接使用缓存
                        print(f"使用缓存活跃值：{缓存值}")
                        return 缓存值
                
                while True:
                    # 但是我们可以确保在连续调用时，使用的是同一帧图像
                    res_活动界面,x_活动,y_活动 = for_ms_row(self.row, [MS.活动界面])
                    
                    if res_活动界面:
                        print("找到活动界面")
                        # 在同一帧图像上继续查找其他特征
                        res_零活跃,x_零,y_零 = for_ms_row(self.row, [MS.零活跃])
                        if res_零活跃:
                            print("当前活跃值：0")
                            self._活跃值缓存 = (time.time(), 0)  # 优化 2：保存缓存
                            return 0
                        else:
                            res_特征,x_特征,y_特征 = for_ms_row(self.row, [MS.活跃特征])
                            if res_特征:
                                # 根据活跃特征的 X 坐标精确计算活跃值
                                # X 轴映射关系：208-818 像素 -> 0-100 活跃值
                                X_MIN = 208    # X 轴最小值（对应活跃值 0）
                                X_MAX = 818    # X 轴最大值（对应活跃值 100）
                                活跃值_MIN = 0   # 活跃值最小值
                                活跃值_MAX = 100 # 活跃值最大值
                                                                                            
                                # 计算特征图中心点 X 坐标（更精确）
                                特征中心X = x_特征 + 30  # 使用批量检测的坐标

                                # 线性映射公式：y = (x - x1) * (y2 - y1) / (x2 - x1) + y1
                                # 活跃值 = (特征中心 X - X_MIN) * (活跃值_MAX - 活跃值_MIN) / (X_MAX - X_MIN) + 活跃值_MIN
                                                            
                                if 特征中心X < X_MIN:
                                    特征中心X = X_MIN  # 限制在有效范围内
                                elif 特征中心X > X_MAX:
                                    特征中心X = X_MAX
                                                            
                                # 计算活跃值（保留整数）
                                活跃值 = int((特征中心X - X_MIN) * (活跃值_MAX - 活跃值_MIN) / (X_MAX - X_MIN) + 活跃值_MIN)
                                                            
                                # 确保在 0-100 范围内
                                活跃值 = max(0, min(100, 活跃值))-1
                                                                                            
                                print(f"识别活跃值：{活跃值} 正确率：90%")
                                self._活跃值缓存 = (time.time(), 活跃值)  # 优化 4：保存缓存
                                return 活跃值
                        continue
                    else:
                        # 优化 6：批量检测右侧任务栏和角色等级
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        角色等级 = 识别角色等级 ()
                        宠物等级 = 识别宠物等级 ()
                                            
                        if 角色等级 != -1 or 宠物等级 != -1 or ress:
                            print("已识别角色等级")
                            if 关闭窗口():
                                print("已关闭窗口")
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)
                                if 关闭窗口():
                                    pass
                                else:
                                    组合按键('alt', 'c')
                        else:
                            if 关闭窗口():
                                pass
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)

                    time.sleep(1)

            def 账号登录(账号):
                show_log(self.row, "开始账号登录")
                print(f"开始账号登录: 账号={账号}")
                卡界面 = 0
                _login_iter = 0
                _login_t0 = time.time()
                _login_last_hb = 0.0
                while True:
                    # 处理弹窗重连失败的时候怎么进入游戏
                    res, x, y = for_ms_row(self.row, [MS.重连失败])
                    if res:
                        print("点击重连失败")
                        移动点击(x + 140, y + 75)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.登录游戏1, MS.登录游戏])
                        if ress:
                            print("点击登录游戏")
                            移动点击(463, 510)
                        time.sleep(1)
                    _login_iter += 1
                    _now = time.time()
                    _login_heartbeat = _login_iter <= 2 or (_now - _login_last_hb) >= 15.0
                    if _login_heartbeat:
                        _login_last_hb = _now
                    # 如果此时界面是用户中心,就点击切换账号到账号界面中去
                    res, x, y = for_ms_row(self.row, [MS.用户中心, MS.用户中心1])
                    if _login_heartbeat:
                        print(
                            f"账号登录 iter={_login_iter} wall={int(time.time() - _login_t0)}s "
                            f"用户中心命中={bool(res)}(res={res})；"
                            f"iter 若在涨=整轮外循环在跑，并非永久卡死在一次 for_ms_row"
                        )
                    if res:
                        print("找到用户中心")
                        time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.切换账号, MS.切换账号1])
                        if res:
                            print("找到切换账号")
                            移动点击(x + 15, y + 10)
                            time.sleep(1)
                            # 等待账号界面出现
                            ress = wait_for_ms(self.row, [MS.进入游戏, MS.进入游戏1, MS.账号界面], for_num=8, delay=0.5)
                            if ress:
                                break
                    # 如果此时是弹窗退出排队，说明正在排队中，点击退出
                    res, x, y = for_ms_row(self.row, [MS.退出排队])
                    if res:
                        print("找到退出排队")
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        continue
                    # 这里是点击退出排队后的确定退出的弹窗界面处理
                    res, x, y = for_ms_row(self.row,[MS.确定,MS.确定1,MS.确定2])
                    if res:
                        print("找到确定")
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        continue
                    # 如果是账号界面，就直接验证账号揪就行
                    res, x, y = for_ms_row(self.row, [MS.账号界面])
                    if res:
                        while True:
                            print("开始账号验证....")
                            if 验证账号是否正确图片版本(账号):
                                print("账号验证成功")
                                # ✅ 账号验证成功后，点击进入游戏
                                res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                                if res:
                                    print("找到进入游戏")
                                    移动点击(x + 15, y + 10)
                                    time.sleep(1)
                                
                                # ✅ 等待进入登录游戏界面
                                ress = wait_for_ms(self.row, [MS.登录游戏1, MS.登录游戏], for_num=5, delay=0.5)
                                if ress:
                                    print("点击登录游戏,账号验证成功")
                                    移动点击(463, 510)
                                    time.sleep(5)
                                    return True  # ✅ 账号登录成功，返回
                            time.sleep(1)

                    #如果是用户图标，就点击用户图标，进入到用户中心界面
                    res, x, y = for_ms_row(self.row, [MS.用户图标,MS.用户图标1])
                    if res:
                        print("找到用户图标")
                        time.sleep(1)
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.用户中心, MS.用户中心1], for_num=8, delay=0.5)
                        if ress:
                            print("找到用户中心")
                            time.sleep(1)
                            continue
                        else:
                            print("疑似网络刷新问题")
                            res, x1, y1 = for_ms_row(self.row, [MS.游戏运行图标])
                            if res:
                                print("找到游戏运行图标")
                                移动点击(x1 + 15, y1 + 10, pixel_verify=False)
                                time.sleep(1)
                                移动点击(x1 + 15, y1 + 10)
                                time.sleep(1)
                                ress = wait_for_ms(self.row, [MS.游戏左上角图标], for_num=5, delay=0.5)
                                if ress:
                                    print("找到游戏左上角图标")
                                    continue
                                else:
                                    移动点击(x1 + 15, y1 + 10, pixel_verify=False)
                    # 如果在游戏中，则退出到登录界面
                    res, x, y = for_ms_row(self.row, [MS.登出])
                    if res:
                        print("找到登出")
                        移动点击(x + 15, y + 10)
                        ress = wait_for_ms(self.row, [MS.进入游戏, MS.进入游戏1, MS.账号界面], for_num=8, delay=0.5)
                        if ress:
                            break
                        continue
                    else:
                        res, x, y = for_ms_row(self.row, [MS.基础设置])
                        if res:
                            print("找到基础设置")
                            res, x, y = for_ms_row(self.row, [MS.切换账号2,MS.切换账号,MS.切换账号1])
                            if res:
                                print("找到切换账号，点击坐标: (248,586)")
                                移动点击(248,586)
                                time.sleep(1)
                                # ✅ 等待账号界面出现（最多等6秒，12次×0.5秒）
                                ress = wait_for_ms(self.row, [MS.进入游戏, MS.进入游戏1, MS.账号界面], for_num=12, delay=0.5)
                                if ress:
                                    print("✅ 已切换到账号界面")
                                    continue
                                else:
                                    print("⚠️ 等待账号界面超时（6秒），尝试其他方式...")
                        else:
                            # 弥补角色等级识别错误的时候，去看任务栏标记判断是否游戏中
                            ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                            # 识别宠物等级
                            if 识别角色等级() != -1 or ress or 识别宠物等级() != -1:
                                print("未找到基础设置,快捷键alt+j")

                                # 确保角色等级识别错误后，清空界面环境，esc
                                self.dx.KM.PressKey('esc')
                                time.sleep(0.5)
                                组合按键('alt', 'j')
                                time.sleep(1)
                            else:
                                res,x,y = for_ms_row(self.row, [MS.离开])
                                if res:
                                    print("找到离开")
                                    移动点击(x + 15, y + 10)
                                    time.sleep(1)
                                    continue
                                else:
                                    if 关闭窗口():
                                        print("检测到游戏内窗口界面")
                                    else:
                                        self.dx.KM.PressKey('esc')
                return False

            def 选择区服(区服):
                show_log(self.row, "开始选择区服")
                print(f"[Row:{self.row}] 开始选择区服: 区服={区服}")
                
                # 检查 VNC 状态
                if hasattr(self.dx, 'screenshot') and self.dx.screenshot:
                    vnc = self.dx.screenshot
                    if not hasattr(vnc, 'client') or vnc.client is None:
                        print(f"[Row:{self.row}] ❌ VNC 连接已断开！尝试重连...")
                        show_log(self.row, "VNC 连接断开，尝试重连", 表格_状态)
                        # 这里可以触发重连逻辑
                        return False, 0, 0
                
                while True:
                    # 如果是未选择服务器，就继续等待服务器更新出来
                    res, x, y = for_ms_row(self.row, [MS.未选择服务器])
                    if res:
                        print("网络卡顿，服务未刷新出来")
                        time.sleep(1)
                        continue
                    # 如果现在还是在进入游戏这个界面，就点击进入游戏（异常情况）
                    res, x, y = for_ms_row(self.row, [MS.进入游戏, MS.进入游戏1])
                    if res:
                        print("找到进入游戏")
                        移动点击(x + 15, y + 10)
                        time.sleep(1)
                        continue
                    # 如果是用户中心，就点击用户中心关闭（异常情况）
                    res, x, y = for_ms_row(self.row, [MS.用户中心, MS.用户中心1])
                    if res:
                        print("找到用户中心")
                        移动点击(630,143)
                        time.sleep(1)
                        continue
                    # 如果重连失败，就点击重连失败
                    res, x, y = for_ms_row(self.row, [MS.重连失败])
                    if res:
                        print("点击重连失败")
                        移动点击(x + 140, y + 75)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.登录游戏1, MS.登录游戏])
                        if ress:
                            continue
                    # 从这里进入到区服选择界面
                    res, x, y = for_ms_row(self.row, [MS.登录游戏, MS.登录游戏1])
                    if res:
                        print("找到登录游戏")
                        移动点击(x+5, y - 70)
                        time.sleep(5)
                        continue
                    # 确认是在正式服分页
                    res, x, y = for_ms_row(self.row, [MS.正式服, MS.轻享服, MS.区服关闭, MS.已有角色])
                    if res:
                        print("找到区服界面")
                        if res == 2:
                            移动点击(149, 154)
                            time.sleep(1)
                        # 特殊服务器 老区服
                        if 区服 == "日月山河":
                            res, x, y = for_ms_row(self.row, [MS.七区])
                            if res:
                                移动点击(x + 5, y + 5)
                                time.sleep(1)
                                print("找到七区")
                                # 重置到最顶层
                                for i in range(10):
                                    检查画面是否变化_前置截图(267, 581, 413, 653)
                                    滑动屏幕(574, 197, 574, 555, 1)  # 从下往上滑动
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                        # 画面未变化 → 已滑到底 → 停止
                                        print("已滑动到最顶部，退出")
                                        break
                                # 先左边识别区服 271,188,500,663
                                res, x, y = for_ms_row(self.row, [[271, 188, 500, 663, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                if res:
                                    print(f"找到区服: {区服}")
                                    移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                    ress = wait_for_ms(self.row, [MS.点击登录])
                                    if ress:
                                        print("找到登录")
                                        return True, x, y
                                    else:
                                        break
                                else:
                                    # 再右边识别区服 577,189,755,646
                                    res, x, y = for_ms_row(self.row,
                                                           [[577, 189, 755, 646, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                    if res:
                                        print(f"找到区服: {区服}")
                                        移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                        ress = wait_for_ms(self.row, [MS.点击登录])
                                        if ress:
                                            print("找到登录")
                                            return True, x, y
                                        else:
                                            break
                                    else:
                                        for i in range(10):
                                            检查画面是否变化_前置截图(267, 581, 413, 653)
                                            滑动屏幕(574,555,574,197, 1)  # 从下往上滑动
                                            time.sleep(1)
                                            if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                                # 画面未变化 → 已滑到底 → 停止
                                                print("已滑动到最顶部，退出")
                                                break

                                            # 先左边识别区服 271,188,500,663
                                            res, x, y = for_ms_row(self.row,
                                                                   [[271, 188, 500, 663, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                            if res:
                                                print(f"找到区服: {区服}")
                                                移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                                ress = wait_for_ms(self.row, [MS.点击登录])
                                                if ress:
                                                    print("找到登录")
                                                    return True, x, y
                                                else:
                                                    break
                                            else:
                                                # 再右边识别区服 577,189,755,646
                                                res, x, y = for_ms_row(self.row,
                                                                       [[577, 189, 755, 646, f"区服\\{区服}.bmp", "", 0.7,
                                                                         5]])
                                                if res:
                                                    print(f"找到区服: {区服}")
                                                    移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                                    ress = wait_for_ms(self.row, [MS.点击登录])
                                                    if ress:
                                                        print("找到登录")
                                                        return True, x, y
                                                    else:
                                                        break
                                        time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.七区1])
                            if res:
                                print("找到时空区")
                                移动点击(x, y, 1)
                            continue
                        # 时空服
                        if 区服 == "2026":
                            res, x, y = for_ms_row(self.row, [MS.时空区])
                            if res:
                                移动点击(x+5, y+5)
                                time.sleep(1)
                                print("找到时空区")
                                # 重置到最顶层
                                for i in range(10):
                                    检查画面是否变化_前置截图(267, 581, 413, 653)
                                    滑动屏幕(574, 197, 574, 555, 1)  # 从下往上滑动
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                        # 画面未变化 → 已滑到底 → 停止
                                        print("已滑动到最顶部，退出")
                                        break
                                # 先左边识别区服 271,188,500,663
                                res, x, y = for_ms_row(self.row, [[271, 188, 500, 663, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                if res:
                                    print(f"找到区服: {区服}")
                                    移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                    ress = wait_for_ms(self.row, [MS.点击登录])
                                    if ress:
                                        print("找到登录")
                                        return True, x, y
                                    else:
                                        break
                                else:
                                    # 再右边识别区服 577,189,755,646
                                    res, x, y = for_ms_row(self.row,
                                                           [[577, 189, 755, 646, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                    if res:
                                        print(f"找到区服: {区服}")
                                        移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                        ress = wait_for_ms(self.row, [MS.点击登录])
                                        if ress:
                                            print("找到登录")
                                            return True, x, y
                                        else:
                                            break
                                    else:
                                        print("未找到匹配的区服,继续滑动查找")
                                        检查画面是否变化_前置截图(267, 581, 413, 653)
                                        滑动屏幕(574,555,574,197,  1)  # 从下往上滑动
                                        if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                            # 画面未变化 → 已滑到底 → 停止
                                            print("已滑动到最顶部，退出")
                                            break
                                            # 先左边识别区服 271,188,500,663
                                            res, x, y = for_ms_row(self.row,
                                                                   [[271, 188, 500, 663, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                            if res:
                                                print(f"找到区服: {区服}")
                                                移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                                ress = wait_for_ms(self.row, [MS.点击登录])
                                                if ress:
                                                    print("找到登录")
                                                    return True, x, y
                                                else:
                                                    break
                                            else:
                                                # 再右边识别区服 577,189,755,646
                                                res, x, y = for_ms_row(self.row,
                                                                       [[577, 189, 755, 646, f"区服\\{区服}.bmp", "", 0.7,
                                                                         5]])
                                                if res:
                                                    print(f"找到区服: {区服}")
                                                    移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                                    ress = wait_for_ms(self.row, [MS.点击登录])
                                                    if ress:
                                                        print("找到登录")
                                                        return True, x, y
                                                    else:
                                                        break
                                        time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.时空区1])
                            if res:
                                print("找到时空区")
                                移动点击(x, y, 1)
                            continue

                        else:
                            res, x, y = for_ms_row(self.row, [MS.时空区])
                            if res:
                                移动点击(x + 5, y + 5)
                                time.sleep(1)
                                print("找到时空区")
                                # 重置到最顶层
                                for i in range(10):
                                    检查画面是否变化_前置截图(267, 581, 413, 653)
                                    滑动屏幕(574, 197, 574, 555, 1)  # 从下往上滑动
                                    time.sleep(1)
                                    if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                        # 画面未变化 → 已滑到底 → 停止
                                        print("已滑动到最顶部，退出")
                                        break
                                # 先左边识别区服 271,188,500,663
                                res, x, y = for_ms_row(self.row, [[271, 188, 500, 663, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                if res:
                                    print(f"找到区服: {区服}")
                                    移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                    ress = wait_for_ms(self.row, [MS.点击登录])
                                    if ress:
                                        print("找到登录")
                                        return True, x, y
                                    else:
                                        break
                                else:
                                    # 再右边识别区服 577,189,755,646
                                    res, x, y = for_ms_row(self.row,
                                                           [[577, 189, 755, 646, f"区服\\{区服}.bmp", "", 0.7, 5]])
                                    if res:
                                        print(f"找到区服: {区服}")
                                        移动点击(x, y, 时间间隔=0.5, pixel_verify=False)
                                        ress = wait_for_ms(self.row, [MS.点击登录])
                                        if ress:
                                            print("找到登录")
                                            return True, x, y
                                        else:
                                            break
                                    else:
                                        print("未找到匹配的区服,继续滑动查找")
                                        检查画面是否变化_前置截图(267, 581, 413, 653)
                                        滑动屏幕(573, 606, 573, 343, 1)  # 从下往上滑动
                                        if not 检查画面是否变化_验证截图(267, 581, 413, 653):
                                            # 画面未变化 → 已滑到底 → 停止
                                            print("已滑动到最底部，退出")
                                            break
                                        time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.时空区1])
                            if res:
                                print("找到时空区")
                                移动点击(x, y, 1)
                return False, 0, 0

            def 选择角色(区服,角色, xx, yy):
                # 🔧 关键修复：检测是否为崩溃/断线后的重新登录
                crash_recovery = False
                try:
                    cfg = gl_info.配置.get("进度配置", {})
                    if self.名称 in cfg:
                        blob = migrate_progress_raw(cfg[self.名称])
                        crash_recovery = blob.get("crash_recovery", False)
                except Exception as e:
                    print(f"⚠️ 检查 crash_recovery 状态异常: {e}")
                
                if crash_recovery:
                    print(f"\n{'='*60}")
                    print(f"🔧 [崩溃恢复模式] 检测到意外退出后重新登录")
                    print(f"   原角色位置: {角色}")
                    print(f"   强制重置为: 1")
                    print(f"   （其他账号信息、区服保持不变）")
                    print(f"{'='*60}\n")
                    角色 = 1  # 强制重置为角色 1
                    show_log(self.row, f"[崩溃恢复] 角色位置已强制重置为 1")
                
                show_log(self.row, f"开始选择角色{角色}")
                while True:
                    res, x, y = for_ms_row(self.row, [MS.重连失败])
                    if res:
                        print("点击重连失败")
                        移动点击(x + 140, y + 75)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.登录游戏1, MS.登录游戏])
                        if ress:
                            print("点击登录游戏")
                            移动点击(463, 510)
                        time.sleep(1)
                    # 新区 多线服
                    if 区服 == "2026":
                        if 角色 == 1:
                            res, x, y = for_ms_row(self.row,[MS.一线, MS.一线1])
                            print("选择角色:")
                            if res:
                                time.sleep(0.5)
                                移动点击(x + 5, y + 5)
                                time.sleep(2)
                                移动点击(370, y + 85)
                                time.sleep(1)
                                return True

                        if 角色 == 2:
                            res, x, y = for_ms_row(self.row,[MS.二线, MS.二线1])
                            if res:
                                移动点击(x + 5, y + 5)
                                time.sleep(2)
                                移动点击(370, y + 85)
                                time.sleep(1)
                                return True
                        if 角色 == 3:
                            res, x, y = for_ms_row(self.row,[MS.三线, MS.三线1])
                            if res:
                                移动点击(x + 5, y + 5)
                                time.sleep(2)
                                移动点击(370, y + 85)
                                time.sleep(1)
                                return True

                    else:
                        print(f"开始选择角色: 角色={角色},xx={xx}, yy={yy}")
                        
                        # 定义角色坐标映射
                        角色坐标 = {
                            1: (370, yy + 80),
                            2: (600, yy + 80),
                            3: (780, yy + 80),
                            4: (370, yy + 210),
                            5: (600, yy + 210),
                            6: (780, yy + 210)
                        }
                        
                        if 角色 not in 角色坐标:
                            print(f"⚠️ 无效的角色编号: {角色}")
                            return False
                        
                        click_x, click_y = 角色坐标[角色]
                        
                        # 先截图作为基准
                        检查画面是否变化_前置截图(366, 187, 560, 257)
                        
                        # 最多尝试5次点击
                        for attempt in range(5):
                            移动点击(click_x, click_y)
                            time.sleep(1.5)  # 等待界面响应
                            
                            # 验证画面是否变化
                            if 检查画面是否变化_验证截图(366, 187, 560, 257):
                                # 画面有变化 → 点击生效 → 成功
                                print(f"✅ 角色{角色}选择成功（第{attempt + 1}次点击）")
                                return True
                            else:
                                # 画面未变化 → 点击未生效 → 继续尝试
                                print(f"⚠️ 角色{角色}点击未生效，第{attempt + 1}次重试...")
                        
                        # 5次都失败
                        print(f"❌ 角色{角色}选择失败，点击5次均无响应")
                        return False

            def 摆摊():
                show_log(self.row, "开始摆摊")
                start_time = time.time()
                while True:
                    # 如果时间超过五分钟，则退出
                    if time.time() - start_time > 300:
                        print("时间超过五分钟，退出")
                        return False
                    print("开始摆摊")
                    res, x, y = for_ms_row(self.row, [MS.摆摊页面, MS.商会界面, MS.商城界面])
                    if res:
                        if res != 1:
                            移动点击(893, 328)
                            time.sleep(1)
                        print("找到摆摊")
                        res, x, y = for_ms_row(self.row, [MS.交易记录, MS.其他玩家正在出售])
                        if res:
                            print("找到交易记录,窗口正确")
                            # 这里开始卖东西啦
                            start_time1 = time.time()
                            while True:
                                print('开始卖东西')
                                # 这里确定要卖什么东西
                                res, x, y = for_ms_row(self.row, [MS.其他玩家正在出售])
                                if res:
                                    print("找到其他玩家正在出售")
                                    其他玩家价格 = 0
                                    临时价格 = 0
                                    当前价格 = 0
                                    坐标 =0,0
                                    精确度 = 0
                                    重试次数 = 0
                                    最大重试次数 = 10  # 防止死循环
                                    while 重试次数 < 最大重试次数:
                                        重试次数 += 1
                                        print(f"对比价格 (第{重试次数}次尝试)")
                                        
                                        # 区域识别价格 - 正确处理OCR返回值
                                        ocr_result_其他 = self.dx.Ocr.Ocr(240, 249, 421, 285)
                                        if not ocr_result_其他 or len(ocr_result_其他) == 0:
                                            print("⚠️ 其他玩家价格识别失败，等待后重试")
                                            time.sleep(1)
                                            continue
                                        
                                        # 提取第一个识别结果的文本
                                        其他玩家价格文本 = ocr_result_其他[0][0]  # (text, position, confidence)
                                        
                                        # 验证是否为数字
                                        try:
                                            # 🔧 处理千分位逗号：'1,000' -> '1000'
                                            其他玩家价格文本_clean = 其他玩家价格文本.replace(',', '').replace('，', '')
                                            其他玩家价格 = int(其他玩家价格文本_clean)
                                        except (ValueError, TypeError):
                                            print(f"⚠️ 其他玩家价格非数字格式: '{其他玩家价格文本}'，等待后重试")
                                            time.sleep(1)
                                            continue
                                        
                                        # 如果当前价格小于100就再后面加个0
                                        if 其他玩家价格 < 100:
                                            其他玩家价格 = 其他玩家价格 * 10
                                        
                                        # 识别当前价格
                                        ocr_result_当前 = self.dx.Ocr.Ocr(631, 456, 736, 491)
                                        if not ocr_result_当前 or len(ocr_result_当前) == 0:
                                            print("⚠️ 当前价格识别失败，等待后重试")
                                            time.sleep(1)
                                            continue
                                        
                                        当前价格文本 = ocr_result_当前[0][0]

                                        try:
                                            # 🔧 处理千分位逗号：'1,000' -> '1000'
                                            当前价格文本_clean = 当前价格文本.replace(',', '').replace('，', '')
                                            当前价格 = int(当前价格文本_clean)
                                        except (ValueError, TypeError):
                                            print(f"⚠️ 当前价格非数字格式: '{当前价格文本}'，等待后重试")
                                            time.sleep(1)
                                            continue
                                        
                                        # 价格比较逻辑
                                        if 其他玩家价格 > 当前价格:
                                            print(f"价格低于其他玩家 (其他:{其他玩家价格}, 当前:{当前价格})")
                                            移动点击(762, 472)
                                            time.sleep(1)
                                            
                                            # 识别调整后的临时价格
                                            ocr_result_临时 = self.dx.Ocr.Ocr(630, 462, 734, 485)
                                            if ocr_result_临时 and len(ocr_result_临时) > 0:
                                                try:
                                                    临时价格 = int(ocr_result_临时[0][0])
                                                    if 临时价格 >= 其他玩家价格:
                                                        res, x, y = for_ms_row(self.row, [MS.本服上架, MS.上架, MS.重新上架])
                                                        if res:
                                                            print("找到本服上架")
                                                            移动点击(x + 10, y + 10)
                                                            time.sleep(1)
                                                            res, x, y = for_ms_row(self.row, [MS.摊位紧缺])
                                                            if res:
                                                                print("摊位紧缺")
                                                                return True
                                                            break  # 成功后退出循环
                                                except (ValueError, TypeError) as e:
                                                    print(f"⚠️ 临时价格识别异常: {e}")

                                                if 临时价格 < 其他玩家价格:
                                                    print(f"价格高于其他玩家 (临时:{临时价格}, 其他:{其他玩家价格})")
                                                    移动点击(569, 465)
                                                    time.sleep(1)

                                                    ocr_result_临时 = self.dx.Ocr.Ocr(630, 462, 734, 485)
                                                    if ocr_result_临时 and len(ocr_result_临时) > 0:
                                                        try:
                                                            临时价格 = int(ocr_result_临时[0][0])
                                                            if 临时价格 <= 其他玩家价格:
                                                                res, x, y = for_ms_row(self.row, [MS.本服上架, MS.上架, MS.重新上架])
                                                                if res:
                                                                    print("找到本服上架")
                                                                    移动点击(x + 10, y + 10)
                                                                    time.sleep(1)
                                                                    res, x, y = for_ms_row(self.row, [MS.摊位紧缺])
                                                                    if res:
                                                                        print("摊位紧缺")
                                                                        return True
                                                                    break  # 成功后退出循环
                                                        except (ValueError, TypeError) as e:
                                                            print(f"⚠️ 临时价格识别异常: {e}")
                                        
                                        elif 其他玩家价格 == 当前价格:
                                            print(f"价格等于其他玩家 ({当前价格})")
                                            res, x, y = for_ms_row(self.row, [MS.本服上架, MS.上架, MS.重新上架])
                                            if res:
                                                print("找到本服上架")
                                                移动点击(x + 10, y + 10)
                                                time.sleep(1)
                                                res,x,y = for_ms_row(self.row, [MS.摊位紧缺])
                                                if res:
                                                    print("摊位紧缺")
                                                    return True
                                                break  # 成功后退出循环
                                        
                                        # 每次循环后短暂等待
                                        time.sleep(0.5)
                                    
                                    # 检查是否达到最大重试次数
                                    if 重试次数 >= 最大重试次数:
                                        print(f"⚠️ 价格对比超过最大重试次数({最大重试次数})，跳过此步骤")

                                res, x, y = for_ms_row(self.row, [MS.七天内不在提醒])
                                if res:
                                    移动点击(x - 26, y + 12)
                                    time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.摆摊确定])
                                if res:
                                    print("找到摆摊确定")
                                    移动点击(x + 10, y + 10)
                                    time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.本服上架, MS.上架, MS.重新上架])
                                if res:
                                    print("找到本服上架")
                                    移动点击(x + 10, y + 10)
                                    time.sleep(1)
                                    res, x, y = for_ms_row(self.row, [MS.摊位紧缺])
                                    if res:
                                        print("摊位紧缺")
                                        return True
                                    break  # 成功后退出循环
                                res, x, y = for_ms_row(self.row, [MS.已过期])
                                if res:
                                    移动点击(x+30, y+30)
                                    time.sleep(1)
                                res, x, y = for_ms_row(self.row, [MS.摊位满了])
                                if res:
                                    print("摊位满了")
                                    return True
                                res, x, y = for_ms_row(self.row, [MS.九转还魂丹,MS.五龙丹,MS.金香玉,MS.法宝碎片, MS.五十级装备, MS.六十级装备, MS.钨金])
                                if res:
                                    移动点击(x, y)
                                    time.sleep(1)
                                    continue
                                # 时间如果过了3分钟，就结束
                                if time.time() - start_time1 > 180:
                                    print("时间已过3分钟，结束")
                                    return True
                                # 异常判断 完成退出
                                res, x, y = for_ms_row(self.row, [MS.摆摊关闭, MS.摆摊关闭1])
                                if not res:
                                    print("没有找到摆摊关闭")
                                    time.sleep(1)
                                    return True
                                time.sleep(2)

                        else:
                            移动点击(323, 165)
                            time.sleep(1)
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 'a')
                            time.sleep(1)
                        else:
                            if 关闭窗口():
                                pass
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)
                        continue
                    time.sleep(1)
            def 帮派任务():
                show_log(self.row, "开始帮派任务")
                start_time = time.time()
                last_progress_log = start_time  # 🔧 新增：记录上次进度日志时间
                while True:
                    # 🔧 新增：每5分钟打印一次进度日志
                    current_time = time.time()
                    if current_time - last_progress_log > 300:  # 5分钟
                        elapsed = int(current_time - start_time)
                        print(f"⏱️ [帮派] 已运行 {elapsed//60}分{elapsed%60}秒")
                        show_log(self.row, f"⏱️ 帮派任务运行中: {elapsed//60}分{elapsed%60}秒", 表格_状态)
                        last_progress_log = current_time
                    
                    res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                    if res:
                        print("仙玉不足")
                        移动点击(653, 180, pixel_verify=False)
                        time.sleep(0.5)
                        return True
                    res, x, y = for_ms_row(self.row, [MS.批量申请])
                    if res:
                        print("找到批量申请")
                        移动点击(x + 10, y + 10)
                        time.sleep(1)
                        ress = wait_for_ms(self.row, [MS.发送申请])
                        if ress:
                            print("找到发送申请")
                            移动点击(474,442)
                            time.sleep(1)
                            return True
                    # 超时30分钟
                    res, x, y = for_ms_row(self.row, [MS.自动完成帮派任务])
                    if res:
                        print("找到自动完成帮派任务")
                        移动点击(x + 10, y + 10)
                        time.sleep(1)
                    
                    # 🔧 新增：检查超时并记录详细日志
                    if time.time() - start_time > 1800:
                        elapsed = int(time.time() - start_time)
                        print(f"❌ 帮派任务超时（{elapsed//60}分{elapsed%60}秒）")
                        show_log(self.row, f"❌ 帮派任务超时: {elapsed//60}分{elapsed%60}秒", 表格_状态)
                        return False
                    res, x, y = for_ms_row(self.row, [MS.背包空间不足])
                    if res:
                        print("背包空间不足")
                        移动点击(x - 50, y + 25)
                        time.sleep(1)
                        清理背包()
                    if not 自动战斗():
                        if not 人物是否移动中():
                            time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.自动购买确定])
                            if res:
                                移动点击(x + 10, y + 10)
                                time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.再来一轮])
                            if res:
                                移动点击(x + 10, y + 10)
                                time.sleep(1)
                            if 请选择():
                                continue
                            if 购买():
                                res, x, y = for_ms_row(self.row, [MS.充值仙玉])
                                if res:
                                    print("仙玉不足")
                                    移动点击(653, 180, pixel_verify=False)
                                    time.sleep(0.5)
                                    return True
                                continue
                            if 上交():
                                continue
                            if 使用():
                                continue
                            if 去完成():
                                continue
                            if 滑屏查任务("帮派"):
                                time.sleep(0.5)
                                continue
                            if 师门任务完成():
                                print(f"师门任务完成，用时{int((time.time() - start_time) / 60)}分钟")
                                return True
                            else:
                                ress, x, y = for_ms_row(self.row, [MS.活动界面, MS.活动面板关闭])
                                if 识别角色等级() != -1 or ress != 0:
                                    if 查任务是否完成('帮派任务'):
                                        # 师门任务完成，用时多少时间
                                        print(f"师门任务完成，用时{int((time.time() - start_time) / 60)}分钟")
                                        return True
                                    time.sleep(1)
                                else:
                                    res, x, y = for_ms_row(self.row,
                                                           [MS.确定, MS.确定1, MS.确定2, MS.确定3, MS.剧情确定, MS.摆摊确定, MS.自动购买确定,
                                                            MS.师门任务完成确定])
                                    if res:
                                        移动点击(x + 10, y + 10)
                                        time.sleep(1)
                                    else:
                                        if 关闭窗口():
                                            continue
                                        else:
                                            print("环境异常,按键(ESC)退出")
                                            self.dx.KM.PressKey('esc')  # ESC
                                            time.sleep(1)
                                            if 关闭窗口():
                                                continue
                                            else:
                                                # 打开活动界面
                                                组合按键('alt', 'c')
                                                time.sleep(1)
            def 捉鬼挂机():
                show_log(self.row, "开始捉鬼挂机")
                start_time = time.time()
                while True:
                    # 如果时间超过3分钟，则退出
                    if time.time() - start_time > 180:
                        print("时间超过15分钟，退出")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.取消])
                    if res:
                        print("找到取消")
                        移动点击(x + 10, y + 10)
                        time.sleep(1)
                        continue
                    res, x, y = for_ms_row(self.row, [MS.队伍界面,MS.队伍界面1, MS.便捷组队])
                    if res:
                        time.sleep(1)
                        print("找到队伍界面")
                        res, x, y = for_ms_row(self.row, [MS.退出队伍])
                        if res:
                            print("退出队伍")
                            移动点击(x + 10, y + 5, pixel_verify=False)
                            time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.暂时离队])
                        if res:
                            print("队伍中...")
                            print("继续检查是否是捉鬼任务")
                            time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.组队页面打开捉鬼页面])
                            if res:
                                print("找到捉鬼任务页面")
                                return  True
                            else:
                                res, x, y = for_ms_row(self.row, [MS.退出队伍])
                                if res:
                                    print("退出队伍")
                                    移动点击(x+10, y+5,pixel_verify=False)
                                    time.sleep(1)
                        res, x, y = for_ms_row(self.row, [MS.便捷组队])
                        if res:
                            移动点击(x, y,pixel_verify=False)
                            time.sleep(1)
                        continue
                    res, x, y = for_ms_row(self.row, [MS.便捷组队页面])
                    if res:
                        res, x, y = for_ms_row(self.row, [MS.捉鬼任务, MS.捉鬼任务1])
                        if res:
                            移动点击(x, y,pixel_verify=False)
                            time.sleep(1)
                            res, x, y = for_ms_row(self.row, [MS.自动匹配])
                            if res:
                                移动点击(x, y,pixel_verify=False)
                                time.sleep(1)
                                # 等待匹配
                                res = wait_for_ms(self.row, [MS.取消匹配],for_num=6,delay=0.5)
                                if not res:
                                    continue
                                start_time1 = time.time()
                                while True:
                                    if  time.time() - start_time1 > 180:
                                        print("时间超过3分钟，退出")
                                        return True
                                    print("开始捉鬼,匹配中")
                                    res, x, y = for_ms_row(self.row, [MS.左三角1, MS.左三角2])
                                    if res:
                                        print("进入战斗场景...")
                                        return True
                                    if 关闭窗口():
                                        pass
                                    if 识别角色等级() != -1 or 识别宠物等级() != -1:
                                        print('环境正确')
                                    else:
                                        self.dx.KM.PressKey('esc')
                                    time.sleep(2)

                        else:
                            res, x, y = for_ms_row(self.row, [MS.日常任务])
                            if res:
                                移动点击(x, y,pixel_verify=False)
                                time.sleep(1)
                                # 等待匹配
                                res = wait_for_ms(self.row, [MS.捉鬼任务], for_num=6, delay=0.5)
                                if res:
                                    print("找到捉鬼任务")
                                    移动点击(x, y)
                                    time.sleep(1)
                                    res, x, y = for_ms_row(self.row, [MS.自动匹配])
                                    if res:
                                        移动点击(x, y,pixel_verify=False)
                                        time.sleep(1)
                                        # 等待匹配
                                        res = wait_for_ms(self.row, [MS.取消匹配], for_num=6, delay=0.5)
                        continue
                    else:

                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 't')
                            time.sleep(1)
                        else:
                            if 关闭窗口():
                                pass
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)
            def 退出队伍():
                show_log(self.row, "检测是否组队中")
                start_time = time.time()
                while True:
                    res, x, y = for_ms_row(self.row, [MS.退出队伍])
                    if res:
                        print("退出队伍")
                        移动点击(x + 10, y + 5, pixel_verify=False)
                        show_log(self.row, "退出队伍成功")
                        ress = wait_for_ms(self.row, [MS.退出队伍], for_num=6, delay=0.5)
                        if not ress:
                            return True
                    # 如果时间超过3分钟，则退出
                    if time.time() - start_time > 180:
                        print("时间超过3分钟，退出")
                        show_log(self.row, "时间超过3分钟，退出")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.队伍界面, MS.队伍界面1, MS.便捷组队])
                    if res:
                        time.sleep(1)
                        print("找到队伍界面")
                        res, x, y = for_ms_row(self.row, [MS.退出队伍])
                        if res:
                            print("退出队伍")
                            移动点击(x + 10, y + 5, pixel_verify=False)
                            show_log(self.row, "退出队伍成功")
                            ress = wait_for_ms(self.row, [MS.退出队伍], for_num=6, delay=0.5)
                            if not ress:
                                return True
                        res, x, y = for_ms_row(self.row, [MS.暂时离队])
                        if res:
                            print("队伍中...")
                            res, x, y = for_ms_row(self.row, [MS.退出队伍])
                            if res:
                                print("退出队伍")
                                移动点击(x + 10, y + 5, pixel_verify=False)
                                ress = wait_for_ms(self.row, [MS.退出队伍], for_num=6, delay=0.5)
                                if not ress:
                                    show_log(self.row, "退出队伍成功")
                                    return True
                        res, x, y = for_ms_row(self.row, [MS.便捷组队])
                        if res:
                            print("没有队伍中")
                            移动点击(x + 10, y + 5, pixel_verify=False)
                            ress = wait_for_ms(self.row, [MS.退出队伍], for_num=6, delay=0.5)
                            if not ress:
                                show_log(self.row, "退出队伍成功")
                                return True
                    else:

                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 't')
                            time.sleep(1)
                        else:
                            if 关闭窗口():
                                pass
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)
            
            def 领取活跃奖励():
                """
                根据当前活跃值自动领取对应的活跃奖励
                
                活跃值档位：
                - 100 活跃：领取 5 个奖励
                - 80 活跃：领取 4 个奖励
                - 60 活跃：领取 3 个奖励
                - 40 活跃：领取 2 个奖励
                - < 40 活跃：领取 1 个奖励
                """
                try:
                    res = 识别活跃值()
                    print(f"[Row:{self.row}] 📊 当前活跃值: {res}")
                    
                    # 🔧 定义活跃奖励坐标（从右到左）
                    活跃奖励坐标 = [
                        (819,543),  # 100 活跃
                        (699,545),  # 80 活跃
                        (573,542),  # 60 活跃
                        (449,543),  # 40 活跃
                        (323,542),  # 20 活跃
                    ]
                    
                    # 🔧 根据活跃值确定需要领取的奖励数量
                    if res >= 100:
                        领取数量 = 5
                    elif res >= 80:
                        领取数量 = 4
                    elif res >= 60:
                        领取数量 = 3
                    elif res >= 40:
                        领取数量 = 2
                    else:
                        领取数量 = 1
                    
                    print(f"[Row:{self.row}] 🎁 开始领取活跃奖励，共 {领取数量} 个")
                    
                    # 🔧 循环点击对应的奖励按钮
                    for i in range(领取数量):
                        x, y = 活跃奖励坐标[i]
                        移动点击(x, y)
                        time.sleep(1)  # 等待动画效果
                    
                    print(f"[Row:{self.row}] ✅ 活跃奖励领取完成")
                    return True
                except Exception as e:
                    print(f"[Row:{self.row}] ⚠️ 活跃奖励领取失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            def 商会清理 ():
                show_log(self.row, "开始清理商会")
                start_time = time.time()
                while True:
                    if time.time() - start_time > 180:
                        print("时间超过3分钟，退出")
                        show_log(self.row, "清理商会失败，时间超过3分钟，退出")
                        return False
                    res, x, y = for_ms_row(self.row, [MS.商会界面, MS.摆摊页面, MS.商城界面])
                    if res:
                        if res != 1:
                            移动点击(891,239, pixel_verify=False)
                            time.sleep(1)
                        res, x, y = for_ms_row(self.row,
                                               [MS.药店购买, MS.兵器购买, MS.摆摊购买, MS.召唤灵购买, MS.购买1, MS.购买2, MS.购买3, MS.购买4])
                        if res:
                            移动点击(316,164)
                            time.sleep(1)
                        res,x, y = for_ms_row(self.row, [MS.出售, MS.出售1,MS.商会出售,MS.商会出售1])
                        if res:
                            移动点击(117,277, pixel_verify=False)
                            time.sleep(1)
                            start_time1 = time.time()
                            while True:
                                res, x, y = for_ms_row(self.row, [MS.没有可以出售的商品])
                                if res:
                                    print("没有商品出售了")
                                    show_log(self.row, "清理商会完成")
                                    return True
                                移动点击(782,617, pixel_verify=False)
                                time.sleep(0.5)
                                res, x, y = for_ms_row(self.row, [MS.出售, MS.出售1, MS.商会出售, MS.商会出售1])
                                if not res:
                                    print("没有商品出售了")
                                    show_log(self.row, "清理商会完成")
                                    return True
                                if time.time() - start_time1 > 180:
                                    print("时间超过3分钟，退出")
                        continue
                    else:
                        ress, x, y = for_ms_row(self.row, [MS.右侧任务栏标记])
                        if 识别角色等级() != -1 or 识别宠物等级() != -1 or ress:
                            组合按键('alt', 'a')
                            time.sleep(1)
                        else:
                            if 关闭窗口():
                                pass
                            else:
                                self.dx.KM.PressKey('esc')
                                time.sleep(1)

            # 初始时间，用来后面统计时间
            start_time总 = time.time()
            # 开始执行具体任务
            print("开始执行任务")
            while True:
                if 游戏窗口位置检查():

                    所有账号信息列表 = self.获取所有账号信息()
                    if not 所有账号信息列表:
                        print("未找到任何账号信息")
                        return

                    saved_account_index = int(self._read_progress_blob()["daily"].get("account_index", 0))
                    calendar_date = self._read_progress_blob()["daily"].get("calendar_date", "")
                    completed_steps = self._read_progress_blob()["daily"].get("completed_steps", [])
                    print(f"\n{'='*60}")
                    print(f"[Row:{self.row}] 📅 当前任务日: {calendar_date}")
                    print(f"[Row:{self.row}] 🔢 已完成的账号索引: {saved_account_index}")
                    print(f"[Row:{self.row}] ✅ 已完成的任务步骤: {completed_steps}")
                    print(f"{'='*60}\n")

                    for 账号信息 in 所有账号信息列表:
                        编号 = 账号信息['编号']
                        账号 = 账号信息['账号']
                        密码 = 账号信息['密码']
                        区服 = 账号信息['区服']
                        角色 = 账号信息['角色']
                        索引 = 账号信息['索引']
                        if 索引 < saved_account_index:
                            print(f"[日常断点] 跳过已完成账号 索引={索引}（断点 account_index={saved_account_index}）")
                            continue

                        # ✅ 关键修复：更新当前账号索引，确保 VNC 连接到正确的窗口
                        self.now_user_id = 索引
                        print(f"[Row:{self.row}] 🔄 切换到账号索引: {索引} (账号: {账号}, 编号: {编号})")

                        # ✅ 重新建立 VNC 连接到正确的窗口
                        print(f"[Row:{self.row}] 📡 重新连接 VNC (127.0.0.1:{编号})...")
                        self._vnc_reconnecting = True
                        self.dx._vnc_reconnecting = True
                        if hasattr(self.dx.screenshot, 'stop'):
                            try:
                                self.dx.screenshot.stop()
                            except:
                                pass
                            time.sleep(1.0)

                        # 🔧 关键修复：重新创建 VNC 后，必须也重新创建 OCR 对象
                        # 因为旧的 OCR 对象还持有已关闭的 VNC 引用
                        self.dx.screenshot = VNC("127.0.0.1", 编号, "", fps=2)  # 🔧 稳定性优化：降低 FPS 至 2，避免长时间运行崩溃，节省资源
                        time.sleep(2.0)  # 等待截图线程启动

                        # 重新初始化键鼠
                        self.dx.KM = VNC_KM("127.0.0.1", 编号, "")
                        md = _env_float("VNC_MOUSE_DELAY", 0.05)
                        kd = _env_float("VNC_KEY_DELAY", 0.01)
                        if md > 0 and kd >= 0:
                            self.dx.KM.set_delay(key_delay=kd, mouse_delay=md)

                        # 🔧 重新创建 OCR 对象，使用新的 VNC 实例
                        print(f"[Row:{self.row}] 🔄 重新初始化 OCR 引擎...")

                        # ⚠️ 关键修复：多开时必须彻底禁用 GPU，避免 CUDA 并发冲突
                        # 1. 设置环境变量（必须在导入 onnx_config 之前）
                        os.environ['ONNX_OCR_SHARED'] = '0'  # 独立模式
                        os.environ['ONNX_USE_GPU'] = '0'     # 强制 CPU 模式

                        # 2. 更新配置类
                        try:
                            from app.onnx_config import ONNXRuntimeConfig
                            ONNXRuntimeConfig.use_cpu()  # 强制切换到 CPU
                            print(f"[Row:{self.row}] ⚙️ 已强制切换到 CPU 模式")
                        except Exception as e:
                            print(f"[Row:{self.row}] ⚠️ 无法切换 CPU 模式: {e}")

                        # 3. 创建 OCR 实例
                        print(f"[Row:{self.row}] ⚙️ 使用 CPU 模式初始化 OCR（多开更稳定）...")
                        self.dx.Ocr = ONNX_OCR(vnc_instance=self.dx.screenshot, use_gpu=False, drop_score=0.5)
                        print(f"[Row:{self.row}] ✅ OCR 引擎已重新初始化")

                        # 预热模型
                        try:
                            import numpy as np
                            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                            _ = self.dx.Ocr._ocr_infer(test_img)
                            print(f"[Row:{self.row}] ✓ OCR 模型预热完成")
                        except Exception as e:
                            print(f"[Row:{self.row}] ❌ OCR 模型预热失败：{e}")
                            import traceback
                            traceback.print_exc()
                            raise  # 抛出异常，阻止继续执行

                        print(f"[Row:{self.row}] ✅ VNC 和键鼠已重新连接到窗口 {编号}")
                        self._vnc_reconnecting = False
                        self.dx._vnc_reconnecting = False

                        #显示当前登录的账号信息
                        show_log(self.row, f"正在登录账号编号：{编号}，账号：{账号}，密码：{密码}，区服：{区服}，角色：{角色}，索引：{索引}")
                        time.sleep(1)
                        if 账号登录(账号):
                            print("账号登录成功")
                            time.sleep(2)
                            res, x, y = 选择区服(区服)
                            if res == True:
                                print("选择区服成功")
                                xx = x
                                yy = y
                                角色 = int(角色)
                                if 选择角色(区服,角色, xx, yy):
                                    self.等待排队结束()
                                    print(f"选择角色成功，位置{角色}，等待10S")
                                    # 展示当前账号信息
                                    print(f"账号编号：{编号}，账号：{账号}，密码：{密码}，区服：{区服}，角色：{角色}，索引：{索引}")
                                    for i in range(10):
                                        print(f"{i + 1}秒后开始执行任务")
                                        time.sleep(1)
                            #
                                    # 额外检查：确保真的不在排队中
                                    res_check, _, _ = for_ms_row(self.row, [MS.退出排队])
                                    if res_check:
                                        print("⚠️ 警告：检测到仍在排队中，重新等待...")
                                        self.等待排队结束()

                                    # 初始时间，用来后面统计时间
                                    start_time总 = time.time()
                                    # 开始执行具体任务
                                    print("开始执行任务")
                                    # 排队结束后：确认窗口在预期区域，按统一任务链基于进度续跑
                                    if 游戏窗口位置检查():
                                        # 🔧 新增：获取金币截图并显示（在进入主界面后立即执行）
                                        try:
                                            print("\n💰 [金币] 开始获取金币截图...")
                                            show_log(self.row, "💰 正在获取金币信息...", 表格_状态)
                                            
                                            # 调用识别金币函数（会自动截图并更新UI）
                                            识别金币()
                                            
                                            print("💰 [金币] 金币截图获取完成")
                                        except Exception as e:
                                            print(f"⚠️ [金币] 获取金币截图失败: {e}")
                                            import traceback
                                            traceback.print_exc()
                                        
                                        # 执行优先任务
                                        退出队伍 ()
                                        商会清理 ()
                                        日常_打工()
                                        # 优先执行的任务
                                        self._daily_run_step(DAILY_STEP_PRAYER, 日常_祈福)
                                        time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_SCRATCH_CARD, 日常_刮刮乐)
                                        time.sleep(2)

                                        _random_jobs = [
                                            (DAILY_STEP_RANDOM_PREFIX + "shimen", 日常_师门),
                                            (DAILY_STEP_RANDOM_PREFIX + "baotu", 日常_宝图),
                                            (DAILY_STEP_RANDOM_PREFIX + "quwen", 日常_趣闻),
                                            (DAILY_STEP_RANDOM_PREFIX + "mijing", 日常_秘境),
                                        ]
                                        id_to_fn = dict(_random_jobs)
                                        #
                                        # self._daily_run_step(DAILY_STEP_PARTNER, 伙伴助战)
                                        blob = self._read_progress_blob()
                                        order = blob["daily"].get("random_order") or []
                                        expected = [pid for pid, _ in _random_jobs]
                                        if len(order) != len(expected) or set(order) != set(expected):
                                            random.shuffle(expected)
                                            self._daily_set_random_order(expected)
                                            order = expected
                                        for rid in order:
                                            fn = id_to_fn.get(rid)
                                            if fn:
                                                print(f"开始执行任务: {rid}")
                                                self._daily_run_step(rid, fn)
                                                time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_DAILY_SANJIE, 日常_三界)
                                        time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_DAILY_KEJU, 日常_科举)
                                        time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_DIG_TREASURE, 日常_挖宝)
                                        time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_ESCORT, 日常_运镖)
                                        time.sleep(2)
                                        self._daily_run_step(DAILY_STEP_WORK, 日常_打工)
                                        time.sleep(2)
                                        #
                                        self._daily_run_step(DAILY_STEP_CLEAR_BAG_L2, 清理背包)
                                        time.sleep(2)
                                        # self._daily_run_step(DAILY_STEP_STALL_L2, 摆摊)
                                        self._daily_run_step(DAILY_STEP_GUILD_TASK, 帮派任务)
                                        time.sleep(2)
                                        # # 收尾动作不走断点跳过：任务都完成时，重启后会直接摆摊+捉鬼挂机
                                        # 摆摊()
                                        商会清理()
                                        捉鬼挂机()
                                        # # 活跃奖励领取
                                        领取活跃奖励()
                                        self._daily_finish_account()
                                    # 计算总运行时长多少分钟
                                    end_time总 = time.time() - start_time总
                                    print(f"总运行时长：{end_time总 / 60:.2f}分钟")
                                    for i in range(10):
                                         print(f"{i + 1}秒后结束任务")
                                         time.sleep(1)
                    self._daily_reset_for_next_run()
                    show_log(self.row, "任务完成")
        # ---------- 日常任务 状态机：与「初始化任务」里其他顶层方法是并列关系，不要与内部嵌套日常混淆 ----------
        while True:
            try:
                # ✅ 检查是否在游戏更新时段（周三 8:00-9:00）
                if self._检查游戏更新时段():
                    time.sleep(60)  # 等待1分钟后再次检查
                    continue
                
                # 🔧 检查是否需要跨天重置（0:15 后自动重启）
                if self._检查跨天重置():
                    print(f"[Row:{self.row}] 🔄 检测到跨天重置，即将退出当前线程...")
                    # 不执行 break，而是直接抛出异常终止线程
                    # 这样不会执行到 clear_resource，避免清理正在进行的重启逻辑
                    raise SystemExit("跨天重置，线程退出")
                
                # 线程心跳：每30秒打印一次，确认线程还活着
                if not hasattr(self, '_last_heartbeat') or time.time() - self._last_heartbeat > 30:
                    self._last_heartbeat = time.time()
                    print(f"[Row:{self.row}] ❤️ 线程心跳正常 - process={td_info[self.row].process}")
                self._watchdog_tick("main_state_loop", max_loop_seconds=60 * 60, log_interval_seconds=60)

                # 单一出口：主任务循环统一消费 VNC 监控故障并退出/重连
                vnc_fault_reason = self._consume_vnc_fault()
                if vnc_fault_reason:
                    show_log(self.row, f"VNC 监控故障: {vnc_fault_reason}", 表格_状态)
                    if hasattr(self, '_vnc_reconnect_attempts'):
                        self._vnc_reconnect_attempts = 999
                    raise RuntimeError(f"VNC 监控触发退出: {vnc_fault_reason}")
                
                self._周常优先检查并执行()
                process = td_info[self.row].process
                show_log(self.row, f"进度:{process}")
                if process == "任务完成":
                    break
                if process == "任务异常":
                    break
                elif process == inspect.currentframe().f_code.co_name:
                    td_info[self.row].process = "登陆"
                elif process == "登陆":
                    self.login()
                    td_info[self.row].process = "进游戏初始化"
                elif process == "进游戏初始化":
                    self.game_init()
                    td_info[self.row].process = "主界面"
                elif process == "主界面":
                    主界面(self.row)
            except SystemExit as e:
                # 🔧 捕获跨天重置的退出信号
                print(f"[Row:{self.row}] 🔄 捕获到跨天重置信号: {e}")
                
                # 🔧 关键修复：设置 crash_recovery 标记，下次登录时强制角色位置为 1
                try:
                    cfg = gl_info.配置.get("进度配置", {})
                    if self.名称 in cfg:
                        blob = migrate_progress_raw(cfg[self.名称])
                        blob["crash_recovery"] = True  # 标记为崩溃恢复模式
                        cfg[self.名称] = blob
                        gl_info.配置.写入本地配置文件()
                        print(f"[Row:{self.row}] ✅ 已设置 crash_recovery=True")
                except Exception as ex:
                    print(f"[Row:{self.row}] ⚠️ 设置 crash_recovery 失败: {ex}")
                
                td_info[self.row].process = "任务完成"
                break
            except Exception as e:
                # 捕获所有未处理的异常，防止线程静默死亡
                import traceback
                error_msg = f"❌ [Row:{self.row}] 线程异常: {e}\n{traceback.format_exc()}"
                print(error_msg)
                show_log(self.row, f"线程异常: {e}", 表格_状态)
                
                # 🔧 关键修复：异常退出时设置 crash_recovery 标记
                try:
                    cfg = gl_info.配置.get("进度配置", {})
                    if self.名称 in cfg:
                        blob = migrate_progress_raw(cfg[self.名称])
                        blob["crash_recovery"] = True  # 标记为崩溃恢复模式
                        cfg[self.名称] = blob
                        gl_info.配置.写入本地配置文件()
                        print(f"[Row:{self.row}] ✅ [异常退出] 已设置 crash_recovery=True")
                except Exception as ex:
                    print(f"[Row:{self.row}] ⚠️ 设置 crash_recovery 失败: {ex}")
                
                td_info[self.row].process = "任务异常"
                break
            except SystemExit as e:
                # 🔧 捕获跨天重置的退出信号
                print(f"[Row:{self.row}] 🔄 捕获到跨天重置信号: {e}")
                td_info[self.row].process = "任务完成"
                break

    # endregion
    # endregion 任务
    
    # region VNC 监控
    def _start_vnc_monitor(self):
        """启动 VNC 状态监控线程"""
        def monitor_func():
            check_interval = 30  # 每 30 秒检查一次
            
            while self._vnc_monitor_enabled:
                self._watchdog_tick("vnc_monitor_loop", max_loop_seconds=24 * 60 * 60, log_interval_seconds=300)
                time.sleep(check_interval)
                
                try:
                    if hasattr(self.dx, 'screenshot') and self.dx.screenshot is not None:
                        vnc = self.dx.screenshot
                        
                        # 检查关键指标
                        if vnc.consecutive_errors > 5:
                            show_log(self.row, f"⚠️ VNC 连续错误过多：{vnc.consecutive_errors}", 表格_收益)
                        
                        # 🔧 关键修复：检测超过 2 分钟未成功截图，主动触发重连
                        idle_time = time.time() - vnc.last_success_time
                        if idle_time > 120:  # 2分钟
                            self._rate_limited_show_log(
                                "vnc_idle_120",
                                30.0,
                                f"⚠️ VNC 超过 {int(idle_time)} 秒未成功截图，准备由主流程统一重连...",
                                表格_收益,
                            )
                            self._set_vnc_fault(f"VNC {int(idle_time)} 秒未成功截图")
                        elif idle_time > 60:  # 1分钟
                            self._rate_limited_show_log(
                                "vnc_idle_60",
                                30.0,
                                f"⚠️ VNC 超过 {int(idle_time)} 秒未成功截图，准备退出任务以避免崩溃",
                                表格_收益,
                            )
                            self._set_vnc_fault(f"VNC 超过 {int(idle_time)} 秒未响应")
                        
                        if vnc.total_screenshots % 500 == 0 and vnc.total_screenshots > 0:
                            self._rate_limited_show_log(
                                "vnc_total_screenshots",
                                120.0,
                                f"✓ VNC 运行正常，已截图 {vnc.total_screenshots} 次",
                                表格_收益,
                            )
                            
                except Exception as e:
                    # 不再静默吞异常：写共享故障标志，让主任务循环单一出口处理
                    self._set_vnc_fault(f"监控线程异常: {e}")
                    self._rate_limited_show_log(
                        "vnc_monitor_exception",
                        10.0,
                        f"⚠️ VNC 监控异常，已请求主流程退出重连: {e}",
                        表格_状态,
                    )
        
        monitor_thread = threading.Thread(target=monitor_func, daemon=True)
        monitor_thread.start()
    
    # endregion
    
    # region 游戏更新时段检查
    def _检查游戏更新时段(self):
        """
        检查当前是否在游戏更新时段（周三 8:00-9:00）
        
        Returns:
            bool: True=在更新时段，需要暂停; False=不在更新时段，可以正常执行
        """
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=周一, 2=周三, 6=周日
        hour = now.hour
        minute = now.minute
        
        # 检查是否是周三 (weekday == 2)
        if weekday == 2:
            # 检查是否在 8:00-9:00 之间
            if hour == 8 and 0 <= minute < 60:  # 8:00-8:59
                # 首次进入更新时段时打印日志
                if not hasattr(self, '_update_pause_logged') or not self._update_pause_logged:
                    print(f"\n{'='*60}")
                    print(f"[Row:{self.row}] ⏸️ 检测到游戏更新时段（周三 8:00-9:00）")
                    print(f"[Row:{self.row}] ⏸️ 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"[Row:{self.row}] ⏸️ 任务已暂停，等待游戏更新完成...")
                    print(f"[Row:{self.row}] ⏸️ 将在 9:00 后自动恢复任务")
                    print(f"{'='*60}\n")
                    show_log(self.row, f"⏸️ 游戏更新时段，任务暂停", 表格_状态)
                    self._update_pause_logged = True
                return True
            elif hour >= 9:
                # 更新时段已过，重置标记
                if hasattr(self, '_update_pause_logged') and self._update_pause_logged:
                    print(f"\n{'='*60}")
                    print(f"[Row:{self.row}] ▶️ 游戏更新时段已结束")
                    print(f"[Row:{self.row}] ▶️ 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"[Row:{self.row}] ▶️ 任务已恢复，继续执行...")
                    print(f"{'='*60}\n")
                    show_log(self.row, f"▶️ 游戏更新完成，任务恢复", 表格_进度)
                    self._update_pause_logged = False
        else:
            # 非周三，重置标记
            if hasattr(self, '_update_pause_logged'):
                self._update_pause_logged = False
        
        return False
    
    def _检查跨天重置(self):
        """
        检查是否需要跨天重置（每天 0:15-0:20 触发）
        
        机制说明：
        - 仅在 0:15-0:20 这个时间窗口内检查
        - 只有在此时间窗口之前就已经在运行的任务才需要重置
        - 0:15 之后手动启动的任务不遵循重置规则，直接正常运行
        
        Returns:
            bool: True=需要重启; False=不需要重启
        """
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 🔧 关键修复：记录任务启动时间（如果还没有记录）
        if not hasattr(self, '_task_start_time'):
            self._task_start_time = time.time()
        
        # 检查是否在 0:15-0:20 这个时间窗口内（避免重复触发）
        if current_hour == 0 and 15 <= current_minute < 20:
            # 检查是否已经触发过重启（防止同一时间段重复触发）
            if not hasattr(self, '_daily_restart_triggered'):
                self._daily_restart_triggered = set()
            
            today_str = now.date().isoformat()
            
            if today_str not in self._daily_restart_triggered:
                # 🔧 关键判断：只有在 0:15 之前就已经在运行的任务才需要重置
                task_running_seconds = time.time() - self._task_start_time
                task_started_before_reset = task_running_seconds > (15 * 60)  # 任务运行超过15分钟，说明是在0:15之前启动的
                
                if not task_started_before_reset:
                    # 任务是在 0:15 之后启动的，不需要重置
                    print(f"[Row:{self.row}] ℹ️ 任务在跨天时间点后启动，跳过重置")
                    return False
                
                # 记录已触发，避免重复
                self._daily_restart_triggered.add(today_str)
                
                print(f"\n{'='*60}")
                print(f"[Row:{self.row}] 🔄 检测到跨天时间点（0:15-0:20）")
                print(f"[Row:{self.row}] 🔄 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"[Row:{self.row}] 🔄 任务已运行: {int(task_running_seconds // 60)}分钟")
                print(f"[Row:{self.row}] 🔄 正在结束当前任务，准备重启...")
                print(f"[Row:{self.row}] 🔄 系统将自动：")
                print(f"[Row:{self.row}] 🔄   1. 结束当前线程")
                print(f"[Row:{self.row}] 🔄   2. 重置任务状态")
                print(f"[Row:{self.row}] 🔄   3. 重新启动新任务")
                print(f"{'='*60}\n")
                show_log(self.row, f"🔄 跨天重置，准备重启...", 表格_状态)
                
                # 🔧 在退出前重置任务状态
                try:
                    controller = gl_info.controller  # 直接使用全局变量，避免局部 import
                    cfg = gl_info.配置.setdefault("进度配置", {})
                    blob = migrate_progress_raw(cfg.get(self.名称))
                    
                    # 重置日常任务状态
                    if "daily" in blob:
                        daily = blob["daily"]
                        daily["account_index"] = 0
                        daily["branch"] = None
                        daily["completed_steps"] = []
                        daily["random_order"] = []
                    
                    # 重置周常任务状态
                    if "weekly" in blob:
                        weekly = blob["weekly"]
                        weekly["completed_tasks"] = []
                    
                    # 保存更新后的进度
                    cfg[self.名称] = blob
                    _sync_progress_attrs(self, blob)
                    gl_info.配置.写入本地配置文件()
                    
                    print(f"[Row:{self.row}] ✅ 任务状态已重置")
                    show_log(self.row, f"✅ 任务状态已重置", 表格_状态)
                except Exception as e:
                    print(f"[Row:{self.row}] ⚠️ 重置任务状态失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                return True
        elif current_hour >= 1:
            # 过了 1:00 后，重置标记，允许第二天再次触发
            if hasattr(self, '_daily_restart_triggered'):
                self._daily_restart_triggered.clear()
        
        return False
    # endregion

# region 公共方法
# endregion
