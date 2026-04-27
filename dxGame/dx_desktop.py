# -*- coding: utf-8 -*-
from dxGame.dx_core import *

def get_desktop_path():
    """获取当前用户的桌面路径"""
    return os.path.join(os.environ['USERPROFILE'], 'Desktop')

def get_desktop_public_path():
    """获取公共桌面路径"""
    return os.path.join(os.environ['PUBLIC'], 'Desktop')

def resolve_lnk_with_powershell(lnk_path):
    """使用 PowerShell 解析 .lnk 文件指向的目标路径"""  # 不支持xp系统
    command = f'powershell -command "(New-Object -COM WScript.Shell).CreateShortcut(\'{lnk_path}\').TargetPath"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def find_all_lnk_name(desktop_path,target_filename):
    for file_name in os.listdir(desktop_path):
        if target_filename in file_name:
            return file_name
    return ""
def find_all_lnk_files_on_desktop(desktop_path,target_filename):
    """在桌面上找到所有 .lnk 文件并解析目标路径"""
    for file_name in os.listdir(desktop_path):
        if file_name.endswith('.lnk'):
            if target_filename in file_name:
                lnk_path = os.path.join(desktop_path, file_name)
                target_path = resolve_lnk_with_powershell(lnk_path)
                print(f"Shortcut: {file_name} -> Target: {target_path}")
                return target_path
if __name__ == '__main__':
    desktop_path = get_desktop_path()
    desktop_path2 = get_desktop_public_path()
    res = ""
    for path in [desktop_path,desktop_path2]:
        res= find_all_lnk_files_on_desktop(path,"剑网3系列启动器")
        if res:
            break
    print(res)
    # dct = find_all_lnk_name(desktop_path,"剑网三无界")
