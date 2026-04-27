# -*- coding: utf-8 -*-
"""
@File    : dxgame.py
@Author  : daXiong
@Date    : 2024/8/18
@Description : 
"""
import os.path
import random
import time

from dxGame.dx_core import *
from dxGame.dx_Window import Window
from dxGame.dx_MiniOpenCV import MiniOpenCV
from dxGame.dx_model import td_info
from dxGame.dx_日志类 import print_log


class DX(Window):
    def __init__(self):
        self.screenshot = None
        self.KM = None
        self.__temp_find_pic_dict = {}  # 图片缓存
        self.__temp_dict_dict = {}  # 字库缓存
        self.__dict_index = 0  # 当前字库
        self.__path = os.getcwd()
        self.debug_screen = False  # 调试截图
        self.screen_no = False  # 为真 则缓存截图
        self.temp_img = None
        self.__pwd = ""
        self.__pwd_insert_value = b"270207756@"
    def __del__(self):
        self.KM = None
        self.screenshot = None

    def set_screen(self, obj_screen):
        self.screenshot = obj_screen

    def set_km(self, obj_km):
        self.KM = obj_km

    def keep_screen(self, flag: bool):
        """
        保持屏幕
        :param flag: True,False 表示开关
        :return:
        """
        if flag:
            if self.debug_screen:
                pass
            else:
                # 等待 VNC 截图就绪（最多等待 2 秒）
                for i in range(20):
                    if hasattr(self.screenshot, 'image') and self.screenshot.image is not None:
                        break
                    time.sleep(0.1)
                    
                # 如果截图已就绪，才捕获
                if hasattr(self.screenshot, 'image') and self.screenshot.image is not None:
                    s = time.time()
                    try:
                        self.temp_img = self.screenshot.Capture()
                    except (OSError, WindowsError, SystemError) as e:
                        # 🔧 关键修复：捕获 Windows API 访问违规（0xC0000005）
                        dxpyd.debugPrint(f"⚠️ LockScreen 截图失败 (可能是访问违规): {e}")
                        # 清空 temp_img，避免使用损坏的数据
                        self.temp_img = None
                        raise
                    except Exception as e:
                        # 🔧 捕获其他异常（如图像数据损坏）
                        dxpyd.debugPrint(f"⚠️ LockScreen 截图异常: {type(e).__name__}: {e}")
                        self.temp_img = None
                        raise
                else:
                    dxpyd.debugPrint("警告：VNC 截图未就绪，无法锁定屏幕")
        self.screen_no = flag

    def __capture(self, x1: int = None, y1: int = None, x2: int = None, y2: int = None):
        if self.screen_no:
            return self.temp_img[y1:y2, x1:x2]
        else:
            _s = time.time()
            try:
                self.temp_img = self.screenshot.Capture(x1, y1, x2, y2)
            except OSError as e:
                # 🔧 捕获 Windows API 访问违规（0xC0000005）
                dxpyd.debugPrint(f"警告：截图API调用失败 (OSError): {e}")
                raise  # 向上抛出，让调用方处理
            dxpyd.debugPrint("截图耗时:%f" % (time.time() - _s))
        return self.temp_img

    def __get_pwd_insert_num(self,content):
        if len(content) > 10000:
            return 10000
        if len(content) > 5000:
            return 5000
        if len(content) > 3000:
            return 3000
        if len(content) > 1000:
            return 1000
        if len(content) > 500:
            return 500
        if len(content) > 100:
            return 100
        raise ValueError("文件内容太短,无法加密")

    def EncodeFile(self, file:str,pwd:str):
        """
        加密图片,在文件的中间插入特殊字符
        :param file:
        :param pwd:
        :return:
        """
        # 1.文件是否存在
        if not os.path.isfile(file):
            raise ValueError("文件不存在 %s" % file)
        if not os.path.exists(file):
            raise ValueError("文件不存在 %s" % file)
        # 2.文件是否加密过,如果加密过则不生效
        with open(file,"rb") as fp:
            contents = fp.read()
        if not contents:
            raise ValueError("文件为空")
        insert_num = self.__get_pwd_insert_num(contents)
        # 是否有加密，如果加密过了就不在加密
        value = contents[insert_num:insert_num + len(self.__pwd_insert_value)]
        if value == self.__pwd_insert_value:
            return False
        contents = contents[:insert_num] + self.__pwd_insert_value + pwd.encode() + contents[insert_num:]
        with open(file,"wb") as fp:
            fp.write(contents)
            return True
    def __readDecodeFile(self, file:str, pwd:str):
        """
        解密文件
        :param file:
        :param pwd:
        :return:
        """
        # 1.文件是否存在
        if not os.path.exists(file):
            raise ValueError("文件不存在 %s" % file)
        # 2.文件是否加密过,如果加密过则不生效
        with open(file,"rb") as fp:
            contents = fp.read()
        if not contents:
            raise ValueError("文件为空")
        insert_num = self.__get_pwd_insert_num(contents)
        # 是否有加密，没有则直接返回内容
        value = contents[insert_num:insert_num + len(self.__pwd_insert_value)]
        if value != self.__pwd_insert_value:
            return contents
        value = contents[insert_num:insert_num + len(self.__pwd_insert_value) + len(pwd.encode())]
        value2 = self.__pwd_insert_value + pwd.encode()
        if value != value2:
            # 无法解密
            return ""
        else:
            # 在中间位置删除lenght个字节
            l = len(self.__pwd_insert_value) + len(pwd.encode())
            contents = contents[:insert_num] + contents[insert_num + l:]
            return contents

    def DecodeFile(self, file:str,pwd:str):
        """
        解密文件
        :param file:
        :param pwd:
        :return:
        """
        # 1.文件是否存在
        if not os.path.exists(file):
            raise ValueError("文件不存在 %s" % file)
        # 2.文件是否加密过,如果加密过则不生效
        with open(file,"rb") as fp:
            contents = fp.read()
        if not contents:
            raise ValueError("文件为空")
        insert_num = self.__get_pwd_insert_num(contents)
        value = contents[insert_num:insert_num + len(self.__pwd_insert_value) + len(pwd.encode())]
        value2 = self.__pwd_insert_value + pwd.encode()
        if value != value2:
            # 无法解密
            return False
        else:
            # 在中间位置删除lenght个字节
            l = len(self.__pwd_insert_value) + len(pwd.encode())
            contents = contents[:insert_num] + contents[insert_num + l:]
            with open(file,"wb") as fp:
                fp.write(contents)
                return True
    def SetPicPwd(self, pwd):
        self.__pwd = pwd

    def Capture(self, x1: int = None, y1: int = None, x2: int = None, y2: int = None, file: str = None) -> memoryview:
        image = self.__capture(x1, y1, x2, y2)
        if file:
            if not file.endswith(".bmp"):
                raise ValueError("文件名必须以.bmp结尾")
            MiniOpenCV.imwrite(file, image)
        return image

    def SetPath(self, path: str):
        self.__path = path
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        return True

    def SetDict(self, index: int, file: str):
        if index < 0 or index > 9:
            raise ValueError("index=%d 不在0-9之间" % index)
        if not os.path.exists(file):
            raise FileNotFoundError(file)

        dic = dict()  # {key1:[arr1],key2:[arr1,arr2],key3:[arr1,arr2,...]} 如果分层三个,kyes,arrs,
        with open(file, "r", encoding="gbk") as fp:
            for line in fp.readlines():
                if "$" in line:
                    line = line.split("$")
                    string = line[0]
                    arr = dxpyd.string2arr2d(string)
                    name = line[1]
                    result = dic.get(name, None)
                    if result is None:
                        dic[name] = [arr]
                    else:
                        dic[name].append(arr)  # 下标字符串，可能有对应多个点阵，因为同名
        # self._allUseDict[index] = dic
        # self.UseDict(index)
        self.__temp_dict_dict.update({index: dic})
        self.__dict_index = index
        return True

    def UseDict(self, index: int):
        self.__dict_index = index

    def CmpColor(self, x: int, y: int, color: str, sim: float) -> bool:
        img = self.__capture()
        s = time.time()
        fp = dxpyd.CmpColor(color)
        res = fp.cmp_color(img, x, y, sim)
        dxpyd.debugPrint("CmpColor耗时:%f" % (time.time() - s))
        return res

    def IsDisplayDead(self, x1: int, y1: int, x2: int, y2: int, t: float, sim: float = 1.0):
        s = time.time()
        try:
            image1 = self.Capture(x1, y1, x2, y2)
        except OSError as e:
            dxpyd.debugPrint(f"警告：IsDisplayDead 截图失败 (OSError): {e}")
            return True  # 截图失败认为画面卡死
        while True:
            time.sleep(0.1)
            try:
                image2 = self.Capture(x1, y1, x2, y2)
            except OSError as e:
                dxpyd.debugPrint(f"警告：IsDisplayDead 截图失败 (OSError): {e}")
                return True  # 截图失败认为画面卡死
            fp = dxpyd.FindPic(image2, "000000")  # todo 未设置缓冲区
            # 开始找图
            _result = fp.find_pic(image1, sim, 0, 0)
            if not _result[0]:
                return False
            if time.time() - s > t:
                return True

    def FindPic(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir_: int) -> Tuple[int, int, int]:
        dxpyd.debugPrint(f"FindPic:start {x1, y1, x2, y2, pic_name, delta_color, sim, dir_}")
        for i in [x1, y1, x2, y2, dir_]:
            if not isinstance(i, int):
                raise TypeError("参数类型不符合 i= %s" % i)
        if not isinstance(sim, float):
            raise TypeError("sim=%s" % sim)
        if not isinstance(pic_name, str):
            raise TypeError("pic_name=%s" % pic_name)

        if not pic_name:
            raise ValueError("pic_name=%d 为空" % pic_name)
        _img = self.__capture(x1, y1, x2, y2)
        if len(delta_color) == 2 and type(delta_color) == str:
            _img = MiniOpenCV.cvtColor(_img, MiniOpenCV.COLOR_BGR2GRAY)
        dxpyd.debugFunc(MiniOpenCV.imshow, "img", _img)
        dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
        h, w = _img.shape[:2]
        if h == 0 or w == 0:
            raise ValueError("图片为空")
        pic_names = pic_name.split("|")
        _s = time.time()
        # 如果是模板匹配,则转灰度图
        if dir_ == 1:
            _img_gray = MiniOpenCV.cvtColor(_img, MiniOpenCV.COLOR_BGR2GRAY)
        for index, name in enumerate(pic_names):
            file = os.path.join(self.__path, name)
            if not os.path.exists(file):
                raise FileNotFoundError(file)
            file_bytes = self.__readDecodeFile(file, self.__pwd) # 解密文件
            arr3d_temp = MiniOpenCV.imread_decode(file_bytes) # 读取图片

            h2, w2 = arr3d_temp.shape[:2]
            if h2 > h or w2 > w:
                raise ValueError(f"找图范围小于模板图片 name=%s" % name)
            if dir_ == 0:
                fp = dxpyd.FindPic(arr3d_temp, delta_color)  # todo 未设置缓冲区
                # 开始找图
                _result = fp.find_pic(_img, sim, dir_, 0)

                dxpyd.debugPrint(f"模板图片大小:{arr3d_temp.shape}")
                dxpyd.debugFunc(MiniOpenCV.imshow, "arr3d_temp", arr3d_temp)
                dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
            elif dir_ == 1:
                arr3d_temp_gray = MiniOpenCV.cvtColor(arr3d_temp, MiniOpenCV.COLOR_BGR2GRAY)
                fp = dxpyd.FindPicTemplate(_img_gray, arr3d_temp_gray, sim)
                _result = fp.template_match(0)
                if not _result:
                    _result = [0, 0, 0]

                dxpyd.debugPrint(f"模板图片大小:{arr3d_temp.shape}")
                dxpyd.debugFunc(MiniOpenCV.imshow, "arr3d_temp", arr3d_temp_gray)
                dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
            elif dir_ == 2:
                image1_hsv = MiniOpenCV.cvtColor(_img, MiniOpenCV.COLOR_BGR2HSV)
                image1_range = MiniOpenCV.inRange(image1_hsv, *delta_color)
                image2_hsv = MiniOpenCV.cvtColor(arr3d_temp, MiniOpenCV.COLOR_BGR2HSV)
                image2_range = MiniOpenCV.inRange(image2_hsv, *delta_color)
                fp = dxpyd.FindPicTemplate(image1_range, image2_range, sim)
                _result = fp.template_match(0)
                if not _result:
                    _result = [0, 0, 0]

                dxpyd.debugFunc(MiniOpenCV.imshow, "image1_range", image1_range)
                dxpyd.debugPrint(f"模板图片大小:{arr3d_temp.shape}")
                dxpyd.debugFunc(MiniOpenCV.imshow, "arr3d_temp", image2_range)
                dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
            elif dir_ == 5: # opencv模板匹配
                import numpy as np,cv2
                mv_templ = arr3d_temp.get_memoryview()
                templ = np.array(mv_templ)
                mv_image = _img.get_memoryview()
                image = np.array(mv_image)
                # cv2.imshow("image", image)
                # cv2.imshow("templ", templ)
                # cv2.waitKey(0)
                result = cv2.matchTemplate(image, templ, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                yloc, xloc = np.where(result >= sim)
                if len(xloc):
                    _result= [1, max_loc[0], max_loc[1]]
                else:
                    _result = [0, 0, 0]
            else:
                raise ValueError("暂时不支持该方法 dir_=%d" % dir_)
            if _result[0]:
                dxpyd.debugPrint(f"找图耗时:%f,结果:%s" % (time.time() - _s, [index + 1, _result[1] + x1, _result[2] + y1]))
                return index + 1, _result[1] + x1, _result[2] + y1
        return 0, 0, 0

    def FindPicEx(self, x1: int, y1: int, x2: int, y2: int, pic_name: str, delta_color: str, sim: float, dir_: int) -> Tuple[int, int, int]:
        dxpyd.debugPrint(f"FindPicEx:start {x1, y1, x2, y2, pic_name, delta_color, sim, dir_}")
        for i in [x1, y1, x2, y2, dir_]:
            if not isinstance(i, int):
                raise TypeError("参数类型不符合 i= %s" % i)
        if not isinstance(sim, float):
            raise TypeError("sim=%s" % sim)
        if not isinstance(pic_name, str):
            raise TypeError("pic_name=%s" % pic_name)

        if not pic_name:
            raise ValueError("pic_name=%d 为空" % pic_name)
        _img = self.__capture(x1, y1, x2, y2)
        if len(delta_color) == 2:
            _img = MiniOpenCV.cvtColor(_img, MiniOpenCV.COLOR_BGR2GRAY)
        dxpyd.debugFunc(MiniOpenCV.imshow, "img", _img)
        dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
        h, w = _img.shape[:2]
        pic_names = pic_name.split("|")
        _s = time.time()
        res_list = []
        # 如果是模板匹配,则转灰度图
        if dir_ == 1:
            _img_gray = MiniOpenCV.cvtColor(_img, MiniOpenCV.COLOR_BGR2GRAY)
        for index, name in enumerate(pic_names):
            file = os.path.join(self.__path, name)
            if not os.path.exists(file):
                raise FileNotFoundError(file)
            file_bytes = self.__readDecodeFile(file, self.__pwd)  # 解密文件
            arr3d_temp = MiniOpenCV.imread_decode(file_bytes)
            dxpyd.debugPrint(f"模板图片大小:{arr3d_temp.shape}")
            dxpyd.debugFunc(MiniOpenCV.imshow, "arr3d_temp", arr3d_temp)
            dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
            h2, w2 = arr3d_temp.shape[:2]
            if h2 > h or w2 > w:
                raise ValueError(f"找图范围小于模板图片 name=%s" % name)
            if dir_ == 0:
                fp = dxpyd.FindPic(arr3d_temp, delta_color)  # todo 未设置缓冲区
                # 开始找图
                _result = fp.find_pic(_img, sim, dir_, 1)
                if _result:
                    _result = [[index + 1, x + x1, y + y1] for x, y in _result]
                    res_list.extend(_result)
            elif dir_ == 1:
                arr3d_temp_gray = MiniOpenCV.cvtColor(arr3d_temp, MiniOpenCV.COLOR_BGR2GRAY)
                fp = dxpyd.FindPicTemplate(_img_gray, arr3d_temp_gray, sim)
                _result = fp.template_match(1)
                if _result:
                    _result = [[index + 1, x + x1, y + y1] for p, x, y in _result]
                    res_list.extend(_result)
            else:
                raise ValueError("暂时不支持该方法 dir_=%d" % dir_)

        dxpyd.debugPrint(f"FindPicEx 找图耗时:%f,结果:%s" % (time.time() - _s, _result))
        return res_list

    def _ocr(self, x1: int, y1: int, x2: int, y2: int, color_format: str, sim: float, ex: Union[str, int], string: str = ""):
        if not self.__temp_dict_dict:
            raise ValueError("请先设置字库")
        dxpyd.debugPrint(f"Ocr:start {x1, y1, x2, y2, color_format, sim}")
        for i in [x1, y1, x2, y2]:
            if not isinstance(i, int):
                raise TypeError("参数类型不符合 i= %s" % i)
        if not isinstance(sim, float):
            raise TypeError("sim=%s" % sim)
        if not isinstance(color_format, str):
            raise TypeError("color_format=%s" % color_format)

        if not color_format:
            raise ValueError("color_format=%d 为空" % color_format)
        _img = self.__capture(x1, y1, x2, y2)
        dxpyd.debugFunc(MiniOpenCV.imshow, "img", _img)
        dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
        _s = time.time()
        _dict_dict = self.__temp_dict_dict[self.__dict_index]
        _ocr = dxpyd.Ocr(_dict_dict, _img, color_format)
        dxpyd.debugPrint("Ocr初始化耗时:%f" % (time.time() - _s,))
        if not string:
            _result = _ocr.ocr(sim)[ex]
        else:
            _result = _ocr.FindStr(string, sim)[ex]
        if ex and _result:
            _result = [[_, x1 + _x1, y1 + _y1, x1 + _x2, y1 + _y2] for _, _x1, _y1, _x2, _y2 in _result]

        dxpyd.debugFunc(MiniOpenCV.imshow, "gray", _ocr.get_name("arr2d"))
        dxpyd.debugFunc(MiniOpenCV.waitKey, 0)
        color_arr2d = _ocr.get_name("color_arr2d")
        _r, _c = color_arr2d.shape[:2]
        dxpyd.debugPrint("字符串格式:%s" % [color_arr2d[i, j] for j in range(_c) for i in range(_r)])
        dxpyd.debugPrint(f"Ocr耗时:%f,结果:%s" % (time.time() - _s, _result))
        return _result

    def FindStr(self, x1: int, y1: int, x2: int, y2: int, string: str, color_format: str, sim: float):
        result_ex = self._ocr(x1, y1, x2, y2, color_format, sim, 1, string)
        if result_ex:
            return result_ex[0][:3]  # 取第一个结果
        return 0, 0, 0

    def FindStrEx(self, x1: int, y1: int, x2: int, y2: int, string: str, color_format: str, sim: float):
        return self._ocr(x1, y1, x2, y2, color_format, sim, 1, string)

    def OcrNum(self, x1, y1, x2, y2, dir_path, color_format, sim, dir_):
        num_dict = {}
        # 遍历图像,并挨个识别
        for i in range(10):
            img_num = dir_path + os.path.sep + f"{i}.bmp"
            if dir_ == 1:
                res_list = self.FindPicEx(x1, y1, x2, y2, img_num, color_format, sim, dir_)
                for index, x, y in res_list:
                    num_dict.update({x: i})


        # 排序字典
        new_num_list = sorted(num_dict.items(), key=lambda x: x[0])  # 对x轴进行排序

        # 遍历并拼接数字
        nums = "".join([str(new_num[1]) for new_num in new_num_list])
        try:
            return nums
        except:
            return ""

    def Ocr(self, x1: int, y1: int, x2: int, y2: int, color_format: str, sim: float):
        return self._ocr(x1, y1, x2, y2, color_format, sim, 0)

    def OcrEx(self, x1: int, y1: int, x2: int, y2: int, color_format: str, sim: float):
        return self._ocr(x1, y1, x2, y2, color_format, sim, 1)

    def KeyDown(self, key: int):
        return self.KM.KeyDown(key)

    def KeyUp(self, key: int):
        return self.KM.KeyUp(key)

    def KeyDownChar(self, key: str):
        return self.KM.KeyDownChar(key)

    def KeyUpChar(self, key: str):
        return self.KM.KeyUpChar(key)

    def GetCursorPos(self):
        return self.KM.GetCurrMousePos()

    def MoveR(self, rx, ry):
        return self.KM.MoveR(rx, ry)

    def SetMouseDelay(self, delay):
        return self.KM.SetMouseDelay(delay)

    def SetKeypadDelay(self, delay):
        return self.KM.SetKeypadDelay(delay)

    def KeyState(self, HidKeyCode: int):
        return self.KM.KeyState(HidKeyCode)

    def slide(self, x1, y1, x2, y2, delay=1):
        return self.KM.slide(x1, y1, x2, y2, delay)

    def input(self, string: str):
        return self.KM.input(string)

    def KeyPressChar(self, key_str):
        # 🔧 性能监控：记录按键操作
        from app.stability_optimizer import vnc_performance_monitor
        vnc_performance_monitor.record_km_keypress()
        return self.KM.KeyPressChar(key_str)

    def MoveTo(self, x, y):
        # 🔧 性能监控：记录移动操作
        from app.stability_optimizer import vnc_performance_monitor
        vnc_performance_monitor.record_km_move()
        try:
            return self.KM.MoveTo(int(x), int(y))
        except OSError as e:
            # 🔧 捕获访问违规错误
            vnc_performance_monitor.record_km_error()
            raise

    def LeftClick(self):
        # 🔧 性能监控：记录点击操作（注意：km_稳妥移动点击中已经记录了，这里避免重复）
        # from app.stability_optimizer import vnc_performance_monitor
        # vnc_performance_monitor.record_km_click()
        return self.KM.LeftClick()

    def LeftDoubleClick(self):
        return self.KM.LeftDoubleClick()

    def RightDoubleClick(self):
        return self.KM.RightDoubleClick()

    def RightClick(self):
        return self.KM.RightClick()

    def LeftDown(self):
        return self.KM.LeftDown()

    def LeftUp(self):
        return self.KM.LeftUp()

    def SendString(self, str_):
        return self.KM.input(str_)

    def KeyPressStr(self, key_str, delay):
        """
        :param key_str: 字符串，如"123abc"
        :param delay: 间隔延迟，单位秒
        :return:
        """
        return self.KM.KeyPressStr(key_str, delay)
    # region 额外的函数，可用可不用，当使用时，需要提前设置好大漠

def is_ms(dx=None, ms=None, find_func=None):
    """
    :param dx: 大漠
    :param ms: 描述特征
    :param find_func: 找图函数，当find_func为真，则不使用大漠找图
    :return:
    """
    if find_func:
        return find_func(ms)

    if len(ms) == 4:
        ret = dx.CmpColor(*ms)
        if ret:
            x, y = ms[0], ms[1]
        else:
            x, y = 0, 0
    elif len(ms) == 7:
        if ms[4][-4:] == ".bmp":
            raise ValueError("ms参数错误,找图应该为8个参数位")
        if type(ms[-2]) in [float, int]:
            ret, x, y = dx.FindColor(*ms)  # 找色
        elif type(ms[-2]) in [str]:
            ret, x, y = dx.FindStr(*ms)  # 找字
    elif len(ms) == 8:
        if ".bmp" in ms[4] or is_chinese(ms[4]):
            ret, x, y = dx.FindPic(*ms)  # 找图
        else:
            ret, x, y = dx.FindMultiColor(*ms)  # 多点找色
    else:
        print(f"error {ms}")
        raise ValueError("ms特征格式不对")
    return ret, x, y


# 遍历查找，找到则返回真
def for_ms(dx=None, ms_list=None, func=None, useDict=0):
    """
    :param dx: 大漠对象
    :param ms_list: 描述特征列表
    :param func: 找图函数，当为真时，不适用大漠找图
    :param useDict:
    :return:
    """
    res = 0
    index, x, y = 0, 0, 0
    
    # 🔧 关键修复：在 keep_screen 前检查 VNC 状态
    try:
        dx.keep_screen(True)
    except (OSError, WindowsError, SystemError) as e:
        # 截图失败，可能是 VNC 连接断开
        dxpyd.debugPrint(f"⚠️ for_ms keep_screen 失败: {e}")
        return 0, 0, 0
    except Exception as e:
        dxpyd.debugPrint(f"⚠️ for_ms keep_screen 异常: {type(e).__name__}: {e}")
        return 0, 0, 0
    
    dx.UseDict(useDict)
    if not ms_list:
        raise ValueError("ms_list为空")
    
    for index, ms in enumerate(ms_list):
        try:
            res, x, y = is_ms(dx, ms, func)
            if res:
                break
        except (OSError, WindowsError, SystemError) as e:
            # 🔧 捕获找图过程中的访问违规
            dxpyd.debugPrint(f"⚠️ is_ms 异常 (可能 VNC 断开): {e}")
            res, x, y = 0, 0, 0
            break
        except Exception as e:
            dxpyd.debugPrint(f"⚠️ is_ms 未知异常: {type(e).__name__}: {e}")
            res, x, y = 0, 0, 0
            break
    
    dx.UseDict(0)
    
    try:
        dx.keep_screen(False)
    except Exception as e:
        dxpyd.debugPrint(f"⚠️ for_ms keep_screen(False) 异常: {e}")
    
    if res:
        index = index + 1
    else:
        index = 0
    return index, x, y


def for_ms_debug(dx=None, ms_list=None, func=None, useDict=0):
    """
    :param dx: 大漠对象
    :param ms_list: 描述特征列表
    :param func: 找图函数，当为真时，不适用大漠找图
    :param useDict:
    :return:
    """
    res = 0
    index, x, y = 0, 0, 0
    dx.keep_screen(True)
    dx.UseDict(useDict)
    if not ms_list:
        raise ValueError("ms_list为空")
    for index, ms in enumerate(ms_list):
        res, x, y = is_ms(dx, ms, func)
        if res:
            break
    dx.UseDict(0)
    dx.keep_screen(False)
    if res:
        index = index + 1
    else:
        index = 0
    return index, x, y


# 判断字符串是否有汉字
def is_chinese(string):
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """
    if type(string) == int or type(string) == float:
        return False
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


# 获取特征中的名称
def get_ms_name(ms):
    if len(ms) == 4:
        return ms[2]
    if len(ms) == 7:
        return ms[4]
    if len(ms) == 8:
        return ms[4]
    raise ValueError("ms格式不对")


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, list):
            return Point(self.x + other[0], self.y + other[1])
        if isinstance(other, tuple):
            return Point(self.x + other[0], self.y + other[1])
        elif isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Unsupported operand type(s) for +: 'MyInteger' and '{}'".format(type(other).__name__))


def for_ms_row(row, ms_list, func=None, useDict=0, debug=None, use_cache=False) -> Tuple[int, int, int]:
    """
    :param row: row
    :param ms_list: 描述特征列表
    :param func: 找图函数，当为真时，不适用大漠找图
    :param useDict: 字库
    :param debug: 是否显示
    :param use_cache: ✅ 是否使用截图缓存（默认False，保持向后兼容）
                      注意：use_cache=True 时，需要外部手动调用 keep_screen(True/False)
    :return:
    """
    dx = td_info[row].dx  # 需要在外部定义td_info
    
    # 截图功能状态检查
    if not _check_screenshot_status(dx, row):
        return 0, 0, 0
    
    # ✅ 新增：如果启用缓存模式，期望外部已经调用了 keep_screen(True)
    # 此时 for_ms 内部不会再重新截图，而是使用缓存的截图
    res, x, y = for_ms(dx, ms_list=ms_list, func=func, useDict=useDict)
    
    if debug:
        if res:
            lv = 0
            ms = get_ms_name(ms_list[res - 1])
        else:
            lv = 1
            ms = ms_list
        print_log(row, (res, x, y, ms), lv=lv)
    return res, x, y


def _check_screenshot_status(dx, row) -> bool:
    """
    检查截图功能是否正常
    
    Args:
        dx: DX 对象
        row: 行号
    
    Returns:
        bool: 截图功能是否正常
    """
    try:
        # 检查 screenshot 对象是否存在
        if not hasattr(dx, 'screenshot') or dx.screenshot is None:
            from app.public_function import show_log
            show_log(row, "❌ 截图对象未初始化！")
            return False
        
        # 🔧 关键修复：检查 VNC 是否超过 1 分钟未成功截图
        vnc = dx.screenshot
        if hasattr(vnc, 'last_success_time'):
            idle_time = time.time() - vnc.last_success_time
            if idle_time > 60:
                from app.public_function import show_log
                show_log(row, f"⚠️ VNC 已超过 {int(idle_time)} 秒未响应，拒绝截图以避免崩溃")
                return False
        
        # 检查 VNC 连接状态（如果使用 VNC）
        if hasattr(dx.screenshot, 'client'):
            # 优化：不仅检查 client 是否为 None，还要检查是否有有效的截图数据
            has_valid_client = (
                dx.screenshot.client is not None and 
                hasattr(dx.screenshot, 'image') and 
                dx.screenshot.image is not None
            )
            
            if not has_valid_client:
                from app.public_function import show_log
                # 只在第一次或每 10 次错误时打印，避免刷屏
                if not hasattr(dx, '_vnc_error_count'):
                    dx._vnc_error_count = 0
                
                # 降低日志频率：从每 5 次改为每 10 次
                if dx._vnc_error_count == 0 or dx._vnc_error_count % 10 == 0:
                    # 区分不同的错误类型
                    if dx.screenshot.client is None:
                        show_log(row, "⚠️ VNC 客户端未连接（可能正在重连）")
                    elif dx.screenshot.image is None:
                        show_log(row, "⚠️ VNC 截图数据为空（可能初始化中）")
                    else:
                        show_log(row, "❌ VNC 客户端未连接！")
                        if dx._vnc_error_count == 0:
                            show_log(row, "   请检查：")
                            show_log(row, "   1. 模拟器是否正在运行")
                            show_log(row, "   2. VNC 服务是否启动")
                            show_log(row, "   3. 尝试重启模拟器并等待 2-3 分钟")
                
                dx._vnc_error_count += 1
                return False
            else:
                # VNC 连接正常，重置错误计数
                if hasattr(dx, '_vnc_error_count'):
                    dx._vnc_error_count = 0
        
        # 检查是否有截图数据
        if hasattr(dx.screenshot, 'image') and dx.screenshot.image is None:
            from app.public_function import show_log
            if not hasattr(dx, '_screenshot_none_count'):
                dx._screenshot_none_count = 0
            
            if dx._screenshot_none_count == 0 or dx._screenshot_none_count % 20 == 0:
                show_log(row, "⚠️ 截图数据为空，可能是初始化中...")
            
            dx._screenshot_none_count += 1
            # 允许一定的容错，不立即返回 False
        
        return True
        
    except Exception as e:
        from app.public_function import show_log
        show_log(row, f"❌ 截图状态检查异常：{e}")
        return False


def for_ms_row_all(row, ms_list, func=None, useDict=0, debug=None):
    dx = td_info[row].dx
    dx.keep_screen(True)
    dx.UseDict(useDict)
    result = []
    if not ms_list:
        raise ValueError("ms_list为空")
    for index, ms in enumerate(ms_list):
        res, x, y = is_ms(dx, ms, func)
        if res:
            result.append([index + 1, x, y])
        if debug:
            if res:
                lv = 0
                ms = get_ms_name(ms_list[res - 1])
            else:
                lv = 1
                ms = ms_list
            print_log(row, (res, x, y, ms), lv=lv)
    dx.UseDict(0)
    dx.keep_screen(False)

    return result
def for_ms_row_all_ex(row,ms_list):
    dx = td_info[row].dx
    dx.keep_screen(True)
    result = []
    if not ms_list:
        raise ValueError("ms_list为空")
    for index, ms in enumerate(ms_list):
        res = dx.FindPicEx(*ms)
        if res:
            result.extend(res)
    dx.UseDict(0)
    dx.keep_screen(False)
    return result


# 等待特征出现
def wait_for_ms(row: int, ms_list: list, for_num=15, delay=1):
    for i in range(for_num):
        res, x, y = for_ms_row(row, ms_list)
        if res:
            return res
        time.sleep(delay)
    return 0


def find_click(row: int, ms_list: list, offset=(0, 0), button="left", for_num=10, click_flag=True, update=None, delay=1,moveR=(),click_num=1,click_num_delay=1):
    """


    :param row: 序号
    :param ms_list:找图特征列表
    :param offset: 偏移点击坐标
    :param button: 点击按钮类型，left,right
    :param for_num: 循环次数
    :param click_flag: 是否点击
    :param update: 是否点击后画面有变化
    :param click_num: 点击几次
    :param click_num_delay: 点击几次的每次间隔时间
    :return:
    """
    update_flag = False
    for i in range(for_num):
        res, x, y = for_ms_row(row, ms_list)
        if res:
            if click_flag:
                if isinstance(offset, Point):
                    x, y = offset.x, offset.y
                else:
                    x, y = x + offset[0], y + offset[1]
                for j in range(click_num):
                    click(row, x, y, button, delay=click_num_delay)
                if moveR:
                    td_info[row].dx.MoveR(moveR[0], moveR[1])
            if update:
                for i in range(10):
                    if for_ms_row(row, ms_list)[0]:
                        time.sleep(1)
                        continue
                    return True
            return True
        time.sleep(delay)
    return False


def click(row, x, y, button="left", delay=1, update=None, offset=(1, 5), moveR=(0, 0),move_delay=0.01):
    _x = random.randint(offset[0], offset[1])
    _y = random.randint(offset[0], offset[1])
    x, y = x + _x, y + _y
    # print_log(row, f"点击{x=},{y=}")
    dx = td_info[row].dx  # 需要在外部定义td_info
    if update:
        img1 = dx.Capture()
    dx.MoveTo(x, y)
    if button == "left":
        dx.LeftClick()
    elif button == "right":
        dx.RightClick()
    elif button == "double":
        dx.LeftDoubleClick()
    time.sleep(delay)
    if not (moveR[0] == moveR[1] == 0):
        dx.MoveR(moveR[0], moveR[1])
    time.sleep(move_delay)
    if update:
        for i in range(10):
            img2 = dx.Capture()
            if dxpyd.MiNiNumPy.array_equal(img1, img2):
                return True
            time.sleep(1)


def click_update(row, loc, ms_list, for_num=10, delay=1):
    print_log(row, f"点击{loc=}")
    for i in range(for_num):
        if for_ms_row(row, ms_list)[0]:
            return True
        click(row, *loc)
        time.sleep(delay)


def input_row(row, string, location, delay=0.01):
    dx = td_info[row].dx
    dx.MoveTo(*location)
    time.sleep(0.1)
    dx.LeftClick()
    dx.KeyPressStr(string, delay)


def open_face(row, ms_list, ms_list2=None, loc=(-1, -1), for_num=10):
    """
    :param row:         行号,用于区分线程
    :param ms_list:     打开界面后的特征
    :param ms_list2:    找图点击特征
    :param loc:         点击后,界面打开
    :param for_num:     循环次数
    :return:
    """
    if not ms_list2 and loc[0] == -1:
        raise "open_face 参数错误 %s,%s" % (ms_list2, loc)
    for i in range(for_num):
        if for_ms_row(row, ms_list)[0]:
            return True
        if loc[0] == -1:
            find_click(row, ms_list2)
        else:
            click(row, *loc)
        print("open_face %d 次, %s" % (i + 1, ms_list))


def close_face(row, ms_list, ms_list2=None, loc=(-1, -1), for_num=10):
    """
    :param row:         行号,用于区分线程
    :param ms_list:     找不到界面就算关闭
    :param ms_list2:    找图点击特征
    :param loc:         点击后,界面打开
    :param for_num:     循环次数
    :return:
    """
    if not ms_list2 and loc[0] == -1:
        raise "open_face 参数错误 %s,%s" % (ms_list2, loc)
    for i in range(for_num):
        if not for_ms_row(row, ms_list)[0]:
            return True
        if loc[0] == -1:
            find_click(row, ms_list2)
        else:
            click(row, *loc)
        print("close_face %d 次, %s" % (i + 1, ms_list))


def is_for_ms_row(row, ms_list, func=None, useDict=0, debug=None):
    dx = td_info[row].dx
    res, x, y = for_ms_debug(dx, ms_list, func=func, useDict=useDict)
    if debug:
        if res:
            print_log(row, f"找到{get_ms_name(ms_list[res - 1])}")
        else:
            print_log(row, f"没找到{[get_ms_name(ms) for ms in ms_list]}", 1)
    return res


def not_is_for_ms_row(row, ms_list, func=None, useDict=0, pri_info=None):
    return not is_for_ms_row(row, ms_list, func, useDict, pri_info)


if __name__ == '__main__':
    # # 测试前台截图
    # hwnd = 919566
    # gdi = GDI(hwnd)
    # s = time.time()
    # for i in range(100):
    #     gdi.CaptureDesktop()
    # print("截图耗时:", (time.time() - s)/100)

    # # 测试后台截图
    # hwnd = 919566
    # gdi = GDI(hwnd)
    # s = time.time()
    # num = 0
    # while True:
    #     s2 = time.time()
    #     img = gdi.Capture()
    #     s3 = time.time()-s2
    #     num += 1
    #     MiniOpenCV.imshow("img", img)
    #     MiniOpenCV.waitKey(1)
    #     if time.time() - s >= 1:
    #         print("显示fps:%d, 截图fps:%d" %(num, 1/s3))
    #         s = time.time()
    #         num = 0

    # # # 测试截图并显示
    # hwnd = 198072
    # gdi = GDI(hwnd)
    # s = time.time()
    # MiniOpenCV.nameWindow("img")
    # print(f"截图耗时:{time.time() - s}")
    # #
    # while True:
    #     start = time.time()
    #     img = gdi.Capture()  # 读取 BMP 文件
    #     t = time.time() - start
    #     if time.time() - s > 1:
    #         s = time.time()
    #         print(f"FPS:{int(1 / t)}")
    #     MiniOpenCV.imshow("img", img)  # 创建窗口并显示图像
    #     MiniOpenCV.waitKey(1)

    # # 测试读取并显示
    img = MiniOpenCV.imread(r"test2.bmp")
    # MiniOpenCV.imshow("test2",img)
    # MiniOpenCV.waitKey(0)
    # 测试写入
    img2 = img[0:100, 0:101]
    MiniOpenCV.imwrite("test2_100.bmp", img2)

    # # 测试找色
    # hwnd = 198072
    # screenshot = Display_gdi(hwnd)
    # dx = DX()
    # dx.set_screen(screenshot)
    # s = time.time()
    # res = dx.CmpColor(354,207, "f4c51f", 1.0)
    # print("找色耗时:%s, 结果:%s" %(time.time() - s, res))

    # # 测试找图
    # dxpyd.set_debug(True)
    # hwnd = 198072
    # screen = Display_gdi(hwnd)
    # dx = DX()
    # dx.set_screen(screen)
    # dx.SetPath(os.getcwd())
    # s = time.time()
    # res = dx.FindPic(0, 0, 1280, 720, "test.bmp", "000000", 1.0, 0)
    # print("找图耗时:%s, 结果:%s" % (time.time() - s, res))
