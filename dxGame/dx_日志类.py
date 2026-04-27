# -*- coding: utf-8 -*-
from dxGame.dx_core import *


def print_log(row, content, lv=0):
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 定义不同日志级别的颜色
    RESET = "\033[0m"  # 重置颜色
    RED = "\033[91m"   # 红色
    YELLOW = "\033[93m"  # 黄色

    # 根据日志级别设置颜色
    if lv == 1:
        color = RED
    elif lv == 2:
        color = YELLOW
    else:
        color = RESET

    # 格式化输出
    print(f"{current_time} | Row: {row} | {color}{content}{RESET}")

class 日志类:
    def __init__(self, 日记目录, 日记保留时间=1):
        self.日记目录 = 日记目录
        self.清理线程标志位 = True
        self.定期清理日记存档(日记保留时间)
        self.默认列 = None

    def __del__(self):
        self.清理资源()

    def 清理资源(self):
        self.清理线程标志位 = False

    def 设置回调函数显示界面(self, 回调函数, 默认列):
        """
        :param 回调函数: 回调函数必须要有3个参数(行,列,内容)
        :return:
        """
        self.显示界面 = 回调函数
        self.默认列 = 默认列

    def 定期清理日记存档(self, 日记保留时间):
        def _定期清理日记缓存():
            s = time.time()
            while self.清理线程标志位:
                time.sleep(0.1)  # 间隔
                if time.time() - s < 60:
                    continue
                else:
                    s = time.time()
                for file in os.listdir(self.日记目录):
                    if ".txt" in file:
                        # 将字符串转换为datetime对象
                        try:
                            日记日期 = file.split(".txt")[0].split("_")[1]
                            target_date = datetime.strptime(日记日期, "%Y-%m-%d")
                            current_date = datetime.now()  # 获取当前日期和时间（如果需要仅日期部分，可以使用.date()方法）
                            delta = target_date - current_date  # 计算两个日期之间的时间差
                            days_difference = delta.days  # 获取相差的天数
                            if days_difference > 日记保留时间:  # 如果delta.days是负数，说明当前日期在目标日期之后
                                os.remove(os.path.join(self.日记目录, file))
                            else:
                                pass
                        except Exception as e:
                            print("日期文件名称格式不符合 %s" % e)

        threading.Thread(target=_定期清理日记缓存, daemon=True).start()

    def 写入日记(self, 编号, 内容):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        日记路径 = f"{self.日记目录}/{编号}_{当前日期}.txt"
        with open(日记路径, "a", encoding="utf-8") as f:
            当前时间 = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            内容 = f"{当前时间} {内容}\n"
            f.write(内容)


    def 打开日记(self, 编号):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        日记路径 = f"{self.日记目录}/{编号}_{当前日期}.txt"
        if os.path.exists(日记路径):
            cmd = f"start {日记路径}"
            os.system(cmd)
            return True
        else:  # 创建目录
            with open(日记路径, 'w', encoding="utf-8") as file:
                pass
            cmd = f"start {日记路径}"
            os.system(cmd)

    def 显示内容到界面(self, 行, 内容, 列=None):
        if 列 is None:
            列 = self.默认列
        self.写入日记(行, 内容)
        print_log(行, 内容)

    def 读取最近行数日志返回(self,行数):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        日记路径 = f"{self.日记目录}/{0}_{当前日期}.txt"
        with open(日记路径, "r", encoding="utf-8") as fp:
            return fp.readlines()[-行数:]
