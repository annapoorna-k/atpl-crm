from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginInput(Input):
    username: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class CompanyInput(Input):
    name: str = Field(min_length=1, max_length=180)
    domain: str = Field("", max_length=180)
    company_type: str = Field("Prospect", max_length=40)
    industry: str = Field("", max_length=100)
    country: str = Field(min_length=1, max_length=80)
    global_account_name: str = Field("", max_length=180)
    primary_region: str = Field("", max_length=80)
    owner: int


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
    seniority: str = Field("Unknown", max_length=40)
    phone: str = Field("", max_length=40)
    mobile: str = Field("", max_length=40)
    linkedin_url: str = Field("", max_length=200)
    country: str = Field(min_length=1, max_length=80)
    city: str = Field("", max_length=80)
    owner: int
    source_channel: str = "Other"
    source_detail: str = Field("", max_length=180)
    engagement_status: str = Field("Not contacted", max_length=40)
    do_not_contact: bool = False
    consent_basis: str = Field("Business card or event", max_length=80)
    notes: str = ""


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

class StageInput(Input):
    stage: str
    revisit_date: date | None = None
    loss_reason: str | None = None
    competitor_name: str = ""
    contract_number: str | None = None
    contract_date: date | None = None
    final_value: Decimal | None = Field(None, ge=0)


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


class ActivityInput(Input):
    pursuit: UUID | None = None
    contact: UUID | None = None
    company: UUID
    activity_type: str
    direction: Literal["Outbound", "Inbound"] = "Outbound"
    activity_date: datetime | None = None
    outcome: str = Field("Responded", max_length=40)
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
    csv_text: str = Field(min_length=1, max_length=2_000_000)
    mapping: dict[str, str] = Field(default_factory=dict)


class MergeInput(Input):
    primary_id: UUID
    duplicate_id: UUID
