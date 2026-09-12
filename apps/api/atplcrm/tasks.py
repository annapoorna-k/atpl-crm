from datetime import datetime, timezone

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import engine
from .models import Tenant, User
from .notifications import emit, record_run, refresh_for_tenant, stable_key, weekly_summary_for_tenant
from .settings import get_settings

settings = get_settings()
celery_app = Celery("atplcrm", broker=settings.redis_url)
celery_app.conf.beat_schedule = {
    "attention-notifications": {"task": "atplcrm.refresh_notifications", "schedule": 900.0},
    "weekly-pipeline-summary": {"task": "atplcrm.weekly_pipeline_summary", "schedule": crontab(hour=7, minute=0, day_of_week=1)},
}
celery_app.conf.timezone = "UTC"


def tenant_and_system_user(db: Session):
    tenant = db.scalar(select(Tenant).where(Tenant.key == settings.tenant_key))
    if not tenant:
        return None, None
    user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True)).order_by(User.is_staff.desc(), User.id))
    return tenant, user


def record_failure(task_name: str, started: datetime, error: Exception) -> None:
    try:
        with Session(engine) as db:
            tenant, system_user = tenant_and_system_user(db)
            if not tenant or not system_user:
                return
            record_run(db, tenant.id, system_user, task_name, started, "Failed", detail=str(error))
            admins = db.scalars(select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True), User.level == "Administrator")).all()
            for admin in admins:
                emit(db, system_user, admin, "system_failures", f"Automation failed: {task_name}", stable_key("system_failures", task_name, started.isoformat()), severity="high")
            db.commit()
    except Exception:
        pass


@celery_app.task(name="atplcrm.refresh_notifications")
def refresh_notifications() -> int:
    started = datetime.now(timezone.utc)
    try:
        with Session(engine) as db:
            tenant, system_user = tenant_and_system_user(db)
            if not tenant or not system_user:
                return 0
            created = refresh_for_tenant(db, tenant.id)
            record_run(db, tenant.id, system_user, "attention-notifications", started, "Succeeded", created)
            db.commit()
            return created
    except Exception as error:
        record_failure("attention-notifications", started, error)
        raise


@celery_app.task(name="atplcrm.weekly_pipeline_summary")
def weekly_pipeline_summary() -> int:
    started = datetime.now(timezone.utc)
    try:
        with Session(engine) as db:
            tenant, system_user = tenant_and_system_user(db)
            if not tenant or not system_user:
                return 0
            created = weekly_summary_for_tenant(db, tenant.id)
            record_run(db, tenant.id, system_user, "weekly-pipeline-summary", started, "Succeeded", created)
            db.commit()
            return created
    except Exception as error:
        record_failure("weekly-pipeline-summary", started, error)
        raise
