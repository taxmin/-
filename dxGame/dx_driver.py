import ctypes
import time
import os
from ctypes import wintypes

# 定义常量
SC_MANAGER_ALL_ACCESS = 0xF003F
SERVICE_ALL_ACCESS = 0xF01FF

SERVICE_KERNEL_DRIVER = 0x00000001
SERVICE_DEMAND_START = 0x00000003
SERVICE_ERROR_NORMAL = 0x00000001

SERVICE_CONTROL_STOP = 0x00000001
SERVICE_CONTROL_INTERROGATE = 0x00000004

SERVICE_STOPPED = 0x00000001
SERVICE_START_PENDING = 0x00000002
SERVICE_STOP_PENDING = 0x00000003
SERVICE_RUNNING = 0x00000004

ERROR_SERVICE_DOES_NOT_EXIST = 0x00000424

# 定义SERVICE_STATUS结构体
class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD)
    ]

# 定义Windows API函数
advapi32 = ctypes.WinDLL('advapi32')
kernel32 = ctypes.WinDLL('kernel32')

OpenSCManager = advapi32.OpenSCManagerW
OpenSCManager.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
OpenSCManager.restype = wintypes.SC_HANDLE

CreateService = advapi32.CreateServiceW
CreateService.argtypes = [
    wintypes.SC_HANDLE,        # hSCManager
    wintypes.LPCWSTR,          # lpServiceName
    wintypes.LPCWSTR,          # lpDisplayName
    wintypes.DWORD,            # dwDesiredAccess
    wintypes.DWORD,            # dwServiceType
    wintypes.DWORD,            # dwStartType
    wintypes.DWORD,            # dwErrorControl
    wintypes.LPCWSTR,          # lpBinaryPathName
    wintypes.LPCWSTR,          # lpLoadOrderGroup
    wintypes.LPDWORD,          # lpdwTagId
    wintypes.LPCWSTR,          # lpDependencies
    wintypes.LPCWSTR,          # lpServiceStartName
    wintypes.LPCWSTR           # lpPassword
]
CreateService.restype = wintypes.SC_HANDLE

OpenService = advapi32.OpenServiceW
OpenService.argtypes = [wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
OpenService.restype = wintypes.SC_HANDLE

StartService = advapi32.StartServiceW
StartService.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.LPCWSTR)]
StartService.restype = wintypes.BOOL

ControlService = advapi32.ControlService
ControlService.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(SERVICE_STATUS)]
ControlService.restype = wintypes.BOOL

DeleteService = advapi32.DeleteService
DeleteService.argtypes = [wintypes.SC_HANDLE]
DeleteService.restype = wintypes.BOOL

CloseServiceHandle = advapi32.CloseServiceHandle
CloseServiceHandle.argtypes = [wintypes.SC_HANDLE]
CloseServiceHandle.restype = wintypes.BOOL

GetLastError = kernel32.GetLastError
GetLastError.argtypes = []
GetLastError.restype = wintypes.DWORD

# 定义安装驱动服务的函数
def InstallDriver(cszDriverName, cszDriverFullPath):
    """
    安装驱动服务
    参数:
        cszDriverName: 驱动服务名称
        cszDriverFullPath: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    import winreg
    if not cszDriverName or not cszDriverFullPath:
        return False

    try:
        # 构造注册表路径
        szBuf = r"SYSTEM\CurrentControlSet\Services\{}".format(cszDriverName)
        # 打开注册表键，若不存在则创建
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, szBuf)
        # 设置DisplayName
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, cszDriverName)
        # 设置ErrorControl
        winreg.SetValueEx(key, "ErrorControl", 0, winreg.REG_DWORD, 1)
        # 设置ImagePath
        winreg.SetValueEx(key, "ImagePath", 0, winreg.REG_EXPAND_SZ, r"\??\{}".format(cszDriverFullPath))
        # 设置Start
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3)
        # 设置Type
        winreg.SetValueEx(key, "Type", 0, winreg.REG_DWORD, 1)
        # 设置Security\Security (空值)
        security_key = winreg.CreateKey(key, "Security")
        winreg.SetValueEx(security_key, "Security", 0, winreg.REG_BINARY, b'')
        winreg.CloseKey(security_key)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        # 可以在这里打印错误信息
        # print("InstallDriver Error:", e)
        return False

# 定义创建驱动服务的函数
def CreateDriver(cszDriverName, cszDriverFullPath):
    """
    创建驱动服务
    参数:
        cszDriverName: 驱动服务名称
        cszDriverFullPath: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = OpenSCManager(None, None, SC_MANAGER_ALL_ACCESS)
    if not schManager:
        return False

    schService = OpenService(schManager, cszDriverName, SERVICE_ALL_ACCESS)
    if schService:
        # 服务已存在，尝试停止服务
        svcStatus = SERVICE_STATUS()
        if ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
            if svcStatus.dwCurrentState != SERVICE_STOPPED:
                # 服务正在运行，尝试停止
                if not ControlService(schService, SERVICE_CONTROL_STOP, ctypes.byref(svcStatus)):
                    CloseServiceHandle(schService)
                    CloseServiceHandle(schManager)
                    return False
                # 等待服务停止
                for i in range(10):
                    if not ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
                        CloseServiceHandle(schService)
                        CloseServiceHandle(schManager)
                        return True
                    else:
                        if svcStatus.dwCurrentState == SERVICE_STOPPED:
                            break
                    time.sleep(4)
                if svcStatus.dwCurrentState != SERVICE_STOPPED:
                    CloseServiceHandle(schService)
                    CloseServiceHandle(schManager)
                    return False
        CloseServiceHandle(schService)
        CloseServiceHandle(schManager)
        return True
    else:
        # 服务不存在，创建服务
        schService = CreateService(
            schManager,
            cszDriverName,
            cszDriverName,
            SERVICE_ALL_ACCESS,
            SERVICE_KERNEL_DRIVER,
            SERVICE_DEMAND_START,
            SERVICE_ERROR_NORMAL,
            cszDriverFullPath,
            None,
            None,
            None,
            None,
            None
        )
        if not schService:
            CloseServiceHandle(schManager)
            return False
        CloseServiceHandle(schService)
        CloseServiceHandle(schManager)
        return True

# 定义启动驱动服务的函数
def StartDriver(cszDriverName, cszDriverFullPath):
    """
    启动驱动服务
    参数:
        cszDriverName: 驱动服务名称
        cszDriverFullPath: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    if not cszDriverName:
        print("驱动服务名称不能为空")
        return False

    if not CreateDriver(cszDriverName, cszDriverFullPath):
        print("驱动创建失败")
        return False

    schManager = OpenSCManager(None, None, SC_MANAGER_ALL_ACCESS)
    if not schManager:
        print("无法打开服务控制管理器。错误代码: %d", GetLastError())
        return False

    schService = OpenService(schManager, cszDriverName, SERVICE_ALL_ACCESS)
    if not schService:
        CloseServiceHandle(schManager)
        return False

    svcStatus = SERVICE_STATUS()

    if ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
        print("服务当前状态: %d", svcStatus.dwCurrentState)
        if svcStatus.dwCurrentState == SERVICE_RUNNING:
            print("服务已在运行。")
            CloseServiceHandle(schService)
            CloseServiceHandle(schManager)
            return True
    else:
        last_error = GetLastError()
        if last_error != 1062:  # ERROR_SERVICE_NOT_ACTIVE
            print("服务控制查询失败。错误代码: %d", last_error)
            CloseServiceHandle(schService)
            CloseServiceHandle(schManager)
            return False

    # 尝试启动服务
    if not StartService(schService, 0, None):
        last_error = GetLastError()
        if last_error == 1056:  # ERROR_SERVICE_ALREADY_RUNNING
            print("服务已经在运行。")
            return True
        elif last_error == 1072 or last_error == 183:  # ERROR_SERVICE_EXISTS
            print("服务已经存在且可能正在运行。")
            return True
        else:
            print("启动服务失败。错误代码: %d", last_error)
            CloseServiceHandle(schService)
            CloseServiceHandle(schManager)
            return False
    # else:
    #     print("启动服务命令已发送。")

    # 等待服务启动
    for i in range(10):
        if not ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
            CloseServiceHandle(schService)
            CloseServiceHandle(schManager)
            return False
        else:
            if svcStatus.dwCurrentState == SERVICE_RUNNING:
                break
        time.sleep(4)

    CloseServiceHandle(schService)
    CloseServiceHandle(schManager)

    if svcStatus.dwCurrentState == SERVICE_RUNNING:
        return True
    else:
        return False

# 定义停止驱动服务的函数
def StopDriver(cszDriverName, cszDriverFullPath):
    """
    停止驱动服务
    参数:
        cszDriverName: 驱动服务名称
        cszDriverFullPath: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = OpenSCManager(None, None, SC_MANAGER_ALL_ACCESS)
    if not schManager:
        return False

    schService = OpenService(schManager, cszDriverName, SERVICE_ALL_ACCESS)
    if not schService:
        CloseServiceHandle(schManager)
        return False

    svcStatus = SERVICE_STATUS()

    if ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
        if svcStatus.dwCurrentState != SERVICE_STOPPED:
            if not ControlService(schService, SERVICE_CONTROL_STOP, ctypes.byref(svcStatus)):
                CloseServiceHandle(schService)
                CloseServiceHandle(schManager)
                return False
            # 等待服务停止
            for i in range(10):
                if not ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
                    break
                else:
                    if svcStatus.dwCurrentState == SERVICE_STOPPED:
                        break
                time.sleep(4)
            if svcStatus.dwCurrentState != SERVICE_STOPPED:
                CloseServiceHandle(schService)
                CloseServiceHandle(schManager)
                return False
    else:
        # 服务未运行
        CloseServiceHandle(schService)
        CloseServiceHandle(schManager)
        return True

    CloseServiceHandle(schService)
    CloseServiceHandle(schManager)
    return True

# 定义卸载驱动服务的函数
def RemoveDriver(cszDriverName, cszDriverFullPath):
    """
    卸载驱动服务
    参数:
        cszDriverName: 驱动服务名称
        cszDriverFullPath: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = OpenSCManager(None, None, SC_MANAGER_ALL_ACCESS)
    if not schManager:
        return False

    schService = OpenService(schManager, cszDriverName, SERVICE_ALL_ACCESS)
    if not schService:
        CloseServiceHandle(schManager)
        return False

    svcStatus = SERVICE_STATUS()

    # 停止服务
    if ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
        if svcStatus.dwCurrentState != SERVICE_STOPPED:
            if not ControlService(schService, SERVICE_CONTROL_STOP, ctypes.byref(svcStatus)):
                CloseServiceHandle(schService)
                CloseServiceHandle(schManager)
                return False
            # 等待服务停止
            for i in range(10):
                if not ControlService(schService, SERVICE_CONTROL_INTERROGATE, ctypes.byref(svcStatus)):
                    break
                else:
                    if svcStatus.dwCurrentState == SERVICE_STOPPED:
                        break
                time.sleep(4)
            if svcStatus.dwCurrentState != SERVICE_STOPPED:
                CloseServiceHandle(schService)
                CloseServiceHandle(schManager)
                return False

    # 删除服务
    if not DeleteService(schService):
        CloseServiceHandle(schService)
        CloseServiceHandle(schManager)
        return False

    CloseServiceHandle(schService)
    CloseServiceHandle(schManager)
    return True

# 获取驱动名称的函数
def GetDriverName(driver_path):
    """
    从驱动文件路径中获取驱动名称
    参数:
        driver_path: 驱动文件的完整路径
    返回值:
        驱动名称（不含扩展名）
    """
    filename = os.path.basename(driver_path)
    name, ext = os.path.splitext(filename)
    return name

# 定义安装函数
def install(driver_path):
    """
    安装驱动服务
    参数:
        driver_path: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    driver_name = GetDriverName(driver_path)
    return InstallDriver(driver_name, driver_path)

# 定义启动函数
def start(driver_path):
    """
    启动驱动服务
    参数:
        driver_path: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    driver_name = GetDriverName(driver_path)
    return StartDriver(driver_name, driver_path)

# 定义停止函数
def stop(driver_path):
    """
    停止驱动服务
    参数:
        driver_path: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    driver_name = GetDriverName(driver_path)
    return StopDriver(driver_name, driver_path)

# 定义卸载函数
def uninstall(driver_path):
    """
    卸载驱动服务
    参数:
        driver_path: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    driver_name = GetDriverName(driver_path)
    return RemoveDriver(driver_name, driver_path)

class DxDriver:
    def __init__(self, driver_path):
        self.driver_path = driver_path

    def install(self):
        return install(self.driver_path)

    def start(self):
        return start(self.driver_path)

    def stop(self):
        return stop(self.driver_path)

    def uninstall(self):
        return uninstall(self.driver_path)

# 示例：安装驱动
if __name__ == '__main__':
    # r"D:\code\python\RuneLiteOne\dxGame\dx_lib\x64\dxkm.sys"
    while True:
        sys_path = input("请输入驱动路径,n退出:")
        if sys_path == "n":
            break
        if not os.path.exists(sys_path):
            print("文件不存在")
            continue

        while True:
            flag = input("请输入操作:\n1:安装驱动\2:启动驱动\3:停止驱动\4:卸载驱动\5:重新输入驱动路径\n")
            if flag == "5":
                break
            if flag == "1":
                is_ok = install(sys_path)
                print("驱动安装",is_ok)
            if flag == "2":
                is_ok = start(sys_path)
                print("启动驱动",is_ok)
            if flag == "3":
                is_ok = stop(sys_path)
                print("停止驱动",is_ok)
            if flag == "4":
                is_ok = uninstall(sys_path)
                print("卸载驱动",is_ok)