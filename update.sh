#!/usr/bin/env bash
# =========================================================================
# alt_celery2 更新脚本
# 用途：拉取 GitHub 最新代码 -> 重新构建镜像 -> 重新拉起 Docker 服务
# 适用环境：Linux 服务器（已安装 git 与 docker compose 插件）
# =========================================================================
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BRANCH="${1:-main}"

echo "==> [1/4] 拉取最新代码（分支: ${BRANCH}）"
if git diff --quiet && git diff --cached --quiet; then
  git pull --ff-only origin "${BRANCH}"
else
  echo "!! 工作区存在未提交的修改，git pull 可能冲突，已中止更新。" >&2
  echo "   请先提交/暂存（git stash）本地修改后重试。" >&2
  exit 1
fi

echo "==> [2/4] 重新构建镜像"
docker compose build --pull

echo "==> [3/4] 重新拉起服务"
docker compose up -d --remove-orphans

echo "==> [4/4] 清理悬空镜像"
docker image prune -f

echo "==> 更新完成。当前服务状态："
docker compose ps
