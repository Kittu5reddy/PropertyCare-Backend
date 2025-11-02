from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "background_task",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
)

celery_app.conf.beat_schedule = {
    "update-user-forms-every-midnight": {
        "task": "cron_jobs.update_user_pd_form_if_any_error_occurs",
        "schedule": crontab(hour=0, minute=0),  # 12:00 AM IST
    },
}
