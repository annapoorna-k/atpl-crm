from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import WorkingCalendar
from .services import utc

def tenant_calendar(db: Session, tenant_id):
    return db.scalar(select(WorkingCalendar).where(WorkingCalendar.tenant_id == tenant_id, WorkingCalendar.is_deleted.is_(False)))

def working_days(start: datetime | date, end: datetime | date, calendar=None) -> int:
    start_date=utc(start).date() if isinstance(start,datetime) else start; end_date=utc(end).date() if isinstance(end,datetime) else end
    if end_date <= start_date: return 0
    weekdays=set(calendar.working_weekdays) if calendar else {0,1,2,3,4}; holidays={date.fromisoformat(v) for v in (calendar.holidays if calendar else [])}
    return sum(1 for offset in range((end_date-start_date).days) if (day:=start_date+timedelta(days=offset+1)).weekday() in weekdays and day not in holidays)
