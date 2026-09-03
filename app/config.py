"""应用配置模块。

所有配置项均从环境变量读取，未设置时回退到安全的默认值，
从而满足「一份镜像、多环境部署」的十二要素应用原则。
"""

import os

# ---------------------------------------------------------------------------
# Redis 连接（redis-stack 服务器，带密码的 URL 形如：
#   redis://:password@redis-stack-host:6379/0
# ---------------------------------------------------------------------------

# 消息中间件（Broker）地址
BROKER_URL: str = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379/0"
)

# 结果后端（Result Backend）地址
RESULT_BACKEND: str = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
)

# ---------------------------------------------------------------------------
# Worker / Beat 行为
# ---------------------------------------------------------------------------

# Worker 并发进程数
WORKER_CONCURRENCY: int = int(os.environ.get("CELERY_WORKER_CONCURRENCY", "2"))

# 日志级别（DEBUG / INFO / WARNING / ERROR）
LOG_LEVEL: str = os.environ.get("CELERY_LOG_LEVEL", "INFO").upper()

# 定时任务时区
TIMEZONE: str = os.environ.get("CELERY_TIMEZONE", "Asia/Shanghai")

# ---------------------------------------------------------------------------
# 定时任务结果的持久化
# ---------------------------------------------------------------------------

# Beat 触发任务的执行结果在 Redis 中的存储键（List 结构，最新结果在前）
BEAT_RESULTS_KEY: str = os.environ.get(
    "CELERY_BEAT_RESULTS_KEY", "alt_celery2:beat:results"
)

# Beat 结果最多保留条数，超出后自动裁剪
BEAT_RESULTS_MAX: int = int(os.environ.get("CELERY_BEAT_RESULTS_MAX", "50"))

# ---------------------------------------------------------------------------
# Flower 监控
# ---------------------------------------------------------------------------

# Flower 监听端口
FLOWER_PORT: int = int(os.environ.get("FLOWER_PORT", "5555"))

# Flower Web 界面基础认证（格式：user:password）
FLOWER_BASIC_AUTH: str = os.environ.get("FLOWER_BASIC_AUTH", "admin:admin")
