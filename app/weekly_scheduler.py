# -*- coding: utf-8 -*-
"""
固定时间周常调度：守护线程只负责到点往 td_info[row] 写队列；
实际周常在 Task 工作线程内协作式执行（见 Task._周常优先检查并执行）。
"""
import datetime
import threading
import time

from dxGame.dx_model import gl_info, td_info

SECTION = "周常调度"
# Scheduler 与 Task 工作线程同时改队列时用
td_weekly_lock = threading.Lock()


def _normalize_rules(raw_list):
    if not raw_list or not isinstance(raw_list, list):
        return []
    out = []
    for i, r in enumerate(raw_list):
        if not isinstance(r, dict):
            continue
        try:
            wd = int(r.get("weekday", -1))
            h = int(r.get("hour", -1))
            m = int(r.get("minute", -1))
            task = str(r.get("task", "") or "").strip()
        except (TypeError, ValueError):
            continue
        if wd < 0 or wd > 6 or h < 0 or h > 23 or m < 0 or m > 59 or not task:
            continue
        rid = r.get("rid", i)
        try:
            rid = int(rid)
        except (TypeError, ValueError):
            rid = i
        out.append({"weekday": wd, "hour": h, "minute": m, "task": task, "rid": rid})
    return out


def _rule_matches_minute(rule, now: datetime.datetime):
    return (
        now.weekday() == rule["weekday"]
        and now.hour == rule["hour"]
        and now.minute == rule["minute"]
    )


def _ensure_queue(row):
    q = getattr(td_info[row], "weekly_task_queue", None)
    if not isinstance(q, list):
        q = []
        td_info[row].weekly_task_queue = q
    return q


def _append_weekly_task(row, task_name, rid, date_key, fired: set):
    key = (row, rid, date_key)
    with td_weekly_lock:
        if key in fired:
            return False
        q = _ensure_queue(row)
        q.append(task_name)
        td_info[row].weekly_pending = True
        fired.add(key)
    return True


def snapshot_weekly_batch(row):
    """
    在 Task 线程调用：已确认可执行周常时，一次性取出队列中的方法名并清除挂起。
    若当前无挂起或队列为空则返回 []。
    """
    with td_weekly_lock:
        if not getattr(td_info[row], "weekly_pending", False):
            return []
        q = _ensure_queue(row)
        if not q:
            td_info[row].weekly_pending = False
            return []
        batch = list(q)
        q.clear()
        td_info[row].weekly_pending = False
    return batch


def _tick(controller, fired: set):
    cfg = getattr(getattr(controller, "配置", None), "data", None)
    if not isinstance(cfg, dict):
        return
    sec = cfg.get(SECTION)
    if not isinstance(sec, dict):
        return
    if not sec.get("启用", False):
        return

    rules = _normalize_rules(sec.get("规则列表", []))
    if not rules:
        return

    tc = getattr(controller, "线程控制器", None)
    if tc is None:
        return
    thread_dict = getattr(tc, "_thread_dict", None)
    if not isinstance(thread_dict, dict):
        return

    now = datetime.datetime.now()
    date_key = now.date().isoformat()
    active_rows = [k for k, th in thread_dict.items() if th is not None and th.is_alive()]
    if not active_rows:
        return

    for row in active_rows:
        for rule in rules:
            if not _rule_matches_minute(rule, now):
                continue
            rid = rule["rid"]
            task_name = rule["task"]
            _append_weekly_task(row, task_name, rid, date_key, fired)

    # 精简 fired，避免集合无限增长（只保留今日键）
    stale = [k for k in fired if len(k) >= 3 and k[2] != date_key]
    for k in stale:
        fired.discard(k)


def start_weekly_scheduler(controller):
    """
    启动守护线程；在 Controller.__init__ 末尾调用一次即可。
    """
    stop_flag = threading.Event()
    controller._weekly_scheduler_stop = stop_flag
    fired = set()

    def loop():
        while not stop_flag.is_set():
            ctl = getattr(gl_info, "controller", None)
            poll = 30
            if ctl is not None:
                try:
                    _tick(ctl, fired)
                except Exception as e:
                    print(f"[周常调度] 异常: {e}")
                try:
                    cfg = getattr(getattr(ctl, "配置", None), "data", None)
                    if isinstance(cfg, dict):
                        sec = cfg.get(SECTION)
                        if isinstance(sec, dict):
                            poll = int(sec.get("轮询秒数", 30))
                    poll = max(5, min(poll, 600))
                except Exception:
                    poll = 30
            stop_flag.wait(timeout=poll)

    t = threading.Thread(target=loop, daemon=True, name="WeeklyScheduler")
    t.start()
    controller._weekly_scheduler_thread = t


def stop_weekly_scheduler(controller):
    ev = getattr(controller, "_weekly_scheduler_stop", None)
    if ev is not None:
        ev.set()
