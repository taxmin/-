# -*- coding: utf-8 -*-
"""
核心配置模板 - 复制为 config_local.py 并填写实际值
此文件不会被提交到 Git
"""

# ==================== VNC 连接配置 ====================
# 模拟器 VNC 端口映射（关键！）
VNC_PORT_MAPPING = {
    # 格式: 行号: (IP, 端口)
    # 示例:
    # 0: ("127.0.0.1", 5900),
    # 1: ("127.0.0.1", 5901),
}

# VNC 密码（如果有）
VNC_PASSWORD = ""

# ==================== 账号配置 ====================
# 账号信息（敏感数据，不要上传）
ACCOUNT_CONFIG = {
    # 格式: 编号: [(账号, 密码, 区服, 角色), ...]
    # 示例:
    # "5601": [
    #     ("18408241173", "12300123.", "2026", "3"),
    # ],
}

# ==================== 任务配置 ====================
# 自定义任务序列（可选）
CUSTOM_TASK_SEQUENCE = {
    # 格式: 行号: ["任务方法1", "任务方法2", ...]
    # 示例:
    # 0: ["日常任务", "师门任务", "挖宝"],
}

# ==================== OCR 配置 ====================
# ONNX OCR 模型路径（如果使用自定义模型）
ONNX_MODEL_PATH = ""

# ==================== 窗口配置 ====================
# VMware/VirtualBox 窗口匹配规则
VMWARE_WINDOW_PATTERN = ""
VIRTUALBOX_WINDOW_PATTERN = ""

# ==================== 高级配置 ====================
# 调试模式（生产环境设为 False）
DEBUG_MODE = False

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# 性能监控开关
ENABLE_PERFORMANCE_MONITOR = True

# ==================== 保留默认配置 ====================
# 以下配置可以公开，从主配置文件加载
import os
import sys

# 尝试加载默认配置
try:
    from dxGame.dx_config import *
except ImportError:
    pass
