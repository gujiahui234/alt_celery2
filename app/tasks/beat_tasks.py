"""定时任务模块（示例）。

由 Celery Beat 按调度表周期触发（见 ``app/celery_app.py`` 中的
``beat_schedule`` 配置）。执行结果会同步写入 Redis 的一个 List，
供 ``run_tasks.py`` 等外部客户端查询最近执行情况。
"""

import json
from datetime import datetime, timezone

import redis

from app import config
from app.celery_app import app


def _redis_client() -> redis.Redis:
    """创建与 Broker 同源的 Redis 客户端。

    Returns:
        redis.Redis: 已配置 decode_responses 的 Redis 客户端实例。
    """
    return redis.Redis.from_url(config.BROKER_URL, decode_responses=True)


def _persist_beat_result(payload: dict) -> None:
    """将定时任务结果写入 Redis，并裁剪列表长度。

    Args:
        payload (dict): 待持久化的任务结果字典。
    """
    client = _redis_client()
    client.lpush(config.BEAT_RESULTS_KEY, json.dumps(payload, ensure_ascii=False))
    client.ltrim(config.BEAT_RESULTS_KEY, 0, config.BEAT_RESULTS_MAX - 1)


@app.task(bind=True, name="tasks.tick")
def tick(self) -> dict:
    """心跳任务：每 30 秒由 Beat 触发一次。

    Args:
        self (Task): Celery 注入的任务实例（bind=True），用于读取任务 ID。

    Returns:
        dict: 包含任务 ID、任务名、执行时间与提示信息的字典。
    """
    payload = {
        "task_id": self.request.id,
        "task": "tasks.tick",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "message": "Heartbeat OK",
    }
    _persist_beat_result(payload)
    return payload


@app.task(bind=True, name="tasks.daily_report")
def daily_report(self) -> dict:
    """每日报告任务：每天 08:00（本地时区）由 Beat 触发。

    Args:
        self (Task): Celery 注入的任务实例（bind=True），用于读取任务 ID。

    Returns:
        dict: 包含统计信息的报告字典。
    """
    total = _redis_client().llen(config.BEAT_RESULTS_KEY)
    payload = {
        "task_id": self.request.id,
        "task": "tasks.daily_report",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "message": f"Beat 已累计记录 {total} 条定时任务结果",
    }
    _persist_beat_result(payload)
    return payload
