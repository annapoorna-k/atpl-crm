export interface Person {
  id: number;
  name: string;
  first_name: string;
  last_name: string;
  level: string;
  job_title: string;
  email: string;
  active: boolean;
  weekly_capacity_days: string;
}
export interface AdminReference {
  id: string;
  category: string;
  code: string;
  label: string;
  numeric_value: number | null;
  sort_order: number;
  active: boolean;
}
export interface Company {
  id: string;
  name: string;
  domain: string;
  company_type: string;
  industry: string;
  country: string;
  owner: string;
  owner_id: number;
  global_account_name: string;
  primary_region: string;
}
export interface Contact {
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  company_id: string;
  company: string;
  email: string;
  job_title: string;
  country: string;
  city: string;
  phone: string;
  mobile: string;
  seniority: string;
  linkedin_url: string;
  owner: string;
  owner_id: number;
  sourced_by: string;
  sourced_by_id: number;
  source_channel: string;
  source_detail: string;
  engagement_status: string;
  do_not_contact: boolean;
  consent_basis: string;
  notes: string;
  touch_count: number;
  first_contacted_at: string | null;
  last_touched_at: string | null;
  last_outbound_at: string | null;
  last_outbound_pursuit: string | null;
}

export interface ArtifactRecord {
  id: string;
  pursuit_id: string;
  pursuit: string;
  company_id: string;
  company: string;
  title: string;
  artifact_type: string;
  kind: string;
  url: string;
  original_filename: string;
  content_type: string;
  byte_size: number;
  checksum_sha256: string;
  version: number;
  supersedes_id: string | null;
  superseded: boolean;
  parent_email_id: string | null;
  email_classification: string;
  message_reference: string;
  email_subject: string;
  email_date: string | null;
  email_direction: string;
  email_participants: string[];
  internal_only: boolean;
  is_reusable: boolean;
  approved: boolean;
  approved_by: string | null;
  approved_at: string | null;
  shared_with_client: boolean;
  shared_at: string | null;
  recipients: { id: string; name: string; email: string }[];
  created_at: string;
}
export interface Pursuit {
  id: string;
  name: string;
  company_id: string;
  company: string;
  owner: string;
  owner_id: number;
  sourced_by: string;
  holder: string;
  holder_id: number;
  ball_since: string;
  days_held: number;
  next_action: string;
  action_type: string;
  action_date: string;
  priority: string;
  source_channel: string;
  source_detail: string;
  blocker: string;
  blocker_owner: string | null;
  blocker_owner_id: number | null;
  resolution_action: string;
  days_blocked: number;
  last_client_interaction: string | null;
  next_meeting: string | null;
  created_at: string;
  version: number;
  milestones: { key: string; label: string; at: string | null }[];
  flags: string[];
  can_work: boolean;
  lead_id: string;
  opportunity_id: string | null;
  team: { user_id: number; name: string; role: string }[];
  contacts: {
    link_id: string;
    id: string;
    name: string;
    role: string;
    job_title: string;
    email: string;
  }[];
  values_visible: boolean;
  can_edit_commercial?: boolean;
  status?: string;
  area_of_interest?: string;
  outcome?: string;
  reason?: string;
  revisit_date?: string;
  stage?: string;
  opportunity_type?: string;
  engagement_type?: string;
  customer_need?: string;
  scope_summary?: string;
  service_line?: string;
  primary_contact?: string;
  primary_contact_id?: string;
  expected_close_date?: string;
  probability?: number;
  probability_note?: string;
  stage_probability?: number;
  gross_margin_pct?: string | null;
  restricted?: boolean;
  current_value?: string;
  currency?: string;
  fx_rate?: string;
  value_usd?: string;
  net_value_usd?: string | null;
  net_value_local?: string | null;
  partner_deduction_local?: string;
  total_partner_share_pct?: string;
  partner_share_warning_pct?: string;
  commercial_warnings?: string[];
  partners?: Partner[];
  approval_recorded?: boolean;
  approval_note?: string;
  loss_reason?: string;
  competitor_name?: string;
  competitor_status?: string;
  contract_number?: string;
  contract_date?: string | null;
  project_start?: string | null;
  duration_months?: number | null;
  handoff_notes?: string;
  close_notes?: string;
  final_evidence_artifact_id?: string | null;
  values?: {
    id: string;
    type: string;
    amount: string;
    currency: string;
    fx_rate: string;
    usd_amount: string;
    date: string;
    note: string;
  }[];
}
export interface Partner {
  id: string;
  company_id: string;
  company: string;
  contact_id: string;
  contact: string;
  role: string;
  introduced: boolean;
  fee_basis: string;
  share_pct: string;
  fixed_fee: string;
  applies_to: string;
  duration_months: number | null;
  status: string;
  agreement_artifact_id: string | null;
  terms_notes: string;
}
export interface Activity {
  id: string;
  subject: string;
  notes: string;
  activity_type: string;
  is_client_facing: boolean;
  date: string;
  direction: string;
  outcome: string;
  author: string;
  company: string;
  contact_id: string | null;
  contact: string | null;
  pursuit_id: string | null;
  pursuit: string | null;
  override_reason: string;
}
export interface ActivityPage {
  items: Activity[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}
export interface Request {
  id: string;
  title: string;
  request_type: string;
  status: string;
  version: number;
  requested_at: string;
  requested_by: string;
  requested_by_id: number;
  assigned_to: string;
  assigned_to_id: number | null;
  needed_by: string;
  customer_meeting_date: string | null;
  estimated_days: string;
  actual_days: string | null;
  opportunity: string;
  opportunity_id: string;
  pursuit_id: string;
  notes: string;
  blocked_reason: string;
  review_note: string;
  deliverable_artifact_id: string | null;
  deliverable_artifact: string | null;
  approved_by: string | null;
  accepted_at: string | null;
  review_ready_at: string | null;
  approved_at: string | null;
  delivered_at: string | null;
  contributors: { id: number; name: string }[];
  can_assign?: boolean;
  can_add_contributors?: boolean;
  can_edit_brief?: boolean;
  can_approve?: boolean;
  allowed_transitions?: string[];
}

export interface PreSalesQueue {
  week_start: string;
  week_end: string;
  requests: Request[];
  team_load: {
    user_id: number;
    name: string;
    job_title: string;
    capacity_days: string;
    assigned_days: string;
    request_count: number;
    supporting_requests: number;
    utilization_pct: string | null;
    over_capacity: boolean;
  }[];
}

export interface PreSalesCostReport {
  delivered_requests: number;
  actual_days: string;
  by_request_type: {
    key: string;
    request_count: number;
    actual_days: string;
  }[];
  by_service_line: {
    key: string;
    request_count: number;
    actual_days: string;
  }[];
  by_outcome: { key: string; request_count: number; actual_days: string }[];
}
export interface Data {
  user: Person;
  permissions: {
    role: string;
    capabilities: { code: string; label: string; granted: boolean }[];
    field_rules: { area: string; fields: string; rule: string }[];
  };
  instance: string;
  mode: string;
  today: string;
  workspace_counts: { companies: number; contacts: number; pursuits: number };
  working_set: {
    companies: number;
    contacts: number;
    pursuits: number;
    truncated: boolean;
  };
  users: Person[];
  admin_users: Person[];
  admin_references: AdminReference[];
  commercial_settings: {
    partner_share_warning_pct: string;
    fx_movement_notice_pct: string;
  };
  working_calendar: {
    working_weekdays: number[];
    holidays: string[];
  };
  companies: Company[];
  contacts: Contact[];
  leads: Pursuit[];
  opportunities: Pursuit[];
  requests: Request[];
  activities: Activity[];
  notifications: {
    id: string;
    message: string;
    category: string;
    severity: string;
    read: boolean;
    read_at: string | null;
    pursuit_id: string | null;
    created_at: string;
  }[];
  reference: {
    stages: [string, string][];
    probabilities: Record<string, number>;
    lead_statuses: [string, string][];
    sources: [string, string][];
    services: [string, string][];
    actions: [string, string][];
    blockers: [string, string][];
    loss_reasons: [string, string][];
    disqualification_reasons: [string, string][];
    request_statuses: [string, string][];
    currencies: {
      id: string;
      currency: string;
      rate: string;
      source: string;
      effective_date: string | null;
    }[];
  };
}
export interface Timeline {
  activities: Activity[];
  events: {
    id: string;
    action: string;
    detail: string;
    date: string;
    author: string;
  }[];
  completed_actions: {
    id: string;
    summary: string;
    action_type: string;
    due_date: string;
    outcome: string;
    note: string;
    completed_at: string;
    completed_by: string;
  }[];
  artifacts: ArtifactRecord[];
  restricted_content?: boolean;
}

export interface MilestoneReport {
  key: string;
  label: string;
  count: number;
  median_working_days: number | null;
  target_working_days: number;
  healthy: boolean;
}

export interface ValidationRoute {
  eligible: Person[];
  current_user_can_validate: boolean;
  reason: string;
}

export interface MovementReport {
  period: string;
  move_count: number;
  regression_count: number;
  transitions: {
    from_label: string;
    to_label: string;
    count: number;
    median_working_days: number;
  }[];
  current_stage_age: {
    stage: string;
    label: string;
    count: number;
    median_working_days: number;
    oldest_working_days: number;
  }[];
  moves: {
    pursuit_id: string;
    pursuit: string;
    company: string;
    from_label: string;
    to_label: string;
    moved_at: string;
    working_days_in_previous_stage: number;
    evidence: string;
    regression: boolean;
  }[];
  calendar: { working_weekdays: number[]; holiday_count: number };
}

export interface NotificationPreference {
  due_actions: boolean;
  stalled_pursuits: boolean;
  blockers: boolean;
  inactivity: boolean;
  proposal_followup: boolean;
  validation: boolean;
  presales: boolean;
  close_dates: boolean;
  revisits: boolean;
  system_failures: boolean;
  weekly_summary: boolean;
  inactivity_days: number;
  proposal_followup_days: number;
  close_notice_days: number;
}

export interface WorkQueues {
  my_work: {
    overdue_actions: Pursuit[];
    today_actions: Pursuit[];
    upcoming_actions: Pursuit[];
    blockers: Pursuit[];
    deliverables: Request[];
  };
  needs_attention: {
    key: string;
    kind: string;
    label: string;
    severity: string;
    pursuit: Pursuit | null;
    request: Request | null;
  }[];
}

export interface UndocumentedPartnerReport {
  partner_id: string;
  opportunity_id: string;
  opportunity: string;
  stage: string;
  partner: string;
  contact: string;
  status: string;
  fee_basis: string;
}

export interface PartnerPerformanceReport {
  company_id: string;
  partner: string;
  opportunities_involved: number;
  opportunities_introduced: number;
  wins: number;
  closed: number;
  win_rate_pct: string | null;
  net_value_usd: string;
}

export interface AutomationStatus {
  latest: {
    task_name: string;
    status: string;
    created_count: number;
    finished_at: string;
    detail: string;
  } | null;
}
