from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "background_task",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "background_task.tasks.email_tasks",  # ✅ Required for Celery to load tasks
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
)

celery_app.conf.beat_schedule = {
    "cleanup-tasks": {
        "task": "background_task.tasks.email_tasks.clean_logs_task",
        "schedule": crontab(hour=0, minute=0),
    },
}
