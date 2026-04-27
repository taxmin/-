# -*- coding: utf-8 -*-
from dxGame.dx_core import *

def is_process_running(exe_name):
    """使用 tasklist 检查进程是否在运行"""
    try:
        # 执行 tasklist 命令，检查是否有匹配的进程
        output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {exe_name}"', shell=True, text=True)
        return exe_name.lower() in output.lower()  # 如果输出包含进程名，表示进程在运行
    except subprocess.CalledProcessError:
        return False  # 如果命令执行失败，则视为未找到进程

def start_process(exe_path):
    """启动指定路径的 exe 文件"""
    command = f'start "" {exe_path}'
    # try:
    #     os.system(command)
    #     print(f"启动进程: {exe_path}")
    # except Exception as e:
    #     print(f"启动进程失败: {e}")
    # 使用 DETACHED_PROCESS 解除与父进程的绑定，并在新控制台中启动
    subprocess.Popen(
        ["cmd", "/c", "start", exe_path],  # 使用列表，避免 shell 解析冲突
        shell=False
    )
def get_process_info(exe_name):
    """使用 wmic 获取进程的详细信息（如 PID 和句柄数）"""
    try:
        # 执行 wmic 命令获取进程信息
        output = subprocess.check_output(f'wmic process where "name=\'{exe_name}\'" get ProcessId,HandleCount', shell=True, text=True)
        lines = output.strip().split('\n')[1:]  # 忽略标题行
        for line in lines:
            if line.strip():
                pid, handles = line.split()
                print(f"进程已启动，PID: {pid}, 句柄数: {handles}")
    except subprocess.CalledProcessError:
        print("无法获取进程信息")

# 检测exe路径并启动exe
def check_or_start_process(exe_path):
    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"文件不存在: {exe_path}")
    """检查进程是否运行，若未运行则启动，若运行则打印句柄信息"""
    exe_name = os.path.basename(exe_path)  # 从路径中提取可执行文件名

    if is_process_running(exe_name):
        print(f"{exe_name} 已在运行")
        get_process_info(exe_name)
    else:
        print(f"{exe_name} 未运行，正在启动...")
        start_process(exe_path)

