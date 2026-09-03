"""任务模块包。

该目录下的所有 ``*.py`` 文件（除 ``__init__.py``）都会被
``app.celery_app.discover_task_modules`` 自动扫描并注册为任务模块。
新增任务只需在此目录新建文件即可。
"""
