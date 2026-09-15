from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginInput(Input):
    username: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class CompanyInput(Input):
    name: str = Field(min_length=1, max_length=180)
    domain: str = Field("", max_length=180)
    company_type: Literal["Client", "Prospect", "Referral partner", "Reseller", "Local partner", "Prime contractor", "Subcontractor"] = "Prospect"
    industry: str = Field("", max_length=100)
    country: str = Field(min_length=1, max_length=80)
    global_account_name: str = Field("", max_length=180)
    primary_region: str = Field("", max_length=80)
    owner: int
    duplicate_override: bool = False


class CompanyPatch(CompanyInput):
    name: str | None = Field(None, min_length=1, max_length=180)
    country: str | None = Field(None, min_length=1, max_length=80)
    owner: int | None = None


class ContactInput(Input):
    company: UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | Literal[""] = ""
    job_title: str = Field("", max_length=100)
    seniority: Literal["C-level", "VP or Head", "Director", "Manager", "Individual contributor", "Unknown"] = "Unknown"
    phone: str = Field("", max_length=40)
    mobile: str = Field("", max_length=40)
    linkedin_url: str = Field("", max_length=200)
    country: str = Field(min_length=1, max_length=80)
    city: str = Field("", max_length=80)
    owner: int
    sourced_by: int | None = None
    source_channel: str = "Other"
    source_detail: str = Field("", max_length=180)
    engagement_status: Literal["Not contacted", "Contacted no response", "Engaged", "Meeting held", "Unresponsive", "Do not contact"] = "Not contacted"
    do_not_contact: bool = False
    consent_basis: Literal["Business card or event", "Referral", "Public professional profile", "Inbound enquiry", "Existing client relationship"] = "Business card or event"
    notes: str = ""
    duplicate_override: bool = False


class ContactPatch(ContactInput):
    company: UUID | None = None
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    country: str | None = Field(None, min_length=1, max_length=80)
    owner: int | None = None


class LeadInput(Input):
    name: str = Field(min_length=1, max_length=180)
    company: UUID
    owner: int
    holder: int
    next_action: str = Field(min_length=1, max_length=250)
    action_type: str
    action_date: date
    source_channel: str
    source_detail: str = Field("", max_length=180)
    priority: str = Field("Medium", max_length=20)
    area_of_interest: str = ""

class ConversionInput(Input):
    customer_need: str = Field(min_length=1)
    scope_summary: str = Field(min_length=1)
    primary_contact: UUID
    current_value: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    currency: str = Field("USD", min_length=3, max_length=3)
    service_line: str
    expected_close_date: date
    opportunity_type: str = Field("New logo", max_length=60)
    engagement_type: str = Field("Fixed price", max_length=60)

class LeadStatusInput(Input):
    status: Literal["new", "working", "engaged", "ready"]


class DisqualifyInput(Input):
    reason: str


class NurtureInput(Input):
    revisit_date: date


class WorkInput(Input):
    version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=250)
    holder: int | None = None
    next_action: str | None = Field(None, max_length=250)
    action_type: str | None = None
    action_date: date | None = None
    blocker: str | None = None
    blocker_owner: int | None = None
    resolution_action: str | None = Field(None, max_length=250)
    next_meeting: date | None = None
    priority: str | None = Field(None, max_length=20)

class OpportunityPatch(Input):
    version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=250)
    name: str | None = Field(None, min_length=1, max_length=180)
    opportunity_type: Literal["New logo", "Expansion at existing client", "Renewal or extension"] | None = None
    customer_need: str | None = Field(None, min_length=1)
    scope_summary: str | None = Field(None, min_length=1)
    primary_contact: UUID | None = None
    service_line: str | None = None
    engagement_type: Literal["Fixed price", "Time and materials", "Retainer or AMC", "Licence plus services", "Milestone"] | None = None
    expected_close_date: date | None = None
    priority: Literal["High", "Medium", "Low"] | None = None


class WorkingCalendarInput(Input):
    working_weekdays: list[int] = Field(min_length=1, max_length=7)
    holidays: list[date] = Field(default_factory=list, max_length=366)

    @model_validator(mode="after")
    def valid_calendar(self):
        if any(day < 0 or day > 6 for day in self.working_weekdays): raise ValueError("Working weekdays must use values 0 through 6.")
        if len(set(self.working_weekdays)) != len(self.working_weekdays): raise ValueError("Working weekdays cannot contain duplicates.")
        if len(set(self.holidays)) != len(self.holidays): raise ValueError("Holiday dates cannot contain duplicates.")
        return self


class StageInput(Input):
    stage: str
    version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=250)
    revisit_date: date | None = None
    loss_reason: str | None = None
    competitor_name: str = ""
    competitor_status: Literal["None known", "Incumbent", "Shortlisted alongside us", "Sole alternative"] = "None known"
    contract_number: str | None = None
    contract_date: date | None = None
    final_value: Decimal | None = Field(None, ge=0)
    project_start: date | None = None
    duration_months: int | None = Field(None, ge=1, le=600)
    handoff_notes: str = ""
    close_notes: str = ""
    final_evidence_artifact_id: UUID | None = None
    approval_recorded: bool = False
    approval_note: str = ""


class ActionCompletionInput(Input):
    version: int = Field(ge=1)
    outcome: str = Field(min_length=1, max_length=80)
    note: str = ""
    next_holder: int
    next_action: str = Field(min_length=1, max_length=250)
    next_action_type: str
    next_action_date: date


class NotificationPreferenceInput(Input):
    due_actions: bool
    stalled_pursuits: bool
    blockers: bool
    inactivity: bool
    proposal_followup: bool
    validation: bool
    presales: bool
    close_dates: bool
    revisits: bool
    system_failures: bool
    weekly_summary: bool
    inactivity_days: int = Field(ge=7, le=120)
    proposal_followup_days: int = Field(ge=1, le=60)
    close_notice_days: int = Field(ge=1, le=60)


class ValueInput(Input):
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    value_type: str
    note: str = ""


class RestrictionInput(Input):
    restricted: bool
    reason: str = Field(min_length=1)


class TeamInput(Input):
    user_id: int
    role: Literal["Pre-sales owner", "Tech lead", "Supporting contributor"]


class ProbabilityInput(Input):
    probability: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)


class OpportunityRateInput(Input):
    rate: Decimal = Field(gt=0, max_digits=18, decimal_places=8)
    reason: str = Field(min_length=1, max_length=500)


class CommercialDetailsInput(Input):
    gross_margin_pct: Decimal | None = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    approval_recorded: bool = False
    approval_note: str = ""

    @model_validator(mode="after")
    def approval_has_evidence(self):
        if self.approval_recorded and not self.approval_note:
            raise ValueError("Add the approval note or linked-email reference.")
        return self


class PartnerInput(Input):
    company_id: UUID
    contact_id: UUID
    role: Literal["Referral source", "Reseller", "Local partner", "Prime contractor", "Delivery subcontractor", "Introducer", "Joint bid partner"]
    introduced: bool = False
    fee_basis: Literal["Percentage of contract value", "Percentage of gross margin", "Fixed fee", "Commission", "Rate card spread", "To be agreed"]
    share_pct: Decimal = Field(0, ge=0, le=100, max_digits=5, decimal_places=2)
    fixed_fee: Decimal = Field(0, ge=0, max_digits=18, decimal_places=2)
    applies_to: Literal["This contract only", "All revenue from this client for a fixed period", "All revenue from this client indefinitely"] = "This contract only"
    duration_months: int | None = Field(None, ge=1, le=600)
    status: Literal["Proposed", "Verbally agreed", "Documented in writing", "Lapsed or superseded"] = "Proposed"
    agreement_artifact_id: UUID | None = None
    terms_notes: str = ""

    @model_validator(mode="after")
    def valid_terms(self):
        percentage = {"Percentage of contract value", "Percentage of gross margin", "Commission"}
        if self.fee_basis in percentage and self.share_pct <= 0:
            raise ValueError("Enter the percentage the partner takes.")
        if self.fee_basis == "Fixed fee" and self.fixed_fee <= 0:
            raise ValueError("Enter the fixed fee in the opportunity currency.")
        if self.fee_basis == "Rate card spread" and self.share_pct <= 0 and self.fixed_fee <= 0:
            raise ValueError("Enter the spread as a percentage or fixed amount.")
        if self.applies_to == "All revenue from this client for a fixed period" and not self.duration_months:
            raise ValueError("Enter the agreement duration in months.")
        if self.status == "Documented in writing" and not self.agreement_artifact_id:
            raise ValueError("Link the artifact that documents the partner terms.")
        return self


class CommercialSettingsInput(Input):
    partner_share_warning_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    fx_movement_notice_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class RateRefreshItem(Input):
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    rate: Decimal = Field(gt=0, max_digits=18, decimal_places=8)


class RateRefreshInput(Input):
    source: str = Field(min_length=1, max_length=100)
    effective_date: date
    rates: list[RateRefreshItem] = Field(min_length=1, max_length=100)


class RebaselineInput(Input):
    opportunity_ids: list[UUID] = Field(min_length=1, max_length=500)
    confirmation: Literal["REBASELINE"]
    reason: str = Field(min_length=1, max_length=500)


class ActivityInput(Input):
    pursuit: UUID | None = None
    contact: UUID | None = None
    company: UUID
    activity_type: Literal["Email", "Call", "LinkedIn message", "LinkedIn connection request", "WhatsApp", "Meeting", "Demo", "Workshop", "Event conversation", "Internal note"]
    direction: Literal["Outbound", "Inbound"] = "Outbound"
    activity_date: datetime | None = None
    outcome: Literal["No response", "Responded", "Meeting booked", "Referred onward", "Declined", "Not relevant"] = "Responded"
    subject: str = Field(min_length=1, max_length=250)
    notes: str = ""
    override_reason: str = ""


class RequestInput(Input):
    opportunity: UUID
    title: str = Field(min_length=1, max_length=180)
    request_type: str = Field("Deck", max_length=60)
    assigned_to: int
    needed_by: date
    customer_meeting_date: date | None = None
    estimated_days: Decimal = Field(0, ge=0)
    notes: str = ""


class RequestPatch(Input):
    status: str
    actual_days: Decimal | None = Field(None, ge=0)
    blocked_reason: str = ""


class ArtifactInput(Input):
    pursuit: UUID
    title: str = Field(min_length=1, max_length=180)
    artifact_type: str = Field("Proposal", max_length=50)
    storage_link: HttpUrl
    version: int = Field(1, ge=1)
    internal_only: bool = False


class AdminUserInput(Input):
    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    job_title: str = Field("", max_length=100)
    level: Literal["Standard", "Manager", "Executive", "Administrator"] = "Standard"
    password: str = Field(min_length=12, max_length=200)


class AdminUserPatch(Input):
    first_name: str | None = Field(None, min_length=1, max_length=150)
    last_name: str | None = Field(None, min_length=1, max_length=150)
    email: EmailStr | None = None
    job_title: str | None = Field(None, max_length=100)
    level: Literal["Standard", "Manager", "Executive", "Administrator"] | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=12, max_length=200)


class ReferenceInput(Input):
    category: str = Field(min_length=1, max_length=40)
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9 _&+./-]*$")
    label: str = Field(min_length=1, max_length=120)
    numeric_value: int | None = Field(None, ge=0, le=100)
    sort_order: int = Field(0, ge=0, le=10000)
    active: bool = True


class ReferencePatch(Input):
    label: str | None = Field(None, min_length=1, max_length=120)
    numeric_value: int | None = Field(None, ge=0, le=100)
    sort_order: int | None = Field(None, ge=0, le=10000)
    active: bool | None = None


class RatePatch(Input):
    rate: Decimal = Field(gt=0, max_digits=18, decimal_places=8)
    source: str = Field(min_length=1, max_length=100)


class ImportInput(Input):
    entity_type: Literal["companies", "contacts", "leads"]
    filename: str = Field(min_length=1, max_length=180)
    csv_text: str = Field("", max_length=8_000_000)
    file_content: str = Field("", max_length=12_000_000)
    file_type: Literal["csv", "xlsx"] = "csv"
    mapping: dict[str, str] = Field(default_factory=dict)
    confirm_warnings: bool = False

    @model_validator(mode="after")
    def has_file_content(self):
        if self.file_type == "csv" and not self.csv_text:
            raise ValueError("CSV content is required.")
        if self.file_type == "xlsx" and not self.file_content:
            raise ValueError("Excel file content is required.")
        return self


class MergeInput(Input):
    primary_id: UUID
    duplicate_id: UUID
    field_sources: dict[str, UUID] = Field(default_factory=dict)


class DuplicateDismissInput(Input):
    first_id: UUID
    second_id: UUID
    reason: str = Field(min_length=3, max_length=250)


class SavedViewInput(Input):
    entity_type: Literal["companies", "contacts", "leads", "opportunities"]
    name: str = Field(min_length=1, max_length=80)
    filters: dict[str, str | int | bool | None] = Field(default_factory=dict)


class SavedViewPatch(Input):
    name: str | None = Field(None, min_length=1, max_length=80)
    filters: dict[str, str | int | bool | None] | None = None


class BulkAssignmentInput(Input):
    pursuit_ids: list[UUID] = Field(min_length=1, max_length=100)
    versions: dict[str, int]
    owner_id: int | None = None
    holder_id: int | None = None
    reason: str = Field(min_length=1, max_length=250)

    @model_validator(mode="after")
    def has_assignment(self):
        if self.owner_id is None and self.holder_id is None:
            raise ValueError("Choose a new owner, a new Ball in Court holder, or both.")
        return self


class StakeholderInput(Input):
    contact_id: UUID
    role: Literal["Champion", "Decision maker", "Influencer", "Procurement", "Technical", "Other"]


class StakeholderPatch(Input):
    role: Literal["Champion", "Decision maker", "Influencer", "Procurement", "Technical", "Other"]
