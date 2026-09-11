from datetime import date
from celery import Celery
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .database import engine
from .models import Notification, Pursuit, Tenant
from .services import flags, stamp
from .settings import get_settings

settings = get_settings()
celery_app = Celery("atplcrm", broker=settings.redis_url)
celery_app.conf.beat_schedule = {"attention-notifications": {"task": "atplcrm.refresh_notifications", "schedule": 300.0}}
celery_app.conf.timezone = "UTC"


@celery_app.task(name="atplcrm.refresh_notifications")
def refresh_notifications() -> int:
    with Session(engine) as db:
        tenant_id = db.scalar(select(Tenant.id).where(Tenant.key == settings.tenant_key))
        if tenant_id is None:
            return 0
        pursuits = db.scalars(select(Pursuit).where(Pursuit.tenant_id == tenant_id, Pursuit.is_deleted.is_(False)).options(selectinload(Pursuit.lead), selectinload(Pursuit.opportunity))).all()
        created = 0
        for pursuit in pursuits:
            notices = [(pursuit.holder_id, flag, f"{flag}:{pursuit.action_date}:{pursuit.version}") for flag in flags(pursuit)]
            revisit = pursuit.opportunity.revisit_date if pursuit.opportunity and pursuit.opportunity.stage == "hold" else pursuit.lead.revisit_date if pursuit.lead and pursuit.lead.outcome == "Nurture" else None
            if revisit and revisit <= date.today(): notices.append((pursuit.owner_id, "Revisit date reached", f"revisit:{revisit}"))
            for recipient, label, key in notices:
                unique = f"{pursuit.id}:{key}"
                if not db.scalar(select(Notification.id).where(Notification.tenant_id == pursuit.tenant_id, Notification.recipient_id == recipient, Notification.key == unique)):
                    db.add(Notification(**stamp(pursuit.holder), recipient_id=recipient, pursuit_id=pursuit.id, key=unique, message=f"{label}: {pursuit.name}"))
                    created += 1
        db.commit()
        return created
