import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  Activity as ActivityIcon,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Building2,
  CalendarDays,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  Clock3,
  FileText,
  Globe2,
  Handshake,
  LayoutDashboard,
  ListTodo,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Menu,
  MoreHorizontal,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  X,
  AlertCircle,
  Layers3,
  KanbanSquare,
  ExternalLink,
  CheckCircle2,
  Database,
  FolderKanban,
} from "lucide-react";
import { api } from "./api";
import { DataTools } from "./DataTools";
import { DocumentCenter } from "./DocumentCenter";
import { RecordList } from "./RecordList";
import { ReportsCenter } from "./ReportsCenter";
import type {
  Company,
  Contact,
  Data,
  Person,
  Pursuit,
  Request,
  Timeline,
  AdminReference,
  NotificationPreference,
  WorkQueues,
  AutomationStatus,
  Partner,
  PartnerPerformanceReport,
  UndocumentedPartnerReport,
  ActivityPage,
  PreSalesCostReport,
  PreSalesQueue,
  ValidationRoute,
} from "./types";

const money = (
  value: string | number | undefined | null,
  currency = "USD",
  compact = false,
) =>
  value == null
    ? "Restricted"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        maximumFractionDigits: compact ? 1 : 0,
        notation: compact ? "compact" : "standard",
      }).format(Number(value));
const date = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
      }).format(new Date(value.slice(0, 10) + "T12:00:00"))
    : "Not scheduled";
const initials = (name: string) =>
  name
    .split(" ")
    .slice(0, 2)
    .map((x) => x[0])
    .join("");
const tomorrow = () => {
  const x = new Date();
  x.setDate(x.getDate() + 1);
  return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
};
const weekStart = () => {
  const value = new Date();
  const day = value.getDay();
  value.setDate(value.getDate() - ((day + 6) % 7));
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
};
const nav = [
  {
    group: "WORKSPACE",
    items: [
      ["overview", "Overview", LayoutDashboard],
      ["work", "My work", ListTodo],
      ["attention", "Needs attention", AlertCircle],
    ],
  },
  {
    group: "RELATIONSHIPS",
    items: [
      ["leads", "Leads", Target],
      ["pipeline", "Opportunities", KanbanSquare],
      ["companies", "Companies", Building2],
      ["contacts", "Contacts", Users],
      ["documents", "Documents", FolderKanban],
    ],
  },
  {
    group: "TEAM & INSIGHTS",
    items: [
      ["presales", "Pre-sales", Layers3],
      ["reports", "Reports", TrendingUp],
      ["data", "Data tools", Database],
      ["settings", "Administration", Settings2],
    ],
  },
] as const;
type Field = {
  name: string;
  label: string;
  type?: string;
  options?: [string, string][];
  value?: string;
  required?: boolean;
  hint?: string;
  multiple?: boolean;
};
type FormSpec = {
  title: string;
  description?: string;
  fields: Field[];
  submit: (values: Record<string, string>) => Promise<unknown>;
  label?: string;
  notice?: (values: Record<string, string>) => string;
};
type RoleDashboard = {
  role: string;
  cards: { label: string; value: string; route: string; record_ids: string[] }[];
};
function Avatar({ name, small = false }: { name: string; small?: boolean }) {
  return (
    <span className={`avatar ${small ? "small" : ""}`} aria-label={name}>
      {initials(name)}
    </span>
  );
}
function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Empty({
  title = "Nothing here yet",
  text = "Create a record to get started.",
}: {
  title?: string;
  text?: string;
}) {
  return (
    <div className="empty">
      <Layers3 size={32} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <span />
      </span>
      <span>
        ATPL<span className="brand-light">CRM</span>
        <small>CLARITY. CONNECTION. GROWTH.</small>
      </span>
    </div>
  );
}

function FormModal({
  spec,
  onClose,
  onSuccess,
}: {
  spec: FormSpec;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(
      () =>
        spec.notice?.(
          Object.fromEntries(
            spec.fields.map((field) => [field.name, field.value ?? ""]),
          ),
        ) ?? "",
    );
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const formData = new FormData(e.currentTarget);
    const values = Object.fromEntries(formData) as Record<string, string>;
    spec.fields
      .filter((field) => field.multiple)
      .forEach((field) => {
        values[field.name] = formData.getAll(field.name).join(",");
      });
    try {
      await spec.submit(values);
      onSuccess();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={ref}
      className="form-dialog"
      onCancel={onClose}
      aria-labelledby="form-title"
    >
      <div className="dialog-heading">
        <div>
          <span className="eyebrow">ATPLCRM WORKSPACE</span>
          <h2 id="form-title">{spec.title}</h2>
        </div>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close form"
        >
          <X size={20} />
        </button>
      </div>
      {spec.description && (
        <p className="form-description">{spec.description}</p>
      )}
      <form
        onSubmit={submit}
        onChange={(event) =>
          setNotice(
            spec.notice?.(
              Object.fromEntries(new FormData(event.currentTarget)) as Record<
                string,
                string
              >,
            ) ?? "",
          )
        }
      >
        <div className="form-grid">
          {spec.fields.map((f) =>
            f.multiple ? (
              <fieldset key={f.name} className="full checkbox-fieldset">
                <legend>
                  {f.label}
                  {f.required !== false && <span className="required"> *</span>}
                </legend>
                <span className="checkbox-options">
                  {f.options?.map(([value, label]) => (
                    <label key={value}>
                      <input
                        type="checkbox"
                        name={f.name}
                        value={value}
                        defaultChecked={(f.value ?? "")
                          .split(",")
                          .includes(value)}
                      />
                      {label}
                    </label>
                  ))}
                </span>
                {f.hint && <small>{f.hint}</small>}
              </fieldset>
            ) : (
              <label
                key={f.name}
                className={f.type === "textarea" ? "full" : ""}
              >
                {f.label}
                {f.required !== false && <span className="required"> *</span>}
                {f.options ? (
                  <select
                    name={f.name}
                    defaultValue={f.value ?? ""}
                    required={f.required !== false}
                  >
                    <option value="">Select…</option>
                    {f.options.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : f.type === "textarea" ? (
                  <textarea
                    name={f.name}
                    defaultValue={f.value}
                    required={f.required !== false}
                    rows={3}
                  />
                ) : (
                  <input
                    name={f.name}
                    type={f.type ?? "text"}
                    defaultValue={f.value}
                    required={f.required !== false}
                    step={f.type === "number" ? "any" : undefined}
                  />
                )}{" "}
                {f.hint && <small>{f.hint}</small>}
              </label>
            ),
          )}
        </div>
        {notice && (
          <div role="status" className="form-notice">
            <AlertCircle size={18} />
            <span>
              <strong>Contact owner warning</strong>
              {notice}
            </span>
          </div>
        )}
        {error && (
          <div role="alert" className="error">
            <AlertCircle size={18} />
            {error}
          </div>
        )}
        <div className="dialog-footer">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button disabled={busy} className="button primary">
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Check size={16} />
            )}{" "}
            {spec.label ?? "Save changes"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await api("session/", "POST", {
        username: form.get("username"),
        password: form.get("password"),
      });
      onLogin();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login">
      <section className="login-brand">
        <Brand />
        <div>
          <span className="eyebrow yellow">YOUR NEXT MOVE, CLEAR.</span>
          <h1>
            Great relationships.
            <br />
            Clear next steps.
            <br />
            <span>Stronger outcomes.</span>
          </h1>
          <p>
            One workspace for your pipeline, your people, and every handoff in
            between.
          </p>
          <div className="login-mini">
            <div>
              <span className="mini-dot" />
              Every pursuit has a person.
            </div>
            <div>
              <span className="mini-dot" />
              Every next step has a date.
            </div>
          </div>
        </div>
        <small>ATPLCRM · An independent sales workspace</small>
      </section>
      <section className="login-form">
        <div>
          <Badge tone="yellow">LOCAL DEMO</Badge>
          <h2>Welcome to your workspace</h2>
          <p>Sign in to turn the next conversation into progress.</p>
          <form onSubmit={submit}>
            <label>
              Email address
              <input
                name="username"
                type="email"
                defaultValue="alex@atplcrm.local"
                autoComplete="username"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
            </label>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button className="button primary" disabled={busy}>
              {busy ? <LoaderCircle className="spin" size={17} /> : null} Sign
              in <ArrowRight size={17} />
            </button>
          </form>
          <div className="login-note">
            <ShieldCheck size={20} />
            <span>
              Synthetic demo data. Your local password is the{" "}
              <code>DEMO_PASSWORD</code> value in the project’s{" "}
              <code>.env</code> file. Microsoft sign-in is not enabled yet.
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState<Person | null | undefined>(undefined),
    [data, setData] = useState<Data | null>(null),
    [page, setPage] = useState(location.hash.slice(1) || "overview"),
    [query, setQuery] = useState(""),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [form, setForm] = useState<FormSpec | null>(null),
    [selected, setSelected] = useState<string | null>(null),
    [companyId, setCompanyId] = useState<string | null>(null),
    [contactId, setContactId] = useState<string | null>(null),
    [timeline, setTimeline] = useState<Timeline | null>(null),
    [detailTab, setDetailTab] = useState("Overview"),
    [notifications, setNotifications] = useState(false),
    [mobile, setMobile] = useState(false),
    [ownerFilter, setOwnerFilter] = useState("all"),
    [pipelineView, setPipelineView] = useState("board"),
    [showLocalCurrency, setShowLocalCurrency] = useState(false),
    [draggedPursuit, setDraggedPursuit] = useState<Pursuit | null>(null),
    [validationRoute, setValidationRoute] = useState<ValidationRoute | null>(
      null,
    ),
    [workQueues, setWorkQueues] = useState<WorkQueues | null>(null),
    [notificationPreferences, setNotificationPreferences] =
      useState<NotificationPreference | null>(null),
    [automationStatus, setAutomationStatus] = useState<AutomationStatus | null>(
      null,
    ),
    [partnerPerformance, setPartnerPerformance] = useState<
      PartnerPerformanceReport[]
    >([]),
    [undocumentedPartners, setUndocumentedPartners] = useState<
      UndocumentedPartnerReport[]
    >([]),
    [presalesQueue, setPresalesQueue] = useState<PreSalesQueue | null>(null),
    [presalesWeek, setPresalesWeek] = useState(weekStart),
    [presalesOwner, setPresalesOwner] = useState(""),
    [presalesStatus, setPresalesStatus] = useState("open"),
    [presalesCost, setPresalesCost] = useState<PreSalesCostReport | null>(null),
    [roleDashboard, setRoleDashboard] = useState<RoleDashboard | null>(null),
    [relationshipHistory, setRelationshipHistory] =
      useState<ActivityPage | null>(null);
  const detailRef = useRef<HTMLDialogElement>(null);
  async function load() {
    try {
      const d = await api<Data>("bootstrap/");
      setData(d);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    api<{ user: Person | null }>("session/")
      .then((x) => setSession(x.user))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (session) void load();
  }, [session]);
  useEffect(() => {
    if (!session || !data || page !== "overview") return;
    api<RoleDashboard>("reports/home/")
      .then(setRoleDashboard)
      .catch((e) => setToast((e as Error).message));
  }, [session, data, page]);
  useEffect(() => {
    if (
      !session ||
      page !== "reports" ||
      !["Administrator", "Manager", "Executive"].includes(session.level)
    )
      return;
    void Promise.all([
      api<PartnerPerformanceReport[]>(
        "commercial/reports/partner-performance/",
      ),
      api<UndocumentedPartnerReport[]>(
        "commercial/reports/undocumented-partners/",
      ),
      api<PreSalesCostReport>("presales/cost-report/"),
    ])
      .then(([performance, undocumented, cost]) => {
        setPartnerPerformance(performance);
        setUndocumentedPartners(undocumented);
        setPresalesCost(cost);
      })
      .catch((e) => setToast((e as Error).message));
  }, [session, page, data]);
  useEffect(() => {
    if (!session || page !== "presales") return;
    const params = new URLSearchParams({
      week: presalesWeek,
      status_filter: presalesStatus,
    });
    if (presalesOwner) params.set("owner_id", presalesOwner);
    api<PreSalesQueue>(`presales/queue/?${params}`)
      .then(setPresalesQueue)
      .catch((e) => setToast((e as Error).message));
  }, [session, page, data, presalesWeek, presalesOwner, presalesStatus]);
  useEffect(() => {
    const handler = () => {
      setPage(location.hash.slice(1) || "overview");
      setQuery("");
      setOwnerFilter("all");
    };
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    if (selected) {
      setTimeline(null);
      api<Timeline>(`pursuits/${selected}/timeline/`)
        .then(setTimeline)
        .catch((e) => setToast(e.message));
    }
  }, [selected, data]);
  useEffect(() => {
    const lead = data?.leads.find((item) => item.id === selected);
    if (!lead || lead.status !== "ready") {
      setValidationRoute(null);
      return;
    }
    api<ValidationRoute>(`leads/${lead.lead_id}/validators/`)
      .then(setValidationRoute)
      .catch((e) => setToast((e as Error).message));
  }, [selected, data]);
  useEffect(() => {
    if (session && ["work", "attention"].includes(page)) {
      setWorkQueues(null);
      api<WorkQueues>("work/")
        .then(setWorkQueues)
        .catch((e) => setToast(e.message));
    }
  }, [page, session, data]);
  useEffect(() => {
    if (session && (page === "settings" || notifications)) {
      api<NotificationPreference>("notifications/preferences/")
        .then(setNotificationPreferences)
        .catch((e) => setToast(e.message));
      api<AutomationStatus>("notifications/status/")
        .then(setAutomationStatus)
        .catch((e) => setToast(e.message));
    }
  }, [page, session, notifications, data]);
  useEffect(() => {
    if (selected || companyId || contactId) detailRef.current?.showModal();
  }, [selected, companyId, contactId]);
  useEffect(() => {
    if (!companyId && !contactId) {
      setRelationshipHistory(null);
      return;
    }
    const filter = contactId ? `contact=${contactId}` : `company=${companyId}`;
    setRelationshipHistory(null);
    api<ActivityPage>(`activities/?${filter}&page=1&page_size=20`)
      .then(setRelationshipHistory)
      .catch((e) => setToast((e as Error).message));
  }, [companyId, contactId, data]);
  const go = (p: string) => {
    location.hash = p;
    setMobile(false);
  };
  const closeDetail = () => {
    setSelected(null);
    setCompanyId(null);
    setContactId(null);
    setDetailTab("Overview");
  };
  const openPursuit = (p: Pursuit) => {
    setCompanyId(null);
    setContactId(null);
    setSelected(p.id);
    setDetailTab("Overview");
  };
  const success = () => {
    void load();
    setToast("Changes saved successfully.");
  };
  const mutate = async (path: string, body: unknown, method = "POST") => {
    try {
      await api(path, method, body);
      success();
    } catch (e) {
      setToast((e as Error).message);
    }
  };
  if (session === undefined)
    return (
      <div className="boot">
        <Brand />
        {error ? (
          <p role="alert">{error}</p>
        ) : (
          <LoaderCircle className="spin" />
        )}
        <span>Opening your workspace…</span>
      </div>
    );
  if (!session)
    return (
      <Login
        onLogin={() =>
          api<{ user: Person }>("session/").then((x) => setSession(x.user))
        }
      />
    );
  if (!data)
    return (
      <div className="boot">
        <Brand />
        {error ? (
          <>
            <p role="alert">{error}</p>
            <button className="button primary" onClick={load}>
              Try again
            </button>
          </>
        ) : (
          <LoaderCircle className="spin" />
        )}
      </div>
    );
  const d = data;
  const all = [
    ...d.opportunities,
    ...d.leads.filter((l) => l.outcome !== "Converted"),
  ];
  const active = all.filter((p) =>
    p.stage ? !["won", "lost"].includes(p.stage) : p.status !== "closed",
  );
  const openOpps = d.opportunities.filter(
    (o) => !["won", "lost", "hold"].includes(o.stage!),
  );
  const visibleOpps = openOpps.filter(
    (o) => o.values_visible && o.net_value_usd != null,
  );
  const total = visibleOpps.reduce((s, o) => s + Number(o.net_value_usd), 0);
  const weighted = visibleOpps.reduce(
    (s, o) => s + (Number(o.net_value_usd) * (o.probability ?? 0)) / 100,
    0,
  );
  const attention = active.filter((p) => p.flags.length);
  const held = active.filter((p) => p.holder_id === d.user.id);
  const p = all.find((x) => x.id === selected);
  const company = d.companies.find((c) => c.id === companyId),
    contact = d.contacts.find((c) => c.id === contactId);
  const userOptions = d.users.map(
    (u) => [String(u.id), u.name] as [string, string],
  );
  const companyOptions = d.companies.map(
    (c) => [c.id, c.name] as [string, string],
  );
  const options = (values: (string | [string, string])[]) =>
    values.map((v) => (Array.isArray(v) ? v : ([v, v] as [string, string])));
  const field = (
    name: string,
    label: string,
    extra: Partial<Field> = {},
  ): Field => ({ name, label, ...extra });
  const adminUserForm = (user?: Person) =>
    setForm({
      title: user ? `Edit ${user.name}` : "Add workspace user",
      description: user
        ? "Changes apply only to this isolated workspace. Password entry is optional."
        : "Create a local workspace account. The temporary password must contain at least 12 characters.",
      fields: [
        field("first_name", "First name", { value: user?.first_name }),
        field("last_name", "Last name", { value: user?.last_name }),
        field("email", "Email address", { type: "email", value: user?.email }),
        field("job_title", "Job title", {
          value: user?.job_title,
          required: false,
        }),
        field("level", "Access level", {
          value: user?.level ?? "Standard",
          options: options([
            "Standard",
            "Manager",
            "Executive",
            "Administrator",
          ]),
        }),
        field("weekly_capacity_days", "Weekly pre-sales capacity (days)", {
          type: "number",
          value: user?.weekly_capacity_days ?? "5",
          hint: "Used by the weekly team-load view.",
        }),
        ...(user
          ? [
              field("is_active", "Account status", {
                value: String(user.active),
                options: [
                  ["true", "Active"],
                  ["false", "Inactive"],
                ],
              }),
            ]
          : []),
        field("password", user ? "New password" : "Temporary password", {
          type: "password",
          required: !user,
          hint: user
            ? "Leave empty to keep the current password."
            : "At least 12 characters.",
        }),
      ],
      submit: (values) => {
        if (!values.password) delete values.password;
        return api(
          `admin/users/${user ? `${user.id}/` : ""}`,
          user ? "PATCH" : "POST",
          values,
        );
      },
      label: user ? "Save user" : "Create user",
    });
  const referenceForm = (item?: AdminReference) =>
    setForm({
      title: item ? `Edit ${item.label}` : "Add reference option",
      description: item
        ? `${item.category.replaceAll("_", " ")} · Stable code: ${item.code}`
        : "Add an option to a configurable list. Workflow stage and status codes remain controlled.",
      fields: item
        ? [
            field("label", "Display label", { value: item.label }),
            ...(item.category === "stages"
              ? [
                  field("numeric_value", "Default probability", {
                    type: "number",
                    value: String(item.numeric_value ?? 0),
                  }),
                ]
              : []),
            field("sort_order", "Sort order", {
              type: "number",
              value: String(item.sort_order),
            }),
            field("active", "Availability", {
              value: String(item.active),
              options: [
                ["true", "Active"],
                ["false", "Inactive"],
              ],
            }),
          ]
        : [
            field("category", "Category", {
              options: [
                ["sources", "Lead and contact sources"],
                ["services", "Service lines"],
                ["actions", "Action types"],
                ["blockers", "Blocker types"],
                ["loss_reasons", "Opportunity loss reasons"],
                ["disqualification_reasons", "Lead disqualification reasons"],
              ],
            }),
            field("code", "Stable code"),
            field("label", "Display label"),
            field("sort_order", "Sort order", { type: "number", value: "100" }),
          ],
      submit: (values) =>
        api(
          `admin/references/${item ? `${item.id}/` : ""}`,
          item ? "PATCH" : "POST",
          values,
        ),
      label: item ? "Save option" : "Add option",
    });
  const rateForm = (rate: Data["reference"]["currencies"][number]) =>
    setForm({
      title: `Update ${rate.currency} rate`,
      description:
        "The new rate affects future conversions. Existing opportunities keep their stored rate.",
      fields: [
        field("rate", `1 ${rate.currency} in USD`, {
          type: "number",
          value: rate.rate,
        }),
        field("source", "Rate source", { value: rate.source }),
      ],
      submit: (values) => api(`admin/rates/${rate.id}/`, "PATCH", values),
      label: "Save rate",
    });
  const matches = (value: string) =>
    value.toLowerCase().includes(query.toLowerCase());
  const filtered = (records: Pursuit[]) =>
    records.filter(
      (r) =>
        matches(`${r.name} ${r.company} ${r.owner} ${r.next_action}`) &&
        (ownerFilter === "all" || r.owner_id === Number(ownerFilter)),
    );
  function newLead() {
    setForm({
      title: "Create a lead",
      description:
        "Start a conversation. Lead volume stays separate from your commercial pipeline.",
      label: "Create lead",
      fields: [
        field("name", "Lead name"),
        field("company", "Company", { options: companyOptions }),
        field("owner", "Commercial owner", {
          options: userOptions,
          value: String(d.user.id),
        }),
        field("holder", "Ball in Court", {
          options: userOptions,
          value: String(d.user.id),
        }),
        field("source_channel", "Source", {
          options: options(d.reference.sources),
          value: "LinkedIn",
        }),
        field("source_detail", "Source detail", { required: false }),
        field("area_of_interest", "Area of interest", {
          type: "textarea",
          required: false,
        }),
        field("next_action", "Next action"),
        field("action_type", "Action type", {
          options: options(d.reference.actions),
          value: "Call",
        }),
        field("action_date", "Due date", { type: "date", value: tomorrow() }),
      ],
      submit: (v) => api("leads/", "POST", v),
    });
  }
  function companyForm(c?: Company) {
    setForm({
      title: c ? "Edit company" : "Create a company",
      fields: [
        field("name", "Company name", { value: c?.name }),
        field("domain", "Domain", { value: c?.domain, required: false }),
        field("company_type", "Company type", {
          options: options([
            "Client",
            "Prospect",
            "Referral partner",
            "Reseller",
            "Local partner",
            "Prime contractor",
            "Subcontractor",
          ]),
          value: c?.company_type ?? "Prospect",
        }),
        field("industry", "Industry", { value: c?.industry, required: false }),
        field("country", "Country", { value: c?.country }),
        field("owner", "Relationship owner", {
          options: userOptions,
          value: String(c?.owner_id ?? d.user.id),
        }),
        field("global_account_name", "Global account name", {
          value: c?.global_account_name,
          required: false,
        }),
        field("primary_region", "Primary region", {
          value: c?.primary_region,
          required: false,
        }),
        ...(!c
          ? [
              field("duplicate_override", "Possible duplicate handling", {
                options: [
                  ["false", "Stop and show a warning"],
                  ["true", "Reviewed — create separate record"],
                ],
                value: "false",
                hint: "Choose the reviewed option only when a similar company is genuinely separate.",
              }),
            ]
          : []),
      ],
      submit: (v) =>
        api(`companies/${c ? c.id + "/" : ""}`, c ? "PATCH" : "POST", v),
    });
  }
  function contactForm(c?: Contact) {
    setForm({
      title: c ? "Edit contact" : "Add a contact",
      fields: [
        field("first_name", "First name", { value: c?.first_name }),
        field("last_name", "Last name", { value: c?.last_name }),
        field("company", "Company", {
          options: companyOptions,
          value: c?.company_id ?? companyId ?? "",
        }),
        field("job_title", "Job title", {
          value: c?.job_title,
          required: false,
        }),
        field("seniority", "Seniority", {
          options: options([
            "C-level",
            "VP or Head",
            "Director",
            "Manager",
            "Individual contributor",
            "Unknown",
          ]),
          value: c?.seniority ?? "Unknown",
        }),
        field("email", "Email", {
          type: "email",
          value: c?.email,
          required: false,
        }),
        field("phone", "Phone", { value: c?.phone, required: false }),
        field("mobile", "Mobile", { value: c?.mobile, required: false }),
        field("linkedin_url", "LinkedIn profile", {
          type: "url",
          value: c?.linkedin_url,
          required: false,
        }),
        field("country", "Country", { value: c?.country }),
        field("city", "City", { value: c?.city, required: false }),
        field("owner", "Relationship owner", {
          options: userOptions,
          value: String(c?.owner_id ?? d.user.id),
        }),
        field("sourced_by", "Sourced by", {
          options: userOptions,
          value: String(c?.sourced_by_id ?? d.user.id),
        }),
        field("source_channel", "Source", {
          options: options(d.reference.sources),
          value: c?.source_channel ?? "LinkedIn",
        }),
        field("source_detail", "Source detail", {
          value: c?.source_detail,
          required: false,
        }),
        field("consent_basis", "Contact obtained through", {
          options: options([
            "Business card or event",
            "Referral",
            "Public professional profile",
            "Inbound enquiry",
            "Existing client relationship",
          ]),
          value: c?.consent_basis ?? "Public professional profile",
        }),
        field("do_not_contact", "Outbound contact", {
          options: [
            ["false", "Allowed"],
            ["true", "Do not contact"],
          ],
          value: String(c?.do_not_contact ?? false),
        }),
        field("engagement_status", "Engagement status", {
          options: options([
            "Not contacted",
            "Contacted no response",
            "Engaged",
            "Meeting held",
            "Unresponsive",
            "Do not contact",
          ]),
          value: c?.engagement_status ?? "Not contacted",
        }),
        field("notes", "Relationship notes", {
          type: "textarea",
          value: c?.notes,
          required: false,
        }),
        ...(!c
          ? [
              field("duplicate_override", "Possible duplicate handling", {
                options: [
                  ["false", "Stop and show a warning"],
                  ["true", "Reviewed — create separate person"],
                ],
                value: "false",
                hint: "Exact email duplicates are always blocked.",
              }),
            ]
          : []),
      ],
      submit: (v) =>
        api(`contacts/${c ? c.id + "/" : ""}`, c ? "PATCH" : "POST", v),
    });
  }
  function workForm(r: Pursuit) {
    setForm({
      title: "Set the next move",
      description:
        "One person, one clear action. Existing overdue actions can remain unchanged.",
      fields: [
        field("holder", "Ball in Court", {
          options: userOptions,
          value: String(r.holder_id),
        }),
        field("next_action", "Next action", { value: r.next_action }),
        field("action_type", "Action type", {
          options: options(d.reference.actions),
          value: r.action_type,
        }),
        field("action_date", "Due date", {
          type: "date",
          value: r.action_date,
        }),
        field("blocker", "Current blocker", {
          options: options(d.reference.blockers),
          value: r.blocker,
        }),
        field("blocker_owner", "Blocker owner", {
          options: userOptions,
          value: r.blocker_owner_id ? String(r.blocker_owner_id) : "",
          required: false,
        }),
        field("resolution_action", "Resolution action", {
          value: r.resolution_action,
          required: false,
        }),
        field("next_meeting", "Next customer meeting", {
          type: "date",
          value: r.next_meeting ?? "",
          required: false,
        }),
        field("reason", "What changed?", { type: "textarea" }),
      ],
      submit: (v) =>
        api(`pursuits/${r.id}/`, "PATCH", {
          ...v,
          version: r.version,
          blocker_owner: v.blocker_owner || null,
          next_meeting: v.next_meeting || null,
        }),
    });
  }
  function activityForm(r?: Pursuit, c?: Contact) {
    const companyId = r?.company_id ?? c?.company_id;
    setForm({
      title: "Log an interaction",
      description:
        "Only client-facing activity updates the last client interaction date.",
      fields: [
        field("company", "Company", {
          options: companyOptions,
          value: companyId,
        }),
        field("contact", "Contact", {
          options: d.contacts
            .filter((x) => !companyId || x.company_id === companyId)
            .map((x) => [x.id, x.name]),
          value: c?.id ?? r?.primary_contact_id,
          required: false,
        }),
        field("activity_type", "Activity type", {
          options: options([
            "Call",
            "Email",
            "Meeting",
            "Demo",
            "Workshop",
            "LinkedIn message",
            "LinkedIn connection request",
            "WhatsApp",
            "Event conversation",
            "Internal note",
          ]),
          value: "Call",
        }),
        field("direction", "Direction", {
          options: options(["Outbound", "Inbound"]),
          value: "Outbound",
        }),
        field("activity_date", "Completed at", {
          type: "datetime-local",
          required: false,
          hint: "Leave blank to use the current time. Future dates are not accepted.",
        }),
        field("subject", "Subject"),
        field("outcome", "Outcome", {
          options: options([
            "No response",
            "Responded",
            "Meeting booked",
            "Referred onward",
            "Declined",
            "Not relevant",
          ]),
          value: "Responded",
        }),
        field("notes", "Notes", { type: "textarea", required: false }),
        field("override_reason", "Do-not-contact override reason", {
          required: false,
        }),
      ],
      notice: (values) => {
        const selectedContact = d.contacts.find(
          (item) => item.id === values.contact,
        );
        if (
          !selectedContact ||
          selectedContact.owner_id === d.user.id ||
          values.direction !== "Outbound" ||
          values.activity_type === "Internal note"
        )
          return "";
        const prior = selectedContact.last_outbound_at
          ? ` Last outbound touch: ${date(selectedContact.last_outbound_at)}${selectedContact.last_outbound_pursuit ? ` on ${selectedContact.last_outbound_pursuit}` : ""}.`
          : " No earlier outbound touch is recorded.";
        return `${selectedContact.owner} owns this relationship.${prior} You may continue; the owner will be notified.`;
      },
      submit: async (v) => {
        const result = await api<{ warning?: string }>("activities/", "POST", {
          ...v,
          contact: v.contact || null,
          pursuit: r?.id ?? null,
          activity_date: v.activity_date || null,
        });
        if (result.warning) setToast(result.warning);
        return result;
      },
    });
  }
  function convertForm(r: Pursuit) {
    setForm({
      title: "Validate & convert",
      description:
        "An independent Manager or Executive validates this lead. All existing history is preserved.",
      label: "Validate & convert",
      fields: [
        field("customer_need", "Customer need", {
          type: "textarea",
          value: r.area_of_interest,
        }),
        field("scope_summary", "Scope summary", { type: "textarea" }),
        field("primary_contact", "Primary contact", {
          options: d.contacts
            .filter((c) => c.company_id === r.company_id)
            .map((c) => [c.id, c.name]),
        }),
        field("current_value", "Initial estimate", { type: "number" }),
        ...(d.instance === "US"
          ? []
          : [
              field("currency", "Currency", {
                options: d.reference.currencies.map((x) => [
                  x.currency,
                  x.currency,
                ]),
                value: "USD",
              }),
            ]),
        field("service_line", "Service line", {
          options: options(d.reference.services),
        }),
        field("expected_close_date", "Expected signature date", {
          type: "date",
          value: tomorrow(),
        }),
      ],
      submit: async (v) => {
        await api(`leads/${r.lead_id}/convert/`, "POST", {
          ...v,
          currency: v.currency || "USD",
        });
        setDetailTab("Overview");
      },
    });
  }
  async function changeStage(r: Pursuit, target: string) {
    if (target === r.stage) return;
    let artifactWarning = "";
    if (target === "proposal") {
      try {
        const artifacts = await api<Timeline["artifacts"]>(`artifacts/?pursuit_id=${r.id}`);
        if (!artifacts.length) artifactWarning = "No artifact is registered on this pursuit yet. You may continue, then register what was sent in Documents.";
      } catch (reason) {
        setToast((reason as Error).message);
        return;
      }
    }
    const fields: Field[] = [
      field("reason", "Stage change evidence", {
        type: "textarea",
        hint: "Record the customer signal, decision, or evidence supporting this movement.",
      }),
    ];
    if (target === "hold")
      fields.push(
        field("revisit_date", "Revisit date", {
          type: "date",
          value: tomorrow(),
        }),
      );
    if (target === "lost")
      fields.push(
        field("loss_reason", "Loss reason", {
          options: options(d.reference.loss_reasons),
        }),
        field("competitor_name", "Competitor", { required: false }),
        field("competitor_status", "Competitor status", {
          options: options([
            "None known",
            "Incumbent",
            "Shortlisted alongside us",
            "Sole alternative",
          ]),
          value: "None known",
        }),
        field("close_notes", "Loss context and learning", {
          type: "textarea",
        }),
        field("revisit_date", "Optional revisit date", {
          type: "date",
          required: false,
        }),
      );
    if (target === "won")
      fields.push(
        field("contract_number", "Contract / PO number"),
        field("contract_date", "Contract date", {
          type: "date",
          value: d.today,
        }),
        field("final_value", "Final contract value", {
          type: "number",
          value: r.current_value,
        }),
        field("project_start", "Expected project start", {
          type: "date",
          value: tomorrow(),
        }),
        field("duration_months", "Expected duration (months)", {
          type: "number",
          value: "1",
        }),
        field("final_evidence_artifact_id", "Final contract evidence", {
          options: (timeline?.artifacts ?? [])
            .filter((artifact) =>
              ["Contract", "Purchase order", "SOW"].includes(artifact.artifact_type),
            )
            .map((artifact) => [
              artifact.id,
              `${artifact.title} · ${artifact.artifact_type}`,
            ]),
          hint: "Register a Contract, Purchase order or SOW in Documents first.",
        }),
        field("approval_recorded", "Commercial approval", {
          options: [
            ["false", "Not recorded"],
            ["true", "Recorded outside ATPLCRM"],
          ],
          value: String(r.approval_recorded ?? false),
        }),
        field("approval_note", "Approval evidence note", {
          type: "textarea",
          required: false,
          value: r.approval_note,
        }),
        field("handoff_notes", "Delivery handoff notes", {
          type: "textarea",
          required: false,
        }),
        field("close_notes", "Close notes", {
          type: "textarea",
          required: false,
        }),
      );
    setForm({
      title: `Move to ${dictLabel(d.reference.stages, target)}`,
      description:
        target === "won"
          ? "Register final contract, PO or SOW evidence before closing."
          : "The movement and its evidence will be retained in the audit timeline.",
      fields,
      notice: () => artifactWarning,
      submit: (v) =>
        api(`opportunities/${r.opportunity_id}/stage/`, "POST", {
          ...v,
          stage: target,
          version: r.version,
        }),
    });
  }
  function completeAction(r: Pursuit) {
    setForm({
      title: "Complete action and set the next step",
      description:
        "The completed action is preserved as history. A future next action keeps ownership clear.",
      fields: [
        field("outcome", "Outcome"),
        field("note", "Completion note", { type: "textarea", required: false }),
        field("next_holder", "New Ball in Court holder", {
          options: d.users.map((u) => [String(u.id), u.name]),
          value: String(r.holder_id),
        }),
        field("next_action", "Next action"),
        field("next_action_type", "Action type", {
          options: options(d.reference.actions),
          value: r.action_type,
        }),
        field("next_action_date", "Next action date", {
          type: "date",
          value: tomorrow(),
        }),
      ],
      label: "Complete action",
      submit: (v) =>
        api(`pipeline/pursuits/${r.id}/actions/complete/`, "POST", {
          ...v,
          version: r.version,
        }),
    });
  }
  function notificationPreferenceForm() {
    const prefs = notificationPreferences;
    if (!prefs) return;
    const enabled = (value: boolean): [string, string][] => [
      ["true", "Enabled"],
      ["false", "Muted"],
    ];
    setForm({
      title: "Notification preferences",
      description:
        "Choose which exception alerts you receive. Critical records remain visible in My Work and Needs Attention.",
      fields: [
        ...[
          ["due_actions", "Due and overdue actions"],
          ["stalled_pursuits", "Ball in Court held over 14 days"],
          ["blockers", "Blockers unresolved over 10 days"],
          ["inactivity", "Client inactivity"],
          ["proposal_followup", "Proposal follow-up"],
          ["validation", "Validation ageing"],
          ["presales", "Pre-sales deadlines"],
          ["close_dates", "Expected close dates"],
          ["revisits", "Nurture and on-hold revisits"],
          ["system_failures", "Automation failures"],
          ["weekly_summary", "Monday leadership summary"],
        ].map(([name, label]) =>
          field(name, label, {
            options: enabled(
              prefs[name as keyof NotificationPreference] as boolean,
            ),
            value: String(prefs[name as keyof NotificationPreference]),
          }),
        ),
        field("inactivity_days", "Client inactivity threshold (days)", {
          type: "number",
          value: String(prefs.inactivity_days),
        }),
        field("proposal_followup_days", "Proposal follow-up threshold (days)", {
          type: "number",
          value: String(prefs.proposal_followup_days),
        }),
        field("close_notice_days", "Close-date warning window (days)", {
          type: "number",
          value: String(prefs.close_notice_days),
        }),
      ],
      submit: (values) => api("notifications/preferences/", "PATCH", values),
    });
  }
  function requestForm() {
    const canAssign =
      ["Executive", "Administrator"].includes(d.user.level) ||
      d.user.job_title
        .toLowerCase()
        .replaceAll("-", " ")
        .includes("head of pre sales") ||
      d.user.job_title.toLowerCase().includes("head of presales");
    setForm({
      title: "Request pre-sales work",
      description: canAssign
        ? "Create the brief and optionally assign its tech lead."
        : "Create the brief; the Head of Pre-Sales will assign its tech lead.",
      fields: [
        field("opportunity", "Opportunity", {
          options: d.opportunities.map((o) => [o.opportunity_id!, o.name]),
        }),
        field("title", "Deliverable title"),
        field("request_type", "Request type", {
          options: options([
            "Deck",
            "Demo",
            "Proof of concept",
            "Technical solution design",
            "Effort estimate",
            "Case study pack",
            "Reference call",
            "RFP or tender response",
            "Proposal section",
            "Video",
            "Other",
          ]),
          value: "Deck",
        }),
        ...(canAssign
          ? [
              field("assigned_to", "Tech lead", {
                options: userOptions,
                required: false,
              }),
            ]
          : []),
        field("needed_by", "Needed by", { type: "date", value: tomorrow() }),
        field("customer_meeting_date", "Customer meeting date", {
          type: "date",
          required: false,
        }),
        field("estimated_days", "Estimated days", {
          type: "number",
          value: "1",
        }),
        field("notes", "Brief", { type: "textarea", required: false }),
      ],
      submit: (v) =>
        api("requests/", "POST", {
          ...v,
          assigned_to: v.assigned_to ? Number(v.assigned_to) : null,
          customer_meeting_date: v.customer_meeting_date || null,
        }),
    });
  }
  async function updateRequest(r: Request) {
    try {
      const [current, requestTimeline] = await Promise.all([
        api<Request>(`requests/${r.id}/`),
        api<Timeline>(`pursuits/${r.pursuit_id}/timeline/`),
      ]);
      const availableStatuses = [
        current.status,
        ...(current.allowed_transitions ?? []),
      ].filter((value, index, values) => values.indexOf(value) === index);
      setForm({
        title: "Update pre-sales deliverable",
        description: `${current.title} · requested by ${current.requested_by}`,
        fields: [
          ...(current.can_assign
            ? [
                field("assigned_to", "Assigned tech lead", {
                  options: userOptions,
                  value: current.assigned_to_id
                    ? String(current.assigned_to_id)
                    : "",
                  required: false,
                }),
              ]
            : []),
          ...(current.can_add_contributors
            ? [
                field("supporting_contributor_ids", "Supporting contributors", {
                  options: userOptions.filter(
                    ([id]) => Number(id) !== current.assigned_to_id,
                  ),
                  value: current.contributors
                    .map((person) => person.id)
                    .join(","),
                  required: false,
                  multiple: true,
                  hint: "The assigned tech lead controls this supporting team.",
                }),
              ]
            : []),
          field("status", "Status", {
            options: options(availableStatuses),
            value: current.status,
          }),
          ...(current.can_edit_brief
            ? [
                field("needed_by", "Needed by", {
                  type: "date",
                  value: current.needed_by,
                }),
                field("customer_meeting_date", "Customer meeting date", {
                  type: "date",
                  required: false,
                  value: current.customer_meeting_date ?? "",
                }),
                field("estimated_days", "Estimated days", {
                  type: "number",
                  value: current.estimated_days,
                }),
                field("deliverable_artifact_id", "Deliverable evidence", {
                  options: requestTimeline.artifacts.map((artifact) => [
                    artifact.id,
                    `${artifact.title} · v${artifact.version}${artifact.internal_only ? " · internal only" : ""}`,
                  ]),
                  value: current.deliverable_artifact_id ?? "",
                  required: false,
                  hint: "Evidence is required before Ready for review and must be client-shareable before approval.",
                }),
                field("review_note", "Review / approval evidence", {
                  type: "textarea",
                  required: false,
                  value: current.review_note,
                }),
                field("actual_days", "Actual days", {
                  type: "number",
                  required: false,
                  value: current.actual_days ?? "",
                  hint: "Required when the assigned tech lead marks the work Delivered.",
                }),
                field("shared_with_contact_ids", "Delivered to", {
                  options: d.contacts
                    .filter((contact) => contact.company_id === d.opportunities.find((opportunity) => opportunity.opportunity_id === current.opportunity_id)?.company_id)
                    .map((contact) => [contact.id, `${contact.name} · ${contact.email}`]),
                  required: false,
                  multiple: true,
                  hint: "Required when marking Delivered; these contacts are written to the client-shared register.",
                }),
                field("blocked_reason", "Blocked reason", {
                  type: "textarea",
                  required: false,
                  value: current.blocked_reason,
                }),
                field("notes", "Brief / notes", {
                  type: "textarea",
                  required: false,
                  value: current.notes,
                }),
              ]
            : []),
        ],
        submit: (v) =>
          api(`requests/${current.id}/`, "PATCH", {
            ...v,
            version: current.version,
            assigned_to:
              "assigned_to" in v && v.assigned_to
                ? Number(v.assigned_to)
                : undefined,
            supporting_contributor_ids:
              "supporting_contributor_ids" in v
                ? v.supporting_contributor_ids
                    .split(",")
                    .filter(Boolean)
                    .map(Number)
                : undefined,
            shared_with_contact_ids:
              "shared_with_contact_ids" in v
                ? v.shared_with_contact_ids.split(",").filter(Boolean)
                : undefined,
            ...("deliverable_artifact_id" in v
              ? { deliverable_artifact_id: v.deliverable_artifact_id || null }
              : {}),
            ...("customer_meeting_date" in v
              ? { customer_meeting_date: v.customer_meeting_date || null }
              : {}),
            ...("actual_days" in v
              ? { actual_days: v.actual_days || null }
              : {}),
          }),
        label: "Save request",
      });
    } catch (e) {
      setToast((e as Error).message);
    }
  }
  function recordValue(r: Pursuit) {
    setForm({
      title: "Record a new value",
      description:
        "Previous values are preserved. The opportunity’s currency and fixed exchange rate apply.",
      fields: [
        field("amount", `Amount (${r.currency})`, {
          type: "number",
          value: r.current_value,
        }),
        field("value_type", "Value type", {
          options: options([
            "Initial estimate",
            "Proposal value",
            "Revised proposal",
            "Negotiated value",
            "Final contract value",
          ]),
          value: "Revised proposal",
        }),
        field("note", "Reason for change", {
          type: "textarea",
          required: false,
        }),
      ],
      submit: (v) => api(`opportunities/${r.opportunity_id}/value/`, "POST", v),
    });
  }
  function opportunityRateForm(r: Pursuit) {
    setForm({
      title: `Update ${r.currency} exchange rate`,
      description:
        "This changes only this opportunity. The previous rate remains in value and audit history.",
      fields: [
        field("rate", `1 ${r.currency} in USD`, {
          type: "number",
          value: r.fx_rate,
        }),
        field("reason", "Reason for changing this opportunity", {
          type: "textarea",
        }),
      ],
      submit: (v) => api(`opportunities/${r.opportunity_id}/rate/`, "POST", v),
      label: "Update stored rate",
    });
  }
  function commercialDetailsForm(r: Pursuit) {
    setForm({
      title: "Commercial assumptions and approval",
      description:
        "Gross margin is required only for partner terms based on gross margin. Approval is recorded as evidence and does not gate stage movement.",
      fields: [
        field("gross_margin_pct", "Expected gross margin (%)", {
          type: "number",
          value: r.gross_margin_pct ?? "",
          required: false,
        }),
        field("approval_recorded", "Commercial approval", {
          options: [
            ["false", "Not recorded"],
            ["true", "Recorded outside ATPLCRM"],
          ],
          value: String(r.approval_recorded ?? false),
        }),
        field("approval_note", "Approval note or linked-email reference", {
          type: "textarea",
          required: false,
          value: r.approval_note,
        }),
      ],
      submit: (v) =>
        api(`opportunities/${r.opportunity_id}/commercial/`, "PATCH", {
          ...v,
          gross_margin_pct: v.gross_margin_pct || null,
        }),
    });
  }
  function partnerForm(r: Pursuit, partner?: Partner) {
    const partnerCompanies = d.companies.filter((company) =>
      [
        "Referral partner",
        "Reseller",
        "Local partner",
        "Prime contractor",
        "Subcontractor",
      ].includes(company.company_type),
    );
    setForm({
      title: partner ? `Edit ${partner.company}` : "Add partner involvement",
      description:
        "Percentages always mean the share the partner takes. Fixed fees are entered in the opportunity currency.",
      fields: [
        field("company_id", "Partner company", {
          options: partnerCompanies.map((company) => [
            company.id,
            company.name,
          ]),
          value: partner?.company_id,
        }),
        field("contact_id", "Partner contact", {
          options: d.contacts
            .filter((contact) =>
              partnerCompanies.some(
                (company) => company.id === contact.company_id,
              ),
            )
            .map((contact) => [
              contact.id,
              `${contact.name} · ${contact.company}`,
            ]),
          value: partner?.contact_id,
          hint: "The selected contact must belong to the selected partner company.",
        }),
        field("role", "Partner role", {
          options: options([
            "Referral source",
            "Reseller",
            "Local partner",
            "Prime contractor",
            "Delivery subcontractor",
            "Introducer",
            "Joint bid partner",
          ]),
          value: partner?.role ?? "Referral source",
        }),
        field("introduced", "Introduced this opportunity", {
          options: [
            ["false", "No"],
            ["true", "Yes"],
          ],
          value: String(partner?.introduced ?? false),
        }),
        field("fee_basis", "Fee basis", {
          options: options([
            "Percentage of contract value",
            "Percentage of gross margin",
            "Fixed fee",
            "Commission",
            "Rate card spread",
            "To be agreed",
          ]),
          value: partner?.fee_basis ?? "To be agreed",
        }),
        field("share_pct", "Partner share taken (%)", {
          type: "number",
          value: partner?.share_pct ?? "0",
        }),
        field("fixed_fee", `Fixed fee / spread (${r.currency})`, {
          type: "number",
          value: partner?.fixed_fee ?? "0",
        }),
        field("applies_to", "Terms apply to", {
          options: options([
            "This contract only",
            "All revenue from this client for a fixed period",
            "All revenue from this client indefinitely",
          ]),
          value: partner?.applies_to ?? "This contract only",
        }),
        field("duration_months", "Duration in months", {
          type: "number",
          required: false,
          value: partner?.duration_months?.toString() ?? "",
        }),
        field("status", "Agreement status", {
          options: options([
            "Proposed",
            "Verbally agreed",
            "Documented in writing",
            "Lapsed or superseded",
          ]),
          value: partner?.status ?? "Proposed",
        }),
        field("agreement_artifact_id", "Agreement evidence", {
          required: false,
          options: [
            ["", "No linked evidence"],
            ...(timeline?.artifacts ?? []).map(
              (artifact) =>
                [artifact.id, `${artifact.title} · v${artifact.version}`] as [
                  string,
                  string,
                ],
            ),
          ],
          value: partner?.agreement_artifact_id ?? "",
        }),
        field("terms_notes", "Terms notes", {
          type: "textarea",
          required: false,
          value: partner?.terms_notes,
        }),
      ],
      submit: (v) =>
        api(
          partner
            ? `partners/${partner.id}/`
            : `opportunities/${r.opportunity_id}/partners/`,
          partner ? "PATCH" : "POST",
          {
            ...v,
            duration_months: v.duration_months || null,
            agreement_artifact_id: v.agreement_artifact_id || null,
          },
        ),
      label: partner ? "Save partner terms" : "Add partner",
    });
  }
  function commercialSettingsForm() {
    setForm({
      title: "Commercial warning thresholds",
      fields: [
        field("partner_share_warning_pct", "Partner share warning (%)", {
          type: "number",
          value: d.commercial_settings.partner_share_warning_pct,
        }),
        field("fx_movement_notice_pct", "FX movement notice (%)", {
          type: "number",
          value: d.commercial_settings.fx_movement_notice_pct,
        }),
      ],
      submit: (v) => api("commercial/settings/", "PATCH", v),
    });
  }
  function workingCalendarForm() {
    setForm({
      title: "Working calendar",
      description:
        "Milestone timing and validation alerts use these workdays and holidays.",
      fields: [
        field("working_weekdays", "Working week", {
          options: [
            ["0,1,2,3,4", "Monday to Friday"],
            ["6,0,1,2,3", "Sunday to Thursday"],
            ["0,1,2,3,4,5", "Monday to Saturday"],
            ["0,1,2,3,4,5,6", "Every day"],
          ],
          value: d.working_calendar.working_weekdays.join(","),
        }),
        field("holidays", "Holidays (YYYY-MM-DD, comma separated)", {
          required: false,
          value: d.working_calendar.holidays.join(", "),
          hint: "These dates are excluded from working-day measurements.",
        }),
      ],
      submit: (v) =>
        api("admin/working-calendar/", "PATCH", {
          working_weekdays: v.working_weekdays.split(",").map(Number),
          holidays: v.holidays
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      label: "Save calendar",
    });
  }
  function opportunityForm(r: Pursuit) {
    setForm({
      title: "Edit opportunity",
      description:
        "Update the qualified need, scope, primary contact and delivery details.",
      fields: [
        field("name", "Opportunity name", { value: r.name }),
        field("opportunity_type", "Opportunity type", {
          options: options([
            "New logo",
            "Expansion at existing client",
            "Renewal or extension",
          ]),
          value: r.opportunity_type,
        }),
        field("customer_need", "Customer need", {
          type: "textarea",
          value: r.customer_need,
        }),
        field("scope_summary", "Scope summary", {
          type: "textarea",
          value: r.scope_summary,
        }),
        field("primary_contact", "Primary contact", {
          options: d.contacts
            .filter((contact) => contact.company_id === r.company_id)
            .map((contact) => [contact.id, contact.name]),
          value: r.primary_contact_id,
        }),
        field("service_line", "Service line", {
          options: options(d.reference.services),
          value: r.service_line,
        }),
        field("engagement_type", "Engagement type", {
          options: options([
            "Fixed price",
            "Time and materials",
            "Retainer or AMC",
            "Licence plus services",
            "Milestone",
          ]),
          value: r.engagement_type,
        }),
        field("expected_close_date", "Expected signature date", {
          type: "date",
          value: r.expected_close_date,
        }),
        field("priority", "Priority", {
          options: options(["High", "Medium", "Low"]),
          value: r.priority,
        }),
        field("reason", "Reason for update", { type: "textarea" }),
      ],
      submit: (v) =>
        api(`opportunities/${r.opportunity_id}/`, "PATCH", {
          ...v,
          version: r.version,
        }),
      label: "Save opportunity",
    });
  }
  function rebaselineOpenRates() {
    const candidates = d.opportunities.filter(
      (opportunity) =>
        !["won", "lost"].includes(opportunity.stage ?? "") &&
        opportunity.values_visible,
    );
    setForm({
      title: "Re-baseline open opportunities",
      description: `Apply current reference rates to ${candidates.length} visible open opportunities. Closed opportunities and restricted records you cannot see are excluded.`,
      fields: [
        field("confirmation", "Type REBASELINE to confirm", {
          value: "",
        }),
        field("reason", "Reason", { type: "textarea" }),
      ],
      submit: (v) =>
        api("commercial/rates/rebaseline/", "POST", {
          ...v,
          opportunity_ids: candidates.map((item) => item.opportunity_id),
        }),
      label: "Re-baseline selected set",
    });
  }
  function teamForm(r: Pursuit) {
    setForm({
      title: "Assign a pursuit role",
      fields: [
        field("user_id", "Team member", { options: userOptions }),
        field("role", "Role on this pursuit", {
          options: options([
            "Pre-sales owner",
            "Tech lead",
            "Supporting contributor",
          ]),
        }),
      ],
      submit: (v) => api(`opportunities/${r.opportunity_id}/team/`, "POST", v),
    });
  }
  function stakeholderForm(
    r: Pursuit,
    stakeholder?: Pursuit["contacts"][number],
  ) {
    setForm({
      title: stakeholder
        ? `Edit ${stakeholder.name}`
        : "Add client stakeholder",
      description:
        "Stakeholders must be contacts at this opportunity's client company.",
      fields: [
        ...(stakeholder
          ? []
          : [
              field("contact_id", "Contact", {
                options: d.contacts
                  .filter(
                    (contact) =>
                      contact.company_id === r.company_id &&
                      !r.contacts.some((item) => item.id === contact.id),
                  )
                  .map(
                    (contact) => [contact.id, contact.name] as [string, string],
                  ),
              }),
            ]),
        field("role", "Relationship role", {
          value: stakeholder?.role ?? "Influencer",
          options: options([
            "Champion",
            "Decision maker",
            "Influencer",
            "Procurement",
            "Technical",
            "Other",
          ]),
        }),
      ],
      submit: (values) =>
        api(
          stakeholder
            ? `productivity/stakeholders/${stakeholder.link_id}/`
            : `productivity/pursuits/${r.id}/stakeholders/`,
          stakeholder ? "PATCH" : "POST",
          values,
        ),
    });
  }
  async function loadMoreHistory() {
    if (
      !relationshipHistory ||
      relationshipHistory.page >= relationshipHistory.pages
    )
      return;
    const filter = contactId ? `contact=${contactId}` : `company=${companyId}`;
    try {
      const next = await api<ActivityPage>(
        `activities/?${filter}&page=${relationshipHistory.page + 1}&page_size=${relationshipHistory.page_size}`,
      );
      setRelationshipHistory({
        ...next,
        items: [...relationshipHistory.items, ...next.items],
      });
    } catch (e) {
      setToast((e as Error).message);
    }
  }
  const historyView = () => {
    if (!relationshipHistory)
      return (
        <div className="history-loading">
          <LoaderCircle className="spin" size={18} /> Loading complete history…
        </div>
      );
    if (!relationshipHistory.items.length)
      return (
        <Empty
          title="No interactions yet"
          text="Log the first email, call, meeting or internal note here."
        />
      );
    return (
      <>
        {relationshipHistory.items.map((a) => (
          <div className="timeline-item" key={a.id}>
            <span
              className={`timeline-dot ${a.is_client_facing ? "client" : "internal"}`}
            />
            <div>
              <small>
                {date(a.date)} · {a.activity_type} · {a.direction} · {a.author}
              </small>
              <h3>{a.subject}</h3>
              <p>
                {[a.contact, a.pursuit, a.outcome].filter(Boolean).join(" · ")}
              </p>
              {a.notes && <p>{a.notes}</p>}
              {a.override_reason && (
                <p className="override-note">Override: {a.override_reason}</p>
              )}
            </div>
          </div>
        ))}
        <div className="history-footer">
          <span>
            Showing {relationshipHistory.items.length} of{" "}
            {relationshipHistory.total} interactions
          </span>
          {relationshipHistory.page < relationshipHistory.pages && (
            <button
              className="button secondary"
              onClick={() => void loadMoreHistory()}
            >
              Load more
            </button>
          )}
        </div>
      </>
    );
  };
  const title =
    nav
      .map((g) => g.items.map(([key, label]) => ({ key, label })))
      .flat()
      .find((n) => n.key === page)?.label ?? "Overview";
  const table = (records: Pursuit[], limit?: number, showAll = false) => (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>OPPORTUNITY / LEAD</th>
            <th>STAGE</th>
            <th>BALL IN COURT</th>
            <th>NEXT ACTION</th>
            <th>DUE</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {(showAll ? records : filtered(records)).slice(0, limit).map((r) => (
            <tr key={r.id}>
              <td>
                <button className="record-name" onClick={() => openPursuit(r)}>
                  {r.name}
                </button>
                <small>{r.company}</small>
              </td>
              <td>
                <Badge
                  tone={
                    r.stage === "won"
                      ? "green"
                      : r.stage === "proposal"
                        ? "blue"
                        : "neutral"
                  }
                >
                  {r.stage
                    ? dictLabel(d.reference.stages, r.stage)
                    : dictLabel(d.reference.lead_statuses, r.status)}
                </Badge>
              </td>
              <td>
                <div className="person">
                  <Avatar name={r.holder} small />
                  <span>
                    {r.holder.split(" ")[0]}
                    <small>{r.days_held}d held</small>
                  </span>
                </div>
              </td>
              <td className="action-cell">{r.next_action}</td>
              <td>
                <span className={r.action_date < d.today ? "overdue" : "date"}>
                  {r.action_date < d.today && <span className="tiny-dot" />}
                  {date(r.action_date)}
                </span>
              </td>
              <td>
                <button
                  className="icon-button"
                  onClick={() => workForm(r)}
                  disabled={!r.can_work}
                  aria-label={`Update ${r.name}`}
                >
                  <ChevronRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!filtered(records).length && (
        <Empty title="All clear" text="No pursuits match this view." />
      )}
    </div>
  );
  const metric = (
    label: string,
    value: string,
    foot: string,
    icon: ReactNode,
    onClick: () => void,
    tone = "",
  ) => (
    <button className={`metric ${tone}`} onClick={onClick}>
      <div>
        <span>{label}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
      <small>
        {foot}
        <ArrowUpRight size={14} />
      </small>
    </button>
  );
  const pipelineChart = (
    <div className="stage-chart">
      {d.reference.stages
        .filter(([s]) => !["won", "lost", "hold"].includes(s))
        .map(([stage]) => {
          const rows = visibleOpps.filter((o) => o.stage === stage),
            value = rows.reduce((s, o) => s + Number(o.net_value_usd), 0);
          return (
            <button
              key={stage}
              className="chart-stage"
              onClick={() => {
                go("pipeline");
                setPipelineView("board");
              }}
            >
              <div className="chart-value">{money(value, "USD", true)}</div>
              <div className="bar-track">
                <div
                  className={`chart-bar stage-${stage}`}
                  style={{
                    height: `${Math.max(6, total ? (value / Math.max(...d.reference.stages.map(([s]) => visibleOpps.filter((o) => o.stage === s).reduce((n, o) => n + Number(o.net_value_usd), 0)))) * 125 : 0)}px`,
                  }}
                />
              </div>
              <span>{dictLabel(d.reference.stages, stage)}</span>
              <small>
                {rows.length} deal{rows.length !== 1 ? "s" : ""}
              </small>
            </button>
          );
        })}
    </div>
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className={`sidebar ${mobile ? "is-open" : ""}`}>
        <Brand />
        <div className="workspace-switch">
          <span className="workspace-icon">A</span>
          <div>
            ATPLCRM Demo
            <small>
              {d.instance === "US" ? "United States" : "International team"}
            </small>
          </div>
          <ChevronDown size={15} />
        </div>
        <nav aria-label="Main navigation">
          {nav.map((group) => (
            <div className="nav-group" key={group.group}>
              <span>{group.group}</span>
              {group.items.map(([key, label, Icon]) => (
                <button
                  key={key}
                  className={`nav-item ${page === key ? "active" : ""}`}
                  aria-current={page === key ? "page" : undefined}
                  onClick={() => go(key)}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                  {key === "attention" && attention.length > 0 && (
                    <b>{attention.length}</b>
                  )}
                  {key === "work" && held.length > 0 && <em>{held.length}</em>}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="workspace-health">
            <span className="live-dot" /> Local workspace <Badge>v0.15</Badge>
          </div>
          <button className="profile" onClick={() => go("settings")}>
            <Avatar name={d.user.name} />
            <span>
              {d.user.name}
              <small>{d.user.job_title}</small>
            </span>
            <ChevronDown size={14} />
          </button>
        </div>
      </aside>
      {mobile && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-toggle"
              onClick={() => setMobile(!mobile)}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-right">
            <label className="search">
              <Search size={16} />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search this view…"
                aria-label="Search this view"
              />
              {query && (
                <button
                  className="icon-button"
                  onClick={() => setQuery("")}
                  aria-label="Clear search"
                >
                  <X size={13} />
                </button>
              )}
            </label>
            <span className="instance">
              <Globe2 size={14} />
              {d.instance === "US" ? "US" : "International"}
            </span>
            <button
              className="icon-button notification-button"
              onClick={() => setNotifications(!notifications)}
              aria-label="Notifications"
            >
              <Bell size={19} />
              {d.notifications.some((n) => !n.read) && <i />}
            </button>
            <button
              className="icon-button"
              onClick={async () => {
                await api("session/", "DELETE");
                setSession(null);
                setData(null);
              }}
              aria-label="Sign out"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        {notifications && (
          <section className="notification-panel" aria-label="Notifications" aria-live="polite">
            <div className="panel-heading">
              <h3>Notifications</h3>
              <span className="notification-actions">
                <button
                  className="text-button"
                  onClick={notificationPreferenceForm}
                >
                  Preferences
                </button>
                <button
                  className="text-button"
                  onClick={() => mutate("notifications/read/", {})}
                >
                  Mark all read
                </button>
              </span>
            </div>
            {d.notifications.length ? (
              d.notifications.map((n) => (
                <button
                  key={n.id}
                  className={`notification-item ${n.read ? "read" : ""}`}
                  onClick={() => {
                    if (!n.read)
                      void api(`notifications/${n.id}/read/`, "POST", {}).then(
                        () => void load(),
                      );
                    if (n.pursuit_id) setSelected(n.pursuit_id);
                    setNotifications(false);
                  }}
                >
                  <Bell size={15} />
                  <span>
                    <Badge tone={n.severity === "high" ? "orange" : "neutral"}>
                      {n.category.replaceAll("_", " ")}
                    </Badge>
                    <strong>{n.message}</strong>
                    <small>{date(n.created_at)} · In-app delivered</small>
                  </span>
                </button>
              ))
            ) : (
              <Empty
                title="You’re up to date"
                text="Action and blocker reminders will appear here."
              />
            )}
          </section>
        )}
        <main id="main-content">
          {d.working_set.truncated && ["pipeline", "leads"].includes(page) && (
            <div className="working-set-notice" role="status">
              <Database size={17} />
              <span>
                This board shows the {d.working_set.pursuits} most recently updated pursuits. Use the complete list or global search to reach all {d.workspace_counts.pursuits} pursuits.
              </span>
            </div>
          )}
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {page === "overview"
                  ? "YOUR WORKSPACE, AT A GLANCE"
                  : page === "pipeline"
                    ? "FROM CONVERSATION TO CONTRACT"
                    : "ATPLCRM WORKSPACE"}
              </div>
              <h1>
                {page === "overview"
                  ? `Good ${new Date().getHours() < 12 ? "morning" : "afternoon"}, ${d.user.name.split(" ")[0]}`
                  : title}
                {page === "overview" && <span className="greeting-dot">.</span>}
              </h1>
              <p>
                {
                  (
                    {
                      overview:
                        "A clear view of your pipeline. A confident next move.",
                      work: "The actions, handoffs and blockers that need you.",
                      attention:
                        "Bring the right attention to the right pursuit.",
                      pipeline:
                        "Every opportunity. Every handoff. One shared view.",
                      leads:
                        "Build relationships before they become opportunities.",
                      companies:
                        "The organizations behind your next great partnership.",
                      contacts:
                        "A shared memory for every client relationship.",
                      documents:
                        "Register every file, link and email the client receives.",
                      presales:
                        "Purposeful deliverables. Clear ownership. On-time outcomes.",
                      reports: "Turn your pipeline into a clearer picture.",
                      data: "Search, import and improve the quality of your CRM data.",
                      settings:
                        "Your people, access and workspace configuration.",
                    } as Record<string, string>
                  )[page]
                }
              </p>
            </div>
            <div className="heading-actions">
              {d.instance !== "US" &&
                ["pipeline", "reports"].includes(page) && (
                  <button
                    className="button secondary"
                    onClick={() => setShowLocalCurrency((value) => !value)}
                  >
                    {showLocalCurrency
                      ? "Show reporting USD"
                      : "Show deal currencies"}
                  </button>
                )}
              {page === "overview" ? (
                <>
                  <span className="today">
                    <CalendarDays size={15} />
                    {new Intl.DateTimeFormat("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    }).format(new Date())}
                  </span>
                  <button className="button primary" onClick={newLead}>
                    <Plus size={17} />
                    New lead
                  </button>
                </>
              ) : ["data", "documents"].includes(page) ? null : (
                <button
                  className="button primary"
                  onClick={
                    page === "companies"
                      ? () => companyForm()
                      : page === "contacts"
                        ? () => contactForm()
                        : page === "presales"
                          ? requestForm
                          : page === "settings"
                            ? d.user.level === "Administrator"
                              ? () => adminUserForm()
                              : async () => {
                                  await api("session/", "DELETE");
                                  setSession(null);
                                  setData(null);
                                }
                            : newLead
                  }
                >
                  <Plus size={17} />
                  {page === "companies"
                    ? "Add company"
                    : page === "contacts"
                      ? "Add contact"
                      : page === "presales"
                        ? "Request work"
                        : page === "settings"
                          ? d.user.level === "Administrator"
                            ? "Add user"
                            : "Sign out"
                          : "New lead"}
                </button>
              )}
            </div>
          </div>
          <div className="demo-ribbon">
            <span>
              <span className="mini-dot" />
              LOCAL DEMO
            </span>{" "}
            Synthetic records · Changes persist in your local database{" "}
            <span className="ribbon-right">
              {d.instance === "US" ? "USD workspace" : "Reporting in USD"}
              <ShieldCheck size={13} />
            </span>
          </div>
          {error && (
            <div role="alert" className="error">
              {error}
              <button onClick={load}>Retry</button>
            </div>
          )}
          {page === "overview" && (
            <>
              {roleDashboard && (
                <section className="role-dashboard" aria-label={`${roleDashboard.role} dashboard`}>
                  <div>
                    <span>ROLE VIEW</span>
                    <strong>{roleDashboard.role}</strong>
                  </div>
                  {roleDashboard.cards.map((card) => (
                    <button
                      key={card.label}
                      onClick={() => {
                        const pursuit = card.record_ids.length === 1
                          ? [...d.opportunities, ...d.leads].find((row) => row.id === card.record_ids[0])
                          : undefined;
                        if (pursuit) openPursuit(pursuit); else go(card.route);
                      }}
                    >
                      <small>{card.label}</small>
                      <strong>{card.value}</strong>
                      <ChevronRight size={16} />
                    </button>
                  ))}
                </section>
              )}
              <div className="metrics">
                {metric(
                  "Open pipeline",
                  money(total, "USD", true),
                  `${openOpps.length} active opportunities`,
                  <Handshake size={18} />,
                  () => go("pipeline"),
                )}
                {metric(
                  "Weighted forecast",
                  money(weighted, "USD", true),
                  "Open pipeline · all close dates",
                  <TrendingUp size={18} />,
                  () => go("reports"),
                )}
                {metric(
                  "Active leads",
                  String(d.leads.filter((l) => l.status !== "closed").length),
                  "Relationships taking shape",
                  <Target size={18} />,
                  () => go("leads"),
                )}
                {metric(
                  "Needs attention",
                  String(attention.length),
                  "A clear next step makes a difference",
                  <AlertCircle size={18} />,
                  () => go("attention"),
                  "attention-metric",
                )}
              </div>
              <div className="overview-middle">
                <section className="panel pipeline-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Pipeline at a glance</h2>
                      <p>Net opportunity value by stage</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => go("pipeline")}
                    >
                      View pipeline <ArrowRight size={14} />
                    </button>
                  </div>
                  <div className="chart-summary">
                    <strong>{money(total)}</strong>
                    <span className="chart-legend">
                      <span />
                      Open pipeline · USD
                    </span>
                  </div>
                  {pipelineChart}
                </section>
                <section className="focus-panel">
                  <div className="focus-label">
                    <span className="focus-star">
                      <Sparkles size={17} />
                    </span>
                    YOUR FOCUS TODAY
                  </div>
                  <h2>
                    Keep the
                    <br />
                    conversation moving.
                  </h2>
                  <p>
                    {held.filter((x) => x.action_date <= d.today).length}{" "}
                    actions need your follow-through.
                    <br />
                    Small steps move great deals.
                  </p>
                  <div className="focus-stats">
                    <div>
                      <strong>
                        {held.filter((x) => x.action_date === d.today).length}
                      </strong>
                      <span>Due today</span>
                    </div>
                    <div>
                      <strong>
                        {held.filter((x) => x.action_date < d.today).length}
                      </strong>
                      <span>Overdue</span>
                    </div>
                    <div>
                      <strong>
                        {
                          active.filter((x) => x.blocker_owner_id === d.user.id)
                            .length
                        }
                      </strong>
                      <span>Your blockers</span>
                    </div>
                  </div>
                  <button className="button yellow" onClick={() => go("work")}>
                    Open my work <ArrowRight size={16} />
                  </button>
                  <div className="focus-decoration" />
                </section>
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>
                      Let’s move these forward{" "}
                      <Badge tone="orange">{attention.length} pursuits</Badge>
                    </h2>
                    <p>
                      Overdue actions, open blockers and quiet conversations.
                    </p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => go("attention")}
                  >
                    View all <ArrowRight size={14} />
                  </button>
                </div>
                {table(attention, 4)}
              </section>
              <div className="overview-bottom">
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Recent interactions</h2>
                      <p>The latest from your client conversations.</p>
                    </div>
                    <ActivityIcon size={18} />
                  </div>
                  <div className="activity-list">
                    {d.activities.slice(0, 3).map((a) => (
                      <div className="activity-row" key={a.id}>
                        <span className="activity-symbol">
                          <Handshake size={16} />
                        </span>
                        <div>
                          <strong>{a.subject}</strong>
                          <p>
                            {a.company} <span>· {a.author}</span>
                          </p>
                        </div>
                        <small>{date(a.date)}</small>
                      </div>
                    ))}
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Pre-sales in motion</h2>
                      <p>What the team is preparing next.</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => go("presales")}
                    >
                      View queue <ArrowRight size={14} />
                    </button>
                  </div>
                  {d.requests.slice(0, 3).map((r) => (
                    <button
                      className="request-mini"
                      key={r.id}
                      onClick={() => updateRequest(r)}
                    >
                      <span className="file-icon">
                        <FileText size={17} />
                      </span>
                      <span>
                        <strong>{r.title}</strong>
                        <small>
                          {r.assigned_to} · Due {date(r.needed_by)}
                        </small>
                      </span>
                      <Badge
                        tone={
                          r.status === "Ready for review" ? "yellow" : "blue"
                        }
                      >
                        {r.status}
                      </Badge>
                    </button>
                  ))}
                </section>
              </div>
            </>
          )}
          {(page === "work" || page === "attention") &&
            (workQueues ? (
              <>
                <div className="mini-stats">
                  <div>
                    <Clock3 size={20} />
                    <span>
                      <strong>
                        {workQueues.my_work.overdue_actions.length}
                      </strong>{" "}
                      Overdue actions
                    </span>
                  </div>
                  <div>
                    <CalendarDays size={20} />
                    <span>
                      <strong>{workQueues.my_work.today_actions.length}</strong>{" "}
                      Due today
                    </span>
                  </div>
                  <div>
                    <AlertCircle size={20} />
                    <span>
                      <strong>
                        {page === "work"
                          ? workQueues.my_work.blockers.length
                          : workQueues.needs_attention.length}
                      </strong>{" "}
                      {page === "work" ? "Blockers you own" : "Exceptions"}
                    </span>
                  </div>
                </div>
                {page === "work" ? (
                  <>
                    {[
                      ["Overdue actions", workQueues.my_work.overdue_actions],
                      ["Due today", workQueues.my_work.today_actions],
                      ["Upcoming actions", workQueues.my_work.upcoming_actions],
                    ].map(([label, rows]) => (
                      <section
                        className="panel work-section"
                        key={label as string}
                      >
                        <div className="panel-heading">
                          <h2>{label as string}</h2>
                          <Badge>{(rows as Pursuit[]).length}</Badge>
                        </div>
                        {(rows as Pursuit[]).length ? (
                          table(rows as Pursuit[])
                        ) : (
                          <Empty
                            title={`No ${(label as string).toLowerCase()}`}
                            text="Nothing requires action in this section."
                          />
                        )}
                      </section>
                    ))}
                    <div className="overview-bottom">
                      <section className="panel">
                        <div className="panel-heading">
                          <h2>Blockers you own</h2>
                          <Badge>{workQueues.my_work.blockers.length}</Badge>
                        </div>
                        {workQueues.my_work.blockers.map((record) => (
                          <button
                            className="blocker-item"
                            key={record.id}
                            onClick={() => openPursuit(record)}
                          >
                            <AlertCircle size={18} />
                            <span>
                              <strong>{record.blocker}</strong>
                              <small>
                                {record.name} · {record.resolution_action}
                              </small>
                            </span>
                          </button>
                        ))}
                        {!workQueues.my_work.blockers.length && (
                          <Empty
                            title="No blockers assigned"
                            text="You have no blockers to resolve right now."
                          />
                        )}
                      </section>
                      <section className="panel">
                        <div className="panel-heading">
                          <h2>Your deliverables</h2>
                          <Badge>
                            {workQueues.my_work.deliverables.length}
                          </Badge>
                        </div>
                        {workQueues.my_work.deliverables.map((request) => (
                          <button
                            className="request-mini"
                            key={request.id}
                            onClick={() => updateRequest(request)}
                          >
                            <FileText size={17} />
                            <span>
                              <strong>{request.title}</strong>
                              <small>Due {date(request.needed_by)}</small>
                            </span>
                            <Badge>{request.status}</Badge>
                          </button>
                        ))}
                        {!workQueues.my_work.deliverables.length && (
                          <Empty
                            title="No assigned deliverables"
                            text="Your next pre-sales request will appear here."
                          />
                        )}
                      </section>
                    </div>
                  </>
                ) : (
                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Needs Attention</h2>
                        <p>
                          Each exception remains visible until the underlying
                          record is corrected.
                        </p>
                      </div>
                      <Badge tone="orange">
                        {workQueues.needs_attention.length} exceptions
                      </Badge>
                    </div>
                    <div className="attention-list">
                      {workQueues.needs_attention.map((issue) => (
                        <button
                          key={issue.key}
                          onClick={() =>
                            issue.pursuit
                              ? openPursuit(issue.pursuit)
                              : issue.request && updateRequest(issue.request)
                          }
                        >
                          <span className={`severity ${issue.severity}`}>
                            {issue.severity}
                          </span>
                          <span>
                            <strong>{issue.label}</strong>
                            <small>
                              {issue.pursuit
                                ? `${issue.pursuit.name} · ${issue.pursuit.company}`
                                : `${issue.request?.title} · ${issue.request?.opportunity}`}
                            </small>
                          </span>
                          <ArrowRight size={15} />
                        </button>
                      ))}
                      {!workQueues.needs_attention.length && (
                        <Empty
                          title="Nothing needs attention"
                          text="There are no active exceptions in this workspace."
                        />
                      )}
                    </div>
                  </section>
                )}
              </>
            ) : (
              <LoaderCircle className="spin" />
            ))}
          {(page === "pipeline" || page === "leads") && (
            <>
              <div className="view-toolbar">
                <div className="segmented">
                  <button
                    className={pipelineView === "board" ? "selected" : ""}
                    onClick={() => setPipelineView("board")}
                  >
                    <KanbanSquare size={15} />
                    Board
                  </button>
                  <button
                    className={pipelineView === "list" ? "selected" : ""}
                    onClick={() => setPipelineView("list")}
                  >
                    <ListTodo size={15} />
                    List
                  </button>
                </div>
                <div className="filters">
                  <label>
                    <Users size={15} />
                    <select
                      aria-label="Filter by owner"
                      value={ownerFilter}
                      onChange={(e) => setOwnerFilter(e.target.value)}
                    >
                      <option value="all">All owners</option>
                      {userOptions.map(([id, name]) => (
                        <option key={id} value={id}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <span>
                    {
                      filtered(page === "pipeline" ? d.opportunities : d.leads)
                        .length
                    }{" "}
                    {page === "pipeline" ? "opportunities" : "leads"}
                  </span>
                </div>
              </div>
              {pipelineView === "list" ? (
                <RecordList
                  entity={page === "pipeline" ? "opportunities" : "leads"}
                  data={d}
                  notify={setToast}
                  onChanged={() => void load()}
                  onOpen={(item) => openPursuit(item as Pursuit)}
                />
              ) : (
                <div className="kanban">
                  {(page === "pipeline"
                    ? d.reference.stages
                    : d.reference.lead_statuses
                  ).map(([key, label]) => {
                    const rows = filtered(
                      page === "pipeline" ? d.opportunities : d.leads,
                    ).filter(
                      (r) => (page === "pipeline" ? r.stage : r.status) === key,
                    );
                    return (
                      <section
                        className={`kanban-column ${draggedPursuit && page === "pipeline" && draggedPursuit.stage !== key ? "drop-ready" : ""}`}
                        key={key}
                        data-stage={key}
                        onDragOver={(event) => {
                          if (page === "pipeline" && draggedPursuit?.can_work)
                            event.preventDefault();
                        }}
                        onDrop={(event) => {
                          event.preventDefault();
                          const pursuitId = event.dataTransfer.getData(
                            "application/x-atplcrm-pursuit",
                          );
                          const droppedPursuit = d.opportunities.find(
                            (item) => item.id === pursuitId,
                          );
                          if (page === "pipeline" && droppedPursuit?.can_work)
                            changeStage(droppedPursuit, key);
                          setDraggedPursuit(null);
                        }}
                      >
                        <div className="kanban-heading">
                          <span className={`stage-dot stage-${key}`} />
                          <strong>
                            {page === "pipeline"
                              ? dictLabel(d.reference.stages, key)
                              : label}
                          </strong>
                          <span className="count">{rows.length}</span>
                        </div>
                        {page === "pipeline" && (
                          <small className="column-value">
                            {money(
                              rows
                                .filter((r) => r.values_visible)
                                .reduce(
                                  (s, r) => s + Number(r.net_value_usd ?? 0),
                                  0,
                                ),
                            )}{" "}
                            ·{" "}
                            {key === "hold"
                              ? "Excluded"
                              : `${d.reference.probabilities[key]}% probability`}
                          </small>
                        )}
                        <div className="kanban-cards">
                          {rows.map((r) => (
                            <button
                              className={`deal-card ${draggedPursuit?.id === r.id ? "dragging" : ""}`}
                              key={r.id}
                              draggable={page === "pipeline" && r.can_work}
                              data-pursuit-id={r.id}
                              aria-label={`${r.name} · ${page === "pipeline" && r.can_work ? "Drag to move stage or open details" : "Open details"}`}
                              onDragStart={(event) => {
                                event.dataTransfer.effectAllowed = "move";
                                event.dataTransfer.setData(
                                  "application/x-atplcrm-pursuit",
                                  r.id,
                                );
                                setDraggedPursuit(r);
                              }}
                              onDragEnd={() => setDraggedPursuit(null)}
                              onClick={() => openPursuit(r)}
                            >
                              <div className="card-company">
                                <span>{r.company}</span>
                                <MoreHorizontal size={16} />
                              </div>
                              <h3>{r.name}</h3>
                              {page === "pipeline" ? (
                                <strong className="card-value">
                                  {showLocalCurrency
                                    ? money(r.net_value_local, r.currency)
                                    : money(r.net_value_usd)}
                                  <small>
                                    net {showLocalCurrency ? r.currency : "USD"}
                                  </small>
                                </strong>
                              ) : (
                                <Badge>{r.source_channel}</Badge>
                              )}
                              <div className="card-divider" />
                              <div className="card-next">
                                <ArrowRight size={14} />
                                <span>{r.next_action}</span>
                              </div>
                              <div className="card-bottom">
                                <div className="person">
                                  <Avatar name={r.holder} small />
                                  <span>{r.holder.split(" ")[0]}</span>
                                </div>
                                <span
                                  className={
                                    r.action_date < d.today ? "overdue" : "date"
                                  }
                                >
                                  <Clock3 size={12} />
                                  {date(r.action_date)}
                                </span>
                              </div>
                              {r.flags.length > 0 && (
                                <div className="card-warning">
                                  <AlertCircle size={12} />
                                  {r.flags[0]}
                                  {r.flags.length > 1 &&
                                    ` +${r.flags.length - 1}`}
                                </div>
                              )}
                              {r.outcome && (
                                <Badge tone="green">{r.outcome}</Badge>
                              )}
                            </button>
                          ))}
                          {!rows.length && (
                            <div className="column-empty">
                              No pursuits in this stage
                            </div>
                          )}
                        </div>
                      </section>
                    );
                  })}
                </div>
              )}
            </>
          )}
          {page === "companies" && (
            <RecordList
              entity="companies"
              data={d}
              notify={setToast}
              onChanged={() => void load()}
              onOpen={(item) => setCompanyId((item as Company).id)}
            />
          )}
          {page === "contacts" && (
            <RecordList
              entity="contacts"
              data={d}
              notify={setToast}
              onChanged={() => void load()}
              onOpen={(item) => setContactId((item as Contact).id)}
            />
          )}
          {page === "documents" && (
            <DocumentCenter data={d} onChanged={() => void load()} />
          )}
          {page === "presales" && (
            <>
              <div className="mini-stats">
                <div>
                  <Layers3 size={20} />
                  <span>
                    <strong>
                      {
                        d.requests.filter(
                          (r) => !["Delivered", "Cancelled"].includes(r.status),
                        ).length
                      }
                    </strong>{" "}
                    Open requests
                  </span>
                </div>
                <div>
                  <CheckCheck size={20} />
                  <span>
                    <strong>
                      {
                        d.requests.filter(
                          (r) => r.status === "Ready for review",
                        ).length
                      }
                    </strong>{" "}
                    Ready for review
                  </span>
                </div>
                <div>
                  <Clock3 size={20} />
                  <span>
                    <strong>
                      {
                        d.requests.filter(
                          (r) =>
                            r.needed_by < d.today &&
                            !["Delivered", "Cancelled"].includes(r.status),
                        ).length
                      }
                    </strong>{" "}
                    Past due
                  </span>
                </div>
              </div>
              <section className="panel presales-capacity-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Weekly team load</h2>
                    <p>
                      Assigned estimates by needed-by week, with supporting
                      commitments.
                    </p>
                  </div>
                  <label className="inline-filter">
                    Week of
                    <input
                      type="date"
                      value={presalesWeek}
                      onChange={(event) => setPresalesWeek(event.target.value)}
                    />
                  </label>
                </div>
                <div className="capacity-grid">
                  {presalesQueue?.team_load.map((person) => (
                    <div
                      className={
                        person.over_capacity
                          ? "capacity-card over"
                          : "capacity-card"
                      }
                      key={person.user_id}
                    >
                      <span>
                        <Avatar name={person.name} small />
                        <strong>{person.name}</strong>
                      </span>
                      <small>{person.job_title}</small>
                      <div>
                        <i
                          style={{
                            width: `${Math.min(100, Number(person.utilization_pct ?? 0))}%`,
                          }}
                        />
                      </div>
                      <strong>
                        {person.assigned_days} / {person.capacity_days} days
                      </strong>
                      <small>
                        {person.request_count} owned ·{" "}
                        {person.supporting_requests} supporting
                      </small>
                      {person.over_capacity && (
                        <Badge tone="orange">Over capacity</Badge>
                      )}
                    </div>
                  ))}
                  {presalesQueue && !presalesQueue.team_load.length && (
                    <Empty
                      title="No team load this week"
                      text="Assign a request with a needed-by date in this week."
                    />
                  )}
                </div>
              </section>
              <section className="panel">
                <div className="presales-filter-bar">
                  <label>
                    Assigned to
                    <select
                      value={presalesOwner}
                      onChange={(event) => setPresalesOwner(event.target.value)}
                    >
                      <option value="">All owners</option>
                      {d.users.map((person) => (
                        <option key={person.id} value={person.id}>
                          {person.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Status
                    <select
                      value={presalesStatus}
                      onChange={(event) =>
                        setPresalesStatus(event.target.value)
                      }
                    >
                      <option value="open">All open</option>
                      <option value="all">All including closed</option>
                      {d.reference.request_statuses.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <span>
                    {presalesQueue?.requests.length ?? 0} matching requests
                  </span>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>DELIVERABLE</th>
                        <th>OPPORTUNITY</th>
                        <th>TECH LEAD / CONTRIBUTORS</th>
                        <th>STATUS</th>
                        <th>NEEDED BY</th>
                        <th>EFFORT</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(presalesQueue?.requests ?? [])
                        .filter((r) =>
                          matches(
                            `${r.title} ${r.opportunity} ${r.assigned_to}`,
                          ),
                        )
                        .map((r) => (
                          <tr key={r.id}>
                            <td>
                              <button
                                className="record-name"
                                onClick={() => void updateRequest(r)}
                              >
                                {r.title}
                              </button>
                              <small>
                                {r.request_type} · requested by {r.requested_by}
                              </small>
                              {r.deliverable_artifact && (
                                <small>
                                  <FileText size={12} />{" "}
                                  {r.deliverable_artifact}
                                </small>
                              )}
                            </td>
                            <td>{r.opportunity}</td>
                            <td>
                              <div className="person">
                                <Avatar small name={r.assigned_to} />
                                {r.assigned_to}
                              </div>
                              <small>
                                {r.contributors.length
                                  ? r.contributors
                                      .map((person) => person.name)
                                      .join(", ")
                                  : "No supporting contributors"}
                              </small>
                            </td>
                            <td>
                              <Badge
                                tone={
                                  r.status === "Ready for review"
                                    ? "yellow"
                                    : r.status === "Blocked"
                                      ? "orange"
                                      : r.status === "Delivered"
                                        ? "green"
                                        : "blue"
                                }
                              >
                                {r.status}
                              </Badge>
                              {r.approved_by && (
                                <small>Approved by {r.approved_by}</small>
                              )}
                            </td>
                            <td
                              className={
                                r.needed_by < d.today &&
                                !["Delivered", "Cancelled"].includes(r.status)
                                  ? "overdue"
                                  : ""
                              }
                            >
                              {date(r.needed_by)}
                              <small>
                                Meeting {date(r.customer_meeting_date)}
                              </small>
                            </td>
                            <td>
                              {r.actual_days ?? r.estimated_days} days
                              <small>
                                {r.actual_days ? "Actual" : "Estimated"}
                              </small>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
                {presalesQueue && !presalesQueue.requests.length && (
                  <Empty
                    title="No matching requests"
                    text="Change the owner or status filter, or create a request."
                  />
                )}
              </section>
            </>
          )}
          {page === "reports" && (
            <>
              <ReportsCenter data={d} onOpen={openPursuit} />
              {["Administrator", "Manager", "Executive"].includes(
                d.user.level,
              ) &&
                presalesCost && (
                  <section className="panel presales-cost-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Cost of pre-sales</h2>
                        <p>
                          Actual delivery days grouped by work type, service
                          line and opportunity outcome.
                        </p>
                      </div>
                      <Badge>{presalesCost.actual_days} actual days</Badge>
                    </div>
                    <div className="presales-cost-grid">
                      {[
                        ["Request type", presalesCost.by_request_type],
                        ["Service line", presalesCost.by_service_line],
                        ["Outcome", presalesCost.by_outcome],
                      ].map(([heading, rows]) => (
                        <div key={heading as string}>
                          <h3>{heading as string}</h3>
                          {(rows as PreSalesCostReport["by_request_type"]).map(
                            (row) => (
                              <div className="report-row" key={row.key}>
                                <span>
                                  <strong>{row.key}</strong>
                                  <small>
                                    {row.request_count} delivered request
                                    {row.request_count === 1 ? "" : "s"}
                                  </small>
                                </span>
                                <Badge>{row.actual_days} days</Badge>
                              </div>
                            ),
                          )}
                          {!(rows as PreSalesCostReport["by_request_type"])
                            .length && (
                            <p className="settings-note">
                              No delivered work yet.
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              {["Administrator", "Manager", "Executive"].includes(
                d.user.level,
              ) && (
                <div className="overview-bottom partner-reports">
                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Partner performance</h2>
                        <p>
                          Introduced and involved pursuits, wins and net won
                          value.
                        </p>
                      </div>
                      <Handshake size={18} />
                    </div>
                    {partnerPerformance.length ? (
                      partnerPerformance.map((row) => (
                        <div className="report-row" key={row.company_id}>
                          <span>
                            <strong>{row.partner}</strong>
                            <small>
                              {row.opportunities_introduced} introduced ·{" "}
                              {row.opportunities_involved} involved
                            </small>
                          </span>
                          <span>
                            <strong>
                              {row.win_rate_pct == null
                                ? "No closed deals"
                                : `${row.win_rate_pct}% win rate`}
                            </strong>
                            <small>{money(row.net_value_usd)} net won</small>
                          </span>
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="No partner performance yet"
                        text="Performance appears after partner involvements are recorded."
                      />
                    )}
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Undocumented partner terms</h2>
                        <p>
                          Proposed or verbal terms at Proposal submitted or
                          beyond.
                        </p>
                      </div>
                      <Badge
                        tone={undocumentedPartners.length ? "orange" : "green"}
                      >
                        {undocumentedPartners.length}
                      </Badge>
                    </div>
                    {undocumentedPartners.length ? (
                      undocumentedPartners.map((row) => (
                        <button
                          className="report-row report-row-button"
                          key={row.partner_id}
                          onClick={() => {
                            const opportunity = d.opportunities.find(
                              (item) =>
                                item.opportunity_id === row.opportunity_id,
                            );
                            if (opportunity) openPursuit(opportunity);
                          }}
                        >
                          <span>
                            <strong>{row.opportunity}</strong>
                            <small>
                              {row.partner} · {row.contact}
                            </small>
                          </span>
                          <Badge tone="orange">{row.status}</Badge>
                        </button>
                      ))
                    ) : (
                      <Empty
                        title="Terms are documented"
                        text="No advanced-stage pursuits have proposed or verbal partner terms."
                      />
                    )}
                  </section>
                </div>
              )}
            </>
          )}
          {page === "settings" && (
            <>
              <div className="settings-banner">
                <ShieldCheck size={30} />
                <div>
                  <h2>One workspace. Clear boundaries.</h2>
                  <p>
                    {d.instance === "US" ? "United States" : "International"}{" "}
                    deployment · Independent database · Local demo
                    authentication
                  </p>
                </div>
                <Badge tone="yellow">LOCAL ADMINISTRATION</Badge>
              </div>
              <div className="overview-bottom">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Workspace team</h2>
                    <Badge>
                      {d.admin_users.length || d.users.length} people
                    </Badge>
                  </div>
                  {(d.admin_users.length ? d.admin_users : d.users).map((u) => (
                    <div className="settings-person" key={u.id}>
                      <Avatar name={u.name} />
                      <span>
                        <strong>{u.name}</strong>
                        <small>
                          {u.job_title} · {u.email}
                        </small>
                      </span>
                      <Badge tone={u.active ? "neutral" : "orange"}>
                        {u.active ? u.level : "Inactive"}
                      </Badge>
                      {d.user.level === "Administrator" && (
                        <button
                          className="text-button"
                          onClick={() => adminUserForm(u)}
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  ))}
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Currency and commercial controls</h2>
                      <p>Reference rates affect new opportunities only.</p>
                    </div>
                    <Badge>
                      {d.instance === "US" ? "USD only" : "USD reporting base"}
                    </Badge>
                  </div>
                  <div className="settings-note">
                    Rates are copied onto a deal at conversion. These seeded
                    rates are examples, not current market quotes.
                  </div>
                  <div className="working-calendar-row">
                    <CalendarDays size={20} />
                    <span>
                      <strong>Working calendar</strong>
                      <small>
                        {d.working_calendar.working_weekdays.length} working
                        days · {d.working_calendar.holidays.length} holidays
                      </small>
                    </span>
                    {d.user.level === "Administrator" && (
                      <button
                        className="text-button"
                        onClick={workingCalendarForm}
                      >
                        Configure
                      </button>
                    )}
                  </div>
                  {d.reference.currencies.map((r) => (
                    <div className="rate-row" key={r.currency}>
                      <strong>{r.currency}</strong>
                      <span>
                        1 {r.currency} = {Number(r.rate).toFixed(6)} USD
                        <small>
                          {r.effective_date
                            ? `Effective ${date(r.effective_date)} · `
                            : ""}
                          {r.source}
                        </small>
                      </span>
                      {d.user.level === "Administrator" && (
                        <button
                          className="text-button"
                          onClick={() => rateForm(r)}
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  ))}
                  <div className="commercial-thresholds">
                    <span>
                      <small>PARTNER SHARE WARNING</small>
                      <strong>
                        {d.commercial_settings.partner_share_warning_pct}%
                      </strong>
                    </span>
                    <span>
                      <small>FX MOVEMENT NOTICE</small>
                      <strong>
                        {d.commercial_settings.fx_movement_notice_pct}%
                      </strong>
                    </span>
                  </div>
                  {d.user.level === "Administrator" && (
                    <div className="detail-actions">
                      <button
                        className="button secondary"
                        onClick={commercialSettingsForm}
                      >
                        Edit thresholds
                      </button>
                      <button
                        className="button secondary"
                        onClick={rebaselineOpenRates}
                        disabled={
                          !d.opportunities.some(
                            (item) =>
                              !["won", "lost"].includes(item.stage ?? ""),
                          )
                        }
                      >
                        Re-baseline open deals
                      </button>
                    </div>
                  )}
                </section>
              </div>
              <div className="overview-bottom notification-settings">
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Notification preferences</h2>
                      <p>
                        Exception alerts stay useful when each person controls
                        what reaches their inbox.
                      </p>
                    </div>
                    <Bell size={18} />
                  </div>
                  <div className="settings-note">
                    {notificationPreferences
                      ? `${Object.entries(notificationPreferences).filter(([key, value]) => typeof value === "boolean" && value && key !== "weekly_summary").length} exception categories enabled · ${notificationPreferences.inactivity_days}-day inactivity threshold`
                      : "Loading your preferences…"}
                  </div>
                  <button
                    className="button secondary"
                    disabled={!notificationPreferences}
                    onClick={notificationPreferenceForm}
                  >
                    <Settings2 size={15} /> Manage preferences
                  </button>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Notification automation</h2>
                      <p>
                        Exception scanning runs every 15 minutes; leadership
                        summaries run Monday at 07:00 UTC.
                      </p>
                    </div>
                    <Badge
                      tone={
                        automationStatus?.latest?.status === "Failed"
                          ? "orange"
                          : "green"
                      }
                    >
                      {automationStatus?.latest?.status ?? "Waiting"}
                    </Badge>
                  </div>
                  <div className="automation-status">
                    <strong>
                      {automationStatus?.latest?.task_name ??
                        "No recorded run yet"}
                    </strong>
                    <span>
                      {automationStatus?.latest
                        ? `${date(automationStatus.latest.finished_at)} · ${automationStatus.latest.created_count} alerts created`
                        : "The scheduler will record its first completed run here."}
                    </span>
                    {automationStatus?.latest?.detail && (
                      <small>{automationStatus.latest.detail}</small>
                    )}
                  </div>
                  {d.user.level === "Administrator" && (
                    <button
                      className="button secondary"
                      onClick={async () => {
                        try {
                          const result = await api<{ created: number }>(
                            "notifications/refresh/",
                            "POST",
                            {},
                          );
                          setToast(
                            `${result.created} new notifications created.`,
                          );
                          setAutomationStatus(
                            await api<AutomationStatus>(
                              "notifications/status/",
                            ),
                          );
                          void load();
                        } catch (e) {
                          setToast((e as Error).message);
                        }
                      }}
                    >
                      <Sparkles size={15} /> Run exception scan
                    </button>
                  )}
                </section>
              </div>
              <section className="panel admin-reference-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Workspace reference data</h2>
                    <p>
                      Labels, ordering, availability and stage probabilities
                      used across forms and boards.
                    </p>
                  </div>
                  {d.user.level === "Administrator" && (
                    <button
                      className="button secondary"
                      onClick={() => referenceForm()}
                    >
                      <Plus size={15} /> Add option
                    </button>
                  )}
                </div>
                {d.user.level !== "Administrator" ? (
                  <div className="settings-note">
                    Sign in as a Workspace Administrator to edit configuration.
                  </div>
                ) : (
                  <div className="admin-reference-grid">
                    {Array.from(
                      new Set(d.admin_references.map((item) => item.category)),
                    ).map((category) => (
                      <details
                        className="admin-reference-group"
                        key={category}
                        open={category === "stages"}
                      >
                        <summary>
                          <strong>{category.replaceAll("_", " ")}</strong>
                          <Badge>
                            {
                              d.admin_references.filter(
                                (item) => item.category === category,
                              ).length
                            }{" "}
                            options
                          </Badge>
                        </summary>
                        {d.admin_references
                          .filter((item) => item.category === category)
                          .map((item) => (
                            <div className="reference-row" key={item.id}>
                              <span>
                                <strong>{item.label}</strong>
                                <small>
                                  {item.code}
                                  {item.numeric_value != null
                                    ? ` · ${item.numeric_value}%`
                                    : ""}
                                </small>
                              </span>
                              <Badge tone={item.active ? "neutral" : "orange"}>
                                {item.active ? "Active" : "Inactive"}
                              </Badge>
                              <button
                                className="text-button"
                                onClick={() => referenceForm(item)}
                              >
                                Edit
                              </button>
                            </div>
                          ))}
                      </details>
                    ))}
                  </div>
                )}
              </section>
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Access policy</h2>
                    <p>Your effective role capabilities and protected field rules.</p>
                  </div>
                  <Badge tone="yellow">{d.permissions.role}</Badge>
                </div>
                <div className="permission-grid">
                  {d.permissions.capabilities.filter((item) => item.granted).map((item) => (
                    <div key={item.code}><ShieldCheck size={16}/><span><strong>{item.label}</strong><small>{item.code}</small></span></div>
                  ))}
                </div>
                <div className="permission-rules">
                  {d.permissions.field_rules.map((rule) => (
                    <div key={rule.area}><strong>{rule.area}</strong><span>{rule.fields}</span><small>{rule.rule}</small></div>
                  ))}
                </div>
              </section>
              <section className="panel">
                <div className="panel-heading">
                  <h2>Integration readiness</h2>
                </div>
                <div className="integration-grid">
                  {[
                    ["Microsoft Entra ID", "Company single sign-on"],
                    [
                      "Outlook & SharePoint",
                      "Email linking and document storage",
                    ],
                    ["Azure AI", "Reviewed, grounded assistance"],
                  ].map(([name, description]) => (
                    <div key={name}>
                      <LockKeyhole size={22} />
                      <h3>{name}</h3>
                      <p>{description}</p>
                      <Badge>Not connected · planned</Badge>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
          {page === "data" && (
            <DataTools
              data={d}
              notify={setToast}
              onChanged={() => void load()}
              onOpen={(type, id) => {
                if (type === "Company") {
                  setCompanyId(id);
                  setContactId(null);
                  setSelected(null);
                } else if (type === "Contact") {
                  setContactId(id);
                  setCompanyId(null);
                  setSelected(null);
                } else {
                  setSelected(id);
                  setCompanyId(null);
                  setContactId(null);
                }
              }}
            />
          )}
          <footer className="page-footer">
            <span>
              ATPLCRM <span>·</span> Clarity at every handoff.
            </span>
            <span>
              <span className="live-dot" />
              Local database connected
            </span>
          </footer>
        </main>
      </div>
      {(selected || companyId || contactId) && (
        <dialog
          ref={detailRef}
          className="detail-dialog"
          onCancel={closeDetail}
          aria-labelledby="detail-title"
        >
          <div className="detail-top">
            <span className="eyebrow">
              {p
                ? p.opportunity_id
                  ? "OPPORTUNITY DETAIL"
                  : "LEAD DETAIL"
                : company
                  ? "COMPANY 360"
                  : "CONTACT DETAIL"}
            </span>
            <button
              className="icon-button"
              onClick={closeDetail}
              aria-label="Close details"
            >
              <X size={21} />
            </button>
          </div>
          <div className="detail-title">
            <h1 id="detail-title">
              {p?.name ?? company?.name ?? contact?.name}
            </h1>
            <p>
              {p?.company ??
                company?.industry ??
                `${contact?.job_title} · ${contact?.company}`}
            </p>
          </div>
          {p && (
            <>
              <div className="detail-actions">
                {p.opportunity_id ? (
                  <select
                    aria-label="Opportunity stage"
                    value={p.stage}
                    disabled={!p.can_work}
                    onChange={(e) => changeStage(p, e.target.value)}
                  >
                    {d.reference.stages.map(([key, label]) => (
                      <option value={key} key={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <select
                    aria-label="Lead status"
                    value={p.status}
                    disabled={!p.can_work || p.status === "closed"}
                    onChange={(e) =>
                      mutate(`leads/${p.lead_id}/status/`, {
                        status: e.target.value,
                      })
                    }
                  >
                    {d.reference.lead_statuses.map(([key, label]) => (
                      <option disabled={key === "closed"} value={key} key={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                )}
                <Badge tone={p.priority === "High" ? "orange" : "neutral"}>
                  {p.priority} priority
                </Badge>
                {p.can_work && (
                  <>
                    {p.opportunity_id && (
                      <button
                        className="button secondary"
                        onClick={() => opportunityForm(p)}
                      >
                        Edit opportunity
                      </button>
                    )}
                    <button
                      className="button secondary"
                      onClick={() => activityForm(p)}
                    >
                      <Plus size={14} />
                      Log interaction
                    </button>
                    {(!p.opportunity_id ||
                      !["won", "lost"].includes(p.stage ?? "")) && (
                      <button
                        className="button secondary"
                        onClick={() => completeAction(p)}
                      >
                        <CheckCheck size={14} /> Complete action
                      </button>
                    )}
                    <button
                      className="button primary"
                      onClick={() => workForm(p)}
                    >
                      Set next action <ArrowRight size={14} />
                    </button>
                  </>
                )}
                {!p.opportunity_id &&
                  p.status === "ready" &&
                  validationRoute?.current_user_can_validate && (
                    <button
                      className="button yellow"
                      onClick={() => convertForm(p)}
                    >
                      Validate & convert
                    </button>
                  )}
              </div>
              {!p.opportunity_id && p.status === "ready" && validationRoute && (
                <div className="validation-route-note">
                  <ShieldCheck size={18} />
                  <span>
                    <strong>Independent validation route</strong>
                    {validationRoute.current_user_can_validate
                      ? " You are eligible to decide this lead."
                      : ` Send this lead to ${validationRoute.eligible.map((person) => person.name).join(", ") || "an eligible Manager or Executive"}.`}
                    <small>{validationRoute.reason}</small>
                  </span>
                </div>
              )}
              <div className="at-glance">
                <div>
                  <small>COMMERCIAL OWNER</small>
                  <strong>{p.owner}</strong>
                </div>
                <div>
                  <small>BALL IN COURT</small>
                  <strong>
                    <Avatar name={p.holder} small />
                    {p.holder}
                  </strong>
                  <span>{p.days_held} days held</span>
                </div>
                <div>
                  <small>NEXT ACTION</small>
                  <strong>{p.next_action}</strong>
                  <span className={p.action_date < d.today ? "overdue" : ""}>
                    {p.action_type} · {date(p.action_date)}
                  </span>
                </div>
                <div>
                  <small>
                    {p.opportunity_id
                      ? `NET VALUE · ${showLocalCurrency ? p.currency : "USD"}`
                      : "SOURCE"}
                  </small>
                  <strong>
                    {p.opportunity_id
                      ? showLocalCurrency
                        ? money(p.net_value_local, p.currency)
                        : money(p.net_value_usd)
                      : p.source_channel}
                  </strong>
                  {p.opportunity_id && (
                    <span>{p.probability}% probability</span>
                  )}
                </div>
                <div>
                  <small>BLOCKER</small>
                  <strong>
                    {p.blocker === "None" ? "No blocker" : p.blocker}
                  </strong>
                  <span>
                    {p.blocker_owner ?? "Clear to move forward"}
                    {p.blocker !== "None" && ` · ${p.days_blocked}d`}
                  </span>
                </div>
                <div>
                  <small>LAST CLIENT INTERACTION</small>
                  <strong>
                    {p.last_client_interaction
                      ? date(p.last_client_interaction)
                      : "Not logged"}
                  </strong>
                  <span>Client-facing only</span>
                </div>
                <div>
                  <small>NEXT CUSTOMER MEETING</small>
                  <strong>{date(p.next_meeting)}</strong>
                </div>
                <div>
                  <small>EXPECTED CLOSE / CREATED</small>
                  <strong>{date(p.expected_close_date ?? p.created_at)}</strong>
                </div>
              </div>
              <div className="detail-tabs">
                {[
                  "Overview",
                  "Milestones",
                  "Timeline",
                  "Team & contacts",
                  "Documents",
                  ...(p.opportunity_id ? ["Commercial", "Value history"] : []),
                ].map((tab) => (
                  <button
                    className={detailTab === tab ? "active" : ""}
                    key={tab}
                    onClick={() => setDetailTab(tab)}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <div className="detail-content">
                {detailTab === "Overview" && (
                  <>
                    <h3>
                      {p.opportunity_id ? "Customer need" : "Area of interest"}
                    </h3>
                    <p>
                      {p.customer_need ??
                        p.area_of_interest ??
                        "No detail added yet."}
                    </p>
                    {p.scope_summary && (
                      <>
                        <h3>Scope summary</h3>
                        <p>{p.scope_summary}</p>
                      </>
                    )}
                    {p.blocker !== "None" && (
                      <div className="blocker-callout">
                        <AlertCircle size={20} />
                        <div>
                          <strong>What will unblock this?</strong>
                          <p>{p.resolution_action}</p>
                        </div>
                      </div>
                    )}
                    <div className="detail-meta">
                      <div>
                        <small>Sourced by</small>
                        <strong>{p.sourced_by}</strong>
                      </div>
                      <div>
                        <small>Source</small>
                        <strong>{p.source_channel}</strong>
                      </div>
                      {p.service_line && (
                        <div>
                          <small>Service line</small>
                          <strong>{p.service_line}</strong>
                        </div>
                      )}
                      {p.primary_contact && (
                        <div>
                          <small>Primary contact</small>
                          <strong>{p.primary_contact}</strong>
                        </div>
                      )}
                    </div>
                    {!p.opportunity_id &&
                      p.can_work &&
                      p.status !== "closed" && (
                        <div className="detail-actions">
                          <button
                            className="button secondary"
                            onClick={() =>
                              setForm({
                                title: "Nurture this lead",
                                fields: [
                                  field("revisit_date", "Revisit date", {
                                    type: "date",
                                    value: tomorrow(),
                                  }),
                                ],
                                submit: (v) =>
                                  api(`leads/${p.lead_id}/nurture/`, "POST", v),
                              })
                            }
                          >
                            Move to nurture
                          </button>
                          {validationRoute?.current_user_can_validate && (
                            <button
                              className="button secondary"
                              onClick={() =>
                                setForm({
                                  title: "Disqualify lead",
                                  fields: [
                                    field("reason", "Reason", {
                                      options: options(
                                        d.reference.disqualification_reasons,
                                      ),
                                    }),
                                  ],
                                  submit: (v) =>
                                    api(
                                      `leads/${p.lead_id}/disqualify/`,
                                      "POST",
                                      v,
                                    ),
                                })
                              }
                            >
                              Disqualify
                            </button>
                          )}
                        </div>
                      )}
                    {p.opportunity_id &&
                      ["Manager", "Executive"].includes(d.user.level) && (
                        <div className="detail-actions">
                          <button
                            className="button secondary"
                            onClick={() =>
                              setForm({
                                title: "Value visibility",
                                fields: [
                                  field("restricted", "Visibility", {
                                    options: [
                                      [
                                        "false",
                                        "Visible to all internal users",
                                      ],
                                      [
                                        "true",
                                        "Restricted to team and management",
                                      ],
                                    ],
                                    value: String(p.restricted),
                                  }),
                                  field("reason", "Reason", {
                                    type: "textarea",
                                  }),
                                ],
                                submit: (v) =>
                                  api(
                                    `opportunities/${p.opportunity_id}/restriction/`,
                                    "POST",
                                    v,
                                  ),
                              })
                            }
                          >
                            <LockKeyhole size={14} />
                            Value visibility
                          </button>
                          <button
                            className="button secondary"
                            onClick={() =>
                              setForm({
                                title: "Override probability",
                                fields: [
                                  field("probability", "Probability (%)", {
                                    type: "number",
                                    value: String(p.probability),
                                  }),
                                  field("reason", "Reason", {
                                    type: "textarea",
                                  }),
                                ],
                                submit: (v) =>
                                  api(
                                    `opportunities/${p.opportunity_id}/probability/`,
                                    "POST",
                                    v,
                                  ),
                              })
                            }
                          >
                            Override probability
                          </button>
                        </div>
                      )}
                  </>
                )}
                {detailTab === "Milestones" && (
                  <div
                    className="milestone-detail"
                    aria-label="Seven lifecycle milestones"
                  >
                    {p.milestones.map((milestone, index) => (
                      <div
                        className={milestone.at ? "complete" : "pending"}
                        key={milestone.key}
                      >
                        <span>
                          {milestone.at ? <Check size={14} /> : index + 1}
                        </span>
                        <div>
                          <strong>{milestone.label}</strong>
                          <small>
                            {milestone.at ? date(milestone.at) : "Not reached"}
                          </small>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {detailTab === "Timeline" &&
                  (timeline ? (
                    <>
                      {timeline.restricted_content && (
                        <p className="settings-note">
                          Narrative content is withheld because this
                          opportunity’s values are restricted.
                        </p>
                      )}
                      {[
                        ...timeline.activities.map((a) => ({
                          id: a.id,
                          title: a.subject,
                          detail: a.notes,
                          date: a.date,
                          author: a.author,
                          label: a.activity_type,
                        })),
                        ...timeline.events.map((e) => ({
                          id: e.id,
                          title: e.action,
                          detail: e.detail,
                          date: e.date,
                          author: e.author,
                          label: "System event",
                        })),
                        ...timeline.completed_actions.map((a) => ({
                          id: a.id,
                          title: a.summary,
                          detail: a.note,
                          date: a.completed_at,
                          author: a.completed_by,
                          label: `Completed action · ${a.outcome}`,
                        })),
                      ]
                        .sort((a, b) => b.date.localeCompare(a.date))
                        .map((a) => (
                          <div className="timeline-item" key={a.id}>
                            <span className="timeline-dot" />
                            <div>
                              <small>
                                {date(a.date)} · {a.author} · {a.label}
                              </small>
                              <h3>{a.title}</h3>
                              <p>{a.detail}</p>
                            </div>
                          </div>
                        ))}
                    </>
                  ) : (
                    <LoaderCircle className="spin" />
                  ))}
                {detailTab === "Team & contacts" && (
                  <>
                    <div className="panel-heading">
                      <h3>Pursuit team</h3>
                      {p.opportunity_id && p.can_work && (
                        <button
                          className="button secondary"
                          onClick={() => teamForm(p)}
                        >
                          <Plus size={14} />
                          Assign role
                        </button>
                      )}
                    </div>
                    {[
                      { name: p.owner, role: "Commercial owner" },
                      { name: p.sourced_by, role: "Sourced by" },
                      ...p.team,
                    ].map((t, i) => (
                      <div className="settings-person" key={i}>
                        <Avatar name={t.name} />
                        <strong>{t.name}</strong>
                        <Badge>{t.role}</Badge>
                      </div>
                    ))}
                    <div className="panel-heading stakeholder-heading">
                      <h3>Client stakeholders</h3>
                      {p.opportunity_id && p.can_work && (
                        <button
                          className="button secondary"
                          onClick={() => stakeholderForm(p)}
                        >
                          <Plus size={14} /> Add stakeholder
                        </button>
                      )}
                    </div>
                    {p.contacts.map((c) => (
                      <div className="settings-person" key={c.id}>
                        <Avatar name={c.name} />
                        <span>
                          <strong>{c.name}</strong>
                          <small>{c.job_title || c.email}</small>
                        </span>
                        <Badge>{c.role}</Badge>
                        {p.can_work && (
                          <span className="stakeholder-actions">
                            <button
                              className="text-button"
                              onClick={() => stakeholderForm(p, c)}
                            >
                              Edit
                            </button>
                            <button
                              className="text-button danger"
                              onClick={() =>
                                mutate(
                                  `productivity/stakeholders/${c.link_id}/`,
                                  undefined,
                                  "DELETE",
                                )
                              }
                            >
                              Remove
                            </button>
                          </span>
                        )}
                      </div>
                    ))}
                  </>
                )}
                {detailTab === "Documents" && (
                  <>
                    <div className="panel-heading">
                      <div>
                        <h3>Evidence register</h3>
                        <p>
                          Files, Microsoft 365 links and selected emails, with
                          approval, versions and named client recipients.
                        </p>
                      </div>
                      {p.can_work && (
                        <button
                          className="button secondary"
                          onClick={() => {
                            closeDetail();
                            go("documents");
                          }}
                        >
                          <FolderKanban size={14} />
                          Open document center
                        </button>
                      )}
                    </div>
                    {timeline?.artifacts.length ? (
                      timeline.artifacts.map((a) => (
                        <a
                          className={`document-row ${a.superseded ? "superseded" : ""}`}
                          href={a.url}
                          target="_blank"
                          rel="noreferrer"
                          key={a.id}
                        >
                          <FileText size={22} />
                          <span>
                            <strong>{a.title}</strong>
                            <small>
                              {a.artifact_type} · {a.kind} · Version {a.version}
                              {a.superseded ? " · Superseded" : ""}
                              {a.shared_with_client
                                ? ` · Shared with ${a.recipients.map((person) => person.name).join(", ")}`
                                : ""}
                            </small>
                          </span>
                          <ExternalLink size={16} />
                        </a>
                      ))
                    ) : (
                      <Empty
                        title="No documents registered"
                        text="Add a secure link to a proposal, contract or other evidence."
                      />
                    )}
                  </>
                )}
                {detailTab === "Commercial" && p.opportunity_id && (
                  <>
                    <div className="panel-heading">
                      <div>
                        <h3>Commercial position</h3>
                        <p>
                          Gross value, partner deductions and net forecast use
                          the exchange rate stored on this opportunity.
                        </p>
                      </div>
                      {d.instance !== "US" && p.values_visible && (
                        <button
                          className="button secondary"
                          onClick={() =>
                            setShowLocalCurrency((value) => !value)
                          }
                        >
                          {showLocalCurrency
                            ? "Show USD"
                            : `Show ${p.currency}`}
                        </button>
                      )}
                    </div>
                    {p.values_visible ? (
                      <div className="commercial-summary">
                        <div>
                          <small>GROSS VALUE</small>
                          <strong>
                            {showLocalCurrency
                              ? money(p.current_value, p.currency)
                              : money(p.value_usd)}
                          </strong>
                        </div>
                        <div>
                          <small>PARTNER DEDUCTIONS</small>
                          <strong>
                            {showLocalCurrency
                              ? money(p.partner_deduction_local, p.currency)
                              : money(
                                  Number(p.partner_deduction_local ?? 0) *
                                    Number(p.fx_rate ?? 1),
                                )}
                          </strong>
                        </div>
                        <div>
                          <small>NET FORECAST VALUE</small>
                          <strong>
                            {showLocalCurrency
                              ? money(p.net_value_local, p.currency)
                              : money(p.net_value_usd)}
                          </strong>
                        </div>
                        <div>
                          <small>PARTNER SHARE</small>
                          <strong>{p.total_partner_share_pct ?? "0"}%</strong>
                          <span>
                            Warning above {p.partner_share_warning_pct ?? "40"}%
                          </span>
                        </div>
                        <div>
                          <small>STORED FX RATE</small>
                          <strong>{Number(p.fx_rate).toFixed(6)}</strong>
                          <span>1 {p.currency} in USD</span>
                        </div>
                        <div>
                          <small>PROBABILITY</small>
                          <strong>{p.probability}%</strong>
                          <span>
                            Stage default {p.stage_probability}%
                            {p.probability_note ? " · overridden" : ""}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="settings-note">
                        Commercial values and partner terms are restricted for
                        your role on this opportunity.
                      </div>
                    )}
                    {p.commercial_warnings?.map((warning) => (
                      <div className="commercial-warning" key={warning}>
                        <AlertCircle size={18} />
                        <span>{warning}</span>
                      </div>
                    ))}
                    {p.can_edit_commercial && p.values_visible && (
                      <div className="detail-actions commercial-actions">
                        <button
                          className="button secondary"
                          onClick={() => commercialDetailsForm(p)}
                        >
                          Commercial assumptions
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => opportunityRateForm(p)}
                        >
                          Update stored rate
                        </button>
                        <button
                          className="button primary"
                          onClick={() => partnerForm(p)}
                        >
                          <Plus size={14} /> Add partner
                        </button>
                      </div>
                    )}
                    <div className="panel-heading stakeholder-heading">
                      <div>
                        <h3>Partner involvement</h3>
                        <p>
                          {p.partners?.length ?? 0} partner
                          {(p.partners?.length ?? 0) === 1 ? "" : "s"} linked
                        </p>
                      </div>
                    </div>
                    {p.partners?.length ? (
                      p.partners.map((partner) => (
                        <div className="partner-row" key={partner.id}>
                          <Handshake size={22} />
                          <span>
                            <strong>{partner.company}</strong>
                            <small>
                              {partner.contact} · {partner.role}
                            </small>
                          </span>
                          <span>
                            <strong>
                              {partner.fee_basis === "Fixed fee"
                                ? money(partner.fixed_fee, p.currency)
                                : partner.fee_basis === "To be agreed"
                                  ? "Terms pending"
                                  : `${partner.share_pct}% partner share`}
                            </strong>
                            <small>
                              {partner.status} · {partner.applies_to}
                            </small>
                          </span>
                          {p.can_edit_commercial && p.values_visible && (
                            <span className="stakeholder-actions">
                              <button
                                className="text-button"
                                onClick={() => partnerForm(p, partner)}
                              >
                                Edit
                              </button>
                              <button
                                className="text-button danger"
                                onClick={() =>
                                  mutate(
                                    `partners/${partner.id}/`,
                                    undefined,
                                    "DELETE",
                                  )
                                }
                              >
                                Remove
                              </button>
                            </span>
                          )}
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="No partners linked"
                        text="Add each commercial partner separately. Direct opportunities need no partner record."
                      />
                    )}
                    <div className="detail-meta commercial-evidence">
                      <div>
                        <small>COMMERCIAL APPROVAL</small>
                        <strong>
                          {p.approval_recorded ? "Recorded" : "Not recorded"}
                        </strong>
                        <span>{p.approval_note || "Optional evidence"}</span>
                      </div>
                      <div>
                        <small>GROSS MARGIN INPUT</small>
                        <strong>
                          {p.gross_margin_pct
                            ? `${p.gross_margin_pct}%`
                            : "Not required / not set"}
                        </strong>
                      </div>
                      {p.stage === "won" && (
                        <>
                          <div>
                            <small>CONTRACT / PO</small>
                            <strong>{p.contract_number}</strong>
                            <span>{date(p.contract_date)}</span>
                          </div>
                          <div>
                            <small>PROJECT START</small>
                            <strong>{date(p.project_start)}</strong>
                            <span>{p.duration_months} months</span>
                          </div>
                        </>
                      )}
                    </div>
                  </>
                )}
                {detailTab === "Value history" && (
                  <>
                    <div className="panel-heading">
                      <div>
                        <h3>Every value, preserved</h3>
                        <p>
                          {p.values_visible
                            ? `Currency: ${p.currency} · Current stored rate: ${p.fx_rate}. Each row preserves the rate used at that time.`
                            : "Commercial values are restricted on this opportunity."}
                        </p>
                      </div>
                      {p.can_edit_commercial && p.values_visible && (
                        <button
                          className="button secondary"
                          onClick={() => recordValue(p)}
                        >
                          <Plus size={14} />
                          Record value
                        </button>
                      )}
                    </div>
                    {p.values?.map((v) => (
                      <div className="value-row" key={v.id}>
                        <span>
                          <strong>{v.type}</strong>
                          <small>
                            {date(v.date)} · FX {Number(v.fx_rate).toFixed(6)} ·{" "}
                            {money(v.usd_amount)} · {v.note || "No note added"}
                          </small>
                        </span>
                        <strong>{money(v.amount, v.currency)}</strong>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </>
          )}
          {company && (
            <div className="detail-content">
              <div className="detail-actions">
                <Badge tone="green">{company.company_type}</Badge>
                <span>{company.country}</span>
                <button
                  className="button secondary"
                  onClick={() => companyForm(company)}
                >
                  Edit company
                </button>
                <button
                  className="button primary"
                  onClick={() => contactForm()}
                >
                  <Plus size={14} />
                  Add contact
                </button>
              </div>
              <div className="detail-meta relationship-meta">
                <div>
                  <small>Relationship owner</small>
                  <strong>{company.owner}</strong>
                </div>
                <div>
                  <small>Domain</small>
                  <strong>{company.domain || "Not provided"}</strong>
                </div>
                <div>
                  <small>Industry</small>
                  <strong>{company.industry || "Not provided"}</strong>
                </div>
                <div>
                  <small>Global account</small>
                  <strong>
                    {company.global_account_name || "Local account"}
                  </strong>
                  <span>{company.primary_region || "No primary region"}</span>
                </div>
              </div>
              <h3>Contacts</h3>
              {d.contacts
                .filter((c) => c.company_id === company.id)
                .map((c) => (
                  <button
                    className="settings-person full-button"
                    key={c.id}
                    onClick={() => {
                      setCompanyId(null);
                      setContactId(c.id);
                    }}
                  >
                    <Avatar name={c.name} />
                    <span>
                      <strong>{c.name}</strong>
                      <small>
                        {c.job_title} · {c.email}
                      </small>
                    </span>
                    <ChevronRight size={16} />
                  </button>
                ))}
              <h3 className="spaced">All pursuits</h3>
              {table(
                all.filter((r) => r.company_id === company.id),
                undefined,
                true,
              )}
              <h3 className="spaced">Company interactions</h3>
              {historyView()}
            </div>
          )}
          {contact && (
            <div className="detail-content">
              <div className="detail-actions">
                <Badge tone={contact.do_not_contact ? "orange" : "green"}>
                  {contact.engagement_status}
                </Badge>
                <button
                  className="button secondary"
                  onClick={() => contactForm(contact)}
                >
                  Edit contact
                </button>
                <button
                  className="button primary"
                  onClick={() => activityForm(undefined, contact)}
                >
                  <Plus size={14} />
                  Log interaction
                </button>
              </div>
              <div className="detail-meta">
                <div>
                  <small>Email</small>
                  <strong>{contact.email || "Not provided"}</strong>
                </div>
                <div>
                  <small>Relationship owner</small>
                  <strong>{contact.owner}</strong>
                </div>
                <div>
                  <small>Source</small>
                  <strong>{contact.source_channel}</strong>
                  <span>
                    {contact.source_detail ||
                      `Sourced by ${contact.sourced_by}`}
                  </span>
                </div>
                <div>
                  <small>Outbound touches</small>
                  <strong>{contact.touch_count}</strong>
                  <span>
                    First: {date(contact.first_contacted_at)} · Last:{" "}
                    {date(contact.last_touched_at)}
                  </span>
                </div>
                <div>
                  <small>Phone / mobile</small>
                  <strong>
                    {contact.phone || contact.mobile || "Not provided"}
                  </strong>
                </div>
                <div>
                  <small>Location</small>
                  <strong>
                    {[contact.city, contact.country].filter(Boolean).join(", ")}
                  </strong>
                </div>
                <div>
                  <small>Seniority</small>
                  <strong>{contact.seniority}</strong>
                </div>
                <div>
                  <small>Consent basis</small>
                  <strong>{contact.consent_basis}</strong>
                </div>
              </div>
              {contact.do_not_contact && (
                <div className="dnc-banner">
                  <ShieldCheck size={18} />
                  <span>
                    <strong>Do not contact</strong>Outbound activity requires an
                    override reason. Every override is retained in the activity
                    history.
                  </span>
                </div>
              )}
              {contact.notes && (
                <>
                  <h3>Relationship context</h3>
                  <p className="relationship-notes">{contact.notes}</p>
                </>
              )}
              <h3>Associated pursuits</h3>
              {table(
                all.filter(
                  (p) =>
                    p.contacts.some((c) => c.id === contact.id) ||
                    p.primary_contact_id === contact.id,
                ),
                undefined,
                true,
              )}
              <h3 className="spaced">Interaction history</h3>
              {historyView()}
            </div>
          )}
        </dialog>
      )}
      {form && (
        <FormModal
          key={form.title}
          spec={form}
          onClose={() => setForm(null)}
          onSuccess={success}
        />
      )}{" "}
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={18} />
          <span>{toast}</span>
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Dismiss message"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
function dictLabel(list: [string, string][], key?: string) {
  return list.find((x) => x[0] === key)?.[1] ?? key;
}
