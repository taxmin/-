from app.controller import Controller
from app.core import *
from app.public_function import *
from app.public_function import *
from app.view import Win
from app.view import Win
from dxGame.dx_ldmnq import *
from public import *
from task_list.task import Task

if __name__ == "__main__":
    控制器 = Controller(Task)
    # 界面 = Win(控制器)
    界面 = Win(控制器)
    界面.wm_title("梦幻手游自动日常")
    界面.mainloop()