from app.core import *
from public import 表格_状态

# region 显示日志
def show_log(row,content,col=表格_状态):
    gl_info.日志类.显示内容到界面(row,content)
    gl_info.update_queue.put((row, col, content))
# endregion
# region 弹窗
def show_message(title: str, content: str, all_content: str = ""):
    ctypes.windll.user32.MessageBoxW(0, f"{content}\n{all_content}", title, 1)

# endregion
# region 清除资源

def clear_resource(row):  # 固定写法,不要删除,用于线程停止回调清理
    td_info[row].clear()

# endregion
# region 获取默认所有任务列表
def get_all_task_list(config):
    lst = []
    for task_in_list in [config["全局配置"]["默认任务id"], config["全局配置"]["默认任务id2"], config["全局配置"]["默认任务id3"],config["全局配置"]["默认任务id4"]]:
        lst2 = ""
        for task_id in task_in_list:
            lst2 += config["全局配置"]["所有任务"][str(task_id)] + ","
        lst.append(lst2)
    return lst
# endregion

# region 获取表格指定行内容
def get_row_content(row):
    treeview = gl_info.ui.tk_table_m1ap2ahd
    # 获取指定行的内容
    item = treeview.item(treeview.get_children()[row])
    return item['values']
# endregion
