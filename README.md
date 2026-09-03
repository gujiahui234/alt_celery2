# alt_celery2

基于 **Docker** 部署的生产级 **Celery** 任务队列应用，使用已有的带密码保护的 **Redis-Stack** 服务器作为消息中间件与结果后端，内置 **Flower** 监控面板。

## 功能简介

- **普通任务**：由生产者（客户端）主动提交并异步执行，示例见 `app/tasks/math_tasks.py`（加法任务 `tasks.add`）。
- **定时任务**：由 Celery Beat 按调度表周期触发，示例见 `app/tasks/beat_tasks.py`：
  - `tasks.tick`：每 30 秒一次的心跳任务；
  - `tasks.daily_report`：每天 08:00（Asia/Shanghai）触发的报告任务。
- **易于扩展**：所有任务主体 py 文件统一放在 `app/tasks/` 子文件夹内，应用启动时自动扫描注册，**新增任务无需修改任何配置**。
- **任务客户端**：独立脚本 `run_tasks.py`，可调用全部示例任务、查询定时任务最近结果、查看 Worker 状态。
- **Flower 监控**：Web 界面实时查看任务执行情况（默认端口 `5555`，支持基础认证）。
- **生产级安全**：Dockerfile 内显式创建专用非特权用户 `celeuser`，容器内进程不以 root 运行。

## 项目结构

```text
alt_celery2/
├── app/
│   ├── __init__.py
│   ├── config.py            # 配置模块（从环境变量读取）
│   ├── celery_app.py        # Celery 实例、可靠性配置与 Beat 调度表
│   └── tasks/               # ★ 所有任务主体 py 文件统一放在这里
│       ├── math_tasks.py    #   普通任务示例：tasks.add
│       └── beat_tasks.py    #   定时任务示例：tasks.tick / tasks.daily_report
├── run_tasks.py             # 独立任务客户端（运行任务 / 查询定时任务结果 / 查看状态）
├── Dockerfile               # Python 3.13 镜像，显式创建非特权用户 celeuser
├── docker-compose.yml       # worker / beat / flower / run-tasks 服务编排
├── pyproject.toml           # 现代依赖声明（PEP 621）
├── requirements.txt         # 传统依赖清单
├── .env.example             # 环境变量模板
└── update.sh                # 一键更新脚本（git pull + 重新拉起 docker）
```

## 环境要求

- Python >= 3.13（镜像基于 `python:3.13-slim`）
- Docker（含 Docker Compose v2 插件）
- 一台已运行的、带密码保护的 Redis-Stack 服务器（外部提供，本应用不负责部署）

## 部署过程

### 1. 配置环境变量

```bash
cp .env.example .env
vi .env   # 修改 CELERY_BROKER_URL / CELERY_RESULT_BACKEND 为你的 Redis-Stack 实际地址与密码
```

带密码的 Redis URL 格式：

```text
redis://:<password>@<redis-stack-host>:6379/0
```

> 注意：Broker 与 Result Backend 建议使用不同的 db 编号（如 `/0` 与 `/1`）。  
> 请务必修改 `FLOWER_BASIC_AUTH` 默认值。`.env` 已被 git 与 docker 忽略，不会进入镜像或仓库。

### 2. 构建并启动服务

```bash
docker compose up -d --build
docker compose ps        # 查看服务状态
docker compose logs -f worker   # 查看 Worker 日志
```

启动的常驻服务：

| 服务 | 说明 | 备注 |
|------|------|------|
| `worker` | 执行普通任务与定时任务 | 可水平扩容：`docker compose up -d --scale worker=3` |
| `beat` | 定时任务调度器 | **全集群只允许一个实例** |
| `flower` | 监控面板 | 默认 `http://<host>:5555` |

### 3. 验证部署

```bash
# 方式一：在容器内运行任务客户端
docker compose run --rm run-tasks python run_tasks.py

# 方式二：仅查看定时任务最近结果（需等待 Beat 触发一次心跳）
docker compose run --rm run-tasks python run_tasks.py beat
```

浏览器打开 `http://<host>:5555`（输入 `.env` 中的 `FLOWER_BASIC_AUTH` 账号密码）即可监控任务。

## 使用说明

### run_tasks.py 使用指南

`run_tasks.py` 是独立的任务客户端脚本，用于验证部署与日常调试，无需编写代码即可完成三类操作：**运行示例任务**、**查询定时任务结果**、**查看 Worker 状态**。

#### 前置条件

- `worker` / `beat` 服务已启动（`docker compose ps` 确认）；
- 客户端所在环境能访问 `.env` 中配置的 Redis-Stack。

#### 运行方式

**方式一：容器内运行（推荐，无需本地 Python 环境）**

```bash
# 在部署服务器上直接执行（run-tasks 服务已在 docker-compose.yml 的 tools profile 中定义）
docker compose run --rm run-tasks python run_tasks.py

# 只运行某个子命令
docker compose run --rm run-tasks python run_tasks.py run
docker compose run --rm run-tasks python run_tasks.py beat
docker compose run --rm run-tasks python run_tasks.py status
```

**方式二：本地直接运行（开发调试）**

```bash
# 前提：Python >= 3.13，且本机能连通 Redis-Stack
pip install -r requirements.txt          # 或 pip install -e .
python run_tasks.py                      # 自动读取项目根目录 .env 中的连接配置
```

> 本地运行会自动加载根目录 `.env`（未设置的环境变量以它为准；已手动 `export` 的环境变量优先级更高）。  
> 注意：若当前终端残留过错误的 `CELERY_*` 环境变量，请先 `unset`（Linux）或关闭窗口重开（Windows）再运行。

#### 子命令一览

| 命令 | 作用 | 说明 |
|------|------|------|
| *(默认 / `all`)* | 依次执行以下全部操作 | `python run_tasks.py` 不带参数 |
| `run` | 运行普通任务示例 | 提交两组 `tasks.add` 异步计算并阻塞取回结果，验证 提交→队列→执行→取回 完整链路 |
| `beat` | 查询定时任务最近结果 | 从 Redis 读取 `alt_celery2:beat:results` 列表，展示最近 10 条心跳/报告记录 |
| `status` | 查看 Worker 状态 | 通过 Celery inspect 显示在线 Worker（pong 响应）及其注册的全部任务名 |
| `--help` | 显示帮助 | 查看支持的子命令 |

#### 输出示例

```text
$ docker compose run --rm run-tasks python run_tasks.py
[普通任务] 已提交 tasks.add(3, 5)，task_id=93dab9ea-83d4-4e43-852a-11ba03d03bb6
[普通任务] tasks.add(3, 5) = 8
[普通任务] 已提交 tasks.add(10.5, 20.25)，task_id=51baa6ad-a4a1-4f3b-a261-221c7b0a0e25
[普通任务] tasks.add(10.5, 20.25) = 30.75
[定时任务] 最近 2 条结果：
  - 任务: tasks.tick | 时间: 2026-09-03T12:03:36.114628+00:00 | message: Heartbeat OK | task_id: 2fdf8e4d-...
[状态] 在线 Worker 数量: 1
  - celery@6f3c58531b7d: {'ok': 'pong'}
[状态] celery@6f3c58531b7d 已注册 3 个任务：
    * tasks.add
    * tasks.daily_report
    * tasks.tick
```

#### 常见问题

| 现象 | 原因与处理 |
|------|-----------|
| `[定时任务] 暂无结果` | Beat 尚未触发（心跳间隔 30 秒）。确认 `beat` 容器在运行：`docker compose ps`，稍等片刻重试 |
| `[状态] 没有在线的 Worker` | `worker` 容器未启动或正在重启，查看日志：`docker compose logs worker` |
| 提交后长时间无结果 | Redis 连接不通（检查 `.env` 与网络可达性），或 Worker 未运行 |
| 容器内运行报连接错误 | `docker compose run` 会继承 compose 的环境变量，无需手动设置；检查 `.env` 是否配置正确 |

### 在自己的代码中调用任务（生产者示例）

```python
from app.tasks.math_tasks import add

result = add.delay(1, 2)     # 异步提交
print(result.id)             # 任务 ID
print(result.get(timeout=30))  # 阻塞等待结果 -> 3
```

### 添加新任务（无需改任何配置）

1. 在 `app/tasks/` 下新建 py 文件，例如 `app/tasks/mail_tasks.py`：

```python
"""邮件任务模块。"""
from app.celery_app import app


@app.task(name="tasks.send_mail")
def send_mail(to: str, subject: str) -> str:
    """发送邮件。

    Args:
        to (str): 收件人地址。
        subject (str): 邮件主题。

    Returns:
        str: 发送结果描述。
    """
    return f"邮件已发送至 {to}: {subject}"
```

2. 如需定时执行，在 `app/celery_app.py` 的 `beat_schedule` 中追加一项：

```python
"send-mail-every-hour": {
    "task": "tasks.send_mail",
    "schedule": crontab(minute=0),  # 每小时整点
},
```

3. 重新部署：`docker compose up -d --build`。

## 一键更新（update.sh）

在部署服务器上执行（Linux + Docker Compose v2）：

```bash
chmod +x update.sh   # 仅首次需要
./update.sh          # 默认更新 main 分支
./update.sh master   # 或指定其他分支
```

脚本流程：检查工作区干净 → `git pull --ff-only` 拉取最新代码 → 重新构建镜像 → 重新拉起服务 → 清理悬空镜像。

## 环境变量一览

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `CELERY_BROKER_URL` | ✅ | `redis://localhost:6379/0` | Redis-Stack Broker 地址（含密码） |
| `CELERY_RESULT_BACKEND` | ✅ | `redis://localhost:6379/1` | Redis-Stack 结果后端地址（含密码） |
| `CELERY_WORKER_CONCURRENCY` | ❌ | `2` | Worker 并发进程数 |
| `CELERY_LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `CELERY_TIMEZONE` | ❌ | `Asia/Shanghai` | 定时任务时区 |
| `FLOWER_PORT` | ❌ | `5555` | Flower 对外端口 |
| `FLOWER_BASIC_AUTH` | ❌ | `admin:admin` | Flower 登录凭据（`user:password`） |

## 可靠性说明

- `task_acks_late=True` + `worker_prefetch_multiplier=1`：任务执行完成后才确认，Worker 崩溃时任务会重新投递（要求任务尽量幂等）。
- `worker_max_tasks_per_child=1000`：子进程定期重启，防止内存泄漏。
- `task_soft_time_limit=540 / task_time_limit=600`：任务软/硬超时保护。
- Beat 结果持久化：定时任务结果写入 Redis List（键 `alt_celery2:beat:results`，默认保留最近 50 条），供 `run_tasks.py beat` 查询。
