from dxGame.dx_core import *
from dxGame import ctypes, dx_core_path, Window, get_mouse_path, user32, dxpyd
from comtypes import CoInitialize
from comtypes.client import CreateObject
import logging, socket



# 依赖库
# pip install comtypes -i https://mirror.baidu.com/pypi/simple


class DM:
    def __init__(self, dm=None):
        CoInitialize()
        if not dm:
            print('正在免注册调用')
            dms = ctypes.windll.LoadLibrary(f"{dx_core_path}/DmReg.dll")
            location_dmreg = f"{dx_core_path}/270207756.dll"
            dms.YEuaAOkq(location_dmreg, 0)
        self.dm = CreateObject("dx.dxst")
        print('免注册调用成功 版本号为:', self.Ver())

    def reg(self):
        dm_user = "270207756caf4b32039fc35397d603f9688eaa665"
        dm_pass = "x2ImSD03b7"
        res = self.Reg(dm_user, dm_pass)
        dm_res = {
            -1: "大漠无法连接网络",
            -2: "进程没有以管理员方式运行",
            0: "失败 (未知错误)",
            1: "成功",
            2: "余额不足",
            3: "绑定了本机器，但是账户余额不足50元",
            4: "注册码错误",
            5: "你的机器或者IP在黑名单列表中或者不在白名单列表中",
            6: "非法使用插件. 一般出现在定制插件时，使用了和绑定的用户名不同的注册码.  也有可能是系统的语言设置不是中文简体,也可能有这个错误",
            7: "你的帐号因为非法使用被封禁. （如果是在虚拟机中使用插件，必须使用Reg或者RegEx，不能使用RegNoMac或者RegExNoMac,否则可能会造成封号，或者封禁机器）",
            8: "ver_info不在你设置的附加白名单中",
            77: "机器码或者IP因为非法使用，而被封禁. （如果是在虚拟机中使用插件，必须使用Reg或者RegEx，不能使用RegNoMac或者RegExNoMac,否则可能会造成封号，或者封禁机器）",
        }
        if res == 1:
            print("注册成功")
            return self.dm
        raise ValueError("大漠注册结果: %s" % dm_res[res])

    def CreateObject(self):
        return

    def FindMultiColor(self, x1: int, y1: int, x2: int, y2: int, first_color: str, offset_color: str, sim: float, dir: int):
        return self.dm.AFjxARcQYJmXM(x1, y1, x2, y2, first_color, offset_color, sim, dir)

    def MoveFile(self, src_file: str, dst_file: str):
        return self.dm.ALYwXVgCQvhVxMa(src_file, dst_file)

    def GetDir(self, type: int):
        return self.dm.AebhbPFF(type)

    def GetBindWindow(self):
        return self.dm.AjJaHdfEfTICVUp()

    def SetFindPicMultithreadLimit(self, limit: int):
        return self.dm.AjSgUmrMFy(limit)

    def EnableRealKeypad(self, en: int):
        return self.dm.AnYrMYB(en)

    def FetchWord(self, x1: int, y1: int, x2: int, y2: int, color: str, word: str):
        return self.dm.AniPAVMyBLjHEX(x1, y1, x2, y2, color, word)

    def ExecuteCmd(self, cmd: str, current_dir: str, time_out: int):
        return self.dm.AuEVFyPrGb(cmd, current_dir, time_out)

    def Hex64(self, v: int):
        return self.dm.AzgS(v)

    def RightDown(self):
        return self.dm.BGDi()

    def FindPicSimEx(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: int, dir: int):
        return self.dm.BJeIX(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def ShowScrMsg(self, x1: int, y1: int, x2: int, y2: int, msg: str, color: str):
        return self.dm.BMzCuDGLuC(x1, y1, x2, y2, msg, color)

    def DmGuard(self, en: int, type: str):
        return self.dm.BRDLyyRAaAF(en, type)

    def GetWindowRect(self, hwnd: int):
        return self.dm.BjTYIzz(hwnd)

    def FoobarDrawPic(self, hwnd: int, x: int, y: int, pic: str, trans_color: str):
        return self.dm.BwEjpQdQU(hwnd, x, y, pic, trans_color)

    def CheckFontSmooth(self):
        return self.dm.BweqWLdVaRL()

    def Capture(self, x1: int, y1: int, x2: int, y2: int, file: str):
        return self.dm.CSASiGZcE(x1, y1, x2, y2, file)

    def GetClientSize(self, hwnd: int):
        return self.dm.CYPcattGJWBEREu(hwnd)

    def AddDict(self, index: int, dict_info: str):
        return self.dm.CdKv(index, dict_info)

    def WriteFile(self, file: str, content: str):
        return self.dm.CpFplyF(file, content)

    def ForceUnBindWindow(self, hwnd: int):
        return self.dm.CyuAsksHhIn(hwnd)

    def IsBind(self, hwnd: int):
        return self.dm.DErxgYpeeF(hwnd)

    def FoobarTextLineGap(self, hwnd: int, gap: int):
        return self.dm.DYcbIXIJZ(hwnd, gap)

    def KeyUpChar(self, key_str: str):
        return self.dm.DwyhXCTyQFPNZP(key_str)

    def SetDictMem(self, index: int, addr: int, size: int):
        return self.dm.EBFLmdkVs(index, addr, size)

    def WheelDown(self):
        return self.dm.ECyVgluMxmr()

    def GetDmCount(self):
        return self.dm.ESTDuy()

    def GetMac(self):
        return self.dm.EhhMyyZYpKo()

    def SetFindPicMultithreadCount(self, count: int):
        return self.dm.EhqCYGutmerzUm(count)

    def FindColorBlock(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float, count: int, width: int, height: int):
        return self.dm.EnoDaFfnUiGvg(x1, y1, x2, y2, color, sim, count, width, height)

    def CapturePng(self, x1: int, y1: int, x2: int, y2: int, file: str):
        return self.dm.FJATNxssXhPNYxt(x1, y1, x2, y2, file)

    def SetWordLineHeight(self, line_height: int):
        return self.dm.FKMzEPBjifB(line_height)

    def GetSystemInfo(self, type: str, method: int):
        return self.dm.FLcqaMW(type, method)

    def LeftDoubleClick(self):
        return self.dm.FQscxZsCzYsfZ()

    def FindPicMemE(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: float, dir: int):
        return self.dm.FcGJGshC(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def IsFolderExist(self, folder: str):
        return self.dm.FcTClLsXaBoS(folder)

    def FindStrFastS(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.FtJCzXKVQvfJrM(x1, y1, x2, y2, str, color, sim)

    def ReadFile(self, file: str):
        return self.dm.FvNncTuEEqozSZ(file)

    def AiYoloDetectObjectsToDataBmp(self, x1: int, y1: int, x2: int, y2: int, prob: str, iou: str, mode: int):
        return self.dm.FxViXM(x1, y1, x2, y2, prob, iou, mode)

    def EnableFindPicMultithread(self, en: int):
        return self.dm.GAVA(en)

    def AiYoloSetVersion(self, ver: str):
        return self.dm.GGFh(ver)

    def ImageToBmp(self, pic_name: str, bmp_name: str):
        return self.dm.GRAcxKizedDkkUQ(pic_name, bmp_name)

    def SetInputDm(self, input_dm: int, rx: int, ry: int):
        return self.dm.GSjfhhCe(input_dm, rx, ry)

    def FindStrFast(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.GVHEtRIpNs(x1, y1, x2, y2, str, color, sim)

    def ReleaseRef(self):
        return self.dm.GZmlcmK()

    def EnableBind(self, en: int):
        return self.dm.GaortYCr(en)

    def AiYoloUseModel(self, index: int):
        return self.dm.GcWSNogBEcz(index)

    def GetScreenWidth(self):
        return self.dm.GcWidebaq()

    def EnableFakeActive(self, en: int):
        return self.dm.GguYoR(en)

    def SetDisplayRefreshDelay(self, t: int):
        return self.dm.GhclyI(t)

    def GetAveRGB(self, x1: int, y1: int, x2: int, y2: int):
        return self.dm.GvoHE(x1, y1, x2, y2)

    def FindPicExS(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir: int):
        return self.dm.GwoMyeWKkA(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def EnumIniKeyPwd(self, section: str, file: str, pwd: str):
        return self.dm.HESDiiJzzLEz(section, file, pwd)

    def FoobarStopGif(self, hwnd: int, x: int, y: int, pic_name: str):
        return self.dm.HYLtaIlhs(hwnd, x, y, pic_name)

    def FindWindow(self, class_name: str, title_name: str):
        return self.dm.HdfpVerpXv(class_name, title_name)

    def LoadPicByte(self, addr: int, size: int, name: str):
        return self.dm.HlHGJIJghoF(addr, size, name)

    def ActiveInputMethod(self, hwnd: int, id: str):
        return self.dm.HtUmobXCjY(hwnd, id)

    def GetClientRect(self, hwnd: int):
        return self.dm.HyKleyIsLRelJ(hwnd)

    def EncodeFile(self, file: str, pwd: str):
        return self.dm.IPztXDW(file, pwd)

    def GetMemoryUsage(self):
        return self.dm.IUjTyyzhZtNlS()

    def CheckInputMethod(self, hwnd: int, id: str):
        return self.dm.IbsIhJAQpFzC(hwnd, id)

    def DisableFontSmooth(self):
        return self.dm.ItrorFpRcc()

    def FindMulColor(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.JAMpyRjMVK(x1, y1, x2, y2, color, sim)

    def DmGuardExtract(self, type: str, path: str):
        return self.dm.JFMCmPRXUVT(type, path)

    def GetOsBuildNumber(self):
        return self.dm.JGgyBF()

    def SetDisplayAcceler(self, level: int):
        return self.dm.JPLLkqAvmbSRz(level)

    def GetSpecialWindow(self, flag: int):
        return self.dm.JTMrRdxJa(flag)

    def GetCursorShape(self):
        return self.dm.JUrRMbCAKXaGNe()

    def FoobarTextRect(self, hwnd: int, x: int, y: int, w: int, h: int):
        return self.dm.JXGmru(hwnd, x, y, w, h)

    def GetAveHSV(self, x1: int, y1: int, x2: int, y2: int):
        return self.dm.JaMhHtHnwYYt(x1, y1, x2, y2)

    def GetWordResultCount(self, str: str):
        return self.dm.JkzP(str)

    def SetDisplayDelay(self, t: int):
        return self.dm.JmcFopVMtkl(t)

    def FindPicEx(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir: int):
        return self.dm.KFtEHzkcRJsNhNP(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def ReadIniPwd(self, section: str, key: str, file: str, pwd: str):
        return self.dm.KXksG(section, key, file, pwd)

    def MoveToEx(self, x: int, y: int, w: int, h: int):
        return self.dm.KgEgIEm(x, y, w, h)

    def GetCursorSpot(self):
        return self.dm.KnUiQJZxIptzRf()

    def RightUp(self):
        return self.dm.KpotcbIyCpxF()

    def MiddleClick(self):
        return self.dm.LQcI()

    def GetCursorPos(self):
        return self.dm.LUXpa()

    def FindStrEx(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.LYftzwtSnEfNFF(x1, y1, x2, y2, str, color, sim)

    def GetForegroundWindow(self):
        return self.dm.LgepaeMDE()

    def DownloadFile(self, url: str, save_file: str, timeout: int):
        return self.dm.LkScNbbaSoRgs(url, save_file, timeout)

    def GetDict(self, index: int, font_index: int):
        return self.dm.LwbWQMsxA(index, font_index)

    def CapturePre(self, file: str):
        return self.dm.MDFcFwgxJkmAl(file)

    def GetCpuUsage(self):
        return self.dm.MDynzcaJHfNT()

    def GetPointWindow(self, x: int, y: int):
        return self.dm.MNKY(x, y)

    def Delays(self, min_s: int, max_s: int):
        return self.dm.MgykKiqWdNkX(min_s, max_s)

    def RGB2BGR(self, rgb_color: str):
        return self.dm.MmkLcAxjDIMTQYt(rgb_color)

    def EnumWindow(self, parent: int, title: str, class_name: str, filter: int):
        return self.dm.MrYzjiBLF(parent, title, class_name, filter)

    def GetDPI(self):
        return self.dm.MrgSREqdnVlufj()

    def SendStringIme2(self, hwnd: int, str: str, mode: int):
        return self.dm.MuebCjwplccquWz(hwnd, str, mode)

    def FindPicSim(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: int, dir: int):
        return self.dm.NLWwcd(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def LockInput(self, lock: int):
        return self.dm.NlDULlAZlKyNsKG(lock)

    def GetDisplayInfo(self):
        return self.dm.NosW()

    def FoobarLock(self, hwnd: int):
        return self.dm.PIgzssWb(hwnd)

    def CheckUAC(self):
        return self.dm.PMQFhW()

    def SetMouseSpeed(self, speed: int):
        return self.dm.PPqBUVjjYmDBlkU(speed)

    def GetClipboard(self):
        return self.dm.PTfvSWnQbGUADYa()

    def AiYoloDetectObjects(self, x1: int, y1: int, x2: int, y2: int, prob: str, iou: str):
        return self.dm.PYZxhCB(x1, y1, x2, y2, prob, iou)

    def SetPath(self, path: str):
        return self.dm.PfHmcD(path)

    def FoobarSetSave(self, hwnd: int, file: str, en: int, header: str):
        return self.dm.PmvsS(hwnd, file, en, header)

    def SelectDirectory(self):
        return self.dm.PphrIfeUZyl()

    def WriteIni(self, section: str, key: str, v: str, file: str):
        return self.dm.QBgzCfsfkv(section, key, v, file)

    def GetWordResultStr(self, str: str, index: int):
        return self.dm.QCdQgmghVUuP(str, index)

    def DisablePowerSave(self):
        return self.dm.QNiwqXWouZNLoQc()

    def FoobarUpdate(self, hwnd: int):
        return self.dm.QUtP(hwnd)

    def KeyPressStr(self, key_str: str, delay: int):
        return self.dm.QXFsqceKsyycbb(key_str, delay)

    def DeleteIniPwd(self, section: str, key: str, file: str, pwd: str):
        return self.dm.QXyXh(section, key, file, pwd)

    def FindWindowSuper(self, spec1: str, flag1: int, type1: int, spec2: str, flag2: int, type2: int):
        return self.dm.QjoIPEYwfjjMQqC(spec1, flag1, type1, spec2, flag2, type2)

    def GetResultPos(self, str: str, index: int):
        return self.dm.QriFdGzC(str, index)

    def EnableShareDict(self, en: int):
        return self.dm.QxiKXUeMuSzr(en)

    def FindStr(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.QzyCMhDWF(x1, y1, x2, y2, str, color, sim)

    def ShowTaskBarIcon(self, hwnd: int, is_show: int):
        return self.dm.RHpQEmCCms(hwnd, is_show)

    def Ver(self):
        return self.dm.RKmPFHHHry()

    def GetWindowState(self, hwnd: int, flag: int):
        return self.dm.RWkdjfR(hwnd, flag)

    def SetMinColGap(self, col_gap: int):
        return self.dm.RjbQbYat(col_gap)

    def EnumWindowByProcessId(self, pid: int, title: str, class_name: str, filter: int):
        return self.dm.RrlMiHpyKFllB(pid, title, class_name, filter)

    def FoobarDrawLine(self, hwnd: int, x1: int, y1: int, x2: int, y2: int, color: str, style: int, width: int):
        return self.dm.SAYhRHaHILTFH(hwnd, x1, y1, x2, y2, color, style, width)

    def LeftDown(self):
        return self.dm.SNAKVwr()

    def SetRowGapNoDict(self, row_gap: int):
        return self.dm.SeVUoCnG(row_gap)

    def GetWordResultPos(self, str: str, index: int):
        return self.dm.SgAhFrEWX(str, index)

    def FindColorEx(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float, dir: int):
        return self.dm.SimGQWHVENHT(x1, y1, x2, y2, color, sim, dir)

    def Play(self, file: str):
        return self.dm.SjzVDAtlCnVcqDa(file)

    def SpeedNormalGraphic(self, en: int):
        return self.dm.SnmcKipKoVcs(en)

    def FreePic(self, pic_name: str):
        return self.dm.SpYkdHaAYHL(pic_name)

    def GetCursorShapeEx(self, type: int):
        return self.dm.TIXMSmH(type)

    def SetKeypadDelay(self, type: str, delay: int):
        return self.dm.TTfxFMiMvbsZ(type, delay)

    def EnableSpeedDx(self, en: int):
        return self.dm.TcVefecrQK(en)

    def KeyPressChar(self, key_str: str):
        return self.dm.TeHciqh(key_str)

    def GetWindowThreadId(self, hwnd: int):
        return self.dm.TgkZRMVcYhun(hwnd)

    def EnableMouseAccuracy(self, en: int):
        return self.dm.TlidpBJA(en)

    def SetEnumWindowDelay(self, delay: int):
        return self.dm.TlqkMqhVngRLM(delay)

    def SetMouseDelay(self, type: str, delay: int):
        return self.dm.TmdpvYiDFNTLRW(type, delay)

    def GetColor(self, x: int, y: int):
        return self.dm.TmfNpUdfzFBWBXu(x, y)

    def FindShapeE(self, x1: int, y1: int, x2: int, y2: int, offset_color: str, sim: float, dir: int):
        return self.dm.TqndrGDxtafFJBR(x1, y1, x2, y2, offset_color, sim, dir)

    def GetDictCount(self, index: int):
        return self.dm.TsNHiyr(index)

    def FindColorBlockEx(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float, count: int, width: int, height: int):
        return self.dm.UCKmnTpsz(x1, y1, x2, y2, color, sim, count, width, height)

    def FindStrFastE(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.UCoEo(x1, y1, x2, y2, str, color, sim)

    def MoveTo(self, x: int, y: int):
        return self.dm.UMkfIxsoN(x, y)

    def GetCpuType(self):
        return self.dm.UQdhYYJkuEAvI()

    def FindMultiColorE(self, x1: int, y1: int, x2: int, y2: int, first_color: str, offset_color: str, sim: float, dir: int):
        return self.dm.URnxCIf(x1, y1, x2, y2, first_color, offset_color, sim, dir)

    def GetWindowTitle(self, hwnd: int):
        return self.dm.UaDGCdLYzUaGQL(hwnd)

    def SetAero(self, en: int):
        return self.dm.UjGAdUlzyjGfT(en)

    def FindWindowByProcess(self, process_name: str, class_name: str, title_name: str):
        return self.dm.UpfkxMvcwwFoDT(process_name, class_name, title_name)

    def EnableGetColorByCapture(self, en: int):
        return self.dm.UzWHFQ(en)

    def SetMinRowGap(self, row_gap: int):
        return self.dm.VCvIiGytWLBSYgI(row_gap)

    def GetBasePath(self):
        return self.dm.VSdeZphR()

    def GetWindowClass(self, hwnd: int):
        return self.dm.VZlsqNFAAvNXWQv(hwnd)

    def GetProcessInfo(self, pid: int):
        return self.dm.VbxasgwRj(pid)

    def SetUAC(self, uac: int):
        return self.dm.ViNpCgUIBmDtaJs(uac)

    def IsSurrpotVt(self):
        return self.dm.VknGKPUDpJGx()

    def MoveWindow(self, hwnd: int, x: int, y: int):
        return self.dm.VmRBxTU(hwnd, x, y)

    def LeftUp(self):
        return self.dm.VzErtvfQMgB()

    def SetShowErrorMsg(self, show: int):
        return self.dm.WDFoytE(show)

    def GetFps(self):
        return self.dm.WGbHKvJzkump()

    def GetID(self):
        return self.dm.WLGg()

    def SetWindowTransparent(self, hwnd: int, v: int):
        return self.dm.WhzWS(hwnd, v)

    def GetPicSize(self, pic_name: str):
        return self.dm.WmaQfE(pic_name)

    def FindPicSimE(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: int, dir: int):
        return self.dm.WrYWgtXRfqotyfM(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def AiYoloObjectsToString(self, objects: str):
        return self.dm.Wtha(objects)

    def EnumIniKey(self, section: str, file: str):
        return self.dm.XDIWLyTDQ(section, file)

    def MoveDD(self, dx: int, dy: int):
        return self.dm.XEaqNnbmxirM(dx, dy)

    def FindStrWithFontE(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float, font_name: str, font_size: int, flag: int):
        return self.dm.XIuJRCrJ(x1, y1, x2, y2, str, color, sim, font_name, font_size, flag)

    def SendStringIme(self, str: str):
        return self.dm.XQRrtPLKtQIfDoU(str)

    def SetClientSize(self, hwnd: int, width: int, height: int):
        return self.dm.XQpT(hwnd, width, height)

    def CreateFoobarCustom(self, hwnd: int, x: int, y: int, pic: str, trans_color: str, sim: float):
        return self.dm.XZJTGcfRFMK(hwnd, x, y, pic, trans_color, sim)

    def SetSimMode(self, mode: int):
        return self.dm.XaCARzGlqgxHg(mode)

    def SelectFile(self):
        return self.dm.XgYwa()

    def FindStrWithFontEx(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float, font_name: str, font_size: int, flag: int):
        return self.dm.YVtkUuWUMlGZDsz(x1, y1, x2, y2, str, color, sim, font_name, font_size, flag)

    def SetExportDict(self, index: int, dict_name: str):
        return self.dm.YcRG(index, dict_name)

    def Ocr(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.YkMAsj(x1, y1, x2, y2, color, sim)

    def RegNoMac(self, code: str, ver: str):
        return self.dm.YqCiSQfXXeKc(code, ver)

    def EnableIme(self, en: int):
        return self.dm.ZKqrJUT(en)

    def EnableKeypadMsg(self, en: int):
        return self.dm.ZRCZHbvZ(en)

    def GetWordsNoDict(self, x1: int, y1: int, x2: int, y2: int, color: str):
        return self.dm.ZUWhaeENSpW(x1, y1, x2, y2, color)

    def FindPicMem(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: float, dir: int):
        return self.dm.ZmnEAct(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def MoveR(self, rx: int, ry: int):
        return self.dm.ZzXND(rx, ry)

    def RunApp(self, path: str, mode: int):
        return self.dm.aFmwEEYj(path, mode)

    def WheelUp(self):
        return self.dm.aJNamT()

    def DecodeFile(self, file: str, pwd: str):
        return self.dm.aPHpLdRQlQR(file, pwd)

    def EnumWindowByProcess(self, process_name: str, title: str, class_name: str, filter: int):
        return self.dm.aUBwQclGwCm(process_name, title, class_name, filter)

    def IsFileExist(self, file: str):
        return self.dm.aURRaLZUCcLnTX(file)

    def SetDict(self, index: int, dict_name: str):
        return self.dm.aapnhyfKQP(index, dict_name)

    def AiYoloFreeModel(self, index: int):
        return self.dm.aeSbhiRnek(index)

    def SetPicPwd(self, pwd: str):
        return self.dm.afTCrp(pwd)

    def DisableCloseDisplayAndSleep(self):
        return self.dm.apARP()

    def FindPicSimMemE(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: int, dir: int):
        return self.dm.aqxIXqhBiLLlRd(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def UnBindWindow(self):
        return self.dm.auFbN()

    def GetLocale(self):
        return self.dm.awyXqeFx()

    def SetDictPwd(self, pwd: str):
        return self.dm.azukgS(pwd)

    def CaptureJpg(self, x1: int, y1: int, x2: int, y2: int, file: str, quality: int):
        return self.dm.bENBivmbK(x1, y1, x2, y2, file, quality)

    def FoobarPrintText(self, hwnd: int, text: str, color: str):
        return self.dm.bLqTLqJWf(hwnd, text, color)

    def GetScreenDataBmp(self, x1: int, y1: int, x2: int, y2: int):
        return self.dm.bQzfPcfTV(x1, y1, x2, y2)

    def GetNowDict(self):
        return self.dm.bTFLidyKAssz()

    def GetKeyState(self, vk: int):
        return self.dm.bVQqrTVfBwU(vk)

    def FindWindowEx(self, parent: int, class_name: str, title_name: str):
        return self.dm.bjlf(parent, class_name, title_name)

    def HackSpeed(self, rate: float):
        return self.dm.brVjX(rate)

    def SetExactOcr(self, exact_ocr: int):
        return self.dm.cFgFCHPXutuzV(exact_ocr)

    def SendPaste(self, hwnd: int):
        return self.dm.cIkvgjbzRGuxoYm(hwnd)

    def KeyDown(self, vk: int):
        return self.dm.cKrejhoEYH(vk)

    def EnableDisplayDebug(self, enable_debug: int):
        return self.dm.ceRvESHtELdjo(enable_debug)

    def EnableKeypadPatch(self, en: int):
        return self.dm.ckXJCMetLXvlVM(en)

    def SwitchBindWindow(self, hwnd: int):
        return self.dm.cmlTU(hwnd)

    def GetMouseSpeed(self):
        return self.dm.cmmYepQyXUyAH()

    def Reg(self, code: str, ver: str):
        return self.dm.cpmnlswTILNX(code, ver)

    def LockDisplay(self, lock: int):
        return self.dm.dRqwXq(lock)

    def LoadPic(self, pic_name: str):
        return self.dm.dSITsM(pic_name)

    def GetWords(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.dZoDTYQfMyT(x1, y1, x2, y2, color, sim)

    def EnumIniSectionPwd(self, file: str, pwd: str):
        return self.dm.dzHBVEmccaqW(file, pwd)

    def SetScreen(self, width: int, height: int, depth: int):
        return self.dm.eTeucva(width, height, depth)

    def GetFileLength(self, file: str):
        return self.dm.eWgWg(file)

    def FindStrS(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.egCfCMNfFLR(x1, y1, x2, y2, str, color, sim)

    def FindPicE(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir: int):
        return self.dm.epVtInepc(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def EnableMouseSync(self, en: int, time_out: int):
        return self.dm.eqcRMc(en, time_out)

    def EnumIniSection(self, file: str):
        return self.dm.fDQNp(file)

    def CreateFoobarEllipse(self, hwnd: int, x: int, y: int, w: int, h: int):
        return self.dm.fQsJNHoEpyT(hwnd, x, y, w, h)

    def LeaveCri(self):
        return self.dm.fpiiwVPCU()

    def GetResultCount(self, str: str):
        return self.dm.fwVejppeRCTIH(str)

    def Is64Bit(self):
        return self.dm.fwXFZ()

    def DmGuardParams(self, cmd: str, sub_cmd: str, param: str):
        return self.dm.gHJdItoD(cmd, sub_cmd, param)

    def FoobarClearText(self, hwnd: int):
        return self.dm.gPXncBGNLK(hwnd)

    def OcrExOne(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.gwMQEpxkEfJGe(x1, y1, x2, y2, color, sim)

    def GetOsType(self):
        return self.dm.hEVzIpqcUlPGLpI()

    def FoobarStartGif(self, hwnd: int, x: int, y: int, pic_name: str, repeat_limit: int, delay: int):
        return self.dm.hMDbbePBDgKvS(hwnd, x, y, pic_name, repeat_limit, delay)

    def Md5(self, str: str):
        return self.dm.hZGSlTktSHuUb(str)

    def DeleteFile(self, file: str):
        return self.dm.hljVCjax(file)

    def CreateFoobarRect(self, hwnd: int, x: int, y: int, w: int, h: int):
        return self.dm.hphjZELzqp(hwnd, x, y, w, h)

    def SendString(self, hwnd: int, str: str):
        return self.dm.iMbaNtqgs(hwnd, str)

    def GetPath(self):
        return self.dm.iRrYMzGSPzqEQa()

    def SetWindowSize(self, hwnd: int, width: int, height: int):
        return self.dm.ikyBxhZKADNhR(hwnd, width, height)

    def GetMachineCodeNoMac(self):
        return self.dm.ipyKwGoprN()

    def DmGuardLoadCustom(self, type: str, path: str):
        return self.dm.itqMRY(type, path)

    def FindPicMemEx(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: float, dir: int):
        return self.dm.jAUFqrY(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def MiddleDown(self):
        return self.dm.jBaPcXSBLyvwpA()

    def GetRealPath(self, path: str):
        return self.dm.jDJwpmnvmgr(path)

    def OcrEx(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.jGFHMywXkbU(x1, y1, x2, y2, color, sim)

    def BindWindow(self, hwnd: int, display: str, mouse: str, keypad: str, mode: int):
        return self.dm.jJpbrMrXpqAQRr(hwnd, display, mouse, keypad, mode)

    def RegEx(self, code: str, ver: str, ip: str):
        return self.dm.jRAGwIqzWyy(code, ver, ip)

    def GetLastError(self):
        return self.dm.jgxbuj()

    def Delay(self, mis: int):
        return self.dm.jkcNelVTjI(mis)

    def SetExitThread(self, mode: int):
        return self.dm.jzkXmpdpYMGJBo(mode)

    def Beep(self, fre: int, delay: int):
        return self.dm.kCeX(fre, delay)

    def FindInputMethod(self, id: str):
        return self.dm.kKlcEhoN(id)

    def FindStrWithFont(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float, font_name: str, font_size: int, flag: int):
        return self.dm.kWhVEDAIPbR(x1, y1, x2, y2, str, color, sim, font_name, font_size, flag)

    def OcrInFile(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, color: str, sim: float):
        return self.dm.kfxvIu(x1, y1, x2, y2, pic_name, color, sim)

    def LoadAiMemory(self, addr: int, size: int):
        return self.dm.kkkiUysnsKQraB(addr, size)

    def GetDiskModel(self, index: int):
        return self.dm.kmgyLGoFa(index)

    def FindStrExS(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.lGwGpRtQDZjYZg(x1, y1, x2, y2, str, color, sim)

    def Int64ToInt32(self, v: int):
        return self.dm.lIxeUADqWGXc(v)

    def EnableMouseMsg(self, en: int):
        return self.dm.lPVHsMbGy(en)

    def SetWindowState(self, hwnd: int, flag: int):
        return self.dm.lTGvFh(hwnd, flag)

    def EnableRealMouse(self, en: int, mousedelay: int, mousestep: int):
        return self.dm.leHUGyUpGGBK(en, mousedelay, mousestep)

    def SetWindowText(self, hwnd: int, text: str):
        return self.dm.lpVWgvEFkL(hwnd, text)

    def GetNetTimeByIp(self, ip: str):
        return self.dm.lrAMMtKvCXoFI(ip)

    def IsDisplayDead(self, x1: int, y1: int, x2: int, y2: int, t: int):
        return self.dm.mAxlwxTV(x1, y1, x2, y2, t)

    def FindWindowByProcessId(self, process_id: int, class_name: str, title_name: str):
        return self.dm.mDunFgVuo(process_id, class_name, title_name)

    def LeftClick(self):
        return self.dm.mbBI()

    def SetDisplayInput(self, mode: str):
        return self.dm.mhrMjiyYqcz(mode)

    def AppendPicAddr(self, pic_info: str, addr: int, size: int):
        return self.dm.mmckQZKQzXSox(pic_info, addr, size)

    def FoobarSetTrans(self, hwnd: int, trans: int, color: str, sim: float):
        return self.dm.mqDbEf(hwnd, trans, color, sim)

    def SaveDict(self, index: int, file: str):
        return self.dm.nDGW(index, file)

    def FoobarSetFont(self, hwnd: int, font_name: str, size: int, flag: int):
        return self.dm.nPToKWcmEjYcvCo(hwnd, font_name, size, flag)

    def Hex32(self, v: int):
        return self.dm.nTfzXAbllC(v)

    def KeyPress(self, vk: int):
        return self.dm.nUPm(vk)

    def CreateFolder(self, folder_name: str):
        return self.dm.nWaRciABDd(folder_name)

    def EnablePicCache(self, en: int):
        return self.dm.napbRlkk(en)

    def GetWindow(self, hwnd: int, flag: int):
        return self.dm.nbqbczpdnqmqI(hwnd, flag)

    def SendString2(self, hwnd: int, str: str):
        return self.dm.ncfvf(hwnd, str)

    def KeyUp(self, vk: int):
        return self.dm.nnTiBdqjAG(vk)

    def AiYoloSetModelMemory(self, index: int, addr: int, size: int, pwd: str):
        return self.dm.nvqdekWNDozQ(index, addr, size, pwd)

    def EnumProcess(self, name: str):
        return self.dm.nzkuasfQVYQ(name)

    def EnableKeypadSync(self, en: int, time_out: int):
        return self.dm.oDTpS(en, time_out)

    def RightClick(self):
        return self.dm.oGitD()

    def GetColorHSV(self, x: int, y: int):
        return self.dm.oJelbnGKD(x, y)

    def FoobarTextPrintDir(self, hwnd: int, dir: int):
        return self.dm.oWQDyYmt(hwnd, dir)

    def CreateFoobarRoundRect(self, hwnd: int, x: int, y: int, w: int, h: int, rw: int, rh: int):
        return self.dm.oksGsjwhuyKk(hwnd, x, y, w, h, rw, rh)

    def GetScreenHeight(self):
        return self.dm.oyyTpQgJaANp()

    def GetDiskReversion(self, index: int):
        return self.dm.pJFCKtx(index)

    def GetColorBGR(self, x: int, y: int):
        return self.dm.pKINlrcE(x, y)

    def FoobarFillRect(self, hwnd: int, x1: int, y1: int, x2: int, y2: int, color: str):
        return self.dm.pSPNllTuoiYQUsn(hwnd, x1, y1, x2, y2, color)

    def FindColor(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float, dir: int):
        return self.dm.pkLMDB(x1, y1, x2, y2, color, sim, dir)

    def GetDictInfo(self, str: str, font_name: str, font_size: int, flag: int):
        return self.dm.prAN(str, font_name, font_size, flag)

    def InitCri(self):
        return self.dm.ptVrXAoq()

    def DisableScreenSave(self):
        return self.dm.puAlLzuFGgd()

    def GetDiskSerial(self, index: int):
        return self.dm.pzxLCbS(index)

    def FindStrFastExS(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.qFXwI(x1, y1, x2, y2, str, color, sim)

    def MatchPicName(self, pic_name: str):
        return self.dm.qIpdWXeCbVvdrHj(pic_name)

    def GetNetTimeSafe(self):
        return self.dm.qJknzncgqy()

    def FindPicS(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir: int):
        return self.dm.qNzUdrzz(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def SetColGapNoDict(self, col_gap: int):
        return self.dm.qQvGabGirL(col_gap)

    def FindPicSimMem(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: int, dir: int):
        return self.dm.qSVCZqPD(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def CaptureGif(self, x1: int, y1: int, x2: int, y2: int, file: str, delay: int, time: int):
        return self.dm.qgVmJuFk(x1, y1, x2, y2, file, delay, time)

    def FindShape(self, x1: int, y1: int, x2: int, y2: int, offset_color: str, sim: float, dir: int):
        return self.dm.qieynv(x1, y1, x2, y2, offset_color, sim, dir)

    def ClearDict(self, index: int):
        return self.dm.qjWvnQAWSFkBWHv(index)

    def MiddleUp(self):
        return self.dm.qnGyu()

    def FoobarUnlock(self, hwnd: int):
        return self.dm.qqQpc(hwnd)

    def GetScreenData(self, x1: int, y1: int, x2: int, y2: int):
        return self.dm.quUsYhCYXfmv(x1, y1, x2, y2)

    def LoadAi(self, file: str):
        return self.dm.qubSDpEXPnb(file)

    def GetColorNum(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float):
        return self.dm.qzTpM(x1, y1, x2, y2, color, sim)

    def GetTime(self):
        return self.dm.rAraPrgnkG()

    def EnumWindowSuper(self, spec1: str, flag1: int, type1: int, spec2: str, flag2: int, type2: int, sort: int):
        return self.dm.rBanTGZk(spec1, flag1, type1, spec2, flag2, type2, sort)

    def AiYoloSetModel(self, index: int, file: str, pwd: str):
        return self.dm.rDsVLcQGjvD(index, file, pwd)

    def EnterCri(self):
        return self.dm.rVjLT()

    def WriteIniPwd(self, section: str, key: str, v: str, file: str, pwd: str):
        return self.dm.sGtrrgrSVf(section, key, v, file, pwd)

    def FindStrE(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.sKzwZ(x1, y1, x2, y2, str, color, sim)

    def FindPic(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir: int):
        return self.dm.sPgYCuLFjR(x1, y1, x2, y2, pic_name, delta_color, sim, dir)

    def BGR2RGB(self, bgr_color: str):
        return self.dm.sRVHVpsNXT(bgr_color)

    def FindColorE(self, x1: int, y1: int, x2: int, y2: int, color: str, sim: float, dir: int):
        return self.dm.sahTgi(x1, y1, x2, y2, color, sim, dir)

    def FoobarClose(self, hwnd: int):
        return self.dm.scWEhdNlxjAv(hwnd)

    def GetWindowProcessPath(self, hwnd: int):
        return self.dm.snEhZaWxNhaBzEo(hwnd)

    def KeyDownChar(self, key_str: str):
        return self.dm.swkjsGQYjfKuhJ(key_str)

    def SetExcludeRegion(self, type: int, info: str):
        return self.dm.swwBjtGwlA(type, info)

    def CopyFile(self, src_file: str, dst_file: str, over: int):
        return self.dm.tEVztf(src_file, dst_file, over)

    def BindWindowEx(self, hwnd: int, display: str, mouse: str, keypad: str, public_desc: str, mode: int):
        return self.dm.tEtluWTGikho(hwnd, display, mouse, keypad, public_desc, mode)

    def AiYoloDetectObjectsToFile(self, x1: int, y1: int, x2: int, y2: int, prob: str, iou: str, file: str, mode: int):
        return self.dm.tYJCaip(x1, y1, x2, y2, prob, iou, file, mode)

    def ReadIni(self, section: str, key: str, file: str):
        return self.dm.tZagNG(section, key, file)

    def ExitOs(self, type: int):
        return self.dm.thsxZBeb(type)

    def RegExNoMac(self, code: str, ver: str, ip: str):
        return self.dm.trQyzWPjGkDaYV(code, ver, ip)

    def GetWindowProcessId(self, hwnd: int):
        return self.dm.uGhSFL(hwnd)

    def AiYoloSortsObjects(self, objects: str, height: int):
        return self.dm.uGqMVpEgqtaHe(objects, height)

    def CmpColor(self, x: int, y: int, color: str, sim: float):
        return self.dm.uYfItGRRSY(x, y, color, sim)

    def GetMousePointWindow(self):
        return self.dm.uikirNDDuNICptR()

    def FindStrFastEx(self, x1: int, y1: int, x2: int, y2: int, str: str, color: str, sim: float):
        return self.dm.uptLVWpNwJnqND(x1, y1, x2, y2, str, color, sim)

    def SetLocale(self):
        return self.dm.uwVsWucYxfghc()

    def LockMouseRect(self, x1: int, y1: int, x2: int, y2: int):
        return self.dm.vCIPCXCbBpkqc(x1, y1, x2, y2)

    def SetWordGapNoDict(self, word_gap: int):
        return self.dm.vfDhuBsrd(word_gap)

    def UnLoadDriver(self):
        return self.dm.vfhDd()

    def SetWordGap(self, word_gap: int):
        return self.dm.viPUZjeFCcyhU(word_gap)

    def FindMultiColorEx(self, x1: int, y1: int, x2: int, y2: int, first_color: str, offset_color: str, sim: float, dir: int):
        return self.dm.vklDfoiFEKI(x1, y1, x2, y2, first_color, offset_color, sim, dir)

    def FindShapeEx(self, x1: int, y1: int, x2: int, y2: int, offset_color: str, sim: float, dir: int):
        return self.dm.vvSCmjxS(x1, y1, x2, y2, offset_color, sim, dir)

    def GetNetTime(self):
        return self.dm.wjLjV()

    def SetWordLineHeightNoDict(self, line_height: int):
        return self.dm.wubqZA(line_height)

    def DeleteIni(self, section: str, key: str, file: str):
        return self.dm.wyTzIEBzDj(section, key, file)

    def FoobarDrawText(self, hwnd: int, x: int, y: int, w: int, h: int, text: str, color: str, align: int):
        return self.dm.xFCkjoKpQnisq(hwnd, x, y, w, h, text, color, align)

    def GetScreenDepth(self):
        return self.dm.xIat()

    def GetForegroundFocus(self):
        return self.dm.xbNTYkCTFVc()

    def FindPicSimMemEx(self, x1: int, y1: int, x2: int, y2: int, pic_info: str, delta_color: str, sim: int, dir: int):
        return self.dm.xbsbrHUjxQ(x1, y1, x2, y2, pic_info, delta_color, sim, dir)

    def DownCpu(self, type: int, rate: int):
        return self.dm.xncgeKciU(type, rate)

    def DeleteFolder(self, folder_name: str):
        return self.dm.xosxsx(folder_name)

    def EnableFontSmooth(self):
        return self.dm.xpACahYw()

    def SetClipboard(self, data: str):
        return self.dm.yCkslUeeqKmCnGw(data)

    def WaitKey(self, key_code: int, time_out: int):
        return self.dm.yJClmWQouxexf(key_code, time_out)

    def UseDict(self, index: int):
        return self.dm.yUsLzVrmPYAllS(index)

    def ReadFileData(self, file: str, start_pos: int, end_pos: int):
        return self.dm.ywxdV(file, start_pos, end_pos)

    def Stop(self, id: int):
        return self.dm.zRjf(id)

    def GetMachineCode(self):
        return self.dm.zYJaDkgFvBtUoVo()

    def ClientToScreen(self, hwnd, x, y):
        return self.dm.pUIwG(hwnd, x, y)


class DMKM:
    VK_CODE = {
        'back':0x08,
        'backspace': 0x08,
        'tab': 0x09,
        'clear': 0x0C,
        'enter': 0x0D,
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12,
        'pause': 0x13,
        'caps_lock': 0x14,
        'esc': 0x1B,
        'spacebar': 0x20,
        'space': 0x20,
        'page_up': 0x21,
        'page_down': 0x22,
        'end': 0x23,
        'home': 0x24,
        'left': 0x25,
        'up': 0x26,
        'right': 0x27,
        'down': 0x28,
        'select': 0x29,
        'print': 0x2A,
        'execute': 0x2B,
        'print_screen': 0x2C,
        'ins': 0x2D,
        'del': 0x2E,
        'help': 0x2F,
        '0': 0x30,
        '1': 0x31,
        '2': 0x32,
        '3': 0x33,
        '4': 0x34,
        '5': 0x35,
        '6': 0x36,
        '7': 0x37,
        '8': 0x38,
        '9': 0x39,
        'a': 0x41,
        'b': 0x42,
        'c': 0x43,
        'd': 0x44,
        'e': 0x45,
        'f': 0x46,
        'g': 0x47,
        'h': 0x48,
        'i': 0x49,
        'j': 0x4A,
        'k': 0x4B,
        'l': 0x4C,
        'm': 0x4D,
        'n': 0x4E,
        'o': 0x4F,
        'p': 0x50,
        'q': 0x51,
        'r': 0x52,
        's': 0x53,
        't': 0x54,
        'u': 0x55,
        'v': 0x56,
        'w': 0x57,
        'x': 0x58,
        'y': 0x59,
        'z': 0x5A,
        'numpad_0': 0x60,
        'numpad_1': 0x61,
        'numpad_2': 0x62,
        'numpad_3': 0x63,
        'numpad_4': 0x64,
        'numpad_5': 0x65,
        'numpad_6': 0x66,
        'numpad_7': 0x67,
        'numpad_8': 0x68,
        'numpad_9': 0x69,
        'multiply_key': 0x6A,
        'add_key': 0x6B,
        'separator_key': 0x6C,
        'subtract_key': 0x6D,
        'decimal_key': 0x6E,
        'divide_key': 0x6F,
        'f1': 0x70,
        'f2': 0x71,
        'f3': 0x72,
        'f4': 0x73,
        'f5': 0x74,
        'f6': 0x75,
        'f7': 0x76,
        'f8': 0x77,
        'f9': 0x78,
        'f10': 0x79,
        'f11': 0x7A,
        'f12': 0x7B,
        'f13': 0x7C,
        'f14': 0x7D,
        'f15': 0x7E,
        'f16': 0x7F,
        'f17': 0x80,
        'f18': 0x81,
        'f19': 0x82,
        'f20': 0x83,
        'f21': 0x84,
        'f22': 0x85,
        'f23': 0x86,
        'f24': 0x87,
        'num_lock': 0x90,
        'scroll_lock': 0x91,
        'left_shift': 0xA0,
        'right_shift ': 0xA1,
        'left_control': 0xA2,
        'right_control': 0xA3,
        'left_menu': 0xA4,
        'right_menu': 0xA5,
        'browser_back': 0xA6,
        'browser_forward': 0xA7,
        'browser_refresh': 0xA8,
        'browser_stop': 0xA9,
        'browser_search': 0xAA,
        'browser_favorites': 0xAB,
        'browser_start_and_home': 0xAC,
        'volume_mute': 0xAD,
        'volume_down': 0xAE,
        'volume_up': 0xAF,
        'next_track': 0xB0,
        'previous_track': 0xB1,
        'stop_media': 0xB2,
        'play/pause_media': 0xB3,
        'start_mail': 0xB4,
        'select_media': 0xB5,
        'start_application_1': 0xB6,
        'start_application_2': 0xB7,
        'attn_key': 0xF6,
        'crsel_key': 0xF7,
        'exsel_key': 0xF8,
        'play_key': 0xFA,
        'zoom_key': 0xFB,
        'clear_key': 0xFE,
        '+': 0xBB,
        ',': 0xBC,
        '-': 0xBD,
        '.': 0xBE,
        '/': 0xBF,
        '`': 0xC0,
        ';': 0xBA,
        '[': 0xDB,
        '\\': 0xDC,
        ']': 0xDD,
        "'": 0xDE,
        '`': 0xC0
    }
    shift_keys = {
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0"
    }
    vk_key_map = {
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12,
        ':capslock': 0x14,
        'tab': 0x09,
        'enter': 0x0D,
        'esc': 0x1B,
        'space': 0x20,
        'backspace': 0x08,
    }

    def __init__(self, dm):
        self.dm = dm
        self.hwnd = self.dm.GetBindWindow()
        # self.init_mouse()
        # self.init_keypress()
        self.set_delay()
        self.EnableRealMouse()
    #
    # def __del__(self):
    #     self.dm.UnBindWindow()  # 可以调用stop,也可以不调用

    def EnableRealMouse(self, flag=0):
        # 0 关闭模拟
        # 1 开启模拟(斜线模拟,先快在慢)
        self.__mouse_move_flag = flag

    def release(self):
        # self.init_mouse()
        self.init_keypress()

    def init_mouse(self):
        self.LeftUp()  # 弹起会按一下
        self.RightUp()

    def init_keypress(self):
        for key in self.VK_CODE:
            self.KeyUpChar(key)

    def set_delay(self, key_delay=0.01, mouse_delay=0.01):
        self.key_delay = key_delay
        self.mouse_delay = mouse_delay

    # 按下鼠标按键
    def LeftDown(self):
        self.dm.LeftDown()

    # 松开鼠标按键
    def LeftUp(self):
        self.dm.LeftUp()

    def LeftDoubleClick(self):
        self.dm.LeftDoubleClick()

    def RightDown(self):
        self.dm.RightDown()

    def RightUp(self):
        self.dm.RightUp()

    def LeftClick(self):
        self.LeftDown()
        time.sleep(self.mouse_delay)
        self.LeftUp()

    def RightClick(self):
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()

    def MiddleDown(self):
        self.dm.MiddleDown()

    def MiddleUp(self):
        self.dm.MiddleUp()

    def KeyDownChar(self, code: str):
        code = code.lower()
        self.dm.KeyDown(self.VK_CODE[code])

    def KeyUpChar(self, code: str):
        code = code.lower()
        self.dm.KeyUp(self.VK_CODE[code])  # 弹起本质安监

    def KeyPressChar(self, code: str):
        self.KeyDownChar(code)
        time.sleep(self.key_delay)
        self.KeyUpChar(code)

    def GetCurrMousePos(self):
        now_x, now_y, res = self.dm.GetCursorPos()
        x, y = self.dm.ScreenToClient(self.hwnd, now_x, now_y)
        return x, y

    def MoveTo(self, x: int, y: int):
        self.dm.MoveTo(x,y)
        # now_x, now_y, res = self.dm.GetCursorPos()
        # if self.hwnd:
        #     x1, y1, res = self.dm.ClientToScreen(self.hwnd, x, y)
        # else:
        #     x1, y1 = x, y
        # self.MoveR(x1 - now_x, y1 - now_y)

    def MoveR(self, x: int, y: int):
        if self.__mouse_move_flag == 0:
            self.dm.MoveR(x, y)
        elif self.__mouse_move_flag == 1:
            paths = get_mouse_path(0, 0, x, y)
            for x2, y2 in paths:
                self.dm.MoveR(x2, y2)
                time.sleep(self.mouse_delay)

    def KeyPressStr(self, key_str: str, delay: float = 0.01):
        for i in key_str:
            self.KeyPressChar(i)
            time.sleep(delay)

    def slide(self, x1: int, y1: int, x2: int, y2: int, delay=1):
        self.MoveTo(x1, y1)
        time.sleep(0.01)
        self.LeftDown()
        time.sleep(0.01)
        self.MoveR(x2 - x1, y2 - y1)
        self.LeftUp()
        time.sleep(delay)

    @staticmethod
    def GetCursorPos():
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.c_long),
                ("y", ctypes.c_long)
            ]

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    # 模拟按下 Caps Lock 键
    def press_capslock(self, open=True):
        if open:
            if not user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                self.dm.KeyDown(self.vk_key_map[":capslock"])
                self.dm.KeyUp(self.vk_key_map[":capslock"])
                # self.press_controller_key(":capslock")
        else:
            if user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                # self.press_controller_key(":capslock")
                self.dm.KeyDown(self.vk_key_map[":capslock"])
                self.dm.KeyUp(self.vk_key_map[":capslock"])


class DM_CAPTURE:
    def __init__(self, dm):
        self.dm = dm
        hwnd = self.dm.GetBindWindow()
        if not hwnd:
            hwnd = self.dm.GetSpecialWindow(0)
        self.width, self.height, res = self.dm.GetClientSize(hwnd)
        pass
    def Capture(self, x1=None, y1=None, x2=None, y2=None, file="", return_bytes=False):
        if file:
            return self.dm.Capture(x1, y1, x2, y2, file)
        x1_, y1_, x2_, y2_ = 0, 0, self.width, self.height
        width_, height_ = x2_ - x1_, y2_ - y1_
        if x1 is None or y1 is None or x2 is None or y2 is None:
            x1, y1, x2, y2 = 0, 0, width_, height_
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > width_:
            x2 = width_
        if y2 > height_:
            y2 = height_
        size = (x2 - x1) * (y2 - y1) * 4
        s = time.time()
        while True:
            if time.time() - s > 10:
                raise ValueError("截图超时")
            addr = self.dm.GetScreenData(x1, y1, x2, y2)
            if not addr:
                print("获取内存地址失败,再次尝试，重新绑定测试")
                hwnd = self.dm.GetBindWindow()
                self.dm.UnBindWindow()
                res = self.dm.BindWindow(hwnd, "gdi", "window", "window", 0)
                if res:
                    print("重新绑定成功")
                time.sleep(1)
                continue
            # s = time.time()
            try:
                bgr_image = dxpyd.MiNiNumPy.read_mem_img(addr, size, y2 - y1, x2 - x1)  # 读取内存数据并转BGR格式
                break
            except ValueError:
                print("截图异常,再次尝试失败")
                time.sleep(0.1)
        # opencv_array = np.asarray(bgr_image)  # 转换为opencv格式
        # print(f"读取耗时:{time.time()-s}")
        if return_bytes:
            return bytes(bgr_image.get_memoryview())
        return bgr_image


class DM_VNC_SERVER(DM):

    def Capture(self, x1: int, y1: int, x2: int, y2: int, file: str = None):
        size = (x2 - x1) * (y2 - y1) * 4
        addr = self.GetScreenData(x1, y1, x2, y2)
        bgr_image = dxpyd.MiNiNumPy.read_mem_img(addr, size, y2 - y1, x2 - x1)  # 读取内存数据并转BGR格式
        return bytes(bgr_image.get_memoryview())


class TCP_Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            raise

    def send_request(self, func_name, *args, **kwargs):
        """
        发送请求到服务器
        :param func_name: 要调用的函数名
        :param args: 函数的位置参数
        :param kwargs: 函数的关键字参数
        :return: 服务器的响应结果
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        try:
            # 构造请求数据
            request_data = {
                "func_name": func_name,
                "args": args,
                "kwargs": kwargs
            }
            # 序列化为 JSON 并发送
            self.socket.send(json.dumps(request_data).encode('utf-8'))

            # 接收服务器的响应
            response = self._recv_response(func_name)
            return response

        except Exception as e:
            logging.error(f"Error sending request: {e}")
            raise

    def _recv_response(self, func_name):
        """接收服务器的响应"""
        try:

            # 如果是截图,则直接接受二进制数据头部大小,在接受二进制数据
            if func_name == "Capture":
                # 接收二进制数据的大小（假设大小以4字节的整数形式发送）
                size_data = self.socket.recv(4)
                if not size_data:
                    raise ValueError("Failed to receive size of binary data")

                # 解包二进制数据的大小
                result_size = struct.unpack('!I', size_data)[0]

                # 接收二进制数据
                result_data = self._recv_all(result_size)
                return result_data
            else:
                # 接收响应头（JSON 格式）
                size_data = self.socket.recv(4)
                if not size_data:
                    raise ValueError("Failed to receive size of binary data")
                # 解包二进制数据的大小
                result_size = struct.unpack('!I', size_data)[0]

                # 接收二进制数据
                result_data = self._recv_all(result_size)
                header = json.loads(result_data)

                # 检查响应状态码
                code = header.get("code")
                if code != 200:
                    message = header.get("message", "Unknown error")
                    logging.error(f"Server returned error: {code} - {message}")
                    return None

                # 如果响应包含二进制数据（如截图）
                if "result_size" in header:
                    result_size = header["result_size"]
                    result_data = self._recv_all(result_size)
                    return result_data

                # 返回普通结果
                return header.get("result")

        except Exception as e:
            logging.error(f"Error receiving response: {e}")
            raise

    def _recv_all(self, size):
        """接收指定大小的二进制数据"""
        data = b""
        while len(data) < size:
            part = self.socket.recv(size - len(data))
            if not part:
                raise ConnectionError("Connection closed unexpectedly")
            data += part
        return data

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            logging.info("Connection closed")


class DM_VNC_CAPTURE(DM_CAPTURE):
    def Capture(self, x1=None, y1=None, x2=None, y2=None, file=""):
        if file:
            return self.dm.Capture(x1, y1, x2, y2, file)
        x1_, y1_, x2_, y2_ = 0, 0, self.width, self.height
        width_, height_ = x2_ - x1_, y2_ - y1_
        if x1 is None or y1 is None or x2 is None or y2 is None:
            x1, y1, x2, y2 = 0, 0, width_, height_
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > width_:
            x2 = width_
        if y2 > height_:
            y2 = height_
        w,h = x2-x1,y2-y1
        image_bytes = self.dm.Capture(x1, y1, x2, y2)
        # bgr_image_view = dxpyd.MiNiNumPy.bytes_to_arr3d(image_bytes, height_, width_, 3).copy()
        bgr_image = dxpyd.ManagedMemoryView(shape=(h,w,3),dtype=0,bytes_data=image_bytes)  # 后续
        return bgr_image


class DM_VNC_CLIENT(DM):

    def __init__(self, ip, port):
        self.client = TCP_Client(ip, int(port))
        self.client.connect()
        super().__init__()

    def __getattribute__(self, item):
        """
        所有函数，都重载，获取函数名称，然后self.client.send_request(函数名, *args,**kwargs)
        :param item:
        :return:
        """
        if item == 'client':
            return object.__getattribute__(self, 'client')
        # 获取属性值
        attr = super().__getattribute__(item)

        # 如果属性是方法，则返回一个包装函数
        if callable(attr):
            def wrapper(*args, **kwargs):
                # 调用 self.client.send_request 发送请求
                return self.client.send_request(item, *args, **kwargs)

            return wrapper
        else:
            # 如果不是方法，则直接返回属性值
            return attr

    # 远程执行代码
    def eval(self,code):
        pass

    def exec(self,code):
        pass

# 测试代码
if __name__ == "__main__":
    dm = DM()
    dm.reg()
    res = dm.BindWindow(1181944,"normal","normal","normal",0)
    if not res:
        raise ValueError("绑定窗口失败")
    time.sleep(1)
    hwnd = dm.GetBindWindow()
    print(hwnd)
# km = DMKM(dm)
# km.EnableRealMouse(1)
# # km.MoveTo(100,100)
# km.KeyPressChar("volume_down")
#
# dm = DM_VNC()
# dm.reg()
# dm.Capture(0,0,100,100)
