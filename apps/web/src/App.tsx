import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  Activity as ActivityIcon,
  ArrowDownLeft,
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
} from "lucide-react";
import { api } from "./api";
import { DataTools } from "./DataTools";
import { RecordList } from "./RecordList";
import type {
  Company,
  Contact,
  Data,
  Person,
  Pursuit,
  Request,
  Timeline,
  AdminReference,
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
};
type FormSpec = {
  title: string;
  description?: string;
  fields: Field[];
  submit: (values: Record<string, string>) => Promise<unknown>;
  label?: string;
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
    [error, setError] = useState("");
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(e.currentTarget)) as Record<
      string,
      string
    >;
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
      <form onSubmit={submit}>
        <div className="form-grid">
          {spec.fields.map((f) => (
            <label key={f.name} className={f.type === "textarea" ? "full" : ""}>
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
          ))}
        </div>
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
    [pipelineView, setPipelineView] = useState("board");
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
    if (selected || companyId || contactId) detailRef.current?.showModal();
  }, [selected, companyId, contactId]);
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
        field("email", "Email", {
          type: "email",
          value: c?.email,
          required: false,
        }),
        field("phone", "Phone", { value: c?.phone, required: false }),
        field("country", "Country", { value: c?.country }),
        field("owner", "Relationship owner", {
          options: userOptions,
          value: String(c?.owner_id ?? d.user.id),
        }),
        field("source_channel", "Source", {
          options: options(d.reference.sources),
          value: c?.source_channel ?? "LinkedIn",
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
      submit: async (v) => {
        const result = await api<{ warning?: string }>("activities/", "POST", {
          ...v,
          contact: v.contact || null,
          pursuit: r?.id ?? null,
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
  function changeStage(r: Pursuit, target: string) {
    if (target === r.stage) return;
    const fields: Field[] = [];
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
      );
    if (fields.length)
      setForm({
        title: `Move to ${dictLabel(d.reference.stages, target)}`,
        description:
          target === "won"
            ? "Register final contract, PO or SOW evidence before closing."
            : undefined,
        fields,
        submit: (v) =>
          api(`opportunities/${r.opportunity_id}/stage/`, "POST", {
            ...v,
            stage: target,
          }),
      });
    else
      void mutate(`opportunities/${r.opportunity_id}/stage/`, {
        stage: target,
      });
  }
  function requestForm() {
    setForm({
      title: "Request pre-sales work",
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
        field("assigned_to", "Assigned to", { options: userOptions }),
        field("needed_by", "Needed by", { type: "date", value: tomorrow() }),
        field("estimated_days", "Estimated days", {
          type: "number",
          value: "1",
        }),
        field("notes", "Brief", { type: "textarea", required: false }),
      ],
      submit: (v) => api("requests/", "POST", v),
    });
  }
  function updateRequest(r: Request) {
    setForm({
      title: "Update deliverable",
      description: r.title,
      fields: [
        field("status", "Status", {
          options: options(d.reference.request_statuses),
          value: r.status,
        }),
        field("actual_days", "Actual days (required at delivery)", {
          type: "number",
          required: false,
          value: r.actual_days ?? "",
        }),
        field("blocked_reason", "Blocker reason (required if blocked)", {
          required: false,
          value: r.blocked_reason,
        }),
      ],
      submit: (v) => api(`requests/${r.id}/`, "PATCH", v),
    });
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
  const title =
    nav
      .map((g) => g.items.map(([key, label]) => ({ key, label })))
      .flat()
      .find((n) => n.key === page)?.label ?? "Overview";
  const table = (records: Pursuit[], limit?: number) => (
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
          {filtered(records)
            .slice(0, limit)
            .map((r) => (
              <tr key={r.id}>
                <td>
                  <button
                    className="record-name"
                    onClick={() => openPursuit(r)}
                  >
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
                  <span
                    className={r.action_date < d.today ? "overdue" : "date"}
                  >
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
            ATPL Workspace
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
            <span className="live-dot" /> Local workspace <Badge>v0.5</Badge>
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
          <section className="notification-panel">
            <div className="panel-heading">
              <h3>Notifications</h3>
              <button
                className="text-button"
                onClick={() => mutate("notifications/read/", {})}
              >
                Mark all read
              </button>
            </div>
            {d.notifications.length ? (
              d.notifications.map((n) => (
                <button
                  key={n.id}
                  className={`notification-item ${n.read ? "read" : ""}`}
                  onClick={() => {
                    if (n.pursuit_id) setSelected(n.pursuit_id);
                    setNotifications(false);
                  }}
                >
                  <Bell size={15} />
                  <span>
                    {n.message}
                    <small>{date(n.created_at)}</small>
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
              ) : page === "data" ? null : (
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
          {(page === "work" || page === "attention") && (
            <>
              <div className="mini-stats">
                <div>
                  <Clock3 size={20} />
                  <span>
                    <strong>
                      {
                        (page === "work" ? held : attention).filter(
                          (p) => p.action_date < d.today,
                        ).length
                      }
                    </strong>{" "}
                    Overdue actions
                  </span>
                </div>
                <div>
                  <CalendarDays size={20} />
                  <span>
                    <strong>
                      {held.filter((p) => p.action_date === d.today).length}
                    </strong>{" "}
                    Due today
                  </span>
                </div>
                <div>
                  <AlertCircle size={20} />
                  <span>
                    <strong>
                      {
                        (page === "work"
                          ? active.filter(
                              (p) => p.blocker_owner_id === d.user.id,
                            )
                          : attention
                        ).filter((p) => p.blocker !== "None").length
                      }
                    </strong>{" "}
                    Open blockers
                  </span>
                </div>
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <h2>
                    {page === "work"
                      ? "Your next actions"
                      : "Pursuits needing attention"}
                  </h2>
                  <Badge>
                    {page === "work" ? held.length : attention.length} pursuits
                  </Badge>
                </div>
                {table(page === "work" ? held : attention)}
              </section>
              {page === "work" && (
                <div className="overview-bottom">
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Blockers you own</h2>
                    </div>
                    {active
                      .filter((p) => p.blocker_owner_id === d.user.id)
                      .map((r) => (
                        <button
                          className="blocker-item"
                          key={r.id}
                          onClick={() => openPursuit(r)}
                        >
                          <AlertCircle size={18} />
                          <span>
                            <strong>{r.blocker}</strong>
                            <small>
                              {r.name} · {r.resolution_action}
                            </small>
                          </span>
                        </button>
                      ))}
                    {!active.some((p) => p.blocker_owner_id === d.user.id) && (
                      <Empty
                        title="No blockers assigned"
                        text="You have no blockers to resolve right now."
                      />
                    )}
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Your deliverables</h2>
                    </div>
                    {d.requests
                      .filter((r) => r.assigned_to_id === d.user.id)
                      .map((r) => (
                        <button
                          className="request-mini"
                          key={r.id}
                          onClick={() => updateRequest(r)}
                        >
                          <FileText size={17} />
                          <span>
                            <strong>{r.title}</strong>
                            <small>{date(r.needed_by)}</small>
                          </span>
                          <Badge>{r.status}</Badge>
                        </button>
                      ))}
                    {!d.requests.some(
                      (r) => r.assigned_to_id === d.user.id,
                    ) && (
                      <Empty
                        title="No assigned deliverables"
                        text="Your next pre-sales request will appear here."
                      />
                    )}
                  </section>
                </div>
              )}
            </>
          )}
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
                      <section className="kanban-column" key={key}>
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
                              className="deal-card"
                              key={r.id}
                              onClick={() => openPursuit(r)}
                            >
                              <div className="card-company">
                                <span>{r.company}</span>
                                <MoreHorizontal size={16} />
                              </div>
                              <h3>{r.name}</h3>
                              {page === "pipeline" ? (
                                <strong className="card-value">
                                  {money(r.net_value_usd)}
                                  <small>net USD</small>
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
              <section className="panel">
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>DELIVERABLE</th>
                        <th>OPPORTUNITY</th>
                        <th>ASSIGNED TO</th>
                        <th>STATUS</th>
                        <th>NEEDED BY</th>
                        <th>ESTIMATE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.requests
                        .filter((r) => matches(`${r.title} ${r.opportunity}`))
                        .map((r) => (
                          <tr key={r.id}>
                            <td>
                              <button
                                className="record-name"
                                onClick={() => updateRequest(r)}
                              >
                                {r.title}
                              </button>
                              <small>{r.request_type}</small>
                            </td>
                            <td>{r.opportunity}</td>
                            <td>
                              <div className="person">
                                <Avatar small name={r.assigned_to} />
                                {r.assigned_to}
                              </div>
                            </td>
                            <td>
                              <Badge
                                tone={
                                  r.status === "Ready for review"
                                    ? "yellow"
                                    : "blue"
                                }
                              >
                                {r.status}
                              </Badge>
                            </td>
                            <td
                              className={r.needed_by < d.today ? "overdue" : ""}
                            >
                              {date(r.needed_by)}
                            </td>
                            <td>{r.estimated_days} days</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
          {page === "reports" && (
            <>
              <div className="metrics">
                {metric(
                  "Net pipeline",
                  money(total, "USD", true),
                  "Visible open opportunities",
                  <Handshake size={18} />,
                  () => go("pipeline"),
                )}
                {metric(
                  "Weighted forecast",
                  money(weighted, "USD", true),
                  "Probability × net value",
                  <TrendingUp size={18} />,
                  () => go("pipeline"),
                )}
                {metric(
                  "Converted leads",
                  String(
                    d.leads.filter((l) => l.outcome === "Converted").length,
                  ),
                  "Full history preserved",
                  <ArrowUpRight size={18} />,
                  () => go("leads"),
                )}
                {metric(
                  "Closed won",
                  String(
                    d.opportunities.filter((o) => o.stage === "won").length,
                  ),
                  "Signed business",
                  <CheckCircle2 size={18} />,
                  () => go("pipeline"),
                )}
              </div>
              <div className="overview-bottom">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Pipeline by stage</h2>
                    <Badge>Net USD</Badge>
                  </div>
                  {pipelineChart}
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Lead funnel</h2>
                    <Badge>{d.leads.length} total</Badge>
                  </div>
                  <div className="funnel">
                    {d.reference.lead_statuses.map(([key, label]) => (
                      <button key={key} onClick={() => go("leads")}>
                        <span>{label}</span>
                        <div>
                          <i
                            style={{
                              width: `${Math.max(4, (d.leads.filter((l) => l.status === key).length / Math.max(1, d.leads.length)) * 100)}%`,
                            }}
                          />
                        </div>
                        <strong>
                          {d.leads.filter((l) => l.status === key).length}
                        </strong>
                      </button>
                    ))}
                  </div>
                </section>
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Forecast detail</h2>
                    <p>
                      Restricted values are excluded from your totals. On-hold
                      pursuits are excluded from forecasts.
                    </p>
                  </div>
                  <button
                    className="button secondary"
                    onClick={() => exportCsv(visibleOpps)}
                  >
                    Export CSV <ArrowDownLeft size={15} />
                  </button>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>OPPORTUNITY</th>
                        <th>NET USD</th>
                        <th>PROBABILITY</th>
                        <th>WEIGHTED USD</th>
                        <th>EXPECTED CLOSE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered(visibleOpps).map((r) => (
                        <tr key={r.id}>
                          <td>
                            <button
                              className="record-name"
                              onClick={() => openPursuit(r)}
                            >
                              {r.name}
                            </button>
                          </td>
                          <td>{money(r.net_value_usd)}</td>
                          <td>{r.probability}%</td>
                          <td>
                            {money(
                              (Number(r.net_value_usd) * (r.probability ?? 0)) /
                                100,
                            )}
                          </td>
                          <td>{date(r.expected_close_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
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
                    <h2>Currency reference</h2>
                    <Badge>Demo rates</Badge>
                  </div>
                  <div className="settings-note">
                    Rates are copied onto a deal at conversion. These seeded
                    rates are examples, not current market quotes.
                  </div>
                  {d.reference.currencies.map((r) => (
                    <div className="rate-row" key={r.currency}>
                      <strong>{r.currency}</strong>
                      <span>
                        1 {r.currency} = {Number(r.rate).toFixed(6)} USD
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
                    <button
                      className="button secondary"
                      onClick={() => activityForm(p)}
                    >
                      <Plus size={14} />
                      Log interaction
                    </button>
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
                  ["Manager", "Executive"].includes(d.user.level) && (
                    <button
                      className="button yellow"
                      onClick={() => convertForm(p)}
                    >
                      Validate & convert
                    </button>
                  )}
              </div>
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
                    {p.opportunity_id ? "NET VALUE · USD" : "SOURCE"}
                  </small>
                  <strong>
                    {p.opportunity_id
                      ? money(p.net_value_usd)
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
                  "Timeline",
                  "Team & contacts",
                  "Documents",
                  ...(p.opportunity_id ? ["Value history"] : []),
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
                          {["Manager", "Executive"].includes(d.user.level) && (
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
                          Secure document links. Uploads and Outlook linking are
                          planned.
                        </p>
                      </div>
                      {p.can_work && (
                        <button
                          className="button secondary"
                          onClick={() =>
                            setForm({
                              title: "Register document evidence",
                              fields: [
                                field("title", "Document title"),
                                field("artifact_type", "Type", {
                                  options: options([
                                    "Deck",
                                    "Proposal",
                                    "Pricing",
                                    "NDA",
                                    "SOW",
                                    "Contract",
                                    "Purchase order",
                                    "Customer document",
                                    "Other",
                                  ]),
                                  value: "Proposal",
                                }),
                                field("storage_link", "Secure document URL", {
                                  type: "url",
                                }),
                                field("version", "Version", {
                                  type: "number",
                                  value: "1",
                                }),
                                field("internal_only", "Visibility", {
                                  options: [
                                    ["false", "Pursuit document"],
                                    ["true", "Internal team only"],
                                  ],
                                  value: "false",
                                }),
                              ],
                              submit: (v) =>
                                api("artifacts/", "POST", {
                                  ...v,
                                  pursuit: p.id,
                                }),
                            })
                          }
                        >
                          <Plus size={14} />
                          Add link
                        </button>
                      )}
                    </div>
                    {timeline?.artifacts.length ? (
                      timeline.artifacts.map((a) => (
                        <a
                          className="document-row"
                          href={a.url}
                          target="_blank"
                          rel="noreferrer"
                          key={a.id}
                        >
                          <FileText size={22} />
                          <span>
                            <strong>{a.title}</strong>
                            <small>
                              {a.type} · Version {a.version}
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
                {detailTab === "Value history" && (
                  <>
                    <div className="panel-heading">
                      <div>
                        <h3>Every value, preserved</h3>
                        <p>
                          {p.values_visible
                            ? `Currency: ${p.currency} · Fixed rate: ${p.fx_rate}`
                            : "Commercial values are restricted on this opportunity."}
                        </p>
                      </div>
                      {p.can_work && p.values_visible && (
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
                            {date(v.date)} · {v.note || "No note added"}
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
              {table(all.filter((r) => r.company_id === company.id))}
              <h3 className="spaced">Company interactions</h3>
              {d.activities
                .filter((a) => a.company === company.name)
                .map((a) => (
                  <div className="timeline-item" key={a.id}>
                    <span className="timeline-dot" />
                    <div>
                      <small>
                        {date(a.date)} · {a.author}
                      </small>
                      <h3>{a.subject}</h3>
                      <p>{a.notes}</p>
                    </div>
                  </div>
                ))}
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
                </div>
                <div>
                  <small>Outbound touches</small>
                  <strong>{contact.touch_count}</strong>
                </div>
              </div>
              <h3>Associated pursuits</h3>
              {table(
                all.filter(
                  (p) =>
                    p.contacts.some((c) => c.id === contact.id) ||
                    p.primary_contact_id === contact.id,
                ),
              )}
              <h3 className="spaced">Interaction history</h3>
              {d.activities
                .filter((a) => a.contact_id === contact.id)
                .map((a) => (
                  <div className="timeline-item" key={a.id}>
                    <span className="timeline-dot" />
                    <div>
                      <small>
                        {date(a.date)} · {a.activity_type} · {a.author}
                      </small>
                      <h3>{a.subject}</h3>
                      <p>{a.notes}</p>
                    </div>
                  </div>
                ))}
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
function exportCsv(rows: Pursuit[]) {
  const safe = (value: unknown) => {
    let s = String(value ?? "");
    if (/^[=+@\-\t\r]/.test(s)) s = "'" + s;
    return '"' + s.replaceAll('"', '""') + '"';
  };
  const lines = [
    [
      "Opportunity",
      "Company",
      "Stage",
      "Net USD",
      "Probability",
      "Expected close",
    ],
    ...rows.map((r) => [
      r.name,
      r.company,
      r.stage,
      r.net_value_usd,
      r.probability,
      r.expected_close_date,
    ]),
  ];
  const blob = new Blob(
    [lines.map((row) => row.map(safe).join(",")).join("\r\n")],
    { type: "text/csv;charset=utf-8;" },
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ATPLCRM-visible-forecast.csv";
  a.click();
  URL.revokeObjectURL(url);
}
