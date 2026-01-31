from celery import shared_task
from datetime import datetime
from sqlalchemy import update
from app.core.services.sync_db import SessionLocal
from app.core.models.subscriptions import Subscriptions


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def deactivate_expired_subscriptions(self):
    """
    Runs every night at 12:00 AM IST
    Deactivates subscriptions whose sub_end_date < today
    """
    db = SessionLocal()

    try:
        today = datetime.today().date()

        stmt = (
            update(Subscriptions)
            .where(
                Subscriptions.is_active == True,
                Subscriptions.sub_end_date < today
            )
            .values(is_active=False)
        )

        result = db.execute(stmt)
        db.commit()

        print(
            f"[Celery] Deactivated {result.rowcount} expired subscriptions on {today}"
        )

    except Exception as e:
        db.rollback()
        raise

    finally:
        db.close()
