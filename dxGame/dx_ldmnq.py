# -*- coding: utf-8 -*-
import socket
import threading
import time

from dxGame import PyThread, print_log
from dxGame.dx_core import *
from dxGame.dx_config import ld_read_json,ld_write_json
from dxGame.dx_MiniOpenCV import MiniOpenCV
from dxGame.dx_jpeg import TurboJPEG

ANDROID_KEY_MAPPING = {
    "esc": "KEYCODE_ESC",
    "1": "KEYCODE_1",
    "2": "KEYCODE_2",
    "3": "KEYCODE_3",
    "4": "KEYCODE_4",
    "5": "KEYCODE_5",
    "6": "KEYCODE_6",
    "7": "KEYCODE_7",
    "8": "KEYCODE_8",
    "9": "KEYCODE_9",
    "0": "KEYCODE_0",
    "minus": "KEYCODE_MINUS",
    "equal": "KEYCODE_EQUAL",
    "backspace": "KEYCODE_BACKSPACE",
    "tab": "KEYCODE_TAB",
    "q": "KEYCODE_Q",
    "w": "KEYCODE_W",
    "e": "KEYCODE_E",
    "r": "KEYCODE_R",
    "t": "KEYCODE_T",
    "y": "KEYCODE_Y",
    "u": "KEYCODE_U",
    "i": "KEYCODE_I",
    "o": "KEYCODE_O",
    "p": "KEYCODE_P",
    "leftbrace": "KEYCODE_LEFTBRACE",
    "rightbrace": "KEYCODE_RIGHTBRACE",
    "enter": "KEYCODE_ENTER",
    "ctrl": "KEYCODE_LEFTCTRL",
    "a": "KEYCODE_A",
    "s": "KEYCODE_S",
    "d": "KEYCODE_D",
    "f": "KEYCODE_F",
    "g": "KEYCODE_G",
    "h": "KEYCODE_H",
    "j": "KEYCODE_J",
    "k": "KEYCODE_K",
    "l": "KEYCODE_L",
    "semicolon": "KEYCODE_SEMICOLON",
    "apostrophe": "KEYCODE_APOSTROPHE",
    "grave": "KEYCODE_GRAVE",
    "shift": "KEYCODE_LEFTSHIFT",
    "backslash": "KEYCODE_BACKSLASH",
    "z": "KEYCODE_Z",
    "x": "KEYCODE_X",
    "c": "KEYCODE_C",
    "v": "KEYCODE_V",
    "b": "KEYCODE_B",
    "n": "KEYCODE_N",
    "m": "KEYCODE_M",
    "comma": "KEYCODE_COMMA",
    "dot": "KEYCODE_DOT",
    "slash": "KEYCODE_SLASH",
    "rightshift": "KEYCODE_RIGHTSHIFT",
    "kpasterisk": "KEYCODE_KPASTERISK",
    "leftalt": "KEYCODE_LEFTALT",
    "space": "KEYCODE_SPACE",
    "capslock": "KEYCODE_CAPSLOCK",
    "f1": "KEYCODE_F1",
    "f2": "KEYCODE_F2",
    "f3": "KEYCODE_F3",
    "f4": "KEYCODE_F4",
    "f5": "KEYCODE_F5",
    "f6": "KEYCODE_F6",
    "f7": "KEYCODE_F7",
    "f8": "KEYCODE_F8",
    "f9": "KEYCODE_F9",
    "f10": "KEYCODE_F10",
    "numlock": "KEYCODE_NUMLOCK",
    "scrolllock": "KEYCODE_SCROLLLOCK",
    "kp7": "KEYCODE_KP7",
    "kp8": "KEYCODE_KP8",
    "kp9": "KEYCODE_KP9",
    "kpmminus": "KEYCODE_KPMINUS",
    "kp4": "KEYCODE_KP4",
    "kp5": "KEYCODE_KP5",
    "kp6": "KEYCODE_KP6",
    "kpplus": "KEYCODE_KPPLUS",
    "kp1": "KEYCODE_KP1",
    "kp2": "KEYCODE_KP2",
    "kp3": "KEYCODE_KP3",
    "kp0": "KEYCODE_KP0",
    "kpdot": "KEYCODE_KPDOT",
    "zenkakuhankaku": "KEYCODE_ZENKAKUHANKAKU",
    "102nd": "KEYCODE_102ND",
    "f11": "KEYCODE_F11",
    "f12": "KEYCODE_F12",
    "ro": "KEYCODE_RO",
    "katakana": "KEYCODE_KATAKANA",
    "hiragana": "KEYCODE_HIRAGANA",
    "henkan": "KEYCODE_HENKAN",
    "katakanahiragana": "KEYCODE_KATAKANAHIRAGANA",
    "muhenkan": "KEYCODE_MUHENKAN",
    "kpjcomma": "KEYCODE_KPJPCOMMA",
    "kpenter": "KEYCODE_KPENTER",
    "rightctrl": "KEYCODE_RIGHTCTRL",
    "kpslash": "KEYCODE_KPSLASH",
    "sysrq": "KEYCODE_SYSRQ",
    "rightalt": "KEYCODE_RIGHTALT",
    "linefeed": "KEYCODE_LINEFEED",
    "home": "KEYCODE_HOME",
    "up": "KEYCODE_UP",
    "pageup": "KEYCODE_PAGEUP",
    "left": "KEYCODE_LEFT",
    "right": "KEYCODE_RIGHT",
    "end": "KEYCODE_END",
    "down": "KEYCODE_DOWN",
    "pagedown": "KEYCODE_PAGEDOWN",
    "insert": "KEYCODE_INSERT",
    "delete": "KEYCODE_DELETE",
    "macro": "KEYCODE_MACRO",
    "mute": "KEYCODE_MUTE",
    "volumedown": "KEYCODE_VOLUMEDOWN",
    "volumeup": "KEYCODE_VOLUMEUP",
    "power": "KEYCODE_POWER",
    "kpequal": "KEYCODE_KPEQUAL",
    "kpplusminus": "KEYCODE_KPPLUSMINUS",
    "pause": "KEYCODE_PAUSE",
    "scale": "KEYCODE_SCALE",
    "kpcomma": "KEYCODE_KPCOMMA",
    "hangeul": "KEYCODE_HANGEUL",
    "hanja": "KEYCODE_HANJA",
    "yen": "KEYCODE_YEN",
    "leftmeta": "KEYCODE_LEFTMETA",
    "rightmeta": "KEYCODE_RIGHTMETA",
    "compose": "KEYCODE_COMPOSE",
    "stop": "KEYCODE_STOP",
    "again": "KEYCODE_AGAIN",
    "props": "KEYCODE_PROPS",
    "undo": "KEYCODE_UNDO",
    "front": "KEYCODE_FRONT",
    "copy": "KEYCODE_COPY",
    "open": "KEYCODE_OPEN",
    "paste": "KEYCODE_PASTE",
    "find": "KEYCODE_FIND",
    "cut": "KEYCODE_CUT",
    "help": "KEYCODE_HELP",
    "menu": "KEYCODE_MENU",
    "calc": "KEYCODE_CALC",
    "setup": "KEYCODE_SETUP",
    "sleep": "KEYCODE_SLEEP",
    "wakeup": "KEYCODE_WAKEUP",
    "file": "KEYCODE_FILE",
    "sendfile": "KEYCODE_SENDFILE",
    "deletefile": "KEYCODE_DELETEFILE",
    "xfer": "KEYCODE_XFER",
    "prog1": "KEYCODE_PROG1",
    "prog2": "KEYCODE_PROG2",
    "www": "KEYCODE_WWW",
    "msdos": "KEYCODE_MSDOS",
    "coffee": "KEYCODE_COFFEE",
    "rotate_display": "KEYCODE_ROTATE_DISPLAY",
    "cyclewindows": "KEYCODE_CYCLEWINDOWS",
    "mail": "KEYCODE_MAIL",
    "bookmarks": "KEYCODE_BOOKMARKS",
    "computer": "KEYCODE_COMPUTER",
    "back": "KEYCODE_BACK",
    "forward": "KEYCODE_FORWARD",
    "closecd": "KEYCODE_CLOSECD",
    "ejectcd": "KEYCODE_EJECTCD",
    "ejectclosecd": "KEYCODE_EJECTCLOSECD",
    "nextsong": "KEYCODE_NEXTSONG",
    "playpause": "KEYCODE_PLAYPAUSE",
    "previoussong": "KEYCODE_PREVIOUSSONG",
    "stopcd": "KEYCODE_STOPCD",
    "record": "KEYCODE_RECORD",
    "rewind": "KEYCODE_REWIND",
    "phone": "KEYCODE_PHONE",
    "iso": "KEYCODE_ISO",
    "config": "KEYCODE_CONFIG",
    "homepage": "KEYCODE_HOMEPAGE",
    "refresh": "KEYCODE_REFRESH",
    "exit": "KEYCODE_EXIT",
    "move": "KEYCODE_MOVE",
    "edit": "KEYCODE_EDIT",
    "scrollup": "KEYCODE_SCROLLUP",
    "scrolldown": "KEYCODE_SCROLLDOWN",
    "kpleftparen": "KEYCODE_KPLEFTPAREN",
    "kprightparen": "KEYCODE_KPRIGHTPAREN",
    "new": "KEYCODE_NEW",
    "redo": "KEYCODE_REDO",
    "f13": "KEYCODE_F13",
    "f14": "KEYCODE_F14",
    "f15": "KEYCODE_F15",
    "f16": "KEYCODE_F16",
    "f17": "KEYCODE_F17",
    "f18": "KEYCODE_F18",
    "f19": "KEYCODE_F19",
    "f20": "KEYCODE_F20",
    "f21": "KEYCODE_F21",
    "f22": "KEYCODE_F22",
    "f23": "KEYCODE_F23",
    "f24": "KEYCODE_F24"
}
"""
输入:getevent -p,可以获取如下信息

        添加设备 1: /dev/input
        root/event4
          名称:     "mouse"（鼠标）
          事件:
            KEY (

        添加设备

        添加设备
        0001): BTN_MOUSE             BTN_RIGHT             BTN_MIDDLE
            REL (0002): REL_X                 REL_Y                 REL_WHEEL
          输入属性:
            INPUT_PROP_DIRECT
        无法获取 /dev/input/mouse1 的驱动版本，非打字机类型

        添加设备

        添加设备

        添加设备
        2: /dev/input/event3
          名称:     "gpio"
          事件:
            KEY (
          名称:     0001): KEY_VOLUMEDOWN        KEY_VOLUMEUP
            SW  (
          事件:
            0005): SW_LID
          输入属性:
            <无>

        添加设备 3: /dev/input/event2
          名称:     "input"
          事件:
            KEY (0001): KEY_ESC               KEY_1                 KEY_2                 KEY_3
                        KEY_4                 KEY_5                 KEY_6                 KEY_7
                        KEY_8                 KEY_9                 KEY_0                 KEY_MINUS
                        KEY_EQUAL             KEY_BACKSPACE         KEY_TAB               KEY_Q
                        KEY_W                 KEY_E                 KEY_R                 KEY_T
                        KEY_Y                 KEY_U                 KEY_I                 KEY_O
                        KEY_P                 KEY_LEFTBRACE         KEY_RIGHTBRACE        KEY_ENTER
                        KEY_LEFTCTRL          KEY_A                 KEY_S                 KEY_D
                        KEY_F                 KEY_G                 KEY_H                 KEY_J
                        KEY_K                 KEY_L                 KEY_SEMICOLON         KEY_APOSTROPHE
                        KEY_GRAVE             KEY_LEFTSHIFT         KEY_BACKSLASH         KEY_Z
                        KEY_X                 KEY_C                 KEY_V                 KEY_B
                        KEY_N                 KEY_M                 KEY_COMMA             KEY_DOT
                        KEY_SLASH             KEY_RIGHTSHIFT        KEY_KPASTERISK        KEY_LEFTALT
                        KEY_SPACE             KEY_CAPSLOCK          KEY_F1                KEY_F2
                        KEY_F3                KEY_F4                KEY_F5                KEY_F6
                        KEY_F7                KEY_F8                KEY_F9                KEY_F10
                        KEY_NUMLOCK           KEY_SCROLLLOCK        KEY_KP7               KEY_KP8
                        KEY_KP9               KEY_KPMINUS           KEY_KP4               KEY_KP5
                        KEY_KP6               KEY_KPPLUS            KEY_KP1               KEY_KP2
                        KEY_KP3               KEY_KP0               KEY_KPDOT             0054
                        KEY_ZENKAKUHANKAKU    KEY_102ND             KEY_F11               KEY_F12
                        KEY_RO                KEY_KATAKANA          KEY_HIRAGANA          KEY_HENKAN
                        KEY_KATAKANAHIRAGANA  KEY_MUHENKAN          KEY_KPJPCOMMA         KEY_KPENTER
                        KEY_RIGHTCTRL         KEY_KPSLASH           KEY_SYSRQ             KEY_RIGHTALT
                        KEY_LINEFEED          KEY_HOME              KEY_UP                KEY_PAGEUP
                        KEY_LEFT              KEY_RIGHT             KEY_END               KEY_DOWN
                        KEY_PAGEDOWN          KEY_INSERT            KEY_DELETE            KEY_MACRO
                        KEY_MUTE              KEY_VOLUMEDOWN        KEY_VOLUMEUP          KEY_POWER
                        KEY_KPEQUAL           KEY_KPPLUSMINUS       KEY_PAUSE             KEY_SCALE
                        KEY_KPCOMMA           KEY_HANGEUL           KEY_HANJA             KEY_YEN
                        KEY_LEFTMETA          KEY_RIGHTMETA         KEY_COMPOSE           KEY_STOP
                        KEY_AGAIN             KEY_PROPS             KEY_UNDO              KEY_FRONT
                        KEY_COPY              KEY_OPEN              KEY_PASTE             KEY_FIND
                        KEY_CUT               KEY_HELP              KEY_MENU              KEY_CALC
                        KEY_SETUP             KEY_SLEEP             KEY_WAKEUP            KEY_FILE
                        KEY_SENDFILE          KEY_DELETEFILE        KEY_XFER              KEY_PROG1
                        KEY_PROG2             KEY_WWW               KEY_MSDOS             KEY_COFFEE
                        KEY_ROTATE_DISPLAY    KEY_CYCLEWINDOWS      KEY_MAIL              KEY_BOOKMARKS
                        KEY_COMPUTER          KEY_BACK              KEY_FORWARD           KEY_CLOSECD
                        KEY_EJECTCD           KEY_EJECTCLOSECD      KEY_NEXTSONG          KEY_PLAYPAUSE
                        KEY_PREVIOUSSONG      KEY_STOPCD            KEY_RECORD            KEY_REWIND
                        KEY_PHONE             KEY_ISO               KEY_CONFIG            KEY_HOMEPAGE
                        KEY_REFRESH           KEY_EXIT              KEY_MOVE              KEY_EDIT
                        KEY_SCROLLUP          KEY_SCROLLDOWN        KEY_KPLEFTPAREN       KEY_KPRIGHTPAREN
                        KEY_NEW               KEY_REDO              KEY_F13               KEY_F14
                        KEY_F15               KEY_F16               KEY_F17               KEY_F18
                        KEY_F19               KEY_F20               KEY_F21               KEY_F22
                        KEY_F23               KEY_F24

        00c3                  00c4
                        00c5                  00c6

        00c7                  KEY_PLAYCD
                        KEY_PAUSECD           KEY_PROG3             KEY_PROG4             KEY_DASHBOARD
                        KEY_SUSPEND           KEY_CLOSE             KEY_PLAY              KEY_FASTFORWARD
                        KEY_BASSBOOST         KEY_PRINT             KEY_HP                KEY_CAMERA
                        KEY_SOUND             KEY_QUESTION          KEY_EMAIL             KEY_CHAT
                        KEY_SEARCH            KEY_CONNECT           KEY_FINANCE           KEY_SPORT
                        KEY_SHOP              KEY_ALTERASE          KEY_CANCEL            KEY_BRIGHTNESSDOWN
                        KEY_BRIGHTNESSUP      KEY_MEDIA             KEY_SWITCHVIDEOMODE   KEY_KBDILLUMTOGGLE
                        KEY_KBDILLUMDOWN      KEY_KBDILLUMUP        KEY_SEND              KEY_REPLY
                        KEY_FORWARDMAIL       KEY_SAVE              KEY_DOCUMENTS         KEY_BATTERY
                        KEY_BLUETOOTH         KEY_WLAN              KEY_UWB               KEY_UNKNOWN
                        KEY_VIDEO_NEXT        KEY_VIDEO_PREV        KEY_BRIGHTNESS_CYCLE  KEY_BRIGHTNESS_AUTO
                        KEY_DISPLAY_OFF       KEY_WWAN              KEY_RFKILL            KEY_MICMUTE
                        00f9                  00fa                  00fb                  00fc
                        00fd                  00fe                  00ff                  BTN_TOOL_FINGER
                        BTN_TOUCH
            REL (0002): REL_HWHEEL            REL_WHEEL
            ABS (0003): ABS_MT_SLOT           : value 0, min 0, max 15, fuzz 0, flat

        0, resolution 0
                        ABS_MT_POSITION_X     : value 0, min 0, max 959, fuzz 0, flat 0, resolution 0
                        ABS_MT_POSITION_Y     : value 0, min 0, max 539, fuzz
                        K
                        00c5                  00c6                  00c7
                        00c5                  00c6                  00c7

                        00c5
                        K

                        00f9                  00fa                  00fb                  00fc
                        00fd                  00fe                  00ff
                        00f9                  00fa                  00fb                  00fc
                        00fd

                        00f9
        0, flat 0, resolution 0
                        ABS_MT_TRACKING_ID    : value

        0, min 0, max 65535, fuzz 0, flat 0, resolution 0
                        ABS_MT_PRESSURE       : value
                        ABS_MT_PRESSURE


        0, min 0, max 2, fuzz 0, flat 0, resolution 0
          输入属性:
            INPUT_PROP_DIRECT
        无法获取 /dev/
          输入属性:
            INPUT_PROP_DIRECT
        无法获取 /dev/i

          输入属性:
            INP
        input/mouse0 的驱动版本，非打字机类型

        添加设备 4: /dev/input/event1
          名称:     "Sleep Button"（睡眠按钮）
          事件:
            KEY (
          事件:

        0001): KEY_SLEEP
          输入属性:
            <无>
        无法获取 /dev/

        input/mice 的驱动版本，非打字机类型

        添加设备 5: /dev/input/event0
          名称:
          名称:
        "Power Button"（电源按钮）
          事件:
            KEY (

        0001): KEY_POWER
          输入属性:
            <无>
          输入
"""


class DnPlay:
    def __init__(self, lst):
        self.index = int(lst[0])
        self.name = lst[1]
        self.father_hwnd = int(lst[2])
        self.hwnd = int(lst[3])
        self.isRunning = int(lst[4])
        self.father_pid = int(lst[5])
        self.pid = int(lst[6])
        self.width = int(lst[7])
        self.height = int(lst[8])
        self.dpi = int(lst[9])


class 雷电模拟器终端():
    def __init__(self, 雷电路径):
        # 判断雷电路径是文件夹还是文件
        if os.path.isdir(雷电路径):
            self.console_path = 雷电路径
        else:
            self.console_path = os.path.dirname(雷电路径)
        self.console = self.console_path + "\\ldconsole.exe"  # 和dnonsole的区别是一个显示，一个隐藏,主要功能是操作模拟器
        self.ld = self.console_path + "\\ld.exe "  # 主要功能是封装好了一些模拟器内部操作的实现,不需要在使用adb命令
        self.配置目录 = self.console_path + "\\vms\\config"

        self.temp_dir = None  # 缓存目录

    # 管道方式执行cmd命令
    def _run_command(self, command, encode=True):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # 读取输出并手动解码
        stdout, stderr = process.communicate()
        if encode:
            # 尝试使用 UTF-8 解码
            try:
                stdout_decoded = stdout.decode('utf-8')
            except UnicodeDecodeError:
                stdout_decoded = stdout.decode('gbk')
            # 尝试使用 UTF-8 解码错误输出
            try:
                stderr_decoded = stderr.decode('utf-8')
            except UnicodeDecodeError:
                stderr_decoded = stderr.decode('gbk')
            res = stdout_decoded.strip(), stderr_decoded.strip()
        else:
            res = stdout, stderr
        return res

    # 执行ldconsole命令
    def _run_console(self, index=None, name=None, cmd=None, encode=True, **kwargs):
        kw = ""
        for k, v in kwargs.items():
            if not v is None:
                kw += f" --{k} {v}"
        if not index is None:
            if cmd == "copy":
                cmd = f"{self.console} {cmd} --from {index}"
            else:
                cmd = f"{self.console} {cmd} --index {index}{kw}"

        elif name:
            cmd = f"{self.console} {cmd} --name {name}{kw}"
        else:
            cmd = f"{self.console} {cmd} {kw}"
        res = self._run_command(cmd, encode=encode)
        if res[0]:
            return res[0]
        else:
            self.error = res[1]

    def _run_ld(self, index, command):
        pass

    def 关闭模拟器(self, index=None):
        return self._run_console(index, cmd="quit")

    def 关闭所有模拟器(self):
        return self._run_console(None, cmd="quitall")

    def 启动模拟器(self, index):
        return self._run_console(index, cmd="launch")

    def 重启模拟器(self, index):
        return self._run_console(index, cmd="reboot")

    def 获取所有模拟器实例(self, name_output_list=False):
        lst = self._run_console(None, cmd="list")
        lst = lst.split("\r\n")
        name_lst = []
        for name in lst:
            if name_output_list and name in name_output_list:
                continue
            name_lst.append(name)
        return name_lst

    def 获取所有正在运行的模拟器实例(self):
        return self._run_console(None, cmd="runninglist")

    def 获取模拟器是否运行(self, index):
        return self._run_console(index, cmd="isrunning")

    def 获取所有模拟器实例2(self, 排序列表=()):
        res = self._run_console(cmd="list2")
        if not res:
            return []
        res = res.split("\n")
        res = [i.strip().split(",") for i in res]
        new_res = []
        for lst in res:
            if int(lst[0]) in 排序列表:
                continue
            dp = DnPlay(lst)
            new_res.append(dp)
        return new_res

    def 添加模拟器实例(self, name):
        return self._run_console(name=name, cmd="add")

    def 复制模拟器实例(self, index):
        return self._run_console(index=index, cmd="copy")

    def 删除模拟器(self, index):
        return self._run_console(index=index, cmd="remove")

    def 设置模拟器名称(self, index, title):
        return self._run_console(index=index, cmd="rename", title=title)

    def 设置模拟器属性(self, index,
                       resolution=None,
                       cpu=None,
                       memory=None,
                       manufacturer=None,
                       model=None,
                       pnumber=None,
                       imei=None,
                       imsi=None,
                       simserial=None,
                       androidid=None,
                       mac=None,
                       autorotate=None,
                       lockwindow=None,
                       root=None):
        """
        :param index: 雷电ID
        :param resolution: 分辨率  w,h,dpi
        :param cpu: cpu数量   1 | 2 | 3 | 4
        :param memory: 内存多少M 256 | 512 | 768 | 1024 | 1536 | 2048 | 4096 | 8192
        :param manufacturer: 制造商 asus
        :param model: 型号 ASUS_Z00DUO
        :param pnumber: 手机号 13800000000
        :param imei: imei码 auto | 865166023949731
        :param imsi: imsi码 auto | 460000000000000
        :param simserial: SIM卡序列号 auto | 89860000000000000000
        :param androidid: Android ID    auto | 0123456789abcdef
        :param mac: MAC地址   auto | 000000000000
        :param autorotate: 自动旋转     1 | 0
        :param lockwindow: 锁定窗口     1 | 0
        :param root: Root权限     1 | 0
        :return:
        """
        return self._run_console(index=index,
                                 cmd="modify",
                                 resolution=resolution,
                                 cpu=cpu,
                                 memory=memory,
                                 manufacturer=manufacturer,
                                 model=model,
                                 pnumber=pnumber,
                                 imei=imei,
                                 imsi=imsi,
                                 simserial=simserial,
                                 androidid=androidid,
                                 mac=mac,
                                 autorotate=autorotate,
                                 lockwindow=lockwindow,
                                 root=root)

    def 安装app(self, index, filename):
        return self._run_console(index, cmd="installapp", filename=filename)

    def 卸载app(self, index, packagename):
        return self._run_console(index, cmd="uninstallapp", packagename=packagename)

    def 启动app(self, index, packagename):
        return self._run_console(index, cmd="runapp", packagename=packagename)

    def 停止app(self, index, packagename):
        return self._run_console(index, cmd="killapp", packagename=packagename)

    def 设置模拟器的位置定位(self, index, LLI):
        return self._run_console(index, cmd="locate", LLI=LLI)

    # 如果ADB掉线则不可以使用
    def ADB(self, index, command):
        command = f'"{command}"'
        return self._run_console(index, cmd="adb", command=command, encode=False)

    def 设置系统属性(self, index, value):
        return self._run_console(index, cmd="setprop", value=value)

    def 获取系统属性(self, index):
        res = self._run_console(index, cmd="getprop")
        res = res.split("\n")
        res = [x.strip() for x in res]
        return res

    def 备份模拟器实例(self, index, file):
        return self._run_console(index, cmd="backup", file=file)

    def 恢复模拟器实例(self, index, file):
        return self._run_console(index, cmd="restore", file=file)

    def 动作(self, index, key, value):
        return self._run_console(index, cmd="action", key=key, value=value)

    def 下载文件(self, index, remote, local):
        return self._run_console(index, cmd="pull", remote=remote, local=local)

    def 上传文件(self, index, remote, local):
        return self._run_console(index, cmd="push", remote=remote, local=local)

    def 备份应用的数据(self, index, packagename, file):
        return self._run_console(index, cmd="backupapp", packagename=packagename, file=file)

    def 恢复应用的数据(self, index, packagename, file):
        return self._run_console(index, cmd="restoreapp", packagename=packagename, file=file)

    def 设置全局配置(self, fps, audio, fastplay, cleanmode):
        """
        :param fps: fps 0~60
        :param audio: 声音 1 |0
        :param fastplay: 用于控制是否启用快速播放模式。 1|0
        :param cleanmode:是否启用“清洁模式”或“简洁模式” 1|0
        :return:
        """
        return self._run_console(cmd="globalsetting", fps=fps, audio=audio, fastplay=fastplay, cleanmode=cleanmode)

    def 启动app_调试模式(self, index, packagename):
        return self._run_console(index, cmd="launchex", packagename=packagename)

    def 获取自动化操作记录(self, index):
        return self._run_console(index, cmd="operatelist")

    def 导出自动化操作记录(self, index, file):
        """
        :param index: 雷电序号
        :param file: 导出json文本路径
        :return:
        """
        return self._run_console(index, cmd="operateinfo", file=file)

    def 添加自动化操作记录(self, index, countent):
        """
        最好是先用雷电自动化操作导出后，测试没问题在脚本的形式添加。
        这个命令用于向指定的模拟器实例添加操作记录。你需要通过模 索引 (--index mnq_idx) 来指定实例，
        并通过 --content 参数传入一段 JSON 字符串，表示要记录的操作内容。
        :param index: 雷电序号
        :param countent: json序列，即字符串形式的字典  '{"action":"click","coordinates":{"x":100,"y":200}}'
        :return:
        """
        return self._run_console(index, cmd="operateinfo", countent=countent)

    def 排序模拟器(self, index):
        return self._run_console(index, cmd="sort")
    # ==================================动作拓展命令==============================================================

    # ===================================额外拓展命令=============================================================


_LD_DEBUG = False


class LD:
    def __init__(self, dn: 雷电模拟器终端, index):
        self.dn = dn
        self.ld = dn.ld
        self.index = index
        self.console = dn.console
        self.配置路径 = self.dn.配置目录 + f"\\leidian{index}.config"
        self.配置字典 = ld_read_json(self.配置路径)
        self._pic_time = None  # 截图文件时间
        self._xml_time = None
        self._安装app_间隔时间字典 = {}  # 用于安装app后,下次在安装时的间隔,防止重复安装app
        self.__app_install_interval = 10
        self.last_error = ""

    def __getattribute__(self, item):
        """
        执行函数之前，先更新函数名称到日志中。。。
        """
        ret = super().__getattribute__(item)
        if _LD_DEBUG and str(type(ret)) in ["<class 'function'>", "<class 'method'>"] and ret.__name__ != "wrapper":
            def res(*args, **kwargs):
                print(f"{ret.__name__}({args=}, {kwargs=}")
                return ret(*args, **kwargs)

            return res
        else:
            return ret

    def 更新配置字典(self):
        self.配置字典 = ld_read_json(self.配置路径)

    def set_debug(self, flag: bool):
        global _LD_DEBUG
        _LD_DEBUG = flag

    def _run_command(self, command, encode=True):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # 读取输出并手动解码
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError
        if encode:
            # 尝试使用 UTF-8 解码
            try:
                stdout_decoded = stdout.decode('utf-8')
            except UnicodeDecodeError:
                stdout_decoded = stdout.decode('gbk')
            # 尝试使用 UTF-8 解码错误输出
            try:
                stderr_decoded = stderr.decode('utf-8')
            except UnicodeDecodeError:
                stderr_decoded = stderr.decode('gbk')
            res = stdout_decoded.strip(), stderr_decoded.strip()
            if "not found" in res[0] or "not found" in res[1]:
                print("模拟器未链接，请检查是否启动")
                res = "", "模拟器未链接，请检查是否启动"
        else:
            res = stdout, stderr
            if b"not found" in stdout or b"not found" in stderr:
                print("模拟器未链接，请检查是否启动")
                res = "", "模拟器未链接，请检查是否启动"
        self.last_error = res[1]
        return res[0]

    # 执行ldconsole命令
    def _run_console(self, index=None, name=None, cmd=None, encode=True, **kwargs):
        kw = ""
        for k, v in kwargs.items():
            if not v is None:
                kw += f" --{k} {v}"
        if not index is None:
            if cmd == "copy":
                cmd = f"{self.console} {cmd} --from {index}"
            else:
                cmd = f"{self.console} {cmd} --index {index}{kw}"
        elif name:
            cmd = f"{self.console} {cmd} --name {name}{kw}"
        else:
            cmd = f"{self.console} {cmd} {kw}"
        return self._run_command(cmd, encode=encode)

    def _run_ld(self, cmd, encode=True):
        cmd = f'{self.ld} -s {self.index} "{cmd}"'
        res = self._run_command(cmd, encode=encode)
        return res

    def 关闭模拟器(self):
        return self._run_console(self.index, cmd="quit")

    def 关闭所有模拟器(self):
        return self._run_console(None, cmd="quitall")

    def 启动模拟器(self):
        return self._run_console(self.index, cmd="launch")

    def 重启模拟器(self):
        return self._run_console(self.index, cmd="reboot")

    def 获取所有模拟器实例(self):
        return self._run_console(None, cmd="list")

    def 获取所有正在运行的模拟器实例(self):
        return self._run_console(None, cmd="runninglist")

    def 获取模拟器是否运行(self):
        return self._run_console(self.index, cmd="isrunning")

    def 获取所有模拟器实例2(self, 排序列表=()):
        res = self._run_console(cmd="list2")
        res = res.split("\n")
        res = [line.strip() for line in res]
        res = [i.strip().split(",") for i in res]
        new_res = []
        for lst in res:
            if not int(lst[0]) in 排序列表:
                new_res.append(DnPlay(lst))
        return new_res

    def 获取模拟器名称(self):
        res = self.获取所有模拟器实例2()
        for i in res:
            if i.index == self.index:
                return i.name
        return ""

    def 添加模拟器实例(self, name):
        return self._run_console(name=name, cmd="add")

    def 复制模拟器实例(self):
        return self._run_console(index=self.index, cmd="copy")

    def 删除模拟器(self):
        return self._run_console(index=self.index, cmd="remove")

    def 设置模拟器名称(self, title):
        return self._run_console(index=self.index, cmd="rename", title=title)

    def 设置模拟器属性(self,
                       resolution=None,
                       cpu=None,
                       memory=None,
                       manufacturer=None,
                       model=None,
                       pnumber=None,
                       imei=None,
                       imsi=None,
                       simserial=None,
                       androidid=None,
                       mac=None,
                       autorotate=None,
                       lockwindow=None,
                       root=None):
        """
        注意!!!!!,关闭模拟器设置才生效,如果模拟器已启动是不生效的,重启也不生效,必须先关闭在设置
        :param resolution: 分辨率  w,h,dpi
        :param cpu: cpu数量   1 | 2 | 3 | 4
        :param memory: 内存多少M 256 | 512 | 768 | 1024 | 1536 | 2048 | 4096 | 8192
        :param manufacturer: 制造商 asus
        :param model: 型号 ASUS_Z00DUO
        :param pnumber: 手机号 13800000000
        :param imei: imei码 auto | 865166023949731
        :param imsi: imsi码 auto | 460000000000000
        :param simserial: SIM卡序列号 auto | 89860000000000000000
        :param androidid: Android ID    auto | 0123456789abcdef
        :param mac: MAC地址   auto | 000000000000
        :param autorotate: 自动旋转     1 | 0
        :param lockwindow: 锁定窗口     1 | 0
        :param root: Root权限     1 | 0
        :return:
        """
        return self._run_console(index=self.index,
                                 cmd="modify",
                                 resolution=resolution,
                                 cpu=cpu,
                                 memory=memory,
                                 manufacturer=manufacturer,
                                 model=model,
                                 pnumber=pnumber,
                                 imei=imei,
                                 imsi=imsi,
                                 simserial=simserial,
                                 androidid=androidid,
                                 mac=mac,
                                 autorotate=autorotate,
                                 lockwindow=lockwindow,
                                 root=root)

    def 安装app(self, filename):
        print("安装app")
        if not self._安装app_间隔时间字典.get(filename) or time.time() > self._安装app_间隔时间字典[filename]:
            self._安装app_间隔时间字典[filename] = time.time() + self.__app_install_interval
            return self._run_console(self.index, cmd="installapp", filename=filename)

    def 安装app并等待图片显示(self, filename, func):
        # self.返回主屏幕()
        self.安装app(filename)
        print("安装app并等待图片显示中...%s"%filename)
        for i in range(30):
            if func():
                print("安装app并等待图片%s"%filename)
                return True
            time.sleep(2)
            print("安装app中...%s" % filename)
        return False

    def 卸载app(self, packagename):
        return self._run_console(self.index, cmd="uninstallapp", packagename=packagename)

    def 启动app(self, packagename):
        return self._run_console(self.index, cmd="runapp", packagename=packagename)

    def 停止app(self, packagename):
        for i in range(10):
            self._run_console(self.index, cmd="killapp", packagename=packagename)
            time.sleep(0.5)
            if not self.获取app是否显示(packagename):
                break

    def 获取app是否显示(self,packagename):
        result = self.ADB(f"dumpsys activity activities | grep mResumedActivity")
        return packagename in result

    def 获取app是否运行(self,packagename):
        result = self.ADB(f"dumpsys window windows | grep -E '{packagename}'")
        return packagename in result

    def 获取app包名列表(self):
        res = self._run_ld("pm list packages")
        if not res:
            return []

        res_list = res.split("\n")
        res_list = [x.strip() for x in res_list]
        res_list = [x[8:] if "package:" in x else x for x in res_list]
        return res_list

    def 获取app包名列表_仅用户安装(self):
        res = self._run_ld("pm list packages -3")
        if not res:
            return []

        res_list = res.split("\n")
        res_list = [x.strip() for x in res_list]
        res_list = [x[8:] if "package:" in x else x for x in res_list]
        return res_list

    def 设置模拟器的位置定位(self, LLI):
        return self._run_console(self.index, cmd="locate", LLI=LLI)

    def ADB(self, command):  # 不连接也能用
        return self._run_ld(command)

    def ADBconsolo(self, command):  # ADB命令,链接才能用
        return self._run_console(self.index, cmd="adb", command=f'"{command}"')

    def 设置系统属性(self, value):
        return self._run_console(self.index, cmd="setprop", value=value)

    def 获取系统属性(self):
        res = self._run_console(self.index, cmd="getprop")
        res = res.split("\n")
        res = [x.strip() for x in res]
        return res

    def 备份模拟器实例(self, file):
        return self._run_console(self.index, cmd="backup", file=file)

    def 恢复模拟器实例(self, file):
        return self._run_console(self.index, cmd="restore", file=file)

    def 动作(self, key, value):
        return self._run_console(self.index, cmd="action", key=key, value=value)

    def 下载文件(self, remote, local):
        return self._run_console(self.index, cmd="pull", remote=remote, local=local)

    def 上传文件(self, remote, local):
        return self._run_console(self.index, cmd="push", remote=remote, local=local)

    def 备份应用的数据(self, packagename, file):
        return self._run_console(self.index, cmd="backupapp", packagename=packagename, file=file)

    def 恢复应用的数据(self, packagename, file):
        return self._run_console(self.index, cmd="restoreapp", packagename=packagename, file=file)

    def 设置全局配置(self, fps, audio, fastplay, cleanmode):
        """
        :param fps: fps 0~60
        :param audio: 声音 1 |0
        :param fastplay: 用于控制是否启用快速播放模式。 1|0
        :param cleanmode:是否启用“清洁模式”或“简洁模式” 1|0
        :return:
        """
        return self._run_console(cmd="globalsetting", fps=str(fps), audio=str(audio), fastplay=str(fastplay), cleanmode=str(cleanmode))

    def 启动app_调试模式(self, packagename):
        return self._run_console(self.index, cmd="launchex", packagename=packagename)

    def 获取自动化操作记录(self):
        return self._run_console(self.index, cmd="operatelist")

    def 导出自动化操作记录(self, file):
        """
        :param index: 雷电序号
        :param file: 导出json文本路径
        :return:
        """
        return self._run_console(self.index, cmd="operateinfo", file=file)

    def 添加自动化操作记录(self, countent):
        """
        最好是先用雷电自动化操作导出后，测试没问题在脚本的形式添加。
        这个命令用于向指定的模拟器实例添加操作记录。你需要通过模 索引 (--index mnq_idx) 来指定实例，
        并通过 --content 参数传入一段 JSON 字符串，表示要记录的操作内容。
        :param index: 雷电序号
        :param countent: json序列，即字符串形式的字典  '{"action":"click","coordinates":{"x":100,"y":200}}'
        :return:
        """
        return self._run_console(self.index, cmd="operateinfo", countent=countent)

    def 截图(self, file=None):
        # 获取上一次图片时间,截图后在比对,如果时间不一致,则截图成功
        pic = self.配置字典.get("statusSettings.sharedPictures")
        if not pic:
            self.配置字典 = ld_read_json(self.配置路径)
            return b""
        pic = os.path.join(pic, f"apk_scr{self.index}.png")
        if os.path.exists(pic):
            pic_time = os.path.getmtime(pic)
        else:
            pic_time = ""
        command = f"screencap -p /sdcard/Pictures/apk_scr{self.index}.png"
        self.ADB(command)
        if self.last_error:
            return b""

        s = time.time()
        while True:
            if time.time() - s > 5:
                return b""
            time.sleep(0.01)
            if os.path.exists(pic) and os.path.getmtime(pic) != pic_time:
                self._pic_time = os.path.getmtime(pic)
                break
        with open(pic, "rb") as fp:
            fp_wb = fp.read()
        if file:
            with open(file, "wb") as fp:
                fp.write(fp_wb)
        return fp_wb

    def 排序模拟器(self):
        return self._run_console(cmd="sortWnd")

    def 点击(self, x, y, down_delay=0, interval=0):
        if down_delay > 0:
            cmd = f"input swipe {x} {y} {x} {y} {down_delay*1000}"
        else:
            cmd = f"input tap {x} {y}"
        res = self._run_ld(cmd=cmd)
        time.sleep(interval)
        return res

    def 按键(self, key):
        code = ANDROID_KEY_MAPPING.get(key.lower())
        return self._run_ld(f"input keyevent {code}")

    def 滑动(self, x1, y1, x2, y2, down_delay=1):
        return self._run_ld(f"input swipe {x1} {y1} {x2} {y2} {int(down_delay * 1000)}")

    def 输入(self, text):  # 不支持中文、换行,稳定不掉线
        return self._run_ld(f"input text {text}")

    def 输入2(self, text):  # 支持中文
        return self.动作(key="call.input", value=text)

    # ===================================额外拓展命令=============================================================
    def 获取分辨率(self):
        command = "wm size"
        result = self.ADB(command)
        if result and "size" in result:
            result = result.strip()  # 返回例如 'Physical size: 1080x1920'
            result = result.split("size: ")[1].split("x")
            result = [int(x) for x in result]
            return result
        print("未能获取分辨率")
        return ''

    # 设置or复制文本到剪贴板
    def 设置文本到剪贴板(self, text):
        cmd = "am startservice ca.zgrs.clipper/.ClipboardService"
        self._run_ld(cmd)
        cmd_clear_clipboard = 'am broadcast -a clipper.clear'
        self._run_ld(cmd_clear_clipboard)
        cmd = f'am broadcast -a clipper.set -e text "{text}"'
        result = self._run_ld(cmd)
        return result

    def 获取剪贴板文本(self):
        return self._run_ld("am broadcast -a clipper.get")

    def 粘贴(self, index, text, flag=0, hwnd=None):
        if flag == 0:
            import win32clipboard, win32con, win32gui
            if not hwnd:
                hwnd = self.获取句柄(index)[1]
            ctypes.windll.user32.SetActiveWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            for i in range(10):
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    break
                except:
                    print(f"异常 {hwnd}")
                    time.sleep(0.1)

                self._run_ld("input keyevent KEYCODE_PASTE")
        else:
            self.设置文本到剪贴板(text)
            self._run_ld("input keyevent KEYCODE_PASTE")

    def 获取句柄(self, index=None):
        if index is None:
            index = self.index
        lst = self.获取所有模拟器实例2()
        for dn in lst:
            if dn.index == index:
                return [dn.father_hwnd, dn.hwnd]

    # ================================修改雷电配置文本=========================================
    def 获取雷电图库路径(self):
        return self.配置字典["statusSettings.sharedPictures"]

    def 设置雷电图库路径(self, relative_path: str = None):  # 非绝对路径，只是相对路径
        if relative_path is None:
            relative_path = self.index
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        path = f"{documents}/leidian9/Pictures/{relative_path}"
        if not os.path.exists(path):
            os.makedirs(path)
        old_path = self.配置字典.get("statusSettings.sharedPictures")
        if old_path is None:  # 初始化
            # self.配置字典.pop("statusSettings.playerName", None)
            # self.配置字典.pop("basicSettings.verticalSync", None)
            # self.配置字典.pop("basicSettings.fsAutoSize", None)
            self.配置字典.update({"statusSettings.sharedApplications": f"{documents}/leidian9/Applications",
                                  "statusSettings.sharedPictures": path,
                                  "statusSettings.sharedMisc": f"{documents}/leidian9/Misc",
                                  "basicSettings.left": 0,
                                  "basicSettings.top": 0,
                                  "basicSettings.width": 0,
                                  "basicSettings.height": 0,
                                  "basicSettings.realHeigh": 0,
                                  "basicSettings.realWidth": 0,
                                  "networkSettings.networkEnable": True,
                                  "basicSettings.isForstStart": False,
                                  "basicSettings.mulFsAddSize": 0,
                                  "basicSettings.mulFsAutoSize": 2})
        else:
            self.配置字典.update({"statusSettings.sharedPictures": path})
        ld_write_json(self.配置路径, self.配置字典)

    def 停止app通知(self, pack_name):  # 安卓9不生效
        command = f"appops set {pack_name} POST_NOTIFICATION ignore"
        result = self.ADB(command)
        return result

    def 停止app通知2(self, pack_name, func):  # 找图的方式关闭
        self.打开app通知(pack_name)
        func()
        self.后退()

    # 获取app版本名称
    def 获取app版本名称(self, package: str):
        command = f"dumpsys package {package} | grep -E 'versionName'"
        ver = self.ADB(command)
        if "error" in ver:
            print(f"模拟器{self.index} 获取app版本名称 异常 {ver}")
            return ""
        if ver:
            ver = ver.strip()
            # 去除回车
            ver = ver.replace('\n', '')
            # 提取版本号
            ver = ver.split('=')[1]
        return ver

    # 清除app存储空间和缓存
    def 清除app存储空间和缓存(self, packName):
        result = self.ADB('pm clear %s' % packName)
        return result

    # 清除app缓存，保留数据
    def 清除app缓存(self, packName):
        result = self.ADB('rm -rf /data/data/%s/cache/*' % packName)
        return result

    def 启动APP直到特征显示(self, package, func):
        print(f"启动APP直到特征显示 {package}")
        while True:
            self.启动app(package)
            for i in range(10):
                time.sleep(1)
                if _LD_DEBUG:
                    print(f"等待app{package} 启动第{i}秒")
                if func():
                    return True


    def 获取xml文本(self):
        # 获取当前activity的xml信息
        path = self.配置字典['statusSettings.sharedPictures'] + f'/activity{self.index}.xml'
        while True:
            self.ADB(f'uiautomator dump /sdcard/Pictures/activity{self.index}.xml')
            # self.ADB(f"pm grant com.android.uiautomator android.permission.DUMP")
            for i in range(100):
                if os.path.exists(path):
                    file_time = os.path.getmtime(path)
                    if file_time != self._xml_time:
                        self._xml_time = file_time
                        return path
                time.sleep(0.1)

    # 长按删除文本
    def 清除输入框(self, num=20):
        # 清除输入框
        for _ in range(num):
            self.按键("BACKSPACE")

    def 打开app设置(self, app_name):
        return self.ADB(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{app_name}")

    def 打开系统通知(self):
        return self.ADB(f"am start -a android.settings.NOTIFICATION_SETTINGS")

    def 打开app通知(self, app_name):
        return self.ADB(
            f"am start -a android.settings.APP_NOTIFICATION_SETTINGS --es android.provider.extra.APP_PACKAGE {app_name}")

    def 返回主屏幕(self):
        return self.ADB(f"input keyevent KEYCODE_HOME")

    def 后退(self):
        return self.ADB(f"input keyevent KEYCODE_BACK")

    def ping(self, target_ip):
        try:
            res = self.ADB(f"ping -W 5 -c 1 {target_ip}")
            res = res.strip()
            if "0 received" in res:
                return False
            if "rtt" in res:
                return True
        except TimeoutError:
            return False
        raise "未知ping 返回结果"

    def 跟踪路由(self, target_ip):
        try:
            res = self.ADB(f"traceroute {target_ip}")
            res = res.strip()
            if "0 received" in res:
                return False
            if "rtt" in res:
                return True
        except TimeoutError:
            return False
        raise "未知ping 返回结果"

    def 等待进入桌面(self, max_time=60):
        _start = time.time()
        while time.time() - _start < max_time:
            try:
                res = self.ADB("dumpsys activity activities | grep mResumedActivity")
                if "mResumedActivity" in res:
                    if "FallbackHome" in res:
                        print(f"{self.index}:等待进入桌面")
                    elif "launcher3/.Launcher" in res:
                        print(f"{self.index}:已进入桌面")
                        return True
                    else:
                        print(f"未知界面,返回主界面：%s" % res)
                        self.返回主屏幕()
                else:
                    print(f"{self.index}:等待进入桌面")
            except Exception as e:
                print(f"{self.index}:未知错误 %s" % e)
            time.sleep(2)



# 雷电模拟器截图以及键鼠
class LdKM:
    def __init__(self, ld):
        self.ld = ld
        self.x, self.y = 0, 0
        self.devices_input_path = "/dev/input/event2"   # 键盘,触摸(鼠标,绝对移动)驱动
        self.devices_mouse_path = "/dev/input/event4"          # 鼠标驱动(相对移动)
        self.next_tracking_id = 0                       # 触摸点ID
        self.max_slots = 16                             # 根据设备支持的最大触摸点数调整
        self.active_slots = {}                          # 触摸跟踪id字典
    def _sendevent(self, devices_path, type_code, code, value):
        """
        发送一个 sendevent 命令
        :param type_code: 事件类型
        :param code: 事件代码
        :param value: 事件值
        """
        self.ld.ADB("sendevent %s %s %s %s" % (devices_path, type_code, code, value))

    def sync(self, devices_path):
        """
        发送同步事件
        """
        self._sendevent(devices_path, 0, 0, 0)
        time.sleep(0.01)  # 确保事件被处理

    def input(self, string: str):
        return self.ld.输入2(string)

    def input_enter(self, string: str): # 碰到换行符,按shift+enter代替
        str_list = string.split("\n")
        str_list = [string.strip() for string in str_list]
        for string in str_list:
            self.input(string)
            self.KeyDownChar("shift")
            self.PressKey("enter")
            self.KeyUpChar("shift")


    def slide(self, x1, y1, x2, y2, delay=1):
        return self.ld.滑动(x1, y1, x2, y2, delay)

    # region 鼠标
    def MoveTo(self, x: int, y: int):
        """
        将鼠标移动到绝对坐标 (x, y)
        :param x: X坐标
        :param y: Y坐标
        """
        # 绝对移动通常用于触摸设备，鼠标设备使用相对移动
        # 这里假设使用相对移动
        # self._sendevent(self.devices_mouse_path, 2, 0, x)  # REL_X
        # self._sendevent(self.devices_mouse_path, 2, 1, y)  # REL_Y
        # self.sync(self.devices_mouse_path)
        self.x,self.y = x,y

    def MoveR(self, x: int, y: int):
        """
        将鼠标相对当前位置移动 (x, y)
        :param x: X轴相对移动量
        :param y: Y轴相对移动量
        """
        self._sendevent(self.devices_mouse_path, 2, 0, x)  # REL_X
        self._sendevent(self.devices_mouse_path, 2, 1, y)  # REL_Y
        self.sync(self.devices_mouse_path)

    def WheelDown(self):
        self._sendevent(self.devices_mouse_path, 2, 8, -1)
        self.sync(self.devices_mouse_path)

    def WheelUp(self):
        self._sendevent(self.devices_mouse_path, 2, 8, 1)
        self.sync(self.devices_mouse_path)


    def LeftDown(self):
        """按下鼠标左键"""
        self._sendevent(self.devices_mouse_path, 1, 272, 1)  # BTN_LEFT 按下
        self.sync(self.devices_mouse_path)

    def LeftUp(self):
        """松开鼠标左键"""
        self._sendevent(self.devices_mouse_path, 1, 272, 0)  # BTN_LEFT 松开
        self.sync(self.devices_mouse_path)

    def RightDown(self):
        """按下鼠标右键"""
        self._sendevent(self.devices_mouse_path, 1, 273, 1)  # BTN_RIGHT 按下
        self.sync(self.devices_mouse_path)

    def RightUp(self):
        """松开鼠标右键"""
        self._sendevent(self.devices_mouse_path, 1, 273, 0)  # BTN_RIGHT 松开
        self.sync(self.devices_mouse_path)

    def LeftClick(self):
        """
        点击鼠标左键
        缺点:有鼠标样式残留，影响截图，更改成self.ld.点击
        :return:
        """
        self.ld.点击(self.x, self.y)

        # self.LeftDown()
        # time.sleep(0.05)  # 按下保持时间
        # self.LeftUp()

    def RightClick(self):
        """点击鼠标右键"""
        self.RightDown()
        time.sleep(0.05)  # 按下保持时间
        self.RightUp()

    # endregion 鼠标
    # region 键盘
    def KeyDownChar(self, key_name: str):
        """
        按下指定的按键
        :param key_name: 按键名称，如 "esc"
        """
        key_code = ANDROID_KEY_MAPPING.get(key_name.lower())
        if key_code is None:
            print(f"未找到按键 '{key_name}' 的映射")
            return
        self._sendevent(self.devices_input_path, 1, key_code, 1)  # 按键按下
        self.sync(self.devices_input_path)

    def KeyUpChar(self, key_name: str):
        """
        松开指定的按键
        :param key_name: 按键名称，如 "esc"
        """
        key_code = ANDROID_KEY_MAPPING.get(key_name.lower())
        if key_code is None:
            print(f"未找到按键 '{key_name}' 的映射")
            return
        self._sendevent(self.devices_input_path, 1, key_code, 0)  # 按键松开
        self.sync(self.devices_input_path)

    def PressKey(self, key_name: str):
        """
        按下并松开指定的按键
        :param key_name: 按键名称，如 "esc"
        """
        self.KeyDownChar(key_name)
        time.sleep(0.05)  # 按下保持时间
        self.KeyUpChar(key_name)
    # endregion 键盘

    # region 特殊按键
    def 电源键(self):
        pass

    def 音量加(self):
        pass

    def 音量减(self):
        pass
    # endregion 特殊按键

    # region 触摸按键
    def touch_down(self, slot, x, y):
        """
        模拟触摸按下
        :param slot: 槽位编号（0-14）
        :param x: X坐标
        :param y: Y坐标
        :return: tracking_id
        """
        # tracking_id = self.next_tracking_id
        # self.next_tracking_id += 1
        # self.active_slots[slot] = tracking_id

        self._sendevent(self.devices_input_path, 3, 47, slot)  # ABS_MT_SLOT
        self._sendevent(self.devices_input_path, 3, 53, x)  # ABS_MT_POSITION_X
        self._sendevent(self.devices_input_path, 3, 54, y)  # ABS_MT_POSITION_Y
        self._sendevent(self.devices_input_path, 3, 57, slot)  # ABS_MT_TRACKING_ID
        self._sendevent(self.devices_input_path, 1, 330, 1)  # BTN_TOUCH 按下
        # 不立即同步，以便批量发送
        return slot

    def touch_move(self, slot, x, y):
        """
        todo:移动比例有问题，先不使用
        模拟触摸移动
        :param slot: 槽位编号
        :param x: 新的X坐标
        :param y: 新的Y坐标
        """
        _x,_y = round(x/2*1920/540),round(y/2*1080/960)
        self._sendevent(self.devices_input_path, "ABS", "ABS_MT_POSITION_X", _x)  # ABS_MT_POSITION_X
        self._sendevent(self.devices_input_path, "ABS", "ABS_MT_POSITION_Y", _y)  # ABS_MT_POSITION_Y
        # 不立即同步，以便批量发送

    def touch_up(self, slot):
        """
        模拟触摸松开
        :param slot: 槽位编号
        """
        # tracking_id = self.active_slots.get(slot, -1)
        # if tracking_id == -1:
        #     print(f"槽位 {slot} 没有对应的触摸点")
        #     return

        self._sendevent(self.devices_input_path, 3, 47, slot)  # ABS_MT_SLOT
        self._sendevent(self.devices_input_path, 3, 57, -1)  # ABS_MT_TRACKING_ID: 结束触摸点
        self._sendevent(self.devices_input_path, 1, 330, 0)  # BTN_TOUCH 松开触摸

        # del self.active_slots[slot]
        # 不立即同步，以便批量发送

    def 多指触控(self, xy_start_list, xy_end_list):
        """

        :param xy_start_list: [[x1_start,y1_start],[x2_start,y2_start]...] 最多支持16个手指头的开始位置
        :param xy_end_list: [[x1_end,y1_end],[x2_end,y2_end],...] # 手指头移动的最后位置

        :return:
        """
        if len(xy_start_list) > self.max_slots or len(xy_end_list) > self.max_slots:
            print(f"多指触控最多支持 {self.max_slots} 个手指头")
            return
        if len(xy_start_list) != len(xy_end_list):
            print("开始位置和结束位置的数量不一致")
            return

        tracking_ids = []  # List to store tracking IDs for each touch point

        # Simulate touch down for each finger
        for index, (x, y) in enumerate(xy_start_list):
            tracking_id = self.touch_down(index, x, y)
            tracking_ids.append(tracking_id)

        # Synchronize after touch down events
        self.sync(self.devices_input_path)

        # Simulate touch move for each finger
        for index, (x, y) in enumerate(xy_end_list):
            self.touch_move(index, x, y)

        # Synchronize after touch move events
        self.sync(self.devices_input_path)

        # Simulate touch up for each finger
        for index in range(len(tracking_ids)):
            self.touch_up(index)

        # Synchronize after touch up events
        self.sync(self.devices_input_path)
    def 单指触控(self,x,y,手指头id=0):
        """

        :param x: 横坐标，不能超过分辨率宽度
        :param y: 纵坐标,不能超过分辨率高度
        :param 手指头id: 0-14
        :param 手指压力: 0,1,2
        :return:
        """
        # 使用提供的触摸坐标范围直接发送事件
        _x,_y = round(x/2*1920/540),round(y/2*1080/960)
        self._sendevent(self.devices_input_path, 3, 47, 手指头id)         # ABS_MT_SLOT 选择槽位
        self._sendevent(self.devices_input_path, 3, 57, 手指头id)       # ABS_MT_TRACKING_ID 分配 tracking_id
        self._sendevent(self.devices_input_path, 3, 53, _x)         # ABS_MT_POSITION_X 设置 X 坐标
        self._sendevent(self.devices_input_path, 3, 54, _y)         # ABS_MT_POSITION_Y 设置 Y 坐标
        self._sendevent(self.devices_input_path, 1, 330, 1)        # BTN_TOUCH 按下
        self._sendevent(self.devices_input_path, 0, 0, 0)          # SYN_REPORT
        time.sleep(0.05)                 # 模拟延时

        # 松开触控点
        self._sendevent(self.devices_input_path, 3, 57, -1)        # 释放 tracking_id
        self._sendevent(self.devices_input_path, 1, 330, 0)        # BTN_TOUCH 松开
        self._sendevent(self.devices_input_path, 0, 0, 0)          # SYN_REPORT
        # self.touch_move(手指头id, x, y)
        # self.sync(self.devices_input_path)
        # self.touch_down(手指头id, x, y)
        # self.sync(self.devices_input_path)
        # time.sleep(0.01)
        # self.touch_up(手指头id)
        # self.sync(self.devices_input_path)

    # endregion 触摸按键

class LDCapture:
    def __init__(self, ld: LD):
        """
        :param ld: LD
        """

        self.capture = TCPCapture(ld,pri=print_log,fps=5)

    def __del__(self):
        self.capture.__del__()

    def Capture(self, x1=None, y1=None, x2=None, y2=None):
        """
        该截图模式,需要开启adb,且如果连接vpn,则会掉线,需要重新连接
        :param x1:
        :param y1:
        :param x2:
        :param y2:
        :return:
        """
        return self.capture.Capture(x1, y1, x2, y2)


class TCPCapture:
    """
    基于minicap二开的tcp传输截图,保留原有功能的情况下，修改如下
    1，unix修改为tcp协议,不需要经过adb转发,且客户端修改为服务端，服务端修改为客户端，只需要增加两个参数 -I ip -p prot
    2，截图质量，原先的100为jpeg压缩质量100，修改为发送原图RGBA
    3, 默认fps=30 会导致Ld9BoxHeadless.exe占用会比较高，可以适当调整,建议fps=5
    cpu 2673v3 16核心32线程占用如下
    fps,雷电模拟器cpu占用参考如下
    1:2.6%
    5:4.6%
    10:6.7%
    20:10.5%
    30:13%
    """
    http = None  # http服务器是否开启
    http_port = 8999

    def __init__(self, ld: LD, pri=None, jpeg_quality=100, fps=30):
        self.port = 9000
        self.ld = ld

        if pri is None:
            self.print = lambda *args: None
        else:
            self.print = print
        # 启动http服务器
        with threading.Lock():
            if not TCPCapture.http:
                path = os.path.join(os.path.dirname(dx_core_path), "shared")
                t = PyThread(target=TCPCapture.http_server, args=("0.0.0.0", TCPCapture.http_port, path))
                t.start()
                self.print(self.ld.index, "等待启动http下载服务器")
                while not TCPCapture.http:
                    time.sleep(0.1)
                self.print(self.ld.index, "启动http下载服务器成功")


        self.ip = self.get_local_ip()

        self.width, self.height = self.get_width_height()

        self._minicap_tcp_path = None
        self._minicapso_path = None
        self._check_ver()
        self.server_socket = None
        self._image_id = 0
        self._image = None
        self.jpeg_quality = jpeg_quality
        self._server_capture_flag = True
        self.server_thread = None
        self.conn = None
        self.fps = fps
        self.server()

    def __del__(self):
        self.stop()

    def _check_ver(self):

        ver = self.ld.ADB("getprop ro.build.version.sdk")
        cpu = self.ld.ADB("getprop ro.product.cpu.abi")

        if ver and cpu:
            path = os.path.join(os.path.dirname(dx_core_path), "shared")
            self._minicap_tcp_path = f"{cpu}"
            self._minicapso_path = f"android-{ver}/{cpu}/minicap.so"
            if os.path.exists(os.path.join(path, self._minicapso_path)) and os.path.exists(os.path.join(path, self._minicapso_path)):
                return True
            else:
                raise Exception("不支持当前模拟器版本")
        else:
            raise Exception("请检查是否已启动模拟器")

    def get_width_height(self):
        res = self.ld.ADB("wm size")
        try:
            width, height = res.replace("Physical size: ", "").split("x")
            return int(width), int(height)
        except:
            raise ValueError("无法获取屏幕分辨率, 请检查是否已启动模拟器,error=%s" % res)

    def server(self):
        # region 0 初始化异步or同步 变量
        curl_port = self.port + self.ld.index
        host = "0.0.0.0"
        name = "minicap_tcp"
        # endregion 0 初始化异步or同步 变量
        # region 1.下载文件
        self.ld.更新配置字典()
        screen_path = self.ld.配置字典.get("statusSettings.sharedPictures")
        if screen_path is None:
            raise ValueError("找不到雷电图库路径,请先启动雷电模拟器自动生成")

        res = self.ld.ADB(f"ls /data/local/tmp/{name}")
        # if "No such file or directory" in res:
        self.ld.ADB(f'curl http://{self.ip}:{TCPCapture.http_port}/{self._minicap_tcp_path}/{name} -o /data/local/tmp/{name}')
        self.ld.ADB(f"chmod 777 /data/local/tmp/{name}")

        res = self.ld.ADB("ls /data/local/tmp/minicap.so")
        if "No such file or directory" in res:
            self.ld.ADB(f'curl http://{self.ip}:{TCPCapture.http_port}/{self._minicapso_path} -o /data/local/tmp/minicap.so')
            self.ld.ADB("chmod 777 /data/local/tmp/minicap.so")
        # endregion 1.下载文件

        # region 2.启动pc服务端
        self.ld.ADB(f"killall {name}")  # 先停止服务
        if self.server_thread is None:
            self.server_thread = PyThread(target=self.start_server_capture, args=(host, curl_port))
            self.server_thread.start()
        time.sleep(0.1)
        # endregion 2.启动pc服务端
        # region 3.启动minicap_tcp
        command = f"LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/{name} -P {self.width}x{self.height}@{self.width}x{self.height}/0 -Q {self.jpeg_quality} -r {self.fps} -I {self.ip} -p {curl_port}"
        command = self.ld.ld + f'-s {self.ld.index} {command}'
        self._process = subprocess.Popen(
            command,  # 要执行的命令
            stdout=subprocess.PIPE,  # 将标准输出重定向到管道
            stderr=subprocess.PIPE,  # 将标准错误重定向到管道
            bufsize=1,  # 行缓冲模式
            universal_newlines=True  # 启用文本模式
        )
        time.sleep(0.1)
        # endregion 3.启动minicap_tcp

    def stop(self):

        self.print(self.ld.index, "关闭服务...")
        try:
            # 停止截图
            self._image = None
            self._server_capture_flag = False
            s = time.time()
            while True:
                if not self.server_thread.is_alive():
                    break
                if time.time() - s > 1: # 超市手动停止
                    self.server_thread.stop()
                time.sleep(0.1)
            self.server_thread = None
            # 关闭服务端
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            # 关闭客户端
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            self.ld.ADB(f"killall minicap_tcp")
        except:
            pass
        self.print(self.ld.index, "已关闭服务")

    def capture_one(self):
        try:
            frame_size_data = self._read_from_minicap(self.conn, 4)
            frame_size = struct.unpack('<I', frame_size_data)[0]
            # print(f"Frame Size: {int(frame_size / 1024)}KB")
            # 读取帧数据
            frame_data = self._read_from_minicap(self.conn, frame_size)
            self._image = frame_data
            self._image_id += 1
        except BlockingIOError:
            # 如果没有数据可接收，捕获异常并继续
            time.sleep(0.1)  # 避免CPU占用过高，适当休眠
        except socket.timeout:
            # print("Receive operation timed out")
            pass
        except socket.error as e:
            self.print(self.ld.index, f"截图异常 {e}")
            return True
        except Exception as e:
            self.print(self.ld.index, f"截图进程失败 未知错误代码：{e}")
            return True

    def start_server_capture(self, host, port):
        # 创建 TCP 套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 绑定到指定的主机和端口
        self.server_socket.bind((host, port))

        # 开始监听连接请求
        self.server_socket.listen(1)
        print(f"Listening on {host}:{port}")

        # 接受客户端连接
        conn, addr = self.server_socket.accept()
        conn.settimeout(1)
        print(f"Connection from {addr}")
        # 接受头部数据
        banner = TCPCapture._read_from_minicap(conn, 24)
        # 解析 banner
        version, banner_length, pid, real_width, real_height, virtual_width, virtual_height, orientation, quirks = struct.unpack(
            '<2B5I2B', banner)

        self.print(self.ld.index, f"Version: {version}")  # 版本
        self.print(self.ld.index, f"Banner Length: {banner_length}")  # 头部长度
        self.print(self.ld.index, f"PID: {pid}")  # 进程ID
        self.print(self.ld.index, f"Real Width: {real_width}")  # 屏幕宽
        self.print(self.ld.index, f"Real Height: {real_height}")  # 屏幕高
        self.print(self.ld.index, f"Virtual Width: {virtual_width}")  # 虚拟屏幕宽
        self.print(self.ld.index, f"Virtual Height: {virtual_height}")  # 虚拟屏幕高
        self.print(self.ld.index, f"Orientation: {orientation}")  # 方向，0竖屏保持，1横屏
        self.print(self.ld.index, f"Quirks: {quirks}")  # 1，即使与前一帧没有变化，也会发送帧，2，无论设备方向如何，框架都将始终处于直立方向。渲染图像时需要考虑到这一点。3，框架撕裂可能是可见的。内容丰富，无需执行任何操作。我们目前的两种方法都没有表现出这种行为。
        self.jpeg = TurboJPEG()
        self.conn = conn
        while self._server_capture_flag:
            if self.capture_one():
                break
        self._server_capture_flag = False
        self.print(self.ld.index, "关闭conn")
        self.conn.close()
        self.print(self.ld.index, "关闭server")

    @staticmethod
    def get_local_ip():
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip and local_ip[:3] == "192":
                return local_ip
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('8.8.8.8', 80))  # 114.114.114.114也是dns地址
                ip = s.getsockname()[0]
            finally:
                s.close()
            return ip

        except Exception as e:
            print(f"Unable to get the local IP: {e}")
            raise ValueError("无法获取局域网ip地址,请手动指定")

    @staticmethod
    def _read_from_minicap(sock, buffer_size):
        data = bytearray()  # 使用 bytearray
        n = 0
        while len(data) < buffer_size:
            chunk_size = min(buffer_size - len(data), 1024 * 1024)
            more = sock.recv(chunk_size)
            if not more:
                if n > 1000:
                    raise socket.error(f"截图超时,数据缺失:{buffer_size - len(data)}")
                n += 1
                continue
            data.extend(more)  # 用 extend 替代拼接
        return bytes(data)  # 转为不可变的 bytes 类型

    def Capture(self, x1=None, y1=None, x2=None, y2=None):
        # 继续处理帧数据...
        if x1 is None:
            x1 = 0
        if y1 is None:
            y1 = 0
        if x2 is None:
            x2 = self.width
        if y2 is None:
            y2 = self.height

        for i in range(30):
            if self._image is None:
                time.sleep(0.1)
                continue
            else:
                if self.jpeg_quality == 100:
                    image = dxpyd.MiNiNumPy.bytes_rgba_to_arr3d(self._image, self.height, self.width)
                else:
                    image = self.jpeg.decode(self._image)
                image = image[y1:y2, x1:x2]
                return image
        raise "ld_captrue截图超时异常"

    def capture_test_fps(self):
        start = time.time()
        fps = 0
        n = self._image_id
        while self._server_capture_flag:
            try:
                if n != self._image_id:
                    n = self._image_id
                    fps += 1
                MiniOpenCV.imshow("ld_num:" + str(self.ld.index), self.Capture())
                MiniOpenCV.waitKey(1)
                if time.time() - start >= 1:
                    print(f"ld_num:{self.ld.index} fps:{fps}")
                    start = time.time()
                    fps = 0
            except Exception as e:
                print("显示异常 %s" % e)
                time.sleep(1)
                break

    @staticmethod
    def http_server(host='0.0.0.0', port=8080, dir_name=""):
        if not dir_name:
            dir_name = os.path.dirname(__file__)
        # 创建 TCP 套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
        # 绑定到指定的主机和端口
            server_socket.bind((host, port))
        except OSError:
            raise ValueError("端口冲突 %s" % port)
        # 开始监听连接请求
        server_socket.listen(5)
        print(f"Listening on {host}:{port}")
        TCPCapture.http = True
        while True:
            # 接受客户端连接
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")

            try:
                # 接收请求
                request = client_socket.recv(1024).decode()
                print(f"Received request:\n{request}")

                # 解析请求，获取请求的文件名
                request_line = request.splitlines()[0]
                _, file_name, _ = request_line.split()
                obs_file = os.path.join(dir_name, file_name[1:])
                # 检查文件是否存在
                if os.path.exists(obs_file):
                    with open(obs_file, 'rb') as f:
                        content = f.read()

                    # 构建响应头
                    response_header = "HTTP/1.1 200 OK\r\n"
                    response_header += f"Content-Length: {len(content)}\r\n"
                    response_header += "Content-Type: application/octet-stream\r\n"
                    response_header += "Connection: close\r\n\r\n"

                    # 发送响应头和文件内容
                    client_socket.sendall(response_header.encode() + content)
                    print(f"Sent file: {file_name}")
                else:
                    # 文件不存在，返回 404
                    response_header = "HTTP/1.1 404 Not Found\r\n\r\n"
                    client_socket.sendall(response_header.encode())
                    print(f"File not found: {file_name}")

            except Exception as e:
                print(f"Error: {e}")
            finally:
                # 关闭连接
                client_socket.close()


if __name__ == '__main__':
    from public import *
    dn = 雷电模拟器终端("D:\leidian\LDPlayer9.0.76.1")
    s = time.time()
    ld = LD(dn, 49)
    ld2 = LD(dn, 50)

    # km = LdKM(ld)
    # km.MoveTo(212,242)
    # km.LeftClick()
    # km.MoveTo(9999,9999)
    # km.touch_move(0, 100,100)
    # km._sendevent(km.devices_input_path, 1, 330, 1)
    # km.sync(km.devices_input_path)
    # time.sleep(0.05)
    # km._sendevent(km.devices_input_path, 1, 330, 0)
    # km.sync(km.devices_input_path)
    # km.input_enter("123\n445你好！\n扣你吉瓦")

    # # 截图测试
    tc0 = TCPCapture(ld, pri=print, fps=30)
    tc1 = TCPCapture(ld2, pri=print, fps=30)

    input()
    # tc0.capture_test_fps()
    # input("")
    #

