  # -*- coding: utf-8 -*-
"""
@Time ： 2022/11/29 14:13
@Auth ： 大雄
@File ：CV.py
@IDE ：PyCharm
@Email:3475228828@qq.com
"""
import ctypes,cv2,numpy as np
import os
from io import BytesIO
# from PIL import Image
class CV:
    def __init__(self, path=None, img=None):
        self.min_val = None  # 最小匹配
        self.max_val = None  # 最大相似度
        self.min_loc = None  # 最差匹配坐标
        self.max_loc = None  # 最佳匹配坐标
        self.轮廓列表 = None
        self.windowName = "img"
        class HSV颜色范围:
            保留所有颜色=[[0, 0, 0], [180, 255, 255]]
            保留黑色= [[0, 0, 0], [180, 255, 46]]
            保留灰色=[[0, 0, 46], [180, 43, 220]]
            保留白色= [[0, 0, 221], [180, 30, 255]],
            保留红色1=[[0, 43, 46], [10, 255, 255]]
            保留红色2=[[156, 43, 46], [180, 255, 255]]
            保留橙色=[[11, 43, 46], [25, 255, 255]]
            保留黄色=[[26, 0, 0], [34, 255, 255]]
            保留绿色=[[35, 43, 46], [77, 255, 255]]
            保留青色=[[78, 43, 46], [99, 255, 255]]
            保留蓝色=[[100, 43, 46], [124, 255, 255]]
            保留紫色= [[125, 43, 46], [155, 255, 255]]
        self.HSV颜色范围 = HSV颜色范围
        if path:
            if self.__is_chinese(path):
                self.img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)  # 避免路径有中文
            else:
                self.img = cv2.imread(path)
        elif not None is img:
            self.img = img
        else:
            raise ValueError("必须填写图片路径或者numpy格式的图片")

    # 判断字符串是否有汉字
    def __is_chinese(self, string):
        """
        检查整个字符串是否包含中文
        :param string: 需要检查的字符串
        :return: bool
        """
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    # 颜色格式ffffff-303030 转cv格式遮罩范围(100,100,100),(255,255,255)
    def __color_to_range(self,ps):
        if len(ps) < 6 or ps.find('-') == -1:
            return None, None
        c, weight = ps.split("-")
        color = int(c[:2], 16), int(c[2:4], 16), int(c[4:], 16)
        weight = int(weight[:2], 16), int(weight[2:4], 16), int(weight[4:], 16)
        lower = tuple(map(lambda c, w: max(0, c - w), color, weight))
        upper = tuple(map(lambda c, w: min(c + w, 255), color, weight))
        return lower, upper

    def 获取通道数(self,img):
        if not None is img:
            self.img = img
        if len(self.img.shape)==2:
            return 1
        else:
            self.img.shape[2]

    def 显示图像(self,img=None,name=None):
        if name is None:
            name = self.windowName
        if not img is None:
            cv2.imshow(name, img)
        else:
            cv2.imshow(name,self.img)
        cv2.waitKey()
        cv2.destroyAllWindows()
        return self

    def 保存图像(self,保存路径,img=None):
        hz = os.path.splitext(保存路径)[1]
        if img is None:
            img = self.img
        success, encoded_img = cv2.imencode(hz, img)
        if success:
            encoded_img.tofile(保存路径)  # 支持中文路径
    def 二值化(self, min=0, max=254):
        ret, self.img = cv2.threshold(self.img, min, max, 0)  # 二值化
        return self

    def 模板匹配(self, img1, img2, xsd, func=0):
        func_dict = {
            0: cv2.TM_CCOEFF_NORMED,  # （相关系数匹配法）
            1: cv2.TM_CCOEFF,  # （系数匹配法）
            2: cv2.TM_CCORR,  # （相关匹配法）
            3: cv2.TM_CCORR_NORMED,  # （归一化相关匹配法）
            4: cv2.TM_SQDIFF,  # （平方差匹配法）
            5: cv2.TM_SQDIFF_NORMED  # （归一化平方差匹配法）
        }
        func = func_dict.get(func, None)
        result = cv2.matchTemplate(img1, img2, func)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        yloc, xloc = np.where(result >= xsd)
        if len(xloc):
            self.min_val, self.max_val, self.min_loc, self.max_loc = min_val, max_val, min_loc, max_loc
        return self

    def HSV颜色选取(self,HSV颜色范围:tuple):
        lower, upper = HSV颜色范围
        if len(self.img.shape) != 3:
            print("图像必须是3通道")
            return None
        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        lower_red = np.array(lower)
        upper_red = np.array(upper)
        mask = cv2.inRange(img_hsv, lower_red, upper_red)
        self.img = cv2.bitwise_and(self.img, self.img, mask=mask)
        return self

    def RGB颜色选取(self,ps):
        lower, upper = self.__color_to_range(ps)  # 设置RGB下限和上限
        if lower is None or upper is None:
            return None
        img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        mask = cv2.inRange(img, np.array(lower), np.array(upper))
        res  = cv2.bitwise_and(img, img, mask=mask)
        img = cv2.cvtColor(res, cv2.COLOR_RGB2GRAY)  # 转灰度单通道
        ret, self.img = cv2.threshold(img, 1, 255, 0)  # 二值化
        return self

    def 灰度(self):
        if len(self.img.shape) == 2:
            return self
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        return self

    def 清除杂点(self):
        self.img = cv2.fastNlMeansDenoisingColored(self.img, None, 10, 10, 7, 21)
        return self

    def 获取轮廓(self,轮廓面积范围=(),轮廓周长范围=(),轮廊检索模式=cv2.RETR_TREE,轮廓逼近方法=cv2.CHAIN_APPROX_SIMPLE):
        """
        :param 轮廓面积范围: 按像素点算，如1920,1080的面积为1920*1080
        :param 轮廓周长范围: 轮廓周长筛选
        :param 轮廊检索模式:
            cv2.RETR_EXTERNAL：输出轮廓中只有外侧轮廓信息；
            cv2.RETR_LIST：以列表形式输出轮廓信息，各轮廓之间无等级关系；
            cv2.RETR_CCOMP：输出两层轮廓信息，即内外两个边界（下面将会说到contours的数据结构）；
            cv2.RETR_TREE：以树形结构输出轮廓信息。

        :param 轮廓逼近方法:
            cv2.CHAIN_APPROX_SIMPLE 存储线上的所有点
            cv2.CHAIN_APPROX_NONE 存储关键点,删除冗余的点，如直线时，只存储两端的点,节省内存
        :return:  保留轮廓后的图像,背景为黑色
        """

        轮廓列表, 层次结构 = cv2.findContours(self.img, 轮廊检索模式, 轮廓逼近方法)
        def 筛选(轮廓列表,特征):
            新的轮廓列表 = []
            for cnt in 轮廓列表:
                if 特征==1:
                    轮廓面积 = cv2.contourArea(cnt)
                    if 轮廓面积范围[0] < 轮廓面积 < 轮廓面积范围[1]:
                        新的轮廓列表.append(cnt)
                elif 特征==2:
                    轮廓周长 = cv2.arcLength(cnt, True)
                    if 轮廓周长范围[0] < 轮廓周长 < 轮廓周长范围[1]:
                        新的轮廓列表.append(cnt)
            return 新的轮廓列表

        if 轮廓面积范围 and 轮廓周长范围:
            新的轮廓列表 = 筛选(轮廓列表,1)
            新的轮廓列表 = 筛选(新的轮廓列表, 2)
        elif 轮廓面积范围:
            新的轮廓列表 = 筛选(轮廓列表,1)
        elif 轮廓周长范围:
            新的轮廓列表 = 筛选(轮廓列表,2)
        else:
            新的轮廓列表 = 轮廓列表
        self.轮廓列表 = 新的轮廓列表
        return self

    # 旋转angle角度，缺失背景黑色（0, 0, 0）填充
    def 旋转纠正(self,angle):
        (h, w) = self.img.shape[:2]
        (cX, cY) = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY
        self.img = cv2.warpAffine(self.img, M, (nW, nH), borderValue=(0, 0, 0))
        return self

    def 颠倒颜色(self):
        self.img = 255-self.img
        return self

    def 膨胀(self,value1,value2):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (value1,value2))
        self.img = cv2.dilate(self.img, kernel)
        return self

    def 腐蚀(self,value1,value2):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (value1,value2))  # 可以修改卷积核大小来增加腐蚀效果，越大腐蚀越强
        self.img = cv2.erode(self.img, kernel)
        return self

    # 先腐蚀后膨胀的操作称为开运算
    # 开运算的作用：消除细小物体、在窄区域分离物体、平滑大物体边界等。
    def 开操作(self,腐蚀度:tuple,膨胀度:tuple):
        self.腐蚀(*腐蚀度).膨胀(*膨胀度)
        return self
    # 轮廓线更为光滑，但与开操作相反的是，它通常连接狭窄的间断和长细的鸿沟，消除小的孔洞，并填补轮廓线中的断裂
    def 闭操作(self,膨胀度,腐蚀度):
        self.膨胀(*膨胀度).腐蚀(*腐蚀度)
        return self

    def 等比缩放(self,x,img=None):
        if img is None:
            img = self.img
        self.img = cv2.resize(img,None,fx=x,fy=x,interpolation=cv2.INTER_LINEAR)
        return self

    def 中值滤波(self,孔径线性尺寸=3):
        """
        :param 孔径线性尺寸: 它必须是奇数且大于 1，例如：3、5、7
        :return: self对象
        """
        self.img = cv2.medianBlur(self.img, 孔径线性尺寸)
        return self

    def 连通区域(self,宽=(),高=()):
        """
        num_labels：所有连通域的数目
        labels：图像上每一像素的标记，用数字1、2、3…表示（不同的数字表示不同的连通域）
        stats：每一个标记的统计信息，是一个5列的矩阵，每一行对应每个连通区域的外接矩形的 x（左上角）、y（左上角）、width（宽度）、height（高度）和面积（点的数量），示例如下： 0 0 720 720 291805。
        centroids：连通域的中心。
        :return:
        """
        self.连通区域信息 = []
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(self.img)
        # print(num_labels, "\n======\n",labels,"\n======\n", stats,"\n======\n", centroids)
        for label in stats:
            if 宽 and 高:
                if 宽[0]<=label[2]<=宽[1] and 高[0]<=label[3]<=高[1]:
                    # x,y= label[0],label[1]
                    # x2,y2 = x + label[2],y + label[3]
                    # self.img = self.img[y:y2,x:x2]
                    self.连通区域信息.append(list(label))
        return self


        # print("num_labels",num_labels,"\n", "labels",labels,"\n","stats",stats, "\n","centroids",centroids)

    def 特征匹配(self):
        pass

    @staticmethod
    def 获取内存图像(内存地址,长度):
        imgbt = ctypes.string_at(内存地址,长度)
        dataEnc = BytesIO(imgbt)
        # 使用Image.open,会和pyqt5冲突,导致界面崩溃，原因未知
        # img = Image.open(dataEnc)
        # img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        with dataEnc as f:
            a = f.read()
        img = cv2.imdecode(np.frombuffer(a, np.uint8), cv2.IMREAD_COLOR)

        return img

    def 设置窗口大小(self,宽:int,高:int,窗口名称=None):
        if 窗口名称 is None:
            窗口名称 = self.windowName
        cv2.namedWindow(窗口名称, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(窗口名称, 宽,高)
        return self

    def 设置图片大小(self,X轴缩放倍数 = 0.5,Y轴缩放倍数 = 0.5,img=None):
        if img is None:
            img = self.img
        self.img = cv2.resize(img,None,fx=X轴缩放倍数,fy=Y轴缩放倍数,interpolation=cv2.INTER_LINEAR)
        return self

    # 查找图像的强度
    def 边缘检测(self,最小磁滞阈值=100,最大磁滞阈值=200):
        self.img = cv2.Canny(self.img, 最小磁滞阈值, 最大磁滞阈值)
        return self

    # def 特征检测(self):
    #     if len(self.img.shape)==2 or self.img.shape[2]==1:
    #         self.img = self.灰度()

    def 绘制轮廊(self,img=None,轮廓列表=None):
        if img is None:
            img = self.img
        if 轮廓列表 is None:
            轮廓列表 = self.轮廓列表
        通道 = self.获取通道数(img)
        画笔 = (255) if 通道 == 1  else  (0, 0, 255)
        cv2.drawContours(img, 轮廓列表, -1, 画笔, 3)
        return self

    def 图像裁剪(self,x1,y1,x2,y2):
        self.img = self.img[y1:y2,x1:x2]
        return self

    @staticmethod
    def 获取轮廓面积(轮廓):
        return cv2.contourArea(轮廓)

    @staticmethod
    def 获取轮廊范围(轮廊):
        x,y,w,h =cv2.boundingRect(轮廊)
        return x,y,w,h
