"""alt_celery2 应用包。

基于 Docker 部署的生产级 Celery 应用，任务模块统一放在
``app/tasks`` 子目录中，由 ``app.celery_app`` 自动发现并注册。
"""
