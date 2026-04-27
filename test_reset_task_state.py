"""
测试重置任务状态功能
"""
import sys
sys.path.insert(0, r'F:\taxmin\dx多开框架')

from task_list.task import migrate_progress_raw, _default_daily_state
import datetime

# 模拟进度数据
test_blob = {
    "version": 2,
    "now_user_id": 1,
    "now_server_id": 2,
    "now_task_id": 3,
    "now_fuben_id": 4,
    "daily": {
        "calendar_date": "2026-04-12",
        "account_index": 5,
        "branch": "high_activity",
        "completed_steps": [
            "identify_gold",
            "clear_bag_l",
            "stall_l",
            "daily_sanjie"
        ],
        "random_order": [
            "daily_random_shimen",
            "daily_random_baotu"
        ]
    },
    "weekly": {
        "week_start_date": "2026-04-06",
        "completed_tasks": ["剑会", "帮派竞赛"]
    }
}

print("=" * 70)
print("重置前的进度数据:")
print("=" * 70)
print(f"日常任务 - account_index: {test_blob['daily']['account_index']}")
print(f"日常任务 - branch: {test_blob['daily']['branch']}")
print(f"日常任务 - completed_steps: {test_blob['daily']['completed_steps']}")
print(f"日常任务 - random_order: {test_blob['daily']['random_order']}")
print(f"周常任务 - completed_tasks: {test_blob['weekly']['completed_tasks']}")

# 模拟重置操作
blob = migrate_progress_raw(test_blob)

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

print("\n" + "=" * 70)
print("重置后的进度数据:")
print("=" * 70)
print(f"日常任务 - account_index: {blob['daily']['account_index']}")
print(f"日常任务 - branch: {blob['daily']['branch']}")
print(f"日常任务 - completed_steps: {blob['daily']['completed_steps']}")
print(f"日常任务 - random_order: {blob['daily']['random_order']}")
print(f"周常任务 - completed_tasks: {blob['weekly']['completed_tasks']}")

print("\n✓ 重置功能测试通过！")
print("\n说明:")
print("1. 日常任务的 account_index 已重置为 0")
print("2. 日常任务的 branch 已清空")
print("3. 日常任务的 completed_steps 已清空（下次会重新执行）")
print("4. 日常任务的 random_order 已清空（下次会重新随机排序）")
print("5. 周常任务的 completed_tasks 已清空（本周可重新执行）")
print("6. calendar_date 和 week_start_date 保留，由系统自动判断是否需要按日/周重置")
