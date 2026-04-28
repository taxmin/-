"""
本代码由[Tkinter布局助手]生成
官网:https://www.pytk.net
QQ交流群:905019785
在线反馈:https://support.qq.com/product/618914
"""

from tkinter import *
from tkinter import ttk
import threading
import time
import os
import datetime as dt

from app.core import *
from public import LOG_DIR

try:
    from app.stability_optimizer import km_lock_enhanced, window_recovery_queue
    HAS_STABILITY_OPT = True
except ImportError:
    HAS_STABILITY_OPT = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
class WinGUI(Tk):
    def __init__(self):
        super().__init__()
        self.__win()
        
        # 先创建标签页容器
        self.tk_notebook = ttk.Notebook(self)
        self.tk_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建主框架（任务列表）
        self.tk_tab_main = Frame(self.tk_notebook)
        self.tk_notebook.add(self.tk_tab_main, text='📋 任务列表')
        self.__create_main_tab_layout()
        
        # 创建性能监控标签页
        self.tk_tab_performance = Frame(self.tk_notebook)
        self.tk_notebook.add(self.tk_tab_performance, text='📊 性能监控')
        
        # 现在可以创建表格了（放在左侧表格容器内）
        self.tk_table_m1ap2ahd = self.__tk_table_m1ap2ahd(self.tk_table_frame)
        self.start_log_monitor()
        
        # 填充性能监控页面内容
        self.__create_performance_tab_content()
        
        # 启动性能监控更新线程
        self.performance_update_thread = None
        self.performance_stop_flag = threading.Event()
        self.start_performance_monitor()
    def __win(self):
        self.title("dx多开框架")
        # 设置窗口大小、居中
        width = 1100
        height = 700
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(geometry)
        self.minsize(900, 520)
        self.resizable(width=True, height=True)

    def scrollbar_autohide(self,vbar, hbar, widget):
        """自动隐藏滚动条"""
        def show():
            if vbar: vbar.lift(widget)
            if hbar: hbar.lift(widget)
        def hide():
            if vbar: vbar.lower(widget)
            if hbar: hbar.lower(widget)
        hide()
        widget.bind("<Enter>", lambda e: show())
        if vbar: vbar.bind("<Enter>", lambda e: show())
        if vbar: vbar.bind("<Leave>", lambda e: hide())
        if hbar: hbar.bind("<Enter>", lambda e: show())
        if hbar: hbar.bind("<Leave>", lambda e: hide())
        widget.bind("<Leave>", lambda e: hide())

    def v_scrollbar(self,vbar, widget, x, y, w, h, pw, ph):
        widget.configure(yscrollcommand=vbar.set)
        vbar.config(command=widget.yview)
        vbar.place(relx=(w + x) / pw, rely=y / ph, relheight=h / ph, anchor='ne')
    def h_scrollbar(self,hbar, widget, x, y, w, h, pw, ph):
        widget.configure(xscrollcommand=hbar.set)
        hbar.config(command=widget.xview)
        hbar.place(relx=x / pw, rely=(y + h) / ph, relwidth=w / pw, anchor='sw')
    def create_bar(self,master, widget,is_vbar,is_hbar, x, y, w, h, pw, ph):
        vbar, hbar = None, None
        if is_vbar:
            vbar = Scrollbar(master)
            self.v_scrollbar(vbar, widget, x, y, w, h, pw, ph)
        if is_hbar:
            hbar = Scrollbar(master, orient="horizontal")
            self.h_scrollbar(hbar, widget, x, y, w, h, pw, ph)
        self.scrollbar_autohide(vbar, hbar, widget)
    
    def __create_performance_tab_content(self):
        """创建性能监控标签页的内容"""
        
        # 使用已存在的 tk_tab_performance
        tab_frame = self.tk_tab_performance
        
        # 创建滚动区域
        canvas = Canvas(tab_frame)
        scrollbar = Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scroll_frame = Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ===== 系统资源监控区域 =====
        system_frame = LabelFrame(scroll_frame, text="💻 系统资源监控", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        system_frame.pack(fill="x", padx=10, pady=5)
        
        # CPU使用率
        cpu_frame = Frame(system_frame)
        cpu_frame.pack(fill="x", pady=2)
        Label(cpu_frame, text="CPU使用率:", width=12, anchor="w").pack(side="left")
        self.cpu_progress = ttk.Progressbar(cpu_frame, orient="horizontal", length=400, mode="determinate", maximum=100)
        self.cpu_progress.pack(side="left", padx=5)
        self.cpu_label = Label(cpu_frame, text="0%", width=6)
        self.cpu_label.pack(side="left")
        
        # 内存使用率
        mem_frame = Frame(system_frame)
        mem_frame.pack(fill="x", pady=2)
        Label(mem_frame, text="内存使用率:", width=12, anchor="w").pack(side="left")
        self.mem_progress = ttk.Progressbar(mem_frame, orient="horizontal", length=400, mode="determinate", maximum=100)
        self.mem_progress.pack(side="left", padx=5)
        self.mem_label = Label(mem_frame, text="0%", width=6)
        self.mem_label.pack(side="left")
        
        # 内存详情
        mem_detail_frame = Frame(system_frame)
        mem_detail_frame.pack(fill="x", pady=2)
        self.mem_detail_label = Label(mem_detail_frame, text="已用: 0 MB / 总计: 0 MB", fg="gray")
        self.mem_detail_label.pack(anchor="w")
        
        # ===== 稳定性优化统计区域 =====
        if HAS_STABILITY_OPT:
            stability_frame = LabelFrame(scroll_frame, text="🔧 稳定性优化统计", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
            stability_frame.pack(fill="x", padx=10, pady=5)
            
            stats_frame = Frame(stability_frame)
            stats_frame.pack(fill="x")
            
            # KM操作统计
            Label(stats_frame, text="KM操作总数:", width=12, anchor="w").grid(row=0, column=0, sticky="w", pady=2)
            self.km_total_label = Label(stats_frame, text="0", fg="blue", font=("微软雅黑", 9, "bold"))
            self.km_total_label.grid(row=0, column=1, sticky="w", padx=5)
            
            Label(stats_frame, text="成功操作:", width=12, anchor="w").grid(row=1, column=0, sticky="w", pady=2)
            self.km_success_label = Label(stats_frame, text="0", fg="green", font=("微软雅黑", 9, "bold"))
            self.km_success_label.grid(row=1, column=1, sticky="w", padx=5)
            
            Label(stats_frame, text="失败操作:", width=12, anchor="w").grid(row=2, column=0, sticky="w", pady=2)
            self.km_failed_label = Label(stats_frame, text="0", fg="red", font=("微软雅黑", 9, "bold"))
            self.km_failed_label.grid(row=2, column=1, sticky="w", padx=5)
            
            Label(stats_frame, text="平均等待时间:", width=12, anchor="w").grid(row=3, column=0, sticky="w", pady=2)
            self.km_avg_wait_label = Label(stats_frame, text="0s", fg="purple", font=("微软雅黑", 9, "bold"))
            self.km_avg_wait_label.grid(row=3, column=1, sticky="w", padx=5)
            
            # 队列状态
            queue_frame = Frame(stability_frame)
            queue_frame.pack(fill="x", pady=(10, 0))
            Label(queue_frame, text="恢复队列长度:", width=12, anchor="w").pack(side="left")
            self.queue_length_label = Label(queue_frame, text="0", fg="orange", font=("微软雅黑", 10, "bold"))
            self.queue_length_label.pack(side="left", padx=5)
        
        # ===== VNC 性能监控区域 =====
        vnc_perf_frame = LabelFrame(scroll_frame, text="📊 VNC 性能监控", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        vnc_perf_frame.pack(fill="x", padx=10, pady=5)
        
        vnc_stats_frame = Frame(vnc_perf_frame)
        vnc_stats_frame.pack(fill="x")
        
        # VNC 重连统计
        Label(vnc_stats_frame, text="VNC重连次数:", width=12, anchor="w").grid(row=0, column=0, sticky="w", pady=2)
        self.vnc_reconnect_label = Label(vnc_stats_frame, text="0", fg="red", font=("微软雅黑", 9, "bold"))
        self.vnc_reconnect_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # 截图统计
        Label(vnc_stats_frame, text="截图总次数:", width=12, anchor="w").grid(row=1, column=0, sticky="w", pady=2)
        self.screenshot_total_label = Label(vnc_stats_frame, text="0", fg="blue", font=("微软雅黑", 9, "bold"))
        self.screenshot_total_label.grid(row=1, column=1, sticky="w", padx=5)
        
        Label(vnc_stats_frame, text="截图成功率:", width=12, anchor="w").grid(row=2, column=0, sticky="w", pady=2)
        self.screenshot_rate_label = Label(vnc_stats_frame, text="N/A", fg="green", font=("微软雅黑", 9, "bold"))
        self.screenshot_rate_label.grid(row=2, column=1, sticky="w", padx=5)
        
        # 键鼠统计
        Label(vnc_stats_frame, text="KM移动次数:", width=12, anchor="w").grid(row=3, column=0, sticky="w", pady=2)
        self.km_move_label = Label(vnc_stats_frame, text="0", fg="purple", font=("微软雅黑", 9, "bold"))
        self.km_move_label.grid(row=3, column=1, sticky="w", padx=5)
        
        Label(vnc_stats_frame, text="KM点击次数:", width=12, anchor="w").grid(row=4, column=0, sticky="w", pady=2)
        self.km_click_label = Label(vnc_stats_frame, text="0", fg="purple", font=("微软雅黑", 9, "bold"))
        self.km_click_label.grid(row=4, column=1, sticky="w", padx=5)
        
        Label(vnc_stats_frame, text="KM按键次数:", width=12, anchor="w").grid(row=5, column=0, sticky="w", pady=2)
        self.km_keypress_label = Label(vnc_stats_frame, text="0", fg="purple", font=("微软雅黑", 9, "bold"))
        self.km_keypress_label.grid(row=5, column=1, sticky="w", padx=5)
        
        # 崩溃统计
        crash_frame = Frame(vnc_perf_frame)
        crash_frame.pack(fill="x", pady=(10, 0))
        Label(crash_frame, text="崩溃次数:", width=12, anchor="w").pack(side="left")
        self.crash_count_label = Label(crash_frame, text="0", fg="red", font=("微软雅黑", 10, "bold"))
        self.crash_count_label.pack(side="left", padx=5)
        
        # 导出报告按钮
        Button(crash_frame, text="📄 导出报告", command=self.export_vnc_report,
               bg="#FF9800", fg="white", font=("微软雅黑", 9)).pack(side="right", padx=5)
        
        # 初始化窗口位置存储
        self.window_positions = {}  # {hwnd: (x, y, width, height)}
        self.windows_hidden = False  # 标记窗口是否已隐藏
        
        # ===== 运行状态区域 =====
        status_frame = LabelFrame(scroll_frame, text="⏱️ 运行状态", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_time = time.time()
        self.uptime_label = Label(status_frame, text="运行时长: 0秒", font=("微软雅黑", 9), fg="darkgreen")
        self.uptime_label.pack(anchor="w", pady=2)
        
        self.last_update_label = Label(status_frame, text="最后更新: --", font=("微软雅黑", 9), fg="gray")
        self.last_update_label.pack(anchor="w", pady=2)
        
        # 刷新按钮
        refresh_btn_frame = Frame(status_frame)
        refresh_btn_frame.pack(pady=5)
        Button(refresh_btn_frame, text="🔄 立即刷新", command=self.update_performance_data, 
               bg="#4CAF50", fg="white", font=("微软雅黑", 9)).pack(side="left", padx=5)
        
        auto_refresh_var = BooleanVar(value=True)
        Checkbutton(refresh_btn_frame, text="自动刷新(5秒)", variable=auto_refresh_var,
                    font=("微软雅黑", 9), command=self.toggle_auto_refresh).pack(side="left", padx=5)
        self.auto_refresh_enabled = auto_refresh_var
        
        # ===== 说明信息 =====
        info_frame = LabelFrame(scroll_frame, text="ℹ️ 说明", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """• 数据每5秒自动更新，也可点击"立即刷新"按钮手动刷新
• 绿色进度条表示正常使用范围，红色表示过高
• KM锁统计显示稳定性优化的运行情况
• 恢复队列长度应该保持为0或很小的值"""
        Label(info_frame, text=info_text, justify="left", fg="gray", font=("微软雅黑", 8)).pack()

    def __create_main_tab_layout(self):
        """主页面三栏布局：左侧任务表，中间快捷操作，右侧实时日志"""
        self.tk_tab_main.grid_rowconfigure(0, weight=1)
        self.tk_tab_main.grid_columnconfigure(0, weight=4)
        self.tk_tab_main.grid_columnconfigure(1, weight=1)
        self.tk_tab_main.grid_columnconfigure(2, weight=2)

        self.tk_table_frame = LabelFrame(self.tk_tab_main, text="任务列表", padx=4, pady=4)
        self.tk_table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)
        self.tk_table_frame.grid_rowconfigure(0, weight=1)
        self.tk_table_frame.grid_columnconfigure(0, weight=1)

        # 中间快捷操作区（位于任务列表和实时日志之间）
        self.tk_quick_action_frame = LabelFrame(self.tk_tab_main, text="快捷操作（按钮 / 右键菜单）", padx=6, pady=6)
        self.tk_quick_action_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=2)
        self.tk_quick_action_frame.grid_columnconfigure(0, weight=1)

        log_frame = LabelFrame(self.tk_tab_main, text="实时日志(0/1)", padx=6, pady=6)
        log_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=2)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.tk_log_text = Text(log_frame, wrap="word", font=("Consolas", 9))
        self.tk_log_text.grid(row=0, column=0, sticky="nsew")
        self.tk_log_text.configure(state="disabled")

        self.tk_log_scroll = Scrollbar(log_frame, orient="vertical", command=self.tk_log_text.yview)
        self.tk_log_scroll.grid(row=0, column=1, sticky="ns")
        self.tk_log_text.configure(yscrollcommand=self.tk_log_scroll.set)

        self.log_offsets = {}
        self.log_monitor_enabled = True

    def _append_log_text(self, content):
        """向日志面板追加内容并自动滚动到底部"""
        if not hasattr(self, "tk_log_text"):
            return
        self.tk_log_text.configure(state="normal")
        self.tk_log_text.insert("end", content)
        self.tk_log_text.see("end")
        # 控制文本长度，避免长时间运行占用过高内存
        line_count = int(self.tk_log_text.index("end-1c").split(".")[0])
        if line_count > 2500:
            self.tk_log_text.delete("1.0", "500.0")
        self.tk_log_text.configure(state="disabled")

    def _poll_log_files(self):
        """增量读取日志文件的新增内容"""
        try:
            if not self.log_monitor_enabled:
                return

            today = dt.datetime.now().strftime("%Y-%m-%d")
            log_dir = LOG_DIR
            targets = [
                (0, os.path.join(log_dir, f"0_{today}.txt")),
                (1, os.path.join(log_dir, f"1_{today}.txt")),
            ]
            new_entries = []
            for idx, file_path in targets:
                try:
                    if not os.path.exists(file_path):
                        continue
                    current_size = os.path.getsize(file_path)
                    last_offset = self.log_offsets.get(file_path, 0)
                    # 文件被清空/轮转时，从头重新读取
                    if current_size < last_offset:
                        last_offset = 0
                    if current_size == last_offset:
                        continue

                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(last_offset)
                        new_content = f.read()
                        self.log_offsets[file_path] = f.tell()

                    if new_content:
                        lines = [line for line in new_content.splitlines() if line.strip()]
                        for line in lines:
                            ts = self._extract_log_time(line)
                            new_entries.append((ts, idx, line))
                except Exception:
                    # 单文件读取失败不影响另一个文件
                    pass
            if new_entries:
                new_entries.sort(key=lambda item: item[0])
                display = "\n".join([f"[{idx}] {line}" for _, idx, line in new_entries]) + "\n"
                self._append_log_text(display)
        finally:
            if self.log_monitor_enabled:
                self.after(1000, self._poll_log_files)

    def start_log_monitor(self):
        """启动日志监控"""
        self.after(1000, self._poll_log_files)

    def _extract_log_time(self, line):
        """从日志行提取时间，用于排序。解析失败时返回最小时间。"""
        try:
            first_token = line.split(" ", 1)[0]
            return dt.datetime.strptime(first_token, "%Y-%m-%d-%H:%M:%S")
        except Exception:
            return dt.datetime.min

    def clear_log_panel_and_files(self):
        """清空右侧日志面板和当日日志文件内容。"""
        self.tk_log_text.configure(state="normal")
        self.tk_log_text.delete("1.0", "end")
        self.tk_log_text.configure(state="disabled")

        today = dt.datetime.now().strftime("%Y-%m-%d")
        targets = [
            os.path.join(LOG_DIR, f"0_{today}.txt"),
            os.path.join(LOG_DIR, f"1_{today}.txt"),
        ]
        for file_path in targets:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8"):
                    pass
                self.log_offsets[file_path] = 0
            except Exception:
                pass
    
    def start_performance_monitor(self):
        """启动性能监控更新线程"""
        def update_loop():
            while not self.performance_stop_flag.is_set():
                if self.auto_refresh_enabled.get():
                    try:
                        self.after(0, self.update_performance_data)
                    except:
                        pass
                time.sleep(5)
        
        self.performance_update_thread = threading.Thread(target=update_loop, daemon=True, name="PerformanceMonitor")
        self.performance_update_thread.start()
    
    def toggle_auto_refresh(self):
        """切换自动刷新"""
        pass  # 已经在update_loop中检查标志位
    
    def update_performance_data(self):
        """更新性能监控数据"""
        try:
            # 更新系统资源
            if HAS_PSUTIL:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.cpu_progress['value'] = cpu_percent
                self.cpu_label.config(text=f"{cpu_percent:.1f}%")
                if cpu_percent > 80:
                    self.cpu_label.config(fg="red")
                elif cpu_percent > 50:
                    self.cpu_label.config(fg="orange")
                else:
                    self.cpu_label.config(fg="green")
                
                # 内存
                memory = psutil.virtual_memory()
                mem_percent = memory.percent
                mem_used_mb = memory.used / 1024 / 1024
                mem_total_mb = memory.total / 1024 / 1024
                
                self.mem_progress['value'] = mem_percent
                self.mem_label.config(text=f"{mem_percent:.1f}%")
                self.mem_detail_label.config(text=f"已用: {mem_used_mb:.0f} MB / 总计: {mem_total_mb:.0f} MB")
                
                if mem_percent > 80:
                    self.mem_label.config(fg="red")
                elif mem_percent > 50:
                    self.mem_label.config(fg="orange")
                else:
                    self.mem_label.config(fg="green")
            
            # 更新稳定性统计
            if HAS_STABILITY_OPT:
                stats = km_lock_enhanced.get_stats()
                self.km_total_label.config(text=str(stats["总操作数"]))
                self.km_success_label.config(text=str(stats["成功操作"]))
                self.km_failed_label.config(text=str(stats["失败操作"]))
                self.km_avg_wait_label.config(text=stats["平均等待时间"])
                
                queue_len = window_recovery_queue.queue_length()
                self.queue_length_label.config(text=str(queue_len))
                if queue_len > 3:
                    self.queue_length_label.config(fg="red")
                else:
                    self.queue_length_label.config(fg="orange")
                
                # 🔧 更新 VNC 性能监控
                try:
                    from app.stability_optimizer import vnc_performance_monitor
                    vnc_stats = vnc_performance_monitor.get_stats()
                    
                    self.vnc_reconnect_label.config(text=str(vnc_stats['VNC重连次数']))
                    self.screenshot_total_label.config(text=str(vnc_stats['截图总次数']))
                    self.screenshot_rate_label.config(text=vnc_stats['截图成功率'])
                    self.km_move_label.config(text=str(vnc_stats['KM移动次数']))
                    self.km_click_label.config(text=str(vnc_stats['KM点击次数']))
                    self.km_keypress_label.config(text=str(vnc_stats['KM按键次数']))
                    self.crash_count_label.config(text=str(vnc_stats['崩溃次数']))
                    
                    # 根据崩溃次数设置颜色
                    crash_count = vnc_stats['崩溃次数']
                    if crash_count == 0:
                        self.crash_count_label.config(fg="green")
                    elif crash_count <= 2:
                        self.crash_count_label.config(fg="orange")
                    else:
                        self.crash_count_label.config(fg="red")
                    
                    # 🔧 新增：显示主要崩溃位置（如果有崩溃）
                    if vnc_stats.get('崩溃位置分布') and crash_count > 0:
                        # 找到崩溃次数最多的位置
                        top_crash_loc = max(vnc_stats['崩溃位置分布'].items(), key=lambda x: x[1])
                        if hasattr(self, 'crash_location_label'):
                            self.crash_location_label.config(
                                text=f"主要崩溃位置: {top_crash_loc[0]} ({top_crash_loc[1]}次)",
                                fg="red"
                            )
                        else:
                            # 如果标签不存在，创建它
                            crash_loc_frame = Frame(vnc_perf_frame)
                            crash_loc_frame.pack(fill="x", pady=(5, 0))
                            Label(crash_loc_frame, text="主要崩溃位置:", width=12, anchor="w").pack(side="left")
                            self.crash_location_label = Label(
                                crash_loc_frame, 
                                text=f"{top_crash_loc[0]} ({top_crash_loc[1]}次)", 
                                fg="red", 
                                font=("微软雅黑", 9, "bold")
                            )
                            self.crash_location_label.pack(side="left", padx=5)
                except Exception as e:
                    print(f"更新 VNC 性能监控失败: {e}")
            
            # 更新运行时长
            uptime = int(time.time() - self.start_time)
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            seconds = uptime % 60
            if hours > 0:
                uptime_str = f"{hours}小时{minutes}分{seconds}秒"
            elif minutes > 0:
                uptime_str = f"{minutes}分{seconds}秒"
            else:
                uptime_str = f"{seconds}秒"
            self.uptime_label.config(text=f"运行时长: {uptime_str}")
            
            # 更新时间戳
            now_str = dt.datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(text=f"最后更新: {now_str}")
            
        except Exception as e:
            print(f"更新性能数据失败: {e}")
    
    def export_vnc_report(self):
        """导出 VNC 性能报告"""
        try:
            from app.stability_optimizer import vnc_performance_monitor
            import tkinter.filedialog as fd
            
            filepath = fd.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"vnc_performance_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filepath:
                vnc_performance_monitor.export_report(filepath)
                import tkinter.messagebox as mb
                mb.showinfo("成功", f"性能报告已导出到:\n{filepath}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("错误", f"导出报告失败: {e}")
    
    def _get_ports_from_config(self):
        """
        从配置文件中读取账号配置的端口号
        
        Returns:
            list: 端口号列表，如 ["5600", "5601"]
        """
        try:
            from dxGame.dx_model import gl_info
            
            # 获取配置对象
            config = getattr(gl_info, '配置', None)
            if config is None:
                print("⚠️ 配置对象未初始化")
                return []
            
            # 读取账号配置部分
            account_config = config.data.get('账号配置', {})
            
            if not account_config:
                print("⚠️ 账号配置为空")
                return []
            
            # 提取所有端口号（即账号配置的键）
            ports = list(account_config.keys())
            
            print(f"✓ 从配置文件读取到 {len(ports)} 个端口: {ports}")
            return ports
            
        except Exception as e:
            print(f"❌ 读取配置端口失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def toggle_hide_windows(self):
        """切换窗口隐藏/恢复状态"""
        if self.windows_hidden:
            self.restore_windows()
        else:
            self.hide_windows()
    
    def hide_windows(self):
        """隐藏所有虚拟机窗口（移动到屏幕外）"""
        try:
            import ctypes.wintypes
            from dxGame.dx_Window import Window
            
            # 🔧 从配置文件读取账号配置的端口号
            ports = self._get_ports_from_config()
            
            if not ports:
                import tkinter.messagebox as mb
                mb.showwarning("警告", "未找到正在运行的虚拟机窗口")
                return
            
            hidden_count = 0
            try:
                screen_width = ctypes.windll.user32.GetSystemMetrics(0)  # 获取屏幕宽度
            except Exception as e:
                import logging
                logging.warning(f"⚠️ 获取屏幕宽度失败: {e}，使用默认值 1920")
                screen_width = 1920
            
            for port in ports:
                try:
                    # 🔧 使用端口号构建窗口标题：'5600 - VMware Workstation'
                    window_title_pattern = f"{port} - VMware Workstation"
                    
                    # 🔧 直接枚举所有顶级窗口，查找标题匹配的VMware主窗口
                    target_hwnd = 0
                    
                    def enum_windows_callback(hwnd, lParam):
                        nonlocal target_hwnd
                        
                        # 检查窗口是否可见
                        if not ctypes.windll.user32.IsWindowVisible(hwnd):
                            return True
                        
                        # 获取窗口标题
                        title = Window.GetWindowTitle(hwnd)
                        
                        # 🔧 精确匹配窗口标题
                        if title and window_title_pattern in title:
                            target_hwnd = hwnd
                            print(f"✓ 找到端口 {port} 的VMware主窗口: HWND={hwnd}, 标题='{title}'")
                            return False  # 找到目标，停止枚举
                        
                        return True
                    
                    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
                    ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
                    
                    if not target_hwnd or not ctypes.windll.user32.IsWindow(target_hwnd):
                        print(f"⚠️ 端口 {port} 的VMware窗口未找到（期望标题: '{window_title_pattern}'），跳过")
                        continue
                    
                    # 获取当前窗口位置
                    rect = ctypes.wintypes.RECT()
                    if ctypes.windll.user32.GetWindowRect(target_hwnd, ctypes.byref(rect)):
                        # 保存原始位置
                        width = rect.right - rect.left
                        height = rect.bottom - rect.top
                        self.window_positions[target_hwnd] = (rect.left, rect.top, width, height)
                        
                        # 将窗口移动到屏幕外（右侧）
                        off_screen_x = screen_width + 100
                        ctypes.windll.user32.MoveWindow(
                            target_hwnd, 
                            off_screen_x, 
                            rect.top, 
                            width, 
                            height, 
                            True
                        )
                        hidden_count += 1
                        print(f"✓ 已隐藏端口 {port} 的VMware窗口")
                        
                except Exception as e:
                    print(f"❌ 隐藏窗口 端口:{port} 失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            if hidden_count > 0:
                self.windows_hidden = True
                if hasattr(self, "quick_toggle_windows_btn"):
                    self.quick_toggle_windows_btn.config(
                        text="恢复游戏窗口",
                        bg="#FF9800",
                        fg="white",
                        activebackground="#FB8C00",
                        activeforeground="white"
                    )
                print(f"\n✅ 成功隐藏 {hidden_count} 个VMware虚拟机窗口")
            else:
                import tkinter.messagebox as mb
                mb.showwarning("警告", "未能隐藏任何窗口")
                
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("错误", f"隐藏窗口失败: {e}")
            import traceback
            traceback.print_exc()
    
    def restore_windows(self):
        """恢复所有隐藏的虚拟机窗口到原始位置"""
        try:
            import ctypes.wintypes
            
            if not self.window_positions:
                import tkinter.messagebox as mb
                mb.showwarning("警告", "没有已隐藏的窗口需要恢复")
                return
            
            restored_count = 0
            
            for hwnd, (x, y, width, height) in self.window_positions.items():
                try:
                    if ctypes.windll.user32.IsWindow(hwnd):
                        # 恢复窗口到原始位置
                        ctypes.windll.user32.MoveWindow(
                            hwnd, 
                            x, 
                            y, 
                            width, 
                            height, 
                            True
                        )
                        restored_count += 1
                    else:
                        print(f"⚠️ 窗口句柄 {hwnd} 已失效，跳过恢复")
                        
                except Exception as e:
                    print(f"恢复窗口 {hwnd} 失败: {e}")
            
            if restored_count > 0:
                self.windows_hidden = False
                self.window_positions.clear()  # 清空位置记录
                if hasattr(self, "quick_toggle_windows_btn"):
                    self.quick_toggle_windows_btn.config(
                        text="隐藏游戏窗口",
                        bg="#4CAF50",
                        fg="white",
                        activebackground="#43A047",
                        activeforeground="white"
                    )
                print(f"✓ 已恢复 {restored_count} 个虚拟机窗口")
            else:
                import tkinter.messagebox as mb
                mb.showwarning("警告", "未能恢复任何窗口")
                
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("错误", f"恢复窗口失败: {e}")
            import traceback
            traceback.print_exc()
    
    def on_closing(self):
        """窗口关闭时的清理工作"""
        self.log_monitor_enabled = False
        self.performance_stop_flag.set()
        if self.performance_update_thread:
            self.performance_update_thread.join(timeout=2)
        self.destroy()
    def __tk_table_m1ap2ahd(self,parent):
        # 表头字段 表头宽度
        columns = {"ID":29,"名称":50,"账号/密码":120,"任务状态":80,"金币":60,"状态":119}
        tk_table = Treeview(parent, show="headings", columns=list(columns))
        for text, width in columns.items():  # 批量设置列属性
            tk_table.heading(text, text=text, anchor='center')
            # 固定列宽，内容过长时可通过横向滚动条查看
            tk_table.column(text, anchor='center', width=width, stretch=False)

        h_scrollbar = Scrollbar(parent, orient="horizontal", command=tk_table.xview)
        tk_table.configure(xscrollcommand=h_scrollbar.set)
        tk_table.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 🔧 新增：配置金币列的色彩样式（金黄色，突出显示）
        tk_table.tag_configure('gold_highlight', background='#FFF9E6', foreground='#FF8C00')  # 浅黄背景+橙色文字
        tk_table.tag_configure('gold_normal', background='#FFFFFF', foreground='#DAA520')  # 白色背景+金色文字

        # 不在这里指定布局管理器，由 controller.py 统一使用 grid 管理
        return tk_table
class Win(WinGUI):
    def __init__(self, controller):
        self.ctl = controller
        super().__init__()
        self.__create_log_context_menu()
        self.__event_bind()
        self.__style_config()
        self.ctl.init(self)
        self.__create_task_shortcut_buttons()
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    def __create_task_shortcut_buttons(self):
        """在任务列表页创建与右键菜单一致的快捷按钮。"""
        if not hasattr(self, "tk_quick_action_frame"):
            return
        actions = [
            ("隐藏游戏窗口", self.toggle_hide_windows),
            ("启动所有", self.ctl.start_all),
            ("暂停所有", self.ctl.pause_all),
            ("恢复所有", self.ctl.resume_all),
            ("停止所有", self.ctl.stop_all),
            ("启动", self.ctl.start),
            ("暂停(f3)", self.ctl.pause),
            ("恢复(f4)", self.ctl.resume),
            ("停止(f2)", self.ctl.stop),
            ("打开配置(f5)", self.ctl.open_config),
            ("打开日志", self.ctl.open_log),
            ("重新载入", self.ctl.load_config),
            ("重置任务状态", self.ctl.reset_task_state),
            ("重置所有任务状态", self.ctl.reset_all_task_state),
            ("弹起所有按键", self.ctl.tanQiSuoYouAnJian),
        ]
        for idx, (label, command) in enumerate(actions):
            btn = Button(
                self.tk_quick_action_frame,
                text=label,
                command=command,
                anchor="w",
                padx=6,
                pady=1,
                font=("微软雅黑", 9),
                height=1
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=0)
            if label == "隐藏游戏窗口":
                btn.config(
                    bg="#4CAF50",
                    fg="white",
                    activebackground="#43A047",
                    activeforeground="white"
                )
                self.quick_toggle_windows_btn = btn
    def __create_log_context_menu(self):
        self.log_context_menu = Menu(self, tearoff=0)
        self.log_context_menu.add_command(label="清除日志(并清空表格状态)", command=self.__clear_logs_and_table)
    def __clear_logs_and_table(self):
        self.clear_log_panel_and_files()
        if hasattr(self, "ctl") and self.ctl:
            self.ctl.clear_table_runtime_data()
    def __event_bind(self):
        self.tk_table_m1ap2ahd.bind('<<TreeviewSelect>>', self.ctl.check)
        self.tk_table_m1ap2ahd.bind('<Button-3>', self.ctl.right_show_menu)
        self.tk_table_m1ap2ahd.bind('<Button-1>', self.ctl.left_click)
        self.tk_log_text.bind('<Button-3>', self.__show_log_context_menu)
        pass
    def __show_log_context_menu(self, event):
        self.log_context_menu.tk_popup(event.x_root, event.y_root)
    def __style_config(self):
        pass
    def on_closing(self):
        """重写关闭方法，确保清理监控线程"""
        super().on_closing()
if __name__ == "__main__":
    win = WinGUI()
    win.mainloop()