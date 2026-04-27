# -*- coding: utf-8 -*-
from dxGame.dx_core import *

class PyThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=True):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._pause_state = False  # 线程暂停状态

    def pause(self):
        """
        Windows SuspendThread 会累加挂起计数；重复 pause 会导致必须多次 Resume 才能真正恢复。
        因此：已在暂停状态时不再叠加 SuspendThread。
        """
        if not self.is_alive():
            self._pause_state = False
            printDebug(f"线程不存在或者已暂停,无需暂停线程{self.ident}")
            return
        if self._pause_state:
            printDebug(f"线程{self.ident}已在暂停状态，跳过重复 SuspendThread")
            return
        thread_handle = self._get_handle()
        kernel32.SuspendThread(thread_handle)
        kernel32.CloseHandle(thread_handle)
        printDebug(f"已暂停线程{self.ident}")
        self._pause_state = True

    def resume(self):
        """
        与 pause 对称：若曾被多次 SuspendThread，需循环 ResumeThread 直到挂起计数归零。
        返回值含义（MSDN）：为恢复前的挂起计数；0 表示线程本未挂起；1 表示刚从挂起恢复；>1 仍被挂起。
        """
        if not self._pause_state:
            printDebug(f"线程不存在或者运行中，无需恢复{self.ident}")
            return
        if not self.is_alive():
            self._pause_state = False
            printDebug(f"线程已结束，仅清理暂停标记{self.ident}")
            return
        thread_handle = self._get_handle()
        try:
            while True:
                prev = kernel32.ResumeThread(thread_handle)
                if prev == 0xFFFFFFFF:
                    printDebug(f"ResumeThread 失败 ident={self.ident}")
                    break
                if prev == 0 or prev == 1:
                    break
        finally:
            kernel32.CloseHandle(thread_handle)
        self._pause_state = False
        printDebug(f"已恢复线程{self.ident}")

    def stop(self):
        if not self.is_alive():
            printDebug(f"线程已停止,无法再次停止{self.ident}")
            return
        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.ident), exc)
        time.sleep(0.01)
        if res == 0:
            raise ValueError("找不到线程ID")
        elif res == 1:
            printDebug(f"停止线程{self.ident}")
            self._is_stopped = True
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, None)
            raise SystemError("线程已停止")
        time.sleep(0.1)

    def TerminateThread(self):
        handle = self._get_handle()
        kernel32.TerminateThread(handle, 0)
        if self.__waitforsingleobject():
            kernel32.CloseHandle(handle)  # 关闭句柄，并不是关闭线程
            self._is_stopped = True
            printDebug(f"已杀死线程:{self.ident}")
        else:
            printDebug(f"杀死线程失败:{self.ident}")

    def _get_handle(self):
        handle = kernel32.OpenThread(ctypes.c_ulong(0x1 | 0x2), ctypes.c_bool(False), ctypes.c_ulong(self.ident))
        return handle

    def __thread_state(self):
        state_id = wintypes.DWORD()
        handle = self._get_handle()
        if ctypes.windll.kernel32.GetExitCodeThread(handle, ctypes.byref(state_id)):
            return state_id.value
        return 0

    def __waitforsingleobject(self):
        self.__WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
        self.__WaitForSingleObject.argtypes = wintypes.HANDLE, wintypes.DWORD
        self.__WaitForSingleObject.restype = wintypes.DWORD
        self.__WaitForSingleObject(self._get_handle(), 1000)  # 等待线程关闭
        if self.__thread_state() == 0:  # 确认退出
            return True


class ConsoleColors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'


def printDebug(_string: str):
    print(ConsoleColors.GREEN + _string + ConsoleColors.RESET)

class ThreadController:
    """
    线程控制器，最好是统一使用同一个实例，当循环滚号时不会出错。
    """
    lock = threading.Lock()

    def __init__(self, thread_max_num, call_func, call_stop_func=None, call_print_func=None, call_all_stop_func=None):
        """
        :param thread_max_num:最大线程数量
        :param call_func:回调函数，回调自动填写参数num
        :param call_stop_func:调用停止线程后，在回调清理函数，回调自动填写参数num
        :param call_print_func: 是否指定打印回调函数，默认为print，指定则需要有两个参数:num,content
        """
        self._thread_dict = {}  # {id:线程对象}
        self._start_all_thread = None  # 批量启动线程对象

        self._thread_max_num = thread_max_num  # 最大线程数量
        self._func = call_func  # 回调函数，参数必须为num
        if call_stop_func is None:
            self._call_stop_func = lambda num: None
        else:
            self._call_stop_func = call_stop_func
        if call_print_func is None:
            self._call_print_func = print
        else:
            self._call_print_func = call_print_func
        if call_all_stop_func is None:
            self.call_all_stop_func = lambda: None
        else:
            self.call_all_stop_func = call_all_stop_func

    def set_thread_max_num(self, max_num):
        self._thread_max_num = max_num

    def _pop_thread_safe(self, num):
        """线程字典安全删除：并发场景下避免 KeyError。"""
        with self.lock:
            return self._thread_dict.pop(num, None)

    def _start(self, func, num):
        try:
            func(num)
        except Exception as e:
            import traceback
            error_msg = f"❌ [Row:{num}] 线程异常: {e}\n{traceback.format_exc()}"
            print(error_msg)
            if hasattr(self, '_call_print_func'):
                self._call_print_func(num, f"❌ 线程异常: {e}")
        finally:
            self._call_stop_func(num)
            self._pop_thread_safe(num)

    def get_thread(self, num):
        return self._thread_dict.get(num)

    def start(self, num):
        """
        :param num: 可以是表格行号，也可以是模拟器ID，只需要一个不重复的序号即可
        :return:
            0:无法启动线程，当前线程已达到最大数量，
            1:线程运行中，
            2:线程启动成功
        """
        with self.lock:
            now_num = len(self._thread_dict)
            if now_num >= self._thread_max_num:
                self._call_print_func(num, f"无法启动线程，当前线程已达到最大数量:{self._thread_max_num}")
                return 0
            t = self._thread_dict.get(num)

            if t and t.is_alive():
                self._call_print_func(num, f"线程运行中")
                return 1

            self._call_print_func(num, f"线程启动")
            new_thread = PyThread(target=self._start, args=(self._func, num))
            self._thread_dict[num] = new_thread
        new_thread.start()
        return 2

    def stop(self, num):
        """
        :param num: 可以是表格行号，也可以是模拟器ID，只需要一个不重复的序号即可
        :return:
            0:无法停止线程，当前线程不存在，
            1:线程已经停止
        """
        with self.lock:
            t = self._thread_dict.get(num)
        if t and t.is_alive():
            # 优先协作式退出，降低强杀导致的锁/资源损坏风险
            try:
                t.stop()
                t.join(timeout=2.0)
            except Exception:
                pass
            # 兜底：协作退出超时时再强杀
            if t.is_alive():
                t.TerminateThread()
            if self.lock.locked():  # 解锁,防止死锁
                self.lock.release()
            self._call_print_func(num, f"线程停止")
            if t.is_alive():
                self._call_print_func(num, f"线程停止失败")
                return 0
            self._call_stop_func(num)  # 回调清理函数
            self._pop_thread_safe(num)  # 移除线程
            return 1
        else:
            self._call_print_func(num, "线程不存在")
            self._pop_thread_safe(num)  # 移除线程
            return 0

    def pause(self, num):
        t = self._thread_dict.get(num)
        if t and t.is_alive():
            t.pause()
            self._call_print_func(num, "线程暂停")
            return 1
        else:
            self._call_print_func(num, f"无法暂停线程，当前线程不存在")
            return 0

    def resume(self, num):
        t = self._thread_dict.get(num)
        if t and t.is_alive():
            t.resume()
            self._call_print_func(num, f"线程恢复")
            return 1
        else:
            self._call_print_func(num, f"无法恢复线程，当前线程不存在")
            return 0

    def _start_all(self, nums, delay):
        """
        0:
        1:
        2:
        :param nums:
        :param delay:
        :return:
        """
        n = 0

        def delay_show_state(index, n):
            for de in range(delay):
                time.sleep(1)
                n += 1
                # 更新剩余线程待启动状态
                for num2 in nums[index:]:
                    self._call_print_func(num2, f"待%d启动" % (num2 * delay - n,))
            return n
        # 先更新线程待启动状态

        for num in nums:
            self._call_print_func(num, f"待%d启动" % (num * delay,))
        for index, num in enumerate(nums):
            res = self.start(num)
            if res == 0:  # 无法启动线程，当前线程已达到最大数量,直接阻塞并等待
                self._call_print_func(num, f"当前线程已达到最大数量:{self._thread_max_num},线程等待中...")
                while True:
                    time.sleep(1)
                    if len(self._thread_dict) < self._thread_max_num:
                        break
                self.start(num)
                n = delay_show_state(index, n)
            elif res == 1:  # 线程运行中,直接忽略
                continue
            elif res == 2:  # 线程启动成功
                if index + 1 >= len(nums):
                    break
                n = delay_show_state(index + 1, n)
                continue
            else:
                raise f"_start_all 未知错误res"
        # 等线程全部执行完成，在回调函数
        while True:
            time.sleep(0.1)
            if not len(self._thread_dict):
                break
        # 回调函数
        self.call_all_stop_func()


    def start_all(self, nums, delay):
        if self._start_all_thread and self._start_all_thread.is_alive():
            self._call_print_func(nums[0], "正在批量启动线程，请勿重复操作")
            return 0
        else:
            self._start_all_thread = PyThread(target=self._start_all, args=(nums, delay))
            self._start_all_thread.start()
            self._call_print_func(nums[0], "批量启动线程启动")
            return 1


    def stop_all(self):
        if self._start_all_thread and self._start_all_thread.is_alive():
            self._start_all_thread.stop()
            self._start_all_thread = None
            print("停止滚号线程")
        # 停止线程
        while True:
            if len(self._thread_dict) == 0:
                break
            ld_num = list(self._thread_dict.keys())[0]
            self.stop(ld_num)
        return 1


    def pause_all(self):
        for num, t in self._thread_dict.items():
            self.pause(num)


    def resume_all(self):
        for num, t in self._thread_dict.items():
            self.resume(num)
