# -*- coding: utf-8 -*-
from dxGame.dx_core import *

def ld_read_json(json_path):
    # 目录如果不存在则创建目录，文件如果不存在则创建文件，文件内容如果读取异常则为空字典
    dir_name = os.path.dirname(json_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    if not os.path.exists(json_path):
        with open(json_path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps({}))
    with open(json_path, "r", encoding="utf-8") as fp:
        try:
            client_config_dict = json.loads(fp.read())
        except:
            client_config_dict = {}
    return client_config_dict


def ld_write_json(json_path, json_dict):
    dir_name = os.path.dirname(json_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    if not json_dict:
        json_dict = {}
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(json_dict, fp, indent=4, ensure_ascii=False)

class CaseSensitiveConfigParser:
    def __init__(self):
        self.data = {}

    def read(self, file, encoding="utf-8"):
        section = ""

        def func():
            for line in fp.readlines():
                if line.startswith('\ufeff'):
                    line = line[1:]  # 移除BOM
                line = line.strip()
                if not line:
                    continue
                # 跳过开头注释
                if len(line) >= 2 and line[:2] == "# ":
                    continue
                # 去掉结尾注释
                match = re.search(r'\s*#', line)
                if match:
                    line = line[:match.start()].strip()  # 去掉注释
                    comment = line[match.start():].strip()  # 注释
                else:
                    comment = ""
                # 判断是否是标题
                if line[0] == "[" and line[-1] == "]":
                    section = line[1:-1]
                    self.data[section] = {}
                    continue
                # 处理key,value
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    value = ast.literal_eval(value)
                except Exception as e:
                    value = str(value)
                self.data[section][key] = value

        try:
            with open(file, encoding=encoding) as fp:
                func()
        except UnicodeDecodeError as e:
            with open(file, encoding="gbk") as fp:
                func()
        except SyntaxError as e:
            print("请检查是否使用了中文符号，比如“”等包裹字符串")
        except Exception as e:
            raise e

    def write(self, file, encoding="utf-8"):
        data = ""
        for section in self.data:
            data += f"[{section}]\n"
            for key, value in self.data[section].items():
                data += f"{key} = {value}\n"
        with open(file, "w", encoding=encoding) as fp:
            fp.write(data)


class ConfigHandler:
    """
    由于标准库ConfigParser,只支持字符串,经过封装后,将支持python数据类型
    基本数据类型:

        整数 (int): 例如 42, -5
        浮点数 (float): 例如 3.14, -2.7
        字符串 (str): 例如 "hello", 'world'
        布尔值 (bool): True, False
        空值 (None): None
        集合类型:

        列表 (list): 例如 [1, 2, 3], ["a", "b", "c"]
        元组 (tuple): 例如 (1, 2, 3), ("a", "b", "c")
        字典 (dict): 例如 {"key1": "value1", "key2": "value2"}
        集合 (set): 例如 {1, 2, 3}
        嵌套结构:

        列表嵌套列表: 例如 [[1, 2], [3, 4]]
        字典嵌套字典: 例如 {"outer": {"inner": "value"}}
        混合嵌套: 例如 {"list": [1, 2, 3], "tuple": (4, 5, 6)}
    不支持的类型
        任意函数调用:
        eval("sum([1, 2, 3])")：ast.literal_eval 不支持函数调用和方法调用。
        类实例化:

        eval("MyClass()")：ast.literal_eval 不支持类实例化。
        对象方法调用:

        eval("obj.method()")：ast.literal_eval 不支持对象方法调用。
        运算符表达式:

        eval("1 + 2")：ast.literal_eval 不支持解析数学表达式。
        Lambda表达式:

        eval("lambda x: x + 1")：ast.literal_eval 不支持 lambda 表达式。
        其他不安全或复杂的表达式:

        赋值语句: 例如 eval("a = 5")。
        导入语句: 例如 eval("import os")。
示例
    """

    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.path = path
        self.config = CaseSensitiveConfigParser()
        self.data = {}
        # 多线程（多开 Task）共享同一 ConfigHandler 时，串行化读盘/写盘，避免 INI 竞态
        self._io_lock = threading.Lock()

    def __getitem__(self, item):
        return self.data.get(item)

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key,default)

    def setdefault(self, key, default=None):
        """与 dict.setdefault 一致，供 gl_info.配置.setdefault('进度配置', {}) 等用法。"""
        if key not in self.data:
            self.data[key] = default
        return self.data[key]

    def 读取本地配置文件(self):
        with self._io_lock:
            self.config.read(self.path, encoding='utf-8')
            self.data = self.config.data

    def 写入本地配置文件(self):
        """
        写入配置文件（增强版：先读后写，避免多进程竞态导致重复键）
        
        工作流程：
        1. 加锁
        2. 读取当前文件内容
        3. 合并内存中的数据到读取的数据中
        4. 写入文件
        5. 释放锁
        """
        with self._io_lock:
            # ✅ 先读取当前文件，获取最新的配置
            try:
                temp_config = CaseSensitiveConfigParser()
                temp_config.read(self.path, encoding='utf-8')
                # 将内存中的数据合并到读取的数据中
                for section in self.data:
                    if section not in temp_config.data:
                        temp_config.data[section] = {}
                    # 更新该 section 下的所有键值对
                    for key, value in self.data[section].items():
                        temp_config.data[section][key] = value
                # 使用合并后的数据写入
                temp_config.write(self.path, encoding='utf-8')
            except Exception as e:
                # 如果读取失败，直接写入当前数据
                print(f"⚠️ 配置文件读取失败，直接写入: {e}")
                self.config.data = self.data
                self.config.write(self.path, encoding='utf-8')

    def 配置生成类(self, file_path, add_class_name=""):
        data = ""
        for section in self.data:
            data += f'class {section}{add_class_name}:\n'
            for key, value in self.data[section].items():
                data += f"\t{key} = {value}\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)

    def 添加(self, section, key, value):
        self.data.setdefault(section, {})[key] = value

    def 获取(self, section, key):
        return self.data.get(section, {}).get(key)

    def 删除(self, section, key):
        self.data.get(section, {}).pop(key, None)

    def 删除标题(self, section):
        self.data.pop(section, None)

    def 删除所有(self):
        self.data.clear()
