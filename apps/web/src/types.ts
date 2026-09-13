export interface Person {
  id: number;
  name: string;
  first_name: string;
  last_name: string;
  level: string;
  job_title: string;
  email: string;
  active: boolean;
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
  source_channel: string;
  source_detail: string;
  engagement_status: string;
  do_not_contact: boolean;
  consent_basis: string;
  notes: string;
  touch_count: number;
  last_touched_at: string | null;
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
  pursuit_id: string | null;
}
export interface Request {
  id: string;
  title: string;
  request_type: string;
  status: string;
  assigned_to: string;
  assigned_to_id: number;
  needed_by: string;
  estimated_days: string;
  actual_days: string | null;
  opportunity: string;
  opportunity_id: string;
  pursuit_id: string;
  notes: string;
  blocked_reason: string;
}
export interface Data {
  user: Person;
  instance: string;
  mode: string;
  today: string;
  users: Person[];
  admin_users: Person[];
  admin_references: AdminReference[];
  commercial_settings: {
    partner_share_warning_pct: string;
    fx_movement_notice_pct: string;
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
  artifacts: {
    id: string;
    title: string;
    type: string;
    url: string;
    version: number;
    internal_only: boolean;
    approved: boolean;
    shared_at: string | null;
  }[];
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
