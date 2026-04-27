# -*- coding: utf-8 -*-
"""
多开框架 Web 监控面板
提供浏览器访问的实时监控界面
"""
import threading
import time
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import psutil
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.stability_optimizer import km_lock_enhanced, window_recovery_queue, vnc_pool
except ImportError:
    print("⚠️ 警告: 无法导入稳定性优化模块")


class MonitorDataCollector:
    """监控数据收集器"""
    
    def __init__(self):
        self.crash_count = 0
        self.last_crash_time = None
        self.start_time = time.time()
        
    def get_system_stats(self):
        """获取系统资源统计"""
        # CPU和内存
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / 1024 / 1024
        memory_total_mb = memory.total / 1024 / 1024
        
        # 网络带宽（估算）
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_used_mb": round(memory_used_mb, 2),
            "memory_total_mb": round(memory_total_mb, 2),
            "network_sent_mb": round(bytes_sent / 1024 / 1024, 2),
            "network_recv_mb": round(bytes_recv / 1024 / 1024, 2),
        }
    
    def get_stability_stats(self):
        """获取稳定性优化统计"""
        try:
            km_stats = km_lock_enhanced.get_stats()
            queue_len = window_recovery_queue.queue_length()
            
            return {
                "km_operations": km_stats["总操作数"],
                "km_success": km_stats["成功操作"],
                "km_failed": km_stats["失败操作"],
                "km_avg_wait": km_stats["平均等待时间"],
                "recovery_queue_length": queue_len,
                "crash_count": self.crash_count,
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_account_status(self):
        """获取账号任务状态（从配置文件读取）"""
        try:
            from dxGame.dx_model import gl_info, td_info
            
            accounts = []
            
            # 尝试从配置中获取账号信息
            if hasattr(gl_info, '配置'):
                config = gl_info.配置
                
                # 读取账号配置
                if hasattr(config, 'data'):
                    account_config = config.data.get('账号配置', {})
                    
                    for port, account_list in account_config.items():
                        if isinstance(account_list, list):
                            for i, account_str in enumerate(account_list):
                                # 解析账号字符串: "手机号|密码|角色名|服务器ID"
                                parts = account_str.split('|')
                                phone = parts[0] if len(parts) > 0 else "未知"
                                role_name = parts[2] if len(parts) > 2 else "未知"
                                
                                # 获取任务状态
                                row = int(port) - 5600 if port.isdigit() else 0
                                process = "未知"
                                if row in td_info and hasattr(td_info[row], 'process'):
                                    process = td_info[row].process
                                
                                accounts.append({
                                    "port": port,
                                    "row": row,
                                    "phone": phone,
                                    "role_name": role_name,
                                    "process": process,
                                    "index": i + 1
                                })
            
            return accounts
        except Exception as e:
            return []
    
    def collect_all_stats(self):
        """收集所有统计数据"""
        system_stats = self.get_system_stats()
        stability_stats = self.get_stability_stats()
        account_status = self.get_account_status()
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime_seconds": int(time.time() - self.start_time),
            "system": system_stats,
            "stability": stability_stats,
            "accounts": account_status
        }


# 全局监控数据收集器
collector = MonitorDataCollector()


class MonitorRequestHandler(SimpleHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/api/stats':
            # 返回JSON数据
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            stats = collector.collect_all_stats()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/':
            # 返回HTML页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = self.generate_html()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)
    
    def generate_html(self):
        """生成监控页面HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多开框架监控面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: "Microsoft YaHei", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .stat-item:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.95em;
        }
        
        .stat-value {
            color: #333;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .account-table {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow-x: auto;
        }
        
        .account-table h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .status-idle {
            background: #fff3cd;
            color: #856404;
        }
        
        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .updating {
            animation: pulse 0.5s ease-in-out;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 多开框架监控面板</h1>
            <p>实时系统状态与任务监控</p>
        </div>
        
        <div class="stats-grid">
            <!-- 系统资源 -->
            <div class="stat-card">
                <h3>💻 系统资源</h3>
                <div class="stat-item">
                    <span class="stat-label">CPU 使用率</span>
                    <span class="stat-value" id="cpu_percent">--%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">内存使用率</span>
                    <span class="stat-value" id="memory_percent">--%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">已用内存</span>
                    <span class="stat-value" id="memory_used">-- MB</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">总内存</span>
                    <span class="stat-value" id="memory_total">-- MB</span>
                </div>
            </div>
            
            <!-- 稳定性统计 -->
            <div class="stat-card">
                <h3>🔧 稳定性优化</h3>
                <div class="stat-item">
                    <span class="stat-label">KM 操作总数</span>
                    <span class="stat-value" id="km_operations">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">成功操作</span>
                    <span class="stat-value" id="km_success">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">失败操作</span>
                    <span class="stat-value" id="km_failed">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">平均等待时间</span>
                    <span class="stat-value" id="km_avg_wait">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">恢复队列长度</span>
                    <span class="stat-value" id="recovery_queue">--</span>
                </div>
            </div>
            
            <!-- 运行时间 -->
            <div class="stat-card">
                <h3>⏱️ 运行状态</h3>
                <div class="stat-item">
                    <span class="stat-label">启动时间</span>
                    <span class="stat-value" id="start_time">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">运行时长</span>
                    <span class="stat-value" id="uptime">--</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">最后更新</span>
                    <span class="stat-value" id="last_update">--</span>
                </div>
            </div>
        </div>
        
        <!-- 账号状态表格 -->
        <div class="account-table">
            <h2>📋 多开账号状态</h2>
            <table>
                <thead>
                    <tr>
                        <th>端口</th>
                        <th>行号</th>
                        <th>手机号</th>
                        <th>角色名</th>
                        <th>任务状态</th>
                    </tr>
                </thead>
                <tbody id="account_table_body">
                    <tr>
                        <td colspan="5" style="text-align: center;">加载中...</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="refresh-info">
            <p>🔄 自动刷新：每5秒 | 最后更新：<span id="update_time">--</span></p>
        </div>
    </div>
    
    <script>
        // 格式化运行时长
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}小时${minutes}分${secs}秒`;
            } else if (minutes > 0) {
                return `${minutes}分${secs}秒`;
            } else {
                return `${secs}秒`;
            }
        }
        
        // 更新统计数据
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                // 更新系统资源
                document.getElementById('cpu_percent').textContent = data.system.cpu_percent + '%';
                document.getElementById('memory_percent').textContent = data.system.memory_percent + '%';
                document.getElementById('memory_used').textContent = data.system.memory_used_mb + ' MB';
                document.getElementById('memory_total').textContent = data.system.memory_total_mb + ' MB';
                
                // 更新稳定性统计
                if (data.stability.error) {
                    document.getElementById('km_operations').textContent = 'N/A';
                } else {
                    document.getElementById('km_operations').textContent = data.stability.km_operations;
                    document.getElementById('km_success').textContent = data.stability.km_success;
                    document.getElementById('km_failed').textContent = data.stability.km_failed;
                    document.getElementById('km_avg_wait').textContent = data.stability.km_avg_wait;
                    document.getElementById('recovery_queue').textContent = data.stability.recovery_queue_length;
                }
                
                // 更新运行时间
                document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
                document.getElementById('last_update').textContent = data.timestamp;
                document.getElementById('update_time').textContent = data.timestamp;
                
                // 更新账号表格
                const tbody = document.getElementById('account_table_body');
                if (data.accounts && data.accounts.length > 0) {
                    tbody.innerHTML = data.accounts.map(acc => `
                        <tr>
                            <td>${acc.port}</td>
                            <td>${acc.row}</td>
                            <td>${acc.phone}</td>
                            <td>${acc.role_name}</td>
                            <td><span class="status-badge ${acc.process === '登陆' || acc.process.includes('任务') ? 'status-running' : 'status-idle'}">${acc.process}</span></td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">暂无账号数据</td></tr>';
                }
                
                // 添加更新动画
                document.body.classList.add('updating');
                setTimeout(() => {
                    document.body.classList.remove('updating');
                }, 500);
                
            } catch (error) {
                console.error('获取统计数据失败:', error);
            }
        }
        
        // 初始加载
        updateStats();
        
        // 每5秒自动刷新
        setInterval(updateStats, 5000);
    </script>
</body>
</html>'''


def start_web_monitor(port=8080):
    """启动Web监控服务"""
    server = HTTPServer(('0.0.0.0', port), MonitorRequestHandler)
    
    print("="*60)
    print("🎮 多开框架 Web 监控面板")
    print("="*60)
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"📍 局域网访问: http://<您的IP>:{port}")
    print("="*60)
    print("✅ 监控服务已启动，按 Ctrl+C 停止")
    print("="*60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⚠️ 监控服务已停止")
        server.shutdown()


if __name__ == "__main__":
    start_web_monitor(8080)
