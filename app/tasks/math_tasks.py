"""普通任务模块（示例）。

演示如何编写一个由生产者（客户端）直接触发的普通 Celery 任务。
"""

from app.celery_app import app


@app.task(name="tasks.add")
def add(x: float, y: float) -> float:
    """计算两个数字之和。

    Args:
        x (float): 第一个加数。
        y (float): 第二个加数。

    Returns:
        float: ``x + y`` 的计算结果。
    """
    return x + y
