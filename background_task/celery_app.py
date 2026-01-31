from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "background_task",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "background_task.tasks.email_tasks",
        "background_task.tasks.subscription_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
)

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "deactivate-expired-subscriptions-nightly": {
        "task": "background_task.tasks.subscription_tasks.deactivate_expired_subscriptions",
        "schedule": crontab(hour=1, minute=0),  # ✅ 1:00 AM IST
    },
}

