from queue import Queue


class Custom:
    # dx = DX

    def __init__(self):
        self.thread_son = []
        self.task_list = []
        self.dx = None
        self.ld = None
        self.process = ""
        self.update_queue = Queue()
        self.result = []  # 存储任务结果
        self.hwnd = None
        self.登录器_hwnd = None
        self.ip_row_dict = {}  # ip 和行号映射表
    def __getattr__(self, item):
        setattr(self, item, 0)
        return self.item

    def clear(self):
        for key in self.__dict__:
            self.__dict__[key] = 0
        self.__init__()




def tdi():
    re = []
    for i in range(5000):
        re.append(Custom())
    return re


gl_info = Custom()
td_info = tdi()