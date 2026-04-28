# -*- coding: utf-8 -*-
from dxGame.dx_core import *
import logging


class Window:

    @staticmethod
    def ClientToScreen(hwnd, x, y) -> tuple:
        point = ctypes.wintypes.POINT()
        point.x = x
        point.y = y
        for i in range(10):
            is_ok: bool = user32.ClientToScreen(hwnd, ctypes.byref(point))
            if not is_ok:
                raise Exception('call ClientToScreen failed')
            if point.x !=0 and point.y != 0:
                return (point.x, point.y)
            time.sleep(0.01)
    @staticmethod
    def EnumProcess(name) -> str:
        '''需安装psutil'''
        try:
            import psutil
        except:
            raise Exception("called EnumProcess failed:psutil not install")
        ret = []
        for proc in psutil.process_iter():
            pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
            pname = ''
            if pinfo['name'] != None:
                pname = pinfo['name'].upper()
            if name.upper() in pname:
                ret.append((pinfo['pid'], pinfo['create_time']))
        if len(ret) == 0:
            raise Exception("called EnumProcess failed:process not found")
        ret = sorted(ret, key=lambda x: x[1])
        ret = [str(i[0]) for i in ret]
        return ','.join(ret)




    @staticmethod
    def FindWindow(_class, _title) -> int:
        # 定义EnumWindows函数的回调类型
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.wintypes.HWND,  # HWND
            ctypes.POINTER(ctypes.wintypes.LPARAM)  # LPARAM
        )

        # 定义返回顶级窗口句柄的列表
        top_level_windows = []

        # 回调函数，将窗口句柄添加到列表中
        def enum_windows_proc(hwnd, lParam):
            top_level_windows.append(hwnd)
            return True

        # 枚举所有顶级窗口
        def enum_top_level_windows():
            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
            return top_level_windows

        # 调用函数，获取所有顶级窗口句柄
        hwnds = enum_top_level_windows()

        for hwnd in hwnds:
            _title2 = Window.GetWindowTitle(hwnd)
            _class2 = Window.GetWindowClass(hwnd)
            if _title:
                if _title not in _title2:
                    continue
            if _class:
                if _class not in _class2:
                    continue
            # if _title == _title2 and _class == _class2:
            return hwnd


        return 0

    @staticmethod
    def FindWindowEx(parent, class_, title) -> int:
        retArr = []

        def mycallback(hwnd, extra) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            if class_:
                class1 = class_.upper()
                class2 = Window.GetWindowClass(hwnd).upper()
                if class1 not in class2:
                    return True
            if title:
                title1 = title.upper()
                title2 = Window.GetWindowTitle(hwnd).upper()
                if title1 not in title2:
                    return True
            retArr.append(hwnd)
            return False

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumChildWindows(parent, CMPFUNC(mycallback), 0)
        return retArr

    @staticmethod
    def FindWindowByProcessId(process_id, class_, title) -> int:
        retArr = []

        def mycallback(hwnd, extra) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            lProcessId = ctypes.wintypes.LONG()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lProcessId))
            if process_id != lProcessId.value:
                return True
            if class_.upper() not in Window.GetWindowClass(hwnd).upper():
                return True
            if title.upper() not in Window.GetWindowTitle(hwnd).upper():
                return True
            retArr.append(hwnd)
            return False

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumChildWindows(None, CMPFUNC(mycallback), 0)
        if len(retArr) == 0:
            raise Exception('call FindWindowByProcessId failed:Not Found Window')
        return retArr[0]

    @staticmethod
    def FindWindowByProcess(process_name, class_, title) -> int:
        '''需安装psutil'''
        try:
            import psutil
        except:
            raise Exception("called FindWindowByProcess failed:psutil not install")
        retArr = []

        def mycallback(hwnd, extra) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            lProcessId = Window.GetWindowProcessId(hwnd)
            lProcessName = None
            try:  # 有些进程是无法打开的
                lProcessName = psutil.Process(lProcessId).name()
            except:
                return True
            if (lProcessName == None): lProcessName = ""
            if process_name.upper() not in lProcessName.upper():
                return True
            if class_.upper() not in Window.GetWindowClass(hwnd).upper():
                return True
            if title.upper() not in Window.GetWindowTitle(hwnd).upper():
                return True
            retArr.append(hwnd)
            return False

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumChildWindows(None, CMPFUNC(mycallback), 0)
        if len(retArr) == 0:
            raise Exception('call FindWindowByProcessId failed:Not Found Window')
        return retArr[0]

    @staticmethod
    def GetProcessInfo(pid):
        '''需安装psutil'''
        try:
            import psutil
        except:
            raise Exception("called GetProcessInfo failed:psutil not install")
        p = psutil.Process(pid)
        return p.name() + '|' + p.exe() + '|' + str(p.cpu_percent()) + '|' + str(p.memory_info().rss)

    @staticmethod
    def GetWindowClass(hwnd) -> str:
        class_buffter = ctypes.create_string_buffer(''.encode(), 1000)
        length = user32.GetClassNameW(hwnd, class_buffter, 1000)
        if not length:
            return ""
        classStr = class_buffter.raw[:length * 2].decode('utf-16le')
        return classStr

    @staticmethod
    def GetWindowProcessId(hwnd) -> int:
        lProcessId = ctypes.wintypes.LONG()
        is_ok: bool = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lProcessId))
        if (not is_ok) and kernel32.GetLastError() != 0:
            raise Exception("call GetWindowProcessId failed")
        return lProcessId.value

    @staticmethod
    def GetWindowTitle(hwnd) -> str:
        title_buffer = ctypes.create_string_buffer(''.encode(), 1000)
        length = user32.GetWindowTextW(hwnd, title_buffer, 1000)
        if not length:
            return ""
        title = title_buffer.raw[:length * 2].decode('utf-16le')
        return title

    @staticmethod
    def GetWindowProcessPath(hwnd) -> str:
        '''需安装psutil'''
        try:
            import psutil
        except:
            raise Exception("called GetWindowProcessPath failed:psutil not install")
        process_id = Window.GetWindowProcessId(hwnd)
        p = psutil.Process(process_id)
        return p.exe()

    @staticmethod
    def GetSpecialWindow(flag) -> int:
        if flag == 0:
            return user32.GetDesktopWindow()
        elif flag == 1:
            return user32.FindWindowW("Shell_TrayWnd", 0)
        else:
            raise Exception('call GetSpecialWindow Failed')

    @staticmethod
    def GetForegroundWindow() -> int:
        is_ok: int = user32.GetForegroundWindow()
        if not is_ok:
            raise Exception('call GetForegroundWindow Failed')
        return is_ok

    @staticmethod
    def GetForegroundFocus() -> int:
        wnd: int = Window.GetForegroundWindow()
        if not wnd:
            raise Exception('call GetForegroundFocus Failed')
        SelfThreadId = kernel32.GetCurrentThreadId()
        ForeThreadId = user32.GetWindowThreadProcessId(wnd, 0)
        user32.AttachThreadInput(ForeThreadId, SelfThreadId, True)
        wnd = user32.GetFocus()
        user32.AttachThreadInput(ForeThreadId, SelfThreadId, False)
        if not wnd:
            raise Exception('call GetForegroundFocus Failed')
        return wnd

    @staticmethod
    def GetMousePointWindow() -> int:
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.wintypes.LONG),
                ("y", ctypes.wintypes.LONG)
            ]

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        hwnd = user32.WindowFromPoint(point)
        if not hwnd:
            raise Exception('call GetMousePointWindow failed')
        return hwnd

    @staticmethod
    def GetCursorPos():
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.wintypes.LONG),
                ("y", ctypes.wintypes.LONG)
            ]

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    @staticmethod
    def GetPointWindow(x, y) -> int:
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.wintypes.LONG),
                ("y", ctypes.wintypes.LONG)
            ]

        point = POINT()
        point.x = x
        point.y = y
        hwnd = user32.WindowFromPoint(point)
        if not hwnd:
            raise Exception('call GetMousePointWindow failed')
        return hwnd

    @staticmethod
    def GetWindow(hwnd, flag) -> int:
        rethwnd = None
        if flag == 0:
            rethwnd = user32.GetParent(hwnd)
        elif flag == 1:
            rethwnd = user32.GetWindow(hwnd, 5)
            # def mycallback(hwnd,extra) -> bool:
            #     nonlocal rethwnd
            #     rethwnd = hwnd
            #     return False
            # CMPFUNC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            # user32.EnumChildWindows(hwnd,CMPFUNC(mycallback),0)
        elif flag == 2:
            rethwnd = user32.GetWindow(hwnd, 0)
        elif flag == 3:
            rethwnd = user32.GetWindow(hwnd, 1)
        elif flag == 4:
            rethwnd = user32.GetWindow(hwnd, 2)
        elif flag == 5:
            rethwnd = user32.GetWindow(hwnd, 3)
        elif flag == 6:
            rethwnd = user32.GetWindow(hwnd, 4)
            if not rethwnd:
                rethwnd = user32.GetParent(hwnd)
            if not rethwnd:
                rethwnd = hwnd
        elif flag == 7:
            rethwnd = user32.GetTopWindow(hwnd)
            # top = hwnd
            # while True:
            #     hd = user32.GetParent(top)
            #     if not hd:
            #         rethwnd = top
            #         break
            #     top = hd
        if not rethwnd:
            return 0
        return rethwnd

    @staticmethod
    def GetWindowRect(hwnd) -> tuple:
        rect = ctypes.wintypes.RECT()
        is_ok: bool = user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if not is_ok:
            raise Exception('call GetWindowRect failed')
        return (rect.left, rect.top, rect.right, rect.bottom)

    @staticmethod
    def GetWindowState(hwnd, flag) -> bool:
        if flag == 0:
            return user32.IsWindow(hwnd) == 1
        elif flag == 1:
            return Window.GetForegroundWindow() == hwnd
        elif flag == 2:
            return user32.IsWindowVisible(hwnd) == 1
        elif flag == 3:
            return user32.IsIconic(hwnd) == 1
        elif flag == 4:
            return user32.IsZoomed(hwnd) == 1
        elif flag == 5:
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            if (user32.GetWindowLongA(hwnd, GWL_EXSTYLE) & WS_EX_TOPMOST):
                return True
            else:
                return False
        elif flag == 6 or flag == 8:
            return user32.IsHungAppWindow(hwnd) == 1
        elif flag == 7:
            return user32.IsWindowEnabled(hwnd) == 1
        elif flag == 9:
            def Is64Bit() -> bool:
                class _SYSTEM_INFO(ctypes.Structure):
                    _fields_ = [
                        ("dwOemId", ctypes.wintypes.DWORD),
                        ("dwProcessorType", ctypes.wintypes.DWORD),
                        ("lpMinimumApplicationAddress", ctypes.wintypes.LPVOID),
                        ("lpMaximumApplicationAddress", ctypes.wintypes.LPVOID),
                        ("dwActiveProcessorMask", ctypes.wintypes.LPVOID),
                        ("dwNumberOfProcessors", ctypes.wintypes.DWORD),
                        ("dwProcessorType", ctypes.wintypes.DWORD),
                        ("dwAllocationGranularity", ctypes.wintypes.DWORD),
                        ("wProcessorLevel", ctypes.wintypes.WORD),
                        ("wProcessorRevision", ctypes.wintypes.WORD),
                    ]

                lpSystemInfo = _SYSTEM_INFO()
                kernel32.GetNativeSystemInfo(ctypes.byref(lpSystemInfo))
                PROCESSOR_ARCHITECTURE_IA64 = 6
                PROCESSOR_ARCHITECTURE_AMD64 = 9
                if lpSystemInfo.dwOemId in [PROCESSOR_ARCHITECTURE_IA64, PROCESSOR_ARCHITECTURE_AMD64]:
                    return True
                else:
                    return False

            if not Is64Bit():
                return False
            isWow64Process = ctypes.wintypes.BOOL(True)
            processId = Window.GetWindowProcessId(hwnd)
            PROCESS_QUERY_INFORMATION = 0x0400
            hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, processId)
            if not hProcess:
                raise Exception('call GetWindowState failed:OpenProcess')
            is_ok: bool = kernel32.IsWow64Process(hProcess, ctypes.pointer(isWow64Process))
            kernel32.CloseHandle(hProcess)
            if not is_ok:
                raise Exception('call GetWindowState failed:IsWow64Process')
            if isWow64Process.value:
                return False
            return True

    @staticmethod
    def GetClientSize(hwnd) -> tuple:
        rect = ctypes.wintypes.RECT()
        is_ok: bool = user32.GetClientRect(hwnd, ctypes.byref(rect))
        if not is_ok:
            raise Exception('call GetClientRect failed')
        return (rect.right, rect.bottom)

    @staticmethod
    def ScreenToClient(hwnd, x, y) -> tuple:
        point = ctypes.wintypes.POINT()
        point.x = x
        point.y = y
        is_ok: bool = user32.ScreenToClient(hwnd, ctypes.byref(point))
        if not is_ok:
            raise Exception('call ScreenToClient failed')
        return (point.x, point.y)

    @staticmethod
    def getClientRect(hwnd) -> tuple:
        x1, y1 = Window.ClientToScreen(hwnd, 0, 0)
        x2, y2 = Window.GetClientSize(hwnd)
        x2, y2 = Window.ClientToScreen(hwnd, x2, y2)
        return (x1, y1, x2, y2)

    @staticmethod
    def MoveWindow(hwnd, x, y) -> None:
        x1, y1, x2, y2 = Window.GetWindowRect(hwnd)
        width, height = x2 - x1, y2 - y1
        is_ok: bool = user32.MoveWindow(hwnd, x, y, width, height, False)
        if not is_ok:
            raise Exception('call MoveWindow failed')

    @staticmethod
    def SetWindowSize(hwnd, width, height) -> None:
        x1, y1, x2, y2 = Window.GetWindowRect(hwnd)
        is_ok: bool = user32.MoveWindow(hwnd, x1, y1, width, height, True)
        if not is_ok:
            raise Exception('call SetWindowSize failed')

    @staticmethod
    def SetWindowText(hwnd, title):
        is_ok: bool = user32.SetWindowTextW(hwnd, title)
        if not is_ok:
            raise Exception('call SetWindowText failed')

    @staticmethod
    def SetWindowTransparent(hwnd, trans):
        is_ok: bool = user32.SetLayeredWindowAttributes(hwnd, 0, trans, 2)
        if not is_ok:
            raise Exception('call SetWindowTransparent failed')

    @staticmethod
    def SetClientSize(hwnd, width, height) -> None:
        wx1, wy1, wx2, wy2 = Window.GetWindowRect(hwnd)
        w, h = Window.GetClientSize(hwnd)
        Window.SetWindowSize(hwnd, wx2 - wx1 + width - w, wy2 - wy1 + height - h)

    @staticmethod
    def SendPaste(hwnd) -> None:
        class WINDOWPLACEMENT(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.wintypes.UINT),
                ("flags", ctypes.wintypes.UINT),
                ("showCmd", ctypes.wintypes.UINT),
                ("ptMinPosition", ctypes.wintypes.POINT),
                ("ptMaxPosition", ctypes.wintypes.POINT),
                ("rcNormalPosition", ctypes.wintypes.RECT)
            ]

        if not Window.GetWindowState(hwnd, 0):
            raise Exception('call SendPaste failed:window not exist')
        wtp = WINDOWPLACEMENT()
        user32.GetWindowPlacement(hwnd, ctypes.byref(wtp))
        if (wtp.showCmd != 1):  # 没有最小化
            if wtp.showCmd == 2:  # 被最小化了
                wtp.showCmd = 9
                user32.SetWindowPlacement(hwnd, ctypes.byref(wtp))
        # 正常情况下wtp.showCmd为3，表示前台
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        user32.keybd_event(0x11, 0, 0x0001, 0);
        user32.keybd_event(86, 0, 0x0001, 0);
        user32.keybd_event(86, 0, 0x0001 | 0x0002, 0)
        user32.keybd_event(0x11, 0, 0x0001 | 0x0002, 0)

    @staticmethod
    def SetWindowState(hwnd, flag):
        class WINDOWPLACEMENT(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.wintypes.UINT),
                ("flags", ctypes.wintypes.UINT),
                ("showCmd", ctypes.wintypes.UINT),
                ("ptMinPosition", ctypes.wintypes.POINT),
                ("ptMaxPosition", ctypes.wintypes.POINT),
                ("rcNormalPosition", ctypes.wintypes.RECT)
            ]

        is_ok = False
        if flag == 0:
            is_ok = user32.SendMessageW(hwnd, 0x0010, 0, 0)
        elif flag == 1:
            is_ok = user32.SetForegroundWindow(hwnd)
        elif flag == 2 or flag == 3:
            is_ok = user32.ShowWindow(hwnd, 2)
        elif flag == 4:
            is_ok = user32.ShowWindow(hwnd, 3)
            is_ok = user32.SetActiveWindow(hwnd)
        elif flag == 5:
            wtp = WINDOWPLACEMENT()
            is_ok = user32.GetWindowPlacement(hwnd, ctypes.byref(wtp))
            wtp.showCmd = 9
            is_ok = user32.SetWindowPlacement(hwnd, ctypes.byref(wtp))
        elif flag == 6:
            wtp = WINDOWPLACEMENT()
            is_ok = user32.GetWindowPlacement(hwnd, ctypes.byref(wtp))
            wtp.showCmd = 0
            is_ok = user32.SetWindowPlacement(hwnd, ctypes.byref(wtp))
        elif flag == 7:
            # wtp = WINDOWPLACEMENT()
            # is_ok = user32.GetWindowPlacement(hwnd, ctypes.byref(wtp))
            # wtp.showCmd = 5
            # is_ok = user32.SetWindowPlacement(hwnd, ctypes.byref(wtp))
            is_ok = user32.ShowWindow(hwnd, 9)
        elif flag == 8:
            is_ok = user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)
        elif flag == 9:
            is_ok = user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 3)
        elif flag in [10, 11, 12]:
            pass
        elif flag == 13:
            pid = Window.GetWindowProcessId(hwnd)
            hProcessHandle = kernel32.OpenProcess(1, False, pid)
            is_ok = kernel32.TerminateProcess(hProcessHandle, 4)
            kernel32.CloseHandle(hProcessHandle)
        elif flag == 14:
            is_ok = user32.FlashWindow(hwnd, True)
        elif flag == 15:
            hCurWnd = user32.GetForegroundWindow()
            dwMyID = kernel32.GetCurrentThreadId()
            dwCurID = user32.GetWindowThreadProcessId(hCurWnd, 0)
            user32.AttachThreadInput(dwCurID, dwMyID, True)
            is_ok = user32.SetFocus(hwnd)
            user32.AttachThreadInput(dwCurID, dwMyID, False)
        # if not is_ok:
        #     raise Exception('窗口设置失败,请检查句柄或者参数')

    @staticmethod
    def EnumWindow(parent_, title, class_name, filter):
        """

        :param parent_:
        :param title:
        :param class_name:
        :param filter: 1,标题过滤,2,雷鸣过滤
        :return:
        """
        # 1. 枚举所有句柄
        # 定义必要的类型
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        all_windows = []

        GW_CHILD = 5
        GW_HWNDNEXT = 2

        # 遍历子窗口
        def enumerate_child_windows(hwnd):
            child_hwnd = user32.GetWindow(hwnd, GW_CHILD)
            while child_hwnd:
                all_windows.append(child_hwnd)
                # 递归枚举子窗口的子窗口
                enumerate_child_windows(child_hwnd)
                child_hwnd = user32.GetWindow(child_hwnd, GW_HWNDNEXT)

        # 顶级窗口回调函数
        def enumerate_windows(hwnd, lParam):
            # 添加顶级窗口句柄到列表
            all_windows.append(hwnd)
            # 使用递归手动枚举所有子窗口
            enumerate_child_windows(hwnd)

            return True

        # 调用 EnumWindows 枚举顶级窗口
        user32.EnumWindows(WNDENUMPROC(enumerate_windows), 0)
        # 2.过滤句柄
        hwnds = []
        for hwnd in all_windows:
            try:
                wtitle = Window.GetWindowTitle(hwnd)
                wclass = Window.GetWindowClass(hwnd)
            except:
                return True
            if filter & 1 == 1:
                if title not in wtitle:
                    continue
            if ((filter & 2) >> 1) == 1:
                if class_name.upper() not in wclass.upper():
                    continue
            if ((filter & 4) >> 2) == 1:
                try:
                    if Window.GetWindow(hwnd, 0) != parent_:
                        continue
                except:
                    continue
            if ((filter & 8) >> 3) == 1:
                if not (user32.GetParent(hwnd) == 0):
                    continue
                if kernel32.GetLastError() != 0:
                    continue
            if ((filter & 16) >> 4) == 1:
                if Window.GetWindowState(2, ) == False:
                    continue
            hwnds.append(hwnd)

        return hwnds

    @staticmethod
    def FindVMwareWindowByPort(port: str) -> int:
        """
        通过端口号查找 VMware 虚拟机窗口句柄
        
        Args:
            port: VNC 端口号，如 "5600", "5601"
            
        Returns:
            int: 窗口句柄，如果未找到返回 0
            
        Example:
            >>> hwnd = Window.FindVMwareWindowByPort("5600")
            >>> print(f"找到窗口句柄: {hwnd}")
        """
        try:
            import psutil
        except ImportError:
            raise Exception("FindVMwareWindowByPort 需要安装 psutil: pip install psutil")
        
        # 1. 枚举所有 vmware.exe 进程
        vmware_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'vmware.exe' in proc.info['name'].lower():
                    vmware_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not vmware_pids:
            logging.warning("未找到 vmware.exe 进程")
            return 0
        
        logging.debug(f"找到 {len(vmware_pids)} 个 vmware.exe 进程: {vmware_pids}")
        
        # 2. 遍历所有顶级窗口，查找属于 vmware.exe 且标题包含端口号的窗口
        target_hwnd = 0
        
        def enum_windows_callback(hwnd, lParam):
            nonlocal target_hwnd
            
            # 检查窗口是否可见
            if not user32.IsWindowVisible(hwnd):
                return True
            
            # 获取窗口所属的进程 ID
            window_pid = ctypes.wintypes.LONG()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            
            # 检查是否属于 vmware.exe 进程
            if window_pid.value not in vmware_pids:
                return True
            
            # 获取窗口标题
            title = Window.GetWindowTitle(hwnd)
            
            # 检查窗口标题是否包含端口号
            if port in title:
                target_hwnd = hwnd
                logging.info(f"✓ 找到 VMware 窗口 [端口:{port}] 句柄:{hwnd} 标题:'{title}'")
                return False  # 找到目标，停止枚举
            
            return True
        
        # 枚举所有顶级窗口
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        
        if target_hwnd == 0:
            logging.warning(f"❌ 未找到端口号为 {port} 的 VMware 窗口")
            # 调试信息：列出所有 vmware 窗口
            logging.debug("--- 调试信息：所有 VMware 窗口 ---")
            def debug_callback(hwnd, lParam):
                window_pid = ctypes.wintypes.LONG()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                if window_pid.value in vmware_pids:
                    title = Window.GetWindowTitle(hwnd)
                    logging.debug(f"  PID:{window_pid.value} HWND:{hwnd} 标题:'{title}'")
                return True
            user32.EnumWindows(WNDENUMPROC(debug_callback), 0)
            logging.debug("---------------------------------")
        
        return target_hwnd
    
    @staticmethod
    def FindVMwareRealWindowByPort(port: str) -> int:
        """
        通过端口号查找 VMware 虚拟机的真实游戏窗口句柄（多层级查找）
        
        查找层级：
        第1层: 标题含端口号 + 类名 VMUIFrame
        第2层: 类名 VMUIView
        第3层: 类名 AtlAxWin140
        第4层: 类名 ATL:* (动态变化，如 ATL:587D8470)
        第5层: 类名 VMware.GuestWindow
        第6层: 标题 MKSWindow#0 + 类名 MKSEmbedded (真实窗口)
        
        Args:
            port: VNC 端口号，如 "5600", "5601"
            
        Returns:
            int: 真实的游戏窗口句柄，如果未找到返回 0
            
        Example:
            >>> hwnd = Window.FindVMwareRealWindowByPort("5600")
            >>> print(f"找到真实窗口句柄: {hwnd}")
        """
        try:
            import psutil
        except ImportError:
            raise Exception("FindVMwareRealWindowByPort 需要安装 psutil: pip install psutil")
        
        logging.info(f"\n{'='*70}")
        logging.info(f"开始查找端口 {port} 的 VMware 真实窗口句柄")
        logging.info(f"{'='*70}")
        
        # 1. 枚举所有 vmware.exe 进程
        vmware_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'vmware.exe' in proc.info['name'].lower():
                    vmware_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not vmware_pids:
            logging.warning("未找到 vmware.exe 进程")
            return 0
        
        logging.info(f"步骤 0: 找到 {len(vmware_pids)} 个 vmware.exe 进程: {vmware_pids}")
        
        # 2. 第一层：查找标题包含端口号且类名为 VMUIFrame 的窗口（可能是子窗口）
        layer1_hwnd = 0
        
        def find_layer1(hwnd, lParam):
            nonlocal layer1_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True
            
            window_pid = ctypes.wintypes.LONG()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            
            if window_pid.value not in vmware_pids:
                return True
            
            # 获取类名
            class_name = Window.GetWindowClass(hwnd)
            title = Window.GetWindowTitle(hwnd)
            
            # 第一层：标题包含端口号 且 类名为 VMUIFrame
            if port in title and class_name == "VMUIFrame":
                layer1_hwnd = hwnd
                logging.info(f"✓ 第1层找到: HWND={hwnd}, 类名={class_name}, 标题='{title}'")
                return False
            
            return True
        
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        
        # 先尝试枚举所有窗口（包括子窗口）
        def enum_all_windows(hwnd, lParam):
            if find_layer1(hwnd, 0):
                # 递归枚举子窗口
                user32.EnumChildWindows(hwnd, WNDENUMPROC(enum_all_windows), 0)
            return layer1_hwnd == 0  # 找到后停止
        
        # 枚举顶级窗口
        user32.EnumWindows(WNDENUMPROC(enum_all_windows), 0)
        
        if layer1_hwnd == 0:
            logging.error(f"❌ 第1层未找到 VMUIFrame 窗口 (端口:{port})")
            return 0
        
        # 3. 第二层：在 Layer1 下查找类名 VMUIView 的子窗口
        layer2_hwnd = Window.FindChildWindowByClass(layer1_hwnd, "VMUIView")
        if layer2_hwnd == 0:
            logging.error(f"❌ 第2层未找到 VMUIView 子窗口")
            return 0
        logging.info(f"✓ 第2层找到: HWND={layer2_hwnd}, 类名=VMUIView")
        
        # 4. 第三层：在 Layer2 下查找类名 AtlAxWin140 的子窗口
        layer3_hwnd = Window.FindChildWindowByClass(layer2_hwnd, "AtlAxWin140")
        if layer3_hwnd == 0:
            logging.error(f"❌ 第3层未找到 AtlAxWin140 子窗口")
            return 0
        logging.info(f"✓ 第3层找到: HWND={layer3_hwnd}, 类名=AtlAxWin140")
        
        # 5. 第四层：在 Layer3 下查找所有子窗口（ATL类名是动态变化的）
        layer4_hwnds = []
        
        def find_all_layer4(hwnd, lParam):
            nonlocal layer4_hwnds
            child_class = Window.GetWindowClass(hwnd)
            
            # 记录所有第4层的子窗口（ATL开头的类名）
            if child_class.startswith("ATL:"):
                layer4_hwnds.append(hwnd)
                logging.info(f"✓ 第4层找到: HWND={hwnd}, 类名={child_class}")
            
            return True  # 继续枚举所有子窗口
        
        WNDENUMPROC_LAYER4 = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumChildWindows(layer3_hwnd, WNDENUMPROC_LAYER4(find_all_layer4), 0)
        
        if not layer4_hwnds:
            logging.error(f"❌ 第4层未找到任何 ATL:* 子窗口")
            return 0
        
        logging.info(f"✓ 第4层共找到 {len(layer4_hwnds)} 个 ATL 子窗口")
        
        # 6. 第五层和第六层：在每个 Layer4 下查找 VMware.GuestWindow 和 MKSEmbedded
        real_hwnd = 0
        
        def find_layer5_and_real(parent_hwnd):
            """在指定的第4层窗口下查找最终的MKSEmbedded窗口"""
            result_hwnd = 0
            
            def find_layer5(hwnd, lParam):
                nonlocal result_hwnd
                child_class = Window.GetWindowClass(hwnd)
                
                if child_class == "VMware.GuestWindow":
                    # 在这个 GuestWindow 下查找 MKSEmbedded
                    def check_for_mks(hwnd_child, lParam2):
                        nonlocal result_hwnd
                        mks_class = Window.GetWindowClass(hwnd_child)
                        mks_title = Window.GetWindowTitle(hwnd_child)
                        
                        if mks_class == "MKSEmbedded" and "MKSWindow#0" in mks_title:
                            result_hwnd = hwnd_child
                            logging.info(f"✓ 第5层找到: HWND={hwnd}, 类名=VMware.GuestWindow")
                            logging.info(f"✓ 第6层(最终)找到: HWND={hwnd_child}, 类名={mks_class}, 标题='{mks_title}'")
                            return False  # 找到目标
                        
                        return True
                    
                    WNDENUMPROC_MKS = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
                    user32.EnumChildWindows(hwnd, WNDENUMPROC_MKS(check_for_mks), 0)
                    
                    if result_hwnd != 0:
                        return False  # 找到真实窗口，停止枚举
                
                return True
            
            WNDENUMPROC_LAYER5 = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            user32.EnumChildWindows(parent_hwnd, WNDENUMPROC_LAYER5(find_layer5), 0)
            
            return result_hwnd
        
        # 遍历所有第4层窗口，查找最终的MKSEmbedded窗口
        for layer4_hwnd in layer4_hwnds:
            found_hwnd = find_layer5_and_real(layer4_hwnd)
            if found_hwnd != 0:
                real_hwnd = found_hwnd
                break
        
        if real_hwnd == 0:
            logging.error(f"❌ 未找到 MKSEmbedded 真实窗口 (在所有 {len(layer4_hwnds)} 个第4层窗口中均未找到)")
            return 0
        
        logging.info(f"\n{'='*70}")
        logging.info(f"✅ 成功找到端口 {port} 的真实窗口句柄: {real_hwnd}")
        logging.info(f"{'='*70}\n")
        
        return real_hwnd
    
    @staticmethod
    def FindChildWindowByClass(parent_hwnd: int, class_name: str) -> int:
        """
        在父窗口下查找指定类名的直接子窗口
        
        Args:
            parent_hwnd: 父窗口句柄
            class_name: 要查找的类名
            
        Returns:
            int: 找到的子窗口句柄，未找到返回 0
        """
        result_hwnd = 0
        
        def enum_child_callback(hwnd, lParam):
            nonlocal result_hwnd
            child_class = Window.GetWindowClass(hwnd)
            
            if child_class == class_name:
                result_hwnd = hwnd
                return False  # 找到目标，停止枚举
            
            return True
        
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumChildWindows(parent_hwnd, WNDENUMPROC(enum_child_callback), 0)
        
        return result_hwnd
    
    @staticmethod
    def ActivateWindow(hwnd: int) -> bool:
        """
        激活指定窗口（ bring to front ）
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 是否成功激活
        """
        if hwnd == 0 or hwnd is None:
            logging.error("激活窗口失败：句柄无效")
            return False
        
        # 🔧 验证窗口句柄有效性
        try:
            import ctypes.wintypes
            if not user32.IsWindow(hwnd):
                logging.error(f"激活窗口失败：句柄 {hwnd} 已失效")
                return False
        except Exception as e:
            logging.error(f"验证窗口句柄异常: {e}")
            return False
        
        try:
            # 如果窗口最小化，先恢复
            try:
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            except OSError as e:
                logging.error(f"⚠️ IsIconic/ShowWindow 调用失败 (OSError): {e}")
                return False
            
            # 将窗口置前
            try:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
            except OSError as e:
                logging.error(f"⚠️ SetForegroundWindow/BringWindowToTop 调用失败 (OSError): {e}")
                return False
            
            # 设置焦点
            try:
                user32.SetFocus(hwnd)
            except OSError as e:
                logging.error(f"⚠️ SetFocus 调用失败 (OSError): {e}")
                # 即使 SetFocus 失败，窗口可能已经激活，继续返回 True
            
            logging.debug(f"✓ 窗口 {hwnd} 已激活")
            return True
            
        except MemoryError as e:
            logging.error(f"❌ 激活窗口内存错误: {e}")
            return False
        except WindowsError as e:
            logging.error(f"❌ 激活窗口 Windows API 错误: {e}")
            return False
        except Exception as e:
            logging.error(f"激活窗口 {hwnd} 失败: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            return False
    
    @staticmethod
    def CheckWindowFrozen(hwnd: int, timeout_seconds: int = 300) -> bool:
        """
        检查窗口是否卡住（在规定时间内没有任何变化）
        
        Args:
            hwnd: 窗口句柄
            timeout_seconds: 超时时间（秒），默认 5 分钟
            
        Returns:
            bool: True 表示窗口可能卡住，False 表示正常
        """
        if hwnd == 0 or hwnd is None:
            return False
        
        try:
            from dxGame.dx_core import dxpyd
            import numpy as np
            
            # 确保 hwnd 是标准 Python int，避免 numpy 类型导致的溢出
            if hasattr(hwnd, 'item'):  # numpy 类型
                hwnd = int(hwnd.item())
            else:
                hwnd = int(hwnd)
            
            # 验证 hwnd 范围（HWND 应该是 32 位或 64 位指针大小）
            if hwnd < 0 or hwnd > 0xFFFFFFFFFFFFFFFF:
                logging.error(f"无效的窗口句柄: {hwnd}")
                return False
            
            # 确保 hwnd 是正确的类型
            hwnd_obj = ctypes.wintypes.HWND(hwnd)
            
            # 严格确保 timeout_seconds 是标准 Python int，避免任何类型的溢出
            try:
                logging.debug(f"[CheckWindowFrozen] 原始参数: timeout_seconds={timeout_seconds}, type={type(timeout_seconds).__name__}")
                
                # 处理 numpy 类型或其他异常类型
                if hasattr(timeout_seconds, 'item'):
                    timeout_seconds = int(timeout_seconds.item())
                elif hasattr(timeout_seconds, '__int__'):
                    timeout_seconds = int(timeout_seconds)
                else:
                    timeout_seconds = int(str(timeout_seconds))
                
                # 限制合理范围（1-600秒）
                if timeout_seconds < 1:
                    logging.warning(f"timeout_seconds 过小 ({timeout_seconds})，使用默认值 10")
                    timeout_seconds = 10
                elif timeout_seconds > 600:
                    logging.warning(f"timeout_seconds 过大 ({timeout_seconds})，使用默认值 10")
                    timeout_seconds = 10
            except Exception as e:
                logging.error(f"timeout_seconds 类型转换失败: {e}，使用默认值 10")
                timeout_seconds = 10
            
            # 再次确保是纯 Python int（防止某些边缘情况）
            timeout_seconds = int(timeout_seconds)
            logging.debug(f"[CheckWindowFrozen] 转换后: timeout_seconds={timeout_seconds}, type={type(timeout_seconds).__name__}")
            
            # 获取初始截图
            rect = Window.GetWindowRect(hwnd_obj.value)
            width = int(rect[2] - rect[0])  # 确保是标准 int 类型
            height = int(rect[3] - rect[1])  # 确保是标准 int 类型
            
            if width <= 0 or height <= 0:
                return False
            
            # 限制最大尺寸，避免内存溢出
            max_size = 1920
            if width > max_size or height > max_size:
                logging.warning(f"窗口尺寸过大 ({width}x{height})，跳过检查")
                return False
            
            # 🔧 防止 width * height * 4 溢出 c_int 范围（2^31-1 ≈ 21亿）
            # 1920x1080x4 = 8,294,400 < 2,147,483,647，安全
            # 但如果 width/height 是负数或异常值会导致问题
            buffer_size = int(width) * int(height) * 4
            if buffer_size <= 0 or buffer_size > 2_000_000_000:  # 限制在 20 亿以内
                logging.error(f"缓冲区大小异常: {buffer_size} (width={width}, height={height})")
                return False
            
            # 截取第一帧
            try:
                hdc_screen = user32.GetDC(hwnd_obj)
            except OSError as e:
                logging.error(f"⚠️ GetDC 调用失败 (OSError): {e}")
                return False
            if not hdc_screen:
                logging.error(f"无法获取窗口 DC: {hwnd_obj.value}")
                return False
            
            try:
                hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            except OSError as e:
                logging.error(f"⚠️ CreateCompatibleDC 调用失败 (OSError): {e}")
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            if not hdc_mem:
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                logging.error(f"无法创建兼容 DC")
                return False
            
            try:
                hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, ctypes.c_int(width), ctypes.c_int(height))
            except OSError as e:
                logging.error(f"⚠️ CreateCompatibleBitmap 调用失败 (OSError): {e}")
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            if not hbitmap:
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                logging.error(f"无法创建位图")
                return False
            
            try:
                gdi32.SelectObject(hdc_mem, hbitmap)
                gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, 0x00CC0020)  # SRCCOPY
            except OSError as e:
                logging.error(f"⚠️ BitBlt 调用失败 (OSError): {e}")
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            
            # 转换为 numpy 数组
            bmi = ctypes.create_string_buffer(40)
            gdi32.GetObjectW(hbitmap, 40, bmi)
            
            # 🔧 关键修复：为第一次 GetDIBits 增加异常保护
            try:
                bits = ctypes.create_string_buffer(int(buffer_size))
                result = gdi32.GetDIBits(hdc_mem, hbitmap, 0, int(height), bits, bmi, 0)
                if result == 0:
                    logging.error(f"⚠️ GetDIBits (第一次) 返回 0，可能窗口已关闭")
                    gdi32.DeleteObject(hbitmap)
                    gdi32.DeleteDC(hdc_mem)
                    user32.ReleaseDC(hwnd_obj, hdc_screen)
                    return False
            except OSError as e:
                logging.error(f"❌ GetDIBits (第一次) 调用失败 (OSError): {e}")
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            except Exception as e:
                logging.error(f"❌ GetDIBits (第一次) 异常: {e}")
                import traceback
                logging.debug(traceback.format_exc())
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            
            img1 = np.frombuffer(bits, dtype=np.uint8).reshape((int(height), int(width), 4))
            
            # 清理 GDI 资源
            gdi32.DeleteObject(hbitmap)
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(hwnd_obj, hdc_screen)  # 修复：使用 hwnd_obj 而不是 hwnd
            
            # 等待一段时间后再次截图
            time.sleep(int(timeout_seconds))  # 修复：确保 timeout_seconds 是标准 int
            
            # 截取第二帧
            try:
                hdc_screen = user32.GetDC(hwnd_obj)
            except OSError as e:
                logging.error(f"⚠️ GetDC (第二次) 调用失败 (OSError): {e}")
                return False
            if not hdc_screen:
                logging.error(f"无法获取窗口 DC (第二次): {hwnd_obj.value}")
                return False
            
            try:
                hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            except OSError as e:
                logging.error(f"⚠️ CreateCompatibleDC (第二次) 调用失败 (OSError): {e}")
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            if not hdc_mem:
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                logging.error(f"无法创建兼容 DC (第二次)")
                return False
            
            try:
                hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, ctypes.c_int(width), ctypes.c_int(height))
            except OSError as e:
                logging.error(f"⚠️ CreateCompatibleBitmap (第二次) 调用失败 (OSError): {e}")
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            if not hbitmap:
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                logging.error(f"无法创建位图 (第二次)")
                return False
            
            try:
                gdi32.SelectObject(hdc_mem, hbitmap)
                gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, 0x00CC0020)
            except OSError as e:
                logging.error(f"⚠️ BitBlt (第二次) 调用失败 (OSError): {e}")
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            
            # 🔧 关键修复：为 GetDIBits 增加异常保护（防止访问违规）
            try:
                bits = ctypes.create_string_buffer(int(buffer_size))
                result = gdi32.GetDIBits(hdc_mem, hbitmap, 0, int(height), bits, bmi, 0)
                if result == 0:
                    logging.error(f"⚠️ GetDIBits (第二次) 返回 0，可能窗口已关闭")
                    gdi32.DeleteObject(hbitmap)
                    gdi32.DeleteDC(hdc_mem)
                    user32.ReleaseDC(hwnd_obj, hdc_screen)
                    return False
            except OSError as e:
                logging.error(f"❌ GetDIBits (第二次) 调用失败 (OSError): {e}")
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            except Exception as e:
                logging.error(f"❌ GetDIBits (第二次) 异常: {e}")
                import traceback
                logging.debug(traceback.format_exc())
                gdi32.DeleteObject(hbitmap)
                gdi32.DeleteDC(hdc_mem)
                user32.ReleaseDC(hwnd_obj, hdc_screen)
                return False
            
            img2 = np.frombuffer(bits, dtype=np.uint8).reshape((int(height), int(width), 4))
            
            # 清理 GDI 资源
            gdi32.DeleteObject(hbitmap)
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(hwnd_obj, hdc_screen)
            
            # 比较两帧是否相同
            if np.array_equal(img1, img2):
                logging.warning(f"⚠️ 窗口 {hwnd_obj.value} 在 {timeout_seconds} 秒内无变化，可能已卡住")
                return True
            else:
                logging.debug(f"✓ 窗口 {hwnd_obj.value} 正常运行")
                return False
                
        except MemoryError as e:
            logging.error(f"❌ CheckWindowFrozen 内存错误: {e}")
            return False
        except WindowsError as e:
            logging.error(f"❌ CheckWindowFrozen Windows API 错误: {e}")
            return False
        except Exception as e:
            import traceback
            # 🔧 屏蔽 OverflowError 日志（窗口尺寸异常时频繁触发，属于正常情况）
            if "OverflowError" not in str(e):
                logging.error(f"检查窗口冻结状态失败: {e}")
                logging.debug(f"详细错误信息:\n{traceback.format_exc()}")
            logging.debug(f"hwnd={hwnd}, type={type(hwnd)}, timeout_seconds={timeout_seconds}, type={type(timeout_seconds)}")
            return False

if __name__ == '__main__':
    hwnds = Window.EnumWindow(0,"","SunAwtCanvas",3)
    for hwnd in hwnds:
        son_hwnd = Window.GetWindow(hwnd,1)
        if not son_hwnd:
            print(hwnd)