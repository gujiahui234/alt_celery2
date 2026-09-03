"""Celery 应用工厂与全局配置。

任务模块统一位于 ``app/tasks`` 目录。应用实例化时会自动扫描该目录
并注册其中全部模块，因此**新增任务时无需修改本文件**：

1. 在 ``app/tasks`` 下新建 py 文件；
2. 导入 ``from app.celery_app import app`` 并使用 ``@app.task`` 定义任务。

Example:
    # app/tasks/demo_tasks.py
    from app.celery_app import app

    @app.task(name="tasks.demo")
    def demo() -> str:
        return "ok"
"""

from pathlib import Path

from celery import Celery
from celery.schedules import crontab

from app import config


def discover_task_modules() -> list[str]:
    """自动发现任务模块。

    扫描 ``app/tasks`` 目录下除 ``__init__.py`` 以外的全部 Python 模块，
    返回可用于 Celery ``include`` 参数的模块名列表。

    Returns:
        list[str]: 任务模块名列表，例如
            ``["app.tasks.beat_tasks", "app.tasks.math_tasks"]``。
    """
    tasks_dir = Path(__file__).resolve().parent / "tasks"
    return sorted(
        f"app.tasks.{path.stem}"
        for path in tasks_dir.glob("*.py")
        if path.stem != "__init__"
    )


app = Celery("alt_celery2", include=discover_task_modules())

app.conf.update(
    # --- Broker / Backend ---
    broker_url=config.BROKER_URL,
    result_backend=config.RESULT_BACKEND,
    # --- 序列化（生产环境统一使用 JSON） ---
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,  # 任务结果保留 24 小时
    # --- 时区 ---
    timezone=config.TIMEZONE,
    enable_utc=True,
    # --- 可靠性配置 ---
    task_track_started=True,  # 任务进入 STARTED 状态，便于监控
    task_acks_late=True,  # 任务执行完成后才确认，避免 Worker 崩溃丢任务
    worker_prefetch_multiplier=1,  # 配合 acks_late 实现公平分发
    worker_max_tasks_per_child=1000,  # 子进程处理 1000 个任务后重启，防内存泄漏
    task_time_limit=600,  # 硬超时 10 分钟
    task_soft_time_limit=540,  # 软超时 9 分钟（留给任务优雅收尾）
    # --- 定时任务（Beat）调度表 ---
    beat_schedule={
        "tick-every-30-seconds": {
            # 每 30 秒触发一次心跳任务
            "task": "tasks.tick",
            "schedule": 30.0,
        },
        "daily-report": {
            # 每天北京时间 08:00 触发一次报告任务
            "task": "tasks.daily_report",
            "schedule": crontab(hour=8, minute=0),
        },
    },
)
