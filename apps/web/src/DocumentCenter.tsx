import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Archive, CheckCircle2, Download, ExternalLink, FileClock, FilePlus2, FileText, Library, Link2, Mail, RefreshCw, Search, Send, ShieldCheck, Upload, X } from "lucide-react";
import { api, apiForm } from "./api";
import type { ArtifactRecord, Data } from "./types";

const types = ["Deck", "Proposal", "Case study", "Video", "Demo / POC output", "Technical architecture", "Pricing", "NDA", "SOW", "Contract", "Purchase order", "Customer document", "Other"];
const classifications = ["Customer communication", "Internal approval", "Proposal sent", "Technical information", "Other"];
type DialogState = { kind: "create" | "share" | "version" | "reuse"; artifact?: ArtifactRecord } | null;

const formatDate = (value?: string | null) => value ? new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not recorded";
const size = (value: number) => value ? value > 1024 * 1024 ? `${(value / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(value / 1024)} KB` : "Metadata only";

export function DocumentCenter({ data, onChanged }: { data: Data; onChanged: () => void }) {
  const [scope, setScope] = useState<"all" | "shared" | "library">("all");
  const [query, setQuery] = useState("");
  const [companyFilter, setCompanyFilter] = useState("");
  const [pursuitFilter, setPursuitFilter] = useState("");
  const [rows, setRows] = useState<ArtifactRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState<DialogState>(null);
  const [createMode, setCreateMode] = useState<"link" | "upload" | "email">("link");
  const dialogRef = useRef<HTMLDialogElement>(null);
  const pursuits = useMemo(() => [...data.opportunities, ...data.leads.filter((item) => item.outcome !== "Converted")], [data]);
  const editablePursuits = pursuits.filter((item) => item.can_work);
  const management = ["Administrator", "Manager", "Executive"].includes(data.user.level);

  async function load() {
    setBusy(true); setError("");
    const route = scope === "shared" ? "artifacts/register/" : scope === "library" ? "artifacts/library/" : "artifacts/";
    const params = new URLSearchParams({ search: query });
    if (companyFilter) params.set("company_id", companyFilter);
    if (pursuitFilter) params.set("pursuit_id", pursuitFilter);
    try { setRows(await api<ArtifactRecord[]>(`${route}?${params}`)); }
    catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }
  useEffect(() => { const timer = setTimeout(() => void load(), 180); return () => clearTimeout(timer); }, [scope, query, companyFilter, pursuitFilter, data]);
  useEffect(() => { if (dialog) dialogRef.current?.showModal(); }, [dialog]);
  const close = () => { dialogRef.current?.close(); setDialog(null); setError(""); };
  const changed = async () => { await load(); onChanged(); close(); };

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      if (createMode === "link") {
        await api("artifacts/links/", "POST", {
          pursuit: form.get("pursuit"), title: form.get("title"), artifact_type: form.get("artifact_type"),
          storage_link: form.get("storage_link"), internal_only: form.has("internal_only"), is_reusable: form.has("is_reusable"),
        });
      } else if (createMode === "upload") {
        await apiForm("artifacts/uploads/", form);
      } else {
        form.set("participants", JSON.stringify(String(form.get("participants") || "").split(/[;,\n]/).map((item) => item.trim()).filter(Boolean)));
        form.set("recipient_contact_ids", JSON.stringify(form.getAll("recipient_contact_ids")));
        await apiForm("artifacts/emails/", form);
      }
      await changed();
    } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }

  async function submitAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!dialog?.artifact) return;
    setBusy(true); setError(""); const form = new FormData(event.currentTarget); const item = dialog.artifact;
    try {
      if (dialog.kind === "share") {
        await api(`artifacts/${item.id}/share/`, "POST", { contact_ids: form.getAll("contact_ids"), shared_at: form.get("shared_at") || null });
      } else if (dialog.kind === "reuse") {
        await api(`artifacts/${item.id}/reuse/`, "POST", { pursuit: form.get("pursuit"), title: form.get("title") || null });
      } else if (dialog.kind === "version") {
        if (item.kind === "Uploaded file") await apiForm(`artifacts/${item.id}/versions/upload/`, form);
        else await api(`artifacts/${item.id}/versions/link/`, "POST", {
          pursuit: item.pursuit_id, title: form.get("title"), artifact_type: form.get("artifact_type"), storage_link: form.get("storage_link"),
          internal_only: form.has("internal_only"), is_reusable: form.has("is_reusable"),
        });
      }
      await changed();
    } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }

  async function quick(path: string, body?: unknown) {
    setBusy(true); setError("");
    try { await api(path, "POST", body); await load(); onChanged(); }
    catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }

  return <>
    <section className="panel document-center">
      <div className="panel-heading">
        <div><h2>Documents & client-shared register</h2><p>One controlled record of files, Microsoft 365 links and manually linked emails.</p></div>
        <button className="button primary" onClick={() => { setCreateMode("link"); setDialog({ kind: "create" }); }} disabled={!editablePursuits.length}><FilePlus2 size={17}/> Register artifact</button>
      </div>
      <div className="document-toolbar">
        <div className="segmented">
          <button className={scope === "all" ? "active" : ""} onClick={() => setScope("all")}><Archive size={15}/> All artifacts</button>
          <button className={scope === "shared" ? "active" : ""} onClick={() => setScope("shared")}><Send size={15}/> Client-shared</button>
          <button className={scope === "library" ? "active" : ""} onClick={() => setScope("library")}><Library size={15}/> Reusable library</button>
        </div>
        <label className="document-search"><Search size={16}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title, type or email subject"/></label>
      </div>
      <div className="document-filter-row"><label>Company<select value={companyFilter} onChange={(event) => { setCompanyFilter(event.target.value); setPursuitFilter(""); }}><option value="">All companies</option>{data.companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}</select></label><label>Pursuit<select value={pursuitFilter} onChange={(event) => setPursuitFilter(event.target.value)}><option value="">All pursuits</option>{pursuits.filter((pursuit) => !companyFilter || pursuit.company_id === companyFilter).map((pursuit) => <option key={pursuit.id} value={pursuit.id}>{pursuit.name}</option>)}</select></label></div>
      {scope === "shared" && <div className="register-note"><ShieldCheck size={18}/><span><strong>Client-shared register</strong> Ordered by delivery date with the company, pursuit, version and named recipients.</span></div>}
      {error && <p className="error" role="alert">{error}</p>}
      {busy && !rows.length ? <div className="document-loading"><RefreshCw className="spin"/> Loading artifacts…</div> : rows.length ? <div className="artifact-grid">
        {rows.map((item) => {
          const canWork = pursuits.find((pursuit) => pursuit.id === item.pursuit_id)?.can_work;
          return <article className={`artifact-card ${item.superseded ? "superseded" : ""}`} key={item.id}>
            <div className="artifact-icon">{item.kind === "Linked email" ? <Mail/> : item.kind === "Uploaded file" ? <FileText/> : <Link2/>}</div>
            <div className="artifact-main">
              <div className="artifact-title"><strong>{item.title}</strong><span className="badge neutral">v{item.version}</span>{item.superseded && <span className="badge">Superseded</span>}{item.internal_only && <span className="badge">Internal</span>}</div>
              <p>{item.company} · {item.pursuit}</p>
              <small>{item.artifact_type} · {item.kind} · {size(item.byte_size)}</small>
              {item.kind === "Linked email" && <small>{item.email_classification} · {item.email_direction} · {formatDate(item.email_date)}</small>}
              {item.shared_with_client && <div className="shared-line"><CheckCircle2 size={15}/><span>Shared {formatDate(item.shared_at)} with {item.recipients.map((person) => person.name).join(", ") || "recorded email participants"}</span></div>}
              {!item.shared_with_client && <small>{item.approved ? `Approved by ${item.approved_by}` : "Awaiting approval before client sharing"}</small>}
            </div>
            <div className="artifact-actions">
              {item.url && <a className="icon-button" href={item.url} target="_blank" rel="noreferrer" title={item.kind === "Uploaded file" ? "Download" : "Open"}>{item.kind === "Uploaded file" ? <Download size={17}/> : <ExternalLink size={17}/>}</a>}
              {management && !item.approved && !item.internal_only && !item.superseded && <button className="text-button" onClick={() => void quick(`artifacts/${item.id}/approve/`)}>Approve</button>}
              {canWork && item.approved && !item.internal_only && !item.superseded && <button className="text-button" onClick={() => setDialog({ kind: "share", artifact: item })}>Record share</button>}
              {canWork && item.kind !== "Linked email" && !item.superseded && <button className="text-button" onClick={() => setDialog({ kind: "version", artifact: item })}>New version</button>}
              {canWork && item.kind !== "Linked email" && <button className="text-button" onClick={() => void quick(`artifacts/${item.id}/library/`, { enabled: !item.is_reusable })}>{item.is_reusable ? "Remove from library" : "Add to library"}</button>}
              {scope === "library" && item.is_reusable && <button className="text-button" onClick={() => setDialog({ kind: "reuse", artifact: item })}>Use in pursuit</button>}
            </div>
          </article>;
        })}
      </div> : <div className="empty"><FileText size={32}/><h3>No artifacts found</h3><p>Register a secure link, managed file or selected email.</p></div>}
    </section>
    {dialog && <dialog className="form-dialog artifact-dialog" ref={dialogRef} onCancel={close}>
      <div className="dialog-heading"><div><span className="eyebrow">CONTROLLED ARTIFACT</span><h2>{dialog.kind === "create" ? "Register artifact" : dialog.kind === "share" ? "Record client sharing" : dialog.kind === "reuse" ? "Use reusable asset" : "Add a new version"}</h2></div><button className="icon-button" onClick={close}><X size={20}/></button></div>
      {dialog.kind === "create" ? <form onSubmit={submitCreate}>
        <div className="segmented artifact-methods"><button type="button" className={createMode === "link" ? "active" : ""} onClick={() => setCreateMode("link")}><Link2 size={15}/> M365 link</button><button type="button" className={createMode === "upload" ? "active" : ""} onClick={() => setCreateMode("upload")}><Upload size={15}/> Upload</button><button type="button" className={createMode === "email" ? "active" : ""} onClick={() => setCreateMode("email")}><Mail size={15}/> Selected email</button></div>
        <div className="form-grid">
          <label className="full">Pursuit *<select name="pursuit" required>{editablePursuits.map((item) => <option key={item.id} value={item.id}>{item.company} · {item.name}</option>)}</select></label>
          {createMode !== "email" && <><label>Title *<input name="title" required maxLength={180}/></label><label>Artifact type *<select name="artifact_type" defaultValue="Proposal">{types.map((value) => <option key={value}>{value}</option>)}</select></label></>}
          {createMode === "link" && <label className="full">SharePoint or OneDrive URL *<input type="url" name="storage_link" required/></label>}
          {createMode === "upload" && <label className="full">File *<input type="file" name="file" required accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.png,.jpg,.jpeg,.gif,.msg,.eml,.mp4"/><small>Private managed storage · maximum 10 MB</small></label>}
          {createMode === "email" && <>
            <label className="full">Subject *<input name="subject" required maxLength={250}/></label><label>Classification *<select name="classification">{classifications.map((value) => <option key={value}>{value}</option>)}</select></label><label>Direction *<select name="direction"><option>Outbound</option><option>Inbound</option></select></label>
            <label>Email date *<input name="email_date" type="datetime-local" required/></label><label>Outlook message link or ID *<input name="message_reference" required/></label>
            <label className="full">Participants *<textarea name="participants" rows={2} required placeholder="name@client.com; colleague@atpl.com"/></label>
            <fieldset className="full checkbox-fieldset"><legend>Client recipients (required for outbound email)</legend><span className="checkbox-options">{data.contacts.map((contact) => <label key={contact.id}><input type="checkbox" name="recipient_contact_ids" value={contact.id}/>{contact.name} · {contact.company}</label>)}</span></fieldset>
            <label className="full">Attachments carried by this email<input type="file" name="attachments" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.png,.jpg,.jpeg,.gif,.msg,.eml,.mp4"/><small>Each attachment is registered automatically as its own artifact.</small></label>
          </>}
          {createMode !== "email" && <><label className="check-row"><input type="checkbox" name="internal_only"/> Internal team only</label><label className="check-row"><input type="checkbox" name="is_reusable"/> Add to reusable library</label></>}
          {createMode === "email" && <label className="check-row full"><input type="checkbox" name="internal_only"/> Internal email; do not place it in the client-shared register</label>}
        </div>{error && <p className="error">{error}</p>}<div className="dialog-actions"><button type="button" className="button secondary" onClick={close}>Cancel</button><button className="button primary" disabled={busy}>{busy ? <RefreshCw className="spin" size={16}/> : null} Register</button></div>
      </form> : <form onSubmit={submitAction}><div className="form-grid">
        {dialog.kind === "share" && <><p className="full form-description">Record exactly who received <strong>{dialog.artifact?.title}</strong> and when.</p><fieldset className="full checkbox-fieldset"><legend>Client contacts *</legend><span className="checkbox-options">{data.contacts.filter((contact) => contact.company_id === dialog.artifact?.company_id).map((contact) => <label key={contact.id}><input type="checkbox" name="contact_ids" value={contact.id}/>{contact.name} · {contact.email}</label>)}</span></fieldset><label className="full">Shared at<input type="datetime-local" name="shared_at"/><small>Leave blank to use the current time.</small></label></>}
        {dialog.kind === "reuse" && <><label className="full">Target pursuit *<select name="pursuit" required>{editablePursuits.map((item) => <option key={item.id} value={item.id}>{item.company} · {item.name}</option>)}</select></label><label className="full">Title<input name="title" defaultValue={dialog.artifact?.title}/></label></>}
        {dialog.kind === "version" && <><div className="version-notice full"><FileClock size={18}/> Version {(dialog.artifact?.version || 0) + 1} will supersede v{dialog.artifact?.version}; the earlier version remains visible.</div><label>Title *<input name="title" defaultValue={dialog.artifact?.title} required/></label><label>Artifact type *<select name="artifact_type" defaultValue={dialog.artifact?.artifact_type}>{types.map((value) => <option key={value}>{value}</option>)}</select></label>{dialog.artifact?.kind === "Uploaded file" ? <label className="full">Replacement file *<input type="file" name="file" required/></label> : <label className="full">New SharePoint or OneDrive URL *<input type="url" name="storage_link" required/></label>}<label className="check-row"><input type="checkbox" name="internal_only" defaultChecked={dialog.artifact?.internal_only}/> Internal team only</label><label className="check-row"><input type="checkbox" name="is_reusable" defaultChecked={dialog.artifact?.is_reusable}/> Reusable library</label></>}
      </div>{error && <p className="error">{error}</p>}<div className="dialog-actions"><button type="button" className="button secondary" onClick={close}>Cancel</button><button className="button primary" disabled={busy}>{dialog.kind === "share" ? "Record sharing" : dialog.kind === "reuse" ? "Attach asset" : "Create version"}</button></div></form>}
    </dialog>}
  </>;
}
