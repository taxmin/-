# 示例下载 https://www.pytk.net/blog/1702564569.html



from app.public_function import *
from public import *
from app.view import Win
from app.weekly_scheduler import start_weekly_scheduler, stop_weekly_scheduler
from app.vmware_window_monitor import start_vmware_window_monitor, stop_vmware_window_monitor


class Controller:
    DEBUG = False
    # 导入UI类后，替换以下的 object 类型，将获得 IDE 属性提示功能
    ui: Win

    def __init__(self,task):

        self.当前任务序号 = 0
        self.当前账号序号 = 0
        self.update_queue = gl_info.update_queue
        self.配置 = ConfigHandler(HOME_CONFIG)
        self.配置.读取本地配置文件()
        self.当前选中行号列表 = []
        self.日志类 = 日志类(LOG_DIR, 2)
        self.日志类.设置回调函数显示界面(self.update_table_data, 表格_状态)

        gl_info.配置 = self.配置
        gl_info.日志类 = self.日志类

        dct = gl_info.配置["全局配置"]["所有任务"]
        result = {"message":{"所有任务": dct}}
        self.async_title = ""
        self.async_content = ""
        self.async_color = ""
        gl_info.result = result
        gl_info.show_message_async = self.show_message_async
        def log(row,content):
            # 线程运行日志应显示在“状态”列，而不是“ID”列
            return show_log(row, content, 表格_状态)
        self.线程控制器 = ThreadController(self.配置.data["全局配置"]["最大线程数"], task, call_stop_func=clear_resource, call_print_func=log,
                                           call_all_stop_func=lambda: messagebox.showinfo("ok", "任务完成"))
        gl_info.controller = self
        start_weekly_scheduler(self)
        start_vmware_window_monitor()  # 启动 VMware 窗口监控线程
    def init(self, ui):
        """
        得到UI实例，对组件进行初始化配置
        """
        self.ui = ui
        gl_info.ui = ui
        self.set_icon()
        self.ui.protocol("WM_DELETE_WINDOW", self.close_window)
        self.create_right_menu()
        self.start_dingShiQi()
        self.load_config()
        self.anJianJianKong()
    # region 载入配置
    def load_config(self):
        # 清空原先表格
        self.ui.tk_table_m1ap2ahd.delete(*self.ui.tk_table_m1ap2ahd.get_children())
        self.配置.读取本地配置文件()  # 更新配置
        账号列表 = self.配置["账号配置"]
        任务列表 = self.配置["任务列表"]
        if 账号列表:
            for i, (ip, 账号密码列表) in enumerate(账号列表.items()):
                if self.线程控制器.get_thread(i):
                    thread_flag = "运行中"
                else:
                    thread_flag = ""
                
                # 解析账号信息，只显示当前运行的账号
                显示信息 = self._解析账号显示信息(账号密码列表, i)
                
                # ID列使用连续编号（1,2,3...），状态信息放到“状态”列
                row_data = (str(i + 1), str(ip), 显示信息, f"", f"", f"", thread_flag)
                self.ui.tk_table_m1ap2ahd.insert("", "end", values=row_data)
                self.update_table_data(i, 表格_任务, 任务列表.get(ip,""))  # 设置默认任务
        # 根据多少行自动设置表格高度
        width = user32.GetSystemMetrics(0)  # 获取屏幕宽度
        height = user32.GetSystemMetrics(1)  # 获取屏幕高度
        screenwidth, screenheight = self.ui.winfo_width(), self.ui.winfo_height()
        if 账号列表:
            n = len(账号列表)
            if n == 0:
                return
            if n * 20 < height - 200:
                self.ui.geometry('%dx%d+%d+%d' % (screenwidth, n * 20 + 30, 300, 300))
            else:
                self.ui.geometry('%dx%d+%d+%d' % (screenwidth, height - 200, 300, 300))
        # 调整表格控件的大小和布局
        self.ui.tk_table_m1ap2ahd.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)
        self.ui.tk_tab_main.grid_rowconfigure(0, weight=1)
        self.ui.tk_tab_main.grid_columnconfigure(0, weight=3)
        self.ui.update_idletasks()

    # endregion
    # region 解析账号显示信息
    def _解析账号显示信息(self, 账号密码列表, row_index):
        """
        解析账号配置，只显示当前运行的账号信息（不显示密码）
        
        Args:
            账号密码列表: ['账号|密码|区服|角色', ...] 或单个字符串
            row_index: 行号（端口索引）
            
        Returns:
            str: 格式化的显示信息，如 "账号: xxx | 区服: xxx | 角色: x"
        """
        try:
            # 如果是字符串，先转换为列表
            if isinstance(账号密码列表, str):
                import ast
                try:
                    账号密码列表 = ast.literal_eval(账号密码列表)
                except:
                    return 账号密码列表
            
            # 如果不是列表，直接返回
            if not isinstance(账号密码列表, list):
                return str(账号密码列表)
            
            # 获取当前运行的账号索引（从进度配置中读取）
            当前账号索引 = self._获取当前账号索引(row_index)
            
            # 如果索引有效，显示该账号信息
            if 0 <= 当前账号索引 < len(账号密码列表):
                账号信息 = 账号密码列表[当前账号索引]
                return self._格式化账号信息(账号信息)
            else:
                # 如果没有运行，显示第一个账号的信息
                if 账号密码列表:
                    return self._格式化账号信息(账号密码列表[0])
                return ""
                
        except Exception as e:
            print(f"解析账号信息失败: {e}")
            return str(账号密码列表)
    
    def _获取当前账号索引(self, row_index):
        """
        从进度配置中获取当前运行的账号索引
        
        Args:
            row_index: 行号（端口）
            
        Returns:
            int: 当前账号索引，默认 0
        """
        try:
            进度配置 = self.配置.get("进度配置", {})
            # 查找对应的端口配置
            for key, value in 进度配置.items():
                if str(key) == str(row_index):
                    if isinstance(value, dict):
                        daily = value.get('daily', {})
                        return daily.get('account_index', 0)
            return 0
        except:
            return 0
    
    def _格式化账号信息(self, 账号信息):
        """
        格式化账号信息显示（隐藏密码）
        
        Args:
            账号信息: '账号|密码|区服|角色'
            
        Returns:
            str: '账号: xxx | 区服: xxx | 角色: x'
        """
        try:
            parts = 账号信息.split('|')
            if len(parts) >= 4:
                账号 = parts[0]
                # 密码 = parts[1]  # 不显示密码
                区服 = parts[2]
                角色 = parts[3]
                return f"账号: {账号} | 区服: {区服} | 角色: {角色}"
            elif len(parts) >= 1:
                return f"账号: {parts[0]}"
            else:
                return 账号信息
        except:
            return 账号信息

    # endregion
    # region 设置窗口图标
    def set_icon(self):
        self.ui.iconbitmap(f"{IMAGE_DIR}/icon.ico")

    # endregion
    # region 启动定时器
    def start_dingShiQi(self):
        # 每帧最多处理 N 条队列，避免日志高峰时阻塞 UI 主线程
        max_batch = 50
        for _ in range(max_batch):
            if self.update_queue.empty():
                break
            row, col, content = self.update_queue.get()
            self.update_table_data(row, col, content)
            if self.async_title:
                # 自定义弹窗
                popup = tk.Toplevel()
                popup.title(self.async_title)
                popup.geometry("800x600")  # 设置弹窗大小
                popup.resizable(False, False)
                # 设置窗口置顶
                popup.attributes('-topmost', True)
                label = tk.Label(popup, text=self.async_content, font=("Arial", 36 * 7, "bold"), fg=self.async_color, wraplength=800)
                label.pack(pady=40)

                button = tk.Button(popup, text="确定", font=("Arial", 16), command=popup.destroy)
                button.pack(pady=20)

                popup.grab_set()
                popup.wait_window()
                self.async_title = ""
        self.ui.tk_table_m1ap2ahd.after(50, self.start_dingShiQi)

    # endregion
    # region 选中
    def check(self, event):
        selected_item = self.ui.tk_table_m1ap2ahd.selection()  # 获取选中的行,这个不是行号，而是行ID，跟行号不对应
        if selected_item:
            if isinstance(selected_item, tuple):
                self.当前选中行号列表 = [self.ui.tk_table_m1ap2ahd.get_children().index(item) for item in selected_item]
            else:
                self.当前选中行号列表 = [self.ui.tk_table_m1ap2ahd.get_children().index(selected_item)]
            print("当前选中行号列表:", self.当前选中行号列表)

    # endregion
    # region 右键显示菜单
    def right_show_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    # endregion
    # region 左键点击
    def left_click(self, event):
        row, col = self.get_row_col(event)
        # 点击表格
        if row is None:
            # if col == 表格_账号:
            #     self.user_change()
            if col == 表格_任务:
                当前任务内容 = self._get_task_content()
                if 当前任务内容:
                    for row, item in enumerate(self.ui.tk_table_m1ap2ahd.get_children("")):
                        if self.线程控制器.get_thread(row):
                            continue
                        self.update_table_data(row, 表格_任务, 当前任务内容)

        # 选中以后,才允许更改任务
        elif col == 表格_任务 and row in self.当前选中行号列表:
            当前任务内容 = self._get_task_content()
            if 当前任务内容:
                if self.线程控制器.get_thread(row):
                    return
                self.update_table_data(row, 表格_任务, 当前任务内容)
        # else:  # 内容事件
        #     pass

    # endregion
    # region 获取行列号
    def get_row_col(self, event):
        # 获取点击的行 ID 和列 ID
        item_id = self.ui.tk_table_m1ap2ahd.identify_row(event.y)  # 获取行 ID
        col_id = self.ui.tk_table_m1ap2ahd.identify_column(event.x)  # 获取列 ID，格式为 #1, #2, ...
        col_index = int(col_id.replace("#", "")) - 1
        # 如果点击在表格内的有效行列上
        if item_id and col_id:
            # 将列 ID 转换为列索引 (从 0 开始)
            # 获取所有行的 ID 列表
            all_items = self.ui.tk_table_m1ap2ahd.get_children()
            # 将 item_id 转换为行索引 (从 0 开始)
            row_index = all_items.index(item_id)

            return row_index, col_index
        return None, col_index  # 如果点击无效区域

    # endregion
    # region 更新表格数据
    def update_table_data(self, row, col, content):
        # 获取所有行的 ID
        item_id = self.ui.tk_table_m1ap2ahd.get_children()[row]
        # 更新指定行和列的内容
        current_values = list(self.ui.tk_table_m1ap2ahd.item(item_id)['values'])
        current_values[col] = content  # 更新指定列的内容
        self.ui.tk_table_m1ap2ahd.item(item_id, values=current_values)

    # endregion
    # region 清空表格运行态数据
    def clear_table_runtime_data(self):
        """清空表格中的运行态字段（进度/收益/状态）。"""
        for item_id in self.ui.tk_table_m1ap2ahd.get_children():
            current_values = list(self.ui.tk_table_m1ap2ahd.item(item_id).get('values', []))
            if len(current_values) > 表格_进度:
                current_values[表格_进度] = ""
            if len(current_values) > 表格_收益:
                current_values[表格_收益] = ""
            if len(current_values) > 表格_状态:
                current_values[表格_状态] = ""
            self.ui.tk_table_m1ap2ahd.item(item_id, values=current_values)
    
    def update_gold_display(self, row, gold_value):
        """
        更新指定行的金币列显示（带色彩突出效果）
        
        Args:
            row: 行号（0-based）
            gold_value: 金币数值（字符串或数字）
        """
        try:
            # 获取所有行的 ID
            items = self.ui.tk_table_m1ap2ahd.get_children()
            if row >= len(items):
                print(f"⚠️ [金币UI] 行号 {row} 超出范围")
                return
            
            item_id = items[row]
            current_values = list(self.ui.tk_table_m1ap2ahd.item(item_id)['values'])
            
            # 更新金币列（第6列，索引5）
            if len(current_values) > 5:
                # 🔧 关键修复：排除逗号，直接使用原始数值
                clean_gold = str(gold_value).replace(',', '').replace('，', '')
                
                # 格式化金币显示（添加千位分隔符）
                try:
                    gold_num = int(clean_gold)
                    formatted_gold = f"{gold_num:,}"  # 添加千位分隔符
                except:
                    formatted_gold = clean_gold
                
                current_values[5] = formatted_gold
                
                # 🔧 新增：应用色彩标签（金黄色突出显示）
                # 根据金币数量决定颜色强度
                try:
                    gold_num = int(clean_gold)
                    if gold_num >= 1000000:  # 百万以上 - 高亮
                        tag = 'gold_highlight'
                    else:  # 普通 - 正常
                        tag = 'gold_normal'
                except:
                    tag = 'gold_normal'
                
                # 应用标签到该行
                self.ui.tk_table_m1ap2ahd.item(item_id, values=current_values, tags=(tag,))
                print(f"✅ [金币UI] Row {row} 已更新: {formatted_gold} (色彩: {tag})")
            else:
                print(f"⚠️ [金币UI] Row {row} 列数不足")
                
        except Exception as e:
            print(f"❌ [金币UI] 更新失败: {e}")
            import traceback
            traceback.print_exc()
    # endregion
    # region 获取选中行号
    def get_row(self):
        selected_item = self.ui.tk_table_m1ap2ahd.selection()
        if not selected_item:
            return -1
        return self.ui.tk_table_m1ap2ahd.get_children().index(selected_item[0])  # 获取行号

    # endregion
    # region 关闭窗口
    def close_window(self):
        stop_weekly_scheduler(self)
        stop_vmware_window_monitor()  # 停止 VMware 窗口监控线程
        dct = {}
        for row in self.ui.tk_table_m1ap2ahd.get_children():
            value = self.ui.tk_table_m1ap2ahd.item(row)["values"]
            ip = value[1]
            task = value[3]
            dct[ip] = task
        self.配置.data["任务列表"] = dct
        self.配置.写入本地配置文件()
        gl_info.clear()
        self.ui.destroy()

    # endregion
    # region _获取任务内容
    def _get_task_content(self):
        默认任务列表 = get_all_task_list(self.配置)
        self.当前任务序号 += 1
        if self.当前任务序号 >= len(默认任务列表):
            self.当前任务序号 = 0
        当前任务内容 = 默认任务列表[self.当前任务序号]
        if type(当前任务内容) != str:
            messagebox.showinfo("警告", "任务内容异常,请检查文本")
            return
        return 当前任务内容

    # endregion
    # # region 切换账号
    # def user_change(self):
    #     账号列表 = self.配置["账号配置"]["账号密码"]
    #     if not 账号列表:
    #         show_message("警告", "配置无账号密码")
    #         return
    #     if type(账号列表) != list:
    #         show_message("警告", f"账号密码配置 格式有误")
    #         return
    #     self.当前账号序号 += 1
    #     if self.当前账号序号 >= len(账号列表):
    #         self.当前账号序号 = 0
    #     新的账号列表 = 账号列表[self.当前账号序号:] + 账号列表[:self.当前账号序号]
    #     self.update_table_data(0, 表格_密码, str(新的账号列表))
    #     self.配置["账号配置"]["账号密码"] = 新的账号列表
    #     self.配置.写入本地配置文件()
    #
    # # endregion
    # region 异步弹窗
    def show_message_async(self, title: str, content: str, color="reg"):
        self.async_title = title
        self.async_content = content
        self.async_color = color
    # endregion
    # region 打开配置
    def open_config(self):
        if os.path.exists(HOME_CONFIG):
            os.system("notepad.exe " + HOME_CONFIG)
        else:
            messagebox.showinfo("警告", "主配置路径不存在 %s " % HOME_CONFIG)

    # endregion

    # region 启动所有
    def start_all(self):
        try:
            user_dict = self.配置["账号配置"]
            nums = list(range(len(user_dict)))
        except Exception as e:
            return messagebox.showinfo("异常", "获取账号信息失败 %s" % e)
        if self.DEBUG:
            try:
                delay = self.配置.data["全局配置"]["启动间隔"]
                self.线程控制器.start_all(nums=nums, delay=delay)
            except Exception as e:
                messagebox.showinfo("异常", "启动所有 线程失败 %s" % e)
        else:
            delay = self.配置.data["全局配置"]["启动间隔"]
            self.线程控制器.start_all(nums=nums, delay=delay)

    # endregion
    # region 暂停所有
    def pause_all(self):
        try:
            self.线程控制器.pause_all()
        except Exception as e:
            messagebox.showinfo("异常", "暂停所有 线程失败 %s" % e)

    # endregion
    # region 恢复所有
    def resume_all(self):
        try:
            self.线程控制器.resume_all()
        except Exception as e:
            messagebox.showinfo("异常", "恢复所有 线程失败 %s" % e)

    # endregion
    # region 停止所有
    def stop_all(self):
        try:
            self.线程控制器.stop_all()
        except Exception as e:
            messagebox.showinfo("异常", "停止所有 线程失败 %s" % e)

    # endregion
    # region 启动
    def start(self):
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        if self.DEBUG:
            try:
                for i in self.当前选中行号列表:
                    self.线程控制器.start(int(i))
            except Exception as e:
                messagebox.showinfo("异常", "启动 %s 线程失败 %s" % (self.当前选中行号列表, e))
        else:
            for i in self.当前选中行号列表:
                self.线程控制器.start(int(i))

    # endregion
    # region 暂停
    def pause(self):
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        try:
            for i in self.当前选中行号列表:
                self.线程控制器.pause(i)
        except Exception as e:
            messagebox.showinfo("异常", "暂停 %s 线程失败 %s" % (self.当前选中行号列表, e))

    # endregion
    # region 恢复
    def resume(self):
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        try:
            for i in self.当前选中行号列表:
                self.线程控制器.resume(i)
        except Exception as e:
            messagebox.showinfo("异常", "恢复 %s 线程失败 %s" % (self.当前选中行号列表, e))

    # endregion
    # region 停止
    def stop(self):
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        try:
            for i in self.当前选中行号列表:
                self.线程控制器.stop(i)
        except Exception as e:
            messagebox.showinfo("异常", "停止 %s 线程失败 %s" % (self.当前选中行号列表, e))

    # endregion
    # region 打开日志
    def open_log(self):
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        for i in self.当前选中行号列表:
            self.日志类.打开日记(i)

    # endregion
    # region 弹起所有按键
    def tanQiSuoYouAnJian(self):
        if not gl_info.km:
            gl_info.km = DMKM(gl_info.dm)
        gl_info.km.release()

    # endregion

    # region 按键键控
    def anJianJianKong(self):
        按键停止 = gl_info.配置["全局配置"]["按键停止"]
        按键暂停 = gl_info.配置["全局配置"]["按键暂停"]
        按键恢复 = gl_info.配置["全局配置"]["按键恢复"]
        按键打开配置 = gl_info.配置["全局配置"]["按键打开配置"]

        def func():
            # 快捷键作用行：优先当前表格选中行；未选中时对「所有正在运行的任务线程」生效（避免写死 row=0 只控第一路）
            rows = [int(x) for x in self.当前选中行号列表] if self.当前选中行号列表 else list(self.线程控制器._thread_dict.keys())
            down = lambda k: ctypes.windll.user32.GetAsyncKeyState(LISTEN_NAMES_KEY.get(k)) & 0x8000 != 0
            ks_stop = down(按键停止)
            ks_pause = down(按键暂停)
            ks_resume = down(按键恢复)
            ks_cfg = down(按键打开配置)
            for row in rows:
                t = self.线程控制器._thread_dict.get(row)
                if not t:
                    continue
                if ks_stop:
                    self.线程控制器.stop(row)
                    clear_resource(row)
                    show_log(row, "停止线程")
                    time.sleep(0.2)
                if ks_pause:
                    self.线程控制器.pause(row)
                    show_log(row, "暂停线程")
                    time.sleep(0.5)
                if ks_resume:
                    self.线程控制器.resume(row)
                    show_log(row, "恢复线程")
                    time.sleep(0.5)
            if ks_cfg and rows:
                show_log(rows[0], "打开配置")
                os.system(f"start {HOME_CONFIG}")
                time.sleep(1)
            self.ui.tk_table_m1ap2ahd.after(10, func)

        func()

    # endregion
    # region 重置任务状态（日常+周常）
    def reset_task_state(self):
        """
        重置选中行的任务状态（包括日常任务和周常任务）
        下次登录时会重新执行所有任务
        """
        if not self.当前选中行号列表:
            messagebox.showinfo("警告", "请先用鼠标左键选中行")
            return
        
        try:
            from task_list.task import migrate_progress_raw, _default_daily_state
            import datetime
            
            for row in self.当前选中行号列表:
                ip = get_row_content(row)[1]
                cfg = self.配置.setdefault("进度配置", {})
                
                # 获取或创建进度数据
                blob = migrate_progress_raw(cfg.get(ip))
                
                # 重置日常任务状态
                if "daily" in blob:
                    daily = blob["daily"]
                    daily["account_index"] = 0
                    daily["branch"] = None
                    daily["completed_steps"] = []
                    daily["random_order"] = []
                    # 保留 calendar_date，让系统自动判断是否需要重置
                
                # 重置周常任务状态
                if "weekly" in blob:
                    weekly = blob["weekly"]
                    # 保留 week_start_date，只清空已完成任务列表
                    weekly["completed_tasks"] = []
                
                # 保存更新后的进度
                cfg[ip] = blob
                show_log(row, f"✓ 已重置任务状态 (IP: {ip})", 表格_状态)
            
            # 写入配置文件
            self.配置.写入本地配置文件()
            messagebox.showinfo("成功", f"已重置 {len(self.当前选中行号列表)} 个账号的任务状态")
            
        except Exception as e:
            import traceback
            error_msg = f"重置任务状态失败: {e}\n{traceback.format_exc()}"
            messagebox.showerror("错误", error_msg)
    
    # endregion
    # region 重置所有任务状态
    def reset_all_task_state(self):
        """
        重置所有账号的任务状态
        """
        try:
            from task_list.task import migrate_progress_raw
            
            cfg = self.配置.setdefault("进度配置", {})
            count = 0
            
            for ip in list(cfg.keys()):
                blob = migrate_progress_raw(cfg.get(ip))
                
                # 重置日常任务状态
                if "daily" in blob:
                    daily = blob["daily"]
                    daily["account_index"] = 0
                    daily["branch"] = None
                    daily["completed_steps"] = []
                    daily["random_order"] = []
                
                # 重置周常任务状态
                if "weekly" in blob:
                    weekly = blob["weekly"]
                    weekly["completed_tasks"] = []
                
                cfg[ip] = blob
                count += 1
            
            # 写入配置文件
            self.配置.写入本地配置文件()
            messagebox.showinfo("成功", f"已重置所有 {count} 个账号的任务状态")
            
        except Exception as e:
            import traceback
            error_msg = f"重置所有任务状态失败: {e}\n{traceback.format_exc()}"
            messagebox.showerror("错误", error_msg)
    
    # endregion
    # region 创建右键菜单
    def create_right_menu(self):
        self.context_menu = tk.Menu(self.ui, tearoff=0)
        self.context_menu.add_command(label="启动所有", command=self.start_all)
        self.context_menu.add_command(label="暂停所有", command=self.pause_all)
        self.context_menu.add_command(label="恢复所有", command=self.resume_all)
        self.context_menu.add_command(label="停止所有", command=self.stop_all)
        self.context_menu.add_separator()  # 分割线
        self.context_menu.add_command(label="启动", command=self.start)
        self.context_menu.add_command(label="暂停(f3)", command=self.pause)
        self.context_menu.add_command(label="恢复(f4)", command=self.resume)
        self.context_menu.add_command(label="停止(f2)", command=self.stop)
        self.context_menu.add_separator()  # 分割线
        self.context_menu.add_command(label="打开配置(f5)", command=self.open_config)
        self.context_menu.add_command(label="打开日志", command=self.open_log)
        self.context_menu.add_command(label="重新载入", command=self.load_config)
        self.context_menu.add_separator()  # 分割线
        self.context_menu.add_command(label="重置任务状态", command=self.reset_task_state)
        self.context_menu.add_command(label="重置所有任务状态", command=self.reset_all_task_state)
        self.context_menu.add_separator()  # 分割线
        self.context_menu.add_command(label="弹起所有按键", command=self.tanQiSuoYouAnJian)
        self.context_menu.add_separator()  # 分割线

    # endregion

