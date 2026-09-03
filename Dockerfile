# 注意：不使用 `# syntax=` 指令，避免 BuildKit 额外联网拉取 dockerfile 前端镜像
FROM python:3.13-slim

# ---------------------------------------------------------------------------
# 构建期环境变量：保证日志实时输出、pip 无缓存、减少镜像体积
# ---------------------------------------------------------------------------
# PyPI 源可在构建时切换：--build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

# ---------------------------------------------------------------------------
# 安装依赖（先复制 requirements.txt 以利用 Docker 层缓存）
# ---------------------------------------------------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# 复制应用代码
# ---------------------------------------------------------------------------
COPY app ./app
COPY run_tasks.py ./

# ---------------------------------------------------------------------------
# 显式创建专用非特权用户 celeuser，专供 Celery 进程使用（禁止 root 运行）
# ---------------------------------------------------------------------------
RUN groupadd --gid 1000 celeuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin celeuser \
    && chown -R celeuser:celeuser /app

USER celeuser

# ---------------------------------------------------------------------------
# 默认启动 Worker；beat / flower / run-tasks 由 docker-compose 显式指定命令
# ---------------------------------------------------------------------------
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=INFO"]
