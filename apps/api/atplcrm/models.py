from __future__ import annotations
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import JSON, BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "crm_tenant"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120), default="ATPLCRM")
    instance_type: Mapped[str] = mapped_column(String(20))


class User(Base):
    __tablename__ = "crm_user"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    first_name: Mapped[str] = mapped_column(String(150), default="")
    last_name: Mapped[str] = mapped_column(String(150), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    level: Mapped[str] = mapped_column(String(20), default="Standard")
    job_title: Mapped[str] = mapped_column(String(100), default="")
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_tenant.id", ondelete="RESTRICT"), nullable=True)
    tenant: Mapped[Tenant | None] = relationship()

    @property
    def display_name(self) -> str:
        return (f"{self.first_name} {self.last_name}").strip() or self.username


class RecordMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_tenant.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class Company(RecordMixin, Base):
    __tablename__ = "crm_company"
    name: Mapped[str] = mapped_column(String(180))
    domain: Mapped[str] = mapped_column(String(180), default="")
    company_type: Mapped[str] = mapped_column(String(40), default="Prospect")
    industry: Mapped[str] = mapped_column(String(100), default="")
    country: Mapped[str] = mapped_column(String(80))
    global_account_name: Mapped[str] = mapped_column(String(180), default="")
    primary_region: Mapped[str] = mapped_column(String(80), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    contacts: Mapped[list[Contact]] = relationship(back_populates="company")


class Contact(RecordMixin, Base):
    __tablename__ = "crm_contact"
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_company.id", ondelete="RESTRICT"))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), default="")
    job_title: Mapped[str] = mapped_column(String(100), default="")
    seniority: Mapped[str] = mapped_column(String(40), default="Unknown")
    phone: Mapped[str] = mapped_column(String(40), default="")
    mobile: Mapped[str] = mapped_column(String(40), default="")
    linkedin_url: Mapped[str] = mapped_column(String(200), default="")
    country: Mapped[str] = mapped_column(String(80))
    city: Mapped[str] = mapped_column(String(80), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    sourced_by_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    source_channel: Mapped[str] = mapped_column(String(80), default="Other")
    source_detail: Mapped[str] = mapped_column(String(180), default="")
    first_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    engagement_status: Mapped[str] = mapped_column(String(40), default="Not contacted")
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_basis: Mapped[str] = mapped_column(String(80), default="Business card or event")
    notes: Mapped[str] = mapped_column(Text, default="")
    company: Mapped[Company] = relationship(back_populates="contacts")
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    sourced_by: Mapped[User] = relationship(foreign_keys=[sourced_by_id])

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Pursuit(RecordMixin, Base):
    __tablename__ = "crm_pursuit"
    name: Mapped[str] = mapped_column(String(180))
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_company.id", ondelete="RESTRICT"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    sourced_by_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    holder_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    ball_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    next_action: Mapped[str] = mapped_column(String(250))
    action_type: Mapped[str] = mapped_column(String(40), default="Call")
    action_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    source_channel: Mapped[str] = mapped_column(String(80))
    source_detail: Mapped[str] = mapped_column(String(180), default="")
    blocker: Mapped[str] = mapped_column(String(40), default="None")
    blocker_owner_id: Mapped[int | None] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"), nullable=True)
    blocked_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_action: Mapped[str] = mapped_column(String(250), default="")
    last_client_interaction: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_meeting: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    presales_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proposal_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    company: Mapped[Company] = relationship()
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    sourced_by: Mapped[User] = relationship(foreign_keys=[sourced_by_id])
    holder: Mapped[User] = relationship(foreign_keys=[holder_id])
    blocker_owner: Mapped[User | None] = relationship(foreign_keys=[blocker_owner_id])
    lead: Mapped[Lead | None] = relationship(back_populates="pursuit", uselist=False)
    opportunity: Mapped[Opportunity | None] = relationship(back_populates="pursuit", uselist=False)
    team: Mapped[list[TeamRole]] = relationship(back_populates="pursuit")
    stakeholders: Mapped[list[PursuitContact]] = relationship(back_populates="pursuit")
    completed_actions: Mapped[list[PursuitAction]] = relationship(back_populates="pursuit")


class Lead(RecordMixin, Base):
    __tablename__ = "crm_lead"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="new")
    area_of_interest: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String(40), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    revisit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pursuit: Mapped[Pursuit] = relationship(back_populates="lead")
    converted_opportunity: Mapped[Opportunity | None] = relationship(back_populates="origin_lead", uselist=False)


class Opportunity(RecordMixin, Base):
    __tablename__ = "crm_opportunity"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), unique=True)
    origin_lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_lead.id", ondelete="RESTRICT"), unique=True)
    stage: Mapped[str] = mapped_column(String(20), default="discovery")
    opportunity_type: Mapped[str] = mapped_column(String(60), default="New logo")
    customer_need: Mapped[str] = mapped_column(Text)
    scope_summary: Mapped[str] = mapped_column(Text)
    primary_contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_contact.id", ondelete="RESTRICT"))
    service_line: Mapped[str] = mapped_column(String(80))
    engagement_type: Mapped[str] = mapped_column(String(60), default="Fixed price")
    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=1)
    value_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    expected_close_date: Mapped[date] = mapped_column(Date)
    probability: Mapped[int] = mapped_column(Integer, default=20)
    probability_stage_default: Mapped[int] = mapped_column(Integer, default=20)
    probability_note: Mapped[str] = mapped_column(Text, default="")
    gross_margin_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    restricted: Mapped[bool] = mapped_column(Boolean, default=False)
    restriction_reason: Mapped[str] = mapped_column(Text, default="")
    revisit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    loss_reason: Mapped[str] = mapped_column(String(80), default="")
    competitor_name: Mapped[str] = mapped_column(String(100), default="")
    competitor_status: Mapped[str] = mapped_column(String(60), default="None known")
    contract_number: Mapped[str] = mapped_column(String(100), default="")
    contract_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    project_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handoff_notes: Mapped[str] = mapped_column(Text, default="")
    approval_recorded: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_note: Mapped[str] = mapped_column(Text, default="")
    close_notes: Mapped[str] = mapped_column(Text, default="")
    final_evidence_artifact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_artifact.id", ondelete="RESTRICT"), nullable=True)
    pursuit: Mapped[Pursuit] = relationship(back_populates="opportunity")
    origin_lead: Mapped[Lead] = relationship(back_populates="converted_opportunity")
    primary_contact: Mapped[Contact] = relationship()
    values: Mapped[list[ValueHistory]] = relationship(back_populates="opportunity")
    partners: Mapped[list[PartnerInvolvement]] = relationship(back_populates="opportunity")


class TeamRole(RecordMixin, Base):
    __tablename__ = "crm_teamrole"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"))
    user_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(40))
    pursuit: Mapped[Pursuit] = relationship(back_populates="team")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class PursuitContact(RecordMixin, Base):
    __tablename__ = "crm_pursuitcontact"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"))
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_contact.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(40), default="Champion")
    pursuit: Mapped[Pursuit] = relationship(back_populates="stakeholders")
    contact: Mapped[Contact] = relationship()


class ExchangeRate(RecordMixin, Base):
    __tablename__ = "crm_exchangerate"
    currency: Mapped[str] = mapped_column(String(3))
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    source: Mapped[str] = mapped_column(String(100), default="Demo reference; not live market data")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class ExchangeRateHistory(RecordMixin, Base):
    __tablename__ = "crm_exchangeratehistory"
    currency: Mapped[str] = mapped_column(String(3), index=True)
    old_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    new_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    source: Mapped[str] = mapped_column(String(100))
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    change_type: Mapped[str] = mapped_column(String(30), default="Manual override")


class CommercialSetting(RecordMixin, Base):
    __tablename__ = "crm_commercialsetting"
    __table_args__ = (UniqueConstraint("tenant_id", name="crm_commercialsetting_tenant_uniq"),)
    partner_share_warning_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=40)
    fx_movement_notice_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=5)


class WorkspaceReference(RecordMixin, Base):
    __tablename__ = "crm_workspacereference"
    __table_args__ = (UniqueConstraint("tenant_id", "category", "code", name="crm_reference_tenant_category_code_uniq"),)
    category: Mapped[str] = mapped_column(String(40), index=True)
    code: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(120))
    numeric_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ImportJob(RecordMixin, Base):
    __tablename__ = "crm_importjob"
    filename: Mapped[str] = mapped_column(String(180))
    entity_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="Completed")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)


class SavedView(RecordMixin, Base):
    __tablename__ = "crm_savedview"
    __table_args__ = (
        UniqueConstraint("tenant_id", "owner_id", "entity_type", "name", name="crm_savedview_owner_entity_name_uniq"),
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(80))
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])


class ValueHistory(RecordMixin, Base):
    __tablename__ = "crm_valuehistory"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_opportunity.id", ondelete="RESTRICT"))
    value_type: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    note: Mapped[str] = mapped_column(Text, default="")
    opportunity: Mapped[Opportunity] = relationship(back_populates="values")


class Activity(RecordMixin, Base):
    __tablename__ = "crm_activity"
    pursuit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), nullable=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_contact.id", ondelete="RESTRICT"), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_company.id", ondelete="RESTRICT"))
    activity_type: Mapped[str] = mapped_column(String(40))
    is_client_facing: Mapped[bool] = mapped_column(Boolean, default=True)
    direction: Mapped[str] = mapped_column(String(20), default="Outbound")
    activity_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    outcome: Mapped[str] = mapped_column(String(40), default="Responded")
    subject: Mapped[str] = mapped_column(String(250))
    notes: Mapped[str] = mapped_column(Text, default="")
    override_reason: Mapped[str] = mapped_column(Text, default="")
    pursuit: Mapped[Pursuit | None] = relationship()
    contact: Mapped[Contact | None] = relationship()
    company: Mapped[Company] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys="Activity.created_by_id")


class PursuitAction(RecordMixin, Base):
    __tablename__ = "crm_pursuitaction"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), index=True)
    summary: Mapped[str] = mapped_column(String(250))
    action_type: Mapped[str] = mapped_column(String(40))
    due_date: Mapped[date] = mapped_column(Date)
    outcome: Mapped[str] = mapped_column(String(80))
    note: Mapped[str] = mapped_column(Text, default="")
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_by_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    pursuit: Mapped[Pursuit] = relationship(back_populates="completed_actions")
    completed_by: Mapped[User] = relationship(foreign_keys=[completed_by_id])


class PreSalesRequest(RecordMixin, Base):
    __tablename__ = "crm_presalesrequest"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_opportunity.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(180))
    request_type: Mapped[str] = mapped_column(String(60), default="Deck")
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(40), default="Requested")
    needed_by: Mapped[date] = mapped_column(Date)
    customer_meeting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_days: Mapped[Decimal] = mapped_column(Numeric(7, 1), default=0)
    actual_days: Mapped[Decimal | None] = mapped_column(Numeric(7, 1), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    blocked_reason: Mapped[str] = mapped_column(Text, default="")
    opportunity: Mapped[Opportunity] = relationship()
    assigned_to: Mapped[User] = relationship(foreign_keys=[assigned_to_id])


class PartnerInvolvement(RecordMixin, Base):
    __tablename__ = "crm_partnerinvolvement"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_opportunity.id", ondelete="RESTRICT"))
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_company.id", ondelete="RESTRICT"))
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_contact.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(60))
    introduced: Mapped[bool] = mapped_column(Boolean, default=False)
    fee_basis: Mapped[str] = mapped_column(String(60))
    share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    fixed_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    applies_to: Mapped[str] = mapped_column(String(80), default="This contract only")
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="Proposed")
    agreement_artifact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_artifact.id", ondelete="RESTRICT"), nullable=True)
    terms_notes: Mapped[str] = mapped_column(Text, default="")
    opportunity: Mapped[Opportunity] = relationship(back_populates="partners")
    company: Mapped[Company] = relationship()
    contact: Mapped[Contact] = relationship()
    agreement_artifact: Mapped[Artifact | None] = relationship()


class Artifact(RecordMixin, Base):
    __tablename__ = "crm_artifact"
    pursuit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(180))
    artifact_type: Mapped[str] = mapped_column(String(50), default="Proposal")
    kind: Mapped[str] = mapped_column(String(40), default="SharePoint / OneDrive link")
    storage_link: Mapped[str] = mapped_column(String(1000))
    version: Mapped[int] = mapped_column(Integer, default=1)
    internal_only: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"), nullable=True)
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(RecordMixin, Base):
    __tablename__ = "crm_auditevent"
    pursuit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text, default="")
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[User | None] = relationship(foreign_keys="AuditEvent.created_by_id")


class Notification(RecordMixin, Base):
    __tablename__ = "crm_notification"
    recipient_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="RESTRICT"))
    pursuit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crm_pursuit.id", ondelete="RESTRICT"), nullable=True)
    message: Mapped[str] = mapped_column(String(250))
    key: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40), default="general", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(RecordMixin, Base):
    __tablename__ = "crm_notificationpreference"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="crm_notificationpreference_tenant_user_uniq"),)
    user_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="CASCADE"), index=True)
    due_actions: Mapped[bool] = mapped_column(Boolean, default=True)
    stalled_pursuits: Mapped[bool] = mapped_column(Boolean, default=True)
    blockers: Mapped[bool] = mapped_column(Boolean, default=True)
    inactivity: Mapped[bool] = mapped_column(Boolean, default=True)
    proposal_followup: Mapped[bool] = mapped_column(Boolean, default=True)
    validation: Mapped[bool] = mapped_column(Boolean, default=True)
    presales: Mapped[bool] = mapped_column(Boolean, default=True)
    close_dates: Mapped[bool] = mapped_column(Boolean, default=True)
    revisits: Mapped[bool] = mapped_column(Boolean, default=True)
    system_failures: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    inactivity_days: Mapped[int] = mapped_column(Integer, default=21)
    proposal_followup_days: Mapped[int] = mapped_column(Integer, default=7)
    close_notice_days: Mapped[int] = mapped_column(Integer, default=7)
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class AutomationRun(RecordMixin, Base):
    __tablename__ = "crm_automationrun"
    task_name: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="")


class AppSession(Base):
    __tablename__ = "app_session"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("crm_user.id", ondelete="CASCADE"))
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user: Mapped[User] = relationship()
