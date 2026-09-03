"""任务客户端示例。

提供命令行入口，可运行全部示例任务、查询定时任务最近结果、
查看 Worker 状态。适用于本地调试与容器内验证：

    python run_tasks.py            # 执行全部操作（默认）
    python run_tasks.py run        # 仅运行普通任务示例
    python run_tasks.py beat       # 仅查看定时任务最近结果
    python run_tasks.py status     # 仅查看 Worker 状态

Example:
    # 容器内执行
    docker compose run --rm run-tasks python run_tasks.py beat
"""

import argparse
import json
import sys

import redis

from app import config
from app.celery_app import app
from app.tasks.math_tasks import add


def run_examples() -> None:
    """运行全部普通任务示例并同步等待结果。"""
    result = add.delay(3, 5)
    print(f"[普通任务] 已提交 tasks.add(3, 5)，task_id={result.id}")
    value = result.get(timeout=30)
    print(f"[普通任务] tasks.add(3, 5) = {value}")

    result2 = add.delay(10.5, 20.25)
    print(f"[普通任务] 已提交 tasks.add(10.5, 20.25)，task_id={result2.id}")
    print(f"[普通任务] tasks.add(10.5, 20.25) = {result2.get(timeout=30)}")


def show_beat_results(limit: int = 10) -> None:
    """查询定时任务最近执行结果。

    定时任务的结果由 Worker 端写入 Redis（键见 ``config.BEAT_RESULTS_KEY``），
    此处读取最近 ``limit`` 条并打印。

    Args:
        limit (int): 最多展示的记录条数，默认 10。
    """
    client = redis.Redis.from_url(config.BROKER_URL, decode_responses=True)
    entries = client.lrange(config.BEAT_RESULTS_KEY, 0, limit - 1)
    if not entries:
        print(
            "[定时任务] 暂无结果。请确认 Beat 服务已启动："
            "docker compose up -d beat"
        )
        return
    print(f"[定时任务] 最近 {min(limit, len(entries))} 条结果：")
    for entry in entries:
        data = json.loads(entry)
        print(
            f"  - 任务: {data.get('task')} | 时间: {data.get('executed_at')} "
            f"| message: {data.get('message')} | task_id: {data.get('task_id')}"
        )


def show_status() -> None:
    """查看当前在线 Worker 及其注册的任务列表。"""
    inspector = app.control.inspect(timeout=5)
    ping = inspector.ping() or {}
    if not ping:
        print("[状态] 没有在线的 Worker。请检查：docker compose ps")
        return
    print(f"[状态] 在线 Worker 数量: {len(ping)}")
    for worker_name, info in ping.items():
        print(f"  - {worker_name}: {info}")
    registered = inspector.registered() or {}
    for worker_name, tasks in registered.items():
        print(f"[状态] {worker_name} 已注册 {len(tasks)} 个任务：")
        for task_name in tasks:
            print(f"    * {task_name}")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    Returns:
        argparse.ArgumentParser: 配置完成的参数解析器。
    """
    parser = argparse.ArgumentParser(
        prog="run_tasks.py",
        description="alt_celery2 任务客户端：运行示例任务 / 查询定时任务结果 / 查看 Worker 状态",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="运行全部普通任务示例")
    subparsers.add_parser("beat", help="查看定时任务最近结果")
    subparsers.add_parser("status", help="查看在线 Worker 状态")
    subparsers.add_parser("all", help="执行以上全部操作（默认行为）")
    return parser


def main() -> int:
    """命令行主入口。

    Returns:
        int: 进程退出码，0 表示成功。
    """
    parser = build_parser()
    args = parser.parse_args()
    command = args.command or "all"

    if command in ("all", "run"):
        run_examples()
    if command in ("all", "beat"):
        show_beat_results()
    if command in ("all", "status"):
        show_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
