import { useCallback, useEffect, useState } from "react";
import {
  Bookmark,
  ChevronLeft,
  ChevronRight,
  Download,
  FileSpreadsheet,
  ListFilter,
  LoaderCircle,
  Search,
  Trash2,
  Users,
} from "lucide-react";
import { api } from "./api";
import type { Company, Contact, Data, Pursuit } from "./types";

type Entity = "companies" | "contacts" | "leads" | "opportunities";
type Item = Company | Contact | Pursuit;
type Filters = {
  q: string;
  owner_id: string;
  holder_id: string;
  status: string;
  country: string;
  source: string;
  service: string;
  priority: string;
  blocker: string;
  partner: string;
  action_from: string;
  action_to: string;
  interaction_from: string;
  interaction_to: string;
  close_period: string;
  close_from: string;
  close_to: string;
  value_min: string;
  value_max: string;
  sort: string;
  direction: string;
};
type Result = {
  items: Item[];
  total: number;
  page: number;
  pages: number;
  page_size: number;
};
type SavedView = {
  id: string;
  entity_type: Entity;
  name: string;
  filters: Partial<Filters>;
};

const emptyFilters: Filters = {
  q: "",
  owner_id: "",
  holder_id: "",
  status: "",
  country: "",
  source: "",
  service: "",
  priority: "",
  blocker: "",
  partner: "",
  action_from: "",
  action_to: "",
  interaction_from: "",
  interaction_to: "",
  close_period: "",
  close_from: "",
  close_to: "",
  value_min: "",
  value_max: "",
  sort: "updated",
  direction: "desc",
};
const title = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

export function RecordList({
  entity,
  data,
  notify,
  onChanged,
  onOpen,
}: {
  entity: Entity;
  data: Data;
  notify: (message: string) => void;
  onChanged: () => void;
  onOpen: (item: Item) => void;
}) {
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<Result | null>(null);
  const [views, setViews] = useState<SavedView[]>([]);
  const [showSave, setShowSave] = useState(false);
  const [viewName, setViewName] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [newOwner, setNewOwner] = useState("");
  const [newHolder, setNewHolder] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "xlsx" | "">("");
  const storageKey = `atplcrm-list-${data.user.id}-${entity}`;
  const pursuitList = entity === "leads" || entity === "opportunities";
  const canBulk =
    pursuitList &&
    ["Manager", "Executive", "Administrator"].includes(data.user.level);
  const statuses =
    entity === "leads" ? data.reference.lead_statuses : data.reference.stages;

  const load = useCallback(
    async (requestedPage = page, requestedFilters = filters) => {
      setBusy(true);
      try {
        const params = new URLSearchParams({
          page: String(requestedPage),
          page_size: "25",
        });
        Object.entries(requestedFilters).forEach(([key, value]) => {
          if (value) params.set(key, value);
        });
        setResult(
          await api<Result>(
            `productivity/lists/${entity}/?${params.toString()}`,
          ),
        );
      } catch (error) {
        notify((error as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [entity, filters, notify, page],
  );

  useEffect(() => {
    let restoredFilters = emptyFilters;
    let restoredPage = 1;
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || "null");
      if (saved?.filters) restoredFilters = { ...emptyFilters, ...saved.filters };
      if (Number(saved?.page) > 0) restoredPage = Number(saved.page);
    } catch { /* Ignore invalid local navigation state. */ }
    setFilters(restoredFilters);
    setPage(restoredPage);
    setSelected([]);
    void api<SavedView[]>(`productivity/views/?entity_type=${entity}`).then(
      setViews,
    );
    void load(restoredPage, restoredFilters);
    // load is intentionally triggered only when the entity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entity]);

  function persist(nextFilters: Filters, nextPage: number) {
    sessionStorage.setItem(storageKey, JSON.stringify({ filters: nextFilters, page: nextPage }));
  }

  function change(key: keyof Filters, value: string) {
    const next = { ...filters, [key]: value };
    setFilters(next);
    setPage(1);
    setSelected([]);
    persist(next, 1);
    void load(1, next);
  }
  async function exportList(format: "csv" | "xlsx") {
    const params = new URLSearchParams({ export_format: format });
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    setExporting(format);
    try {
      const response = await fetch(`/api/v1/productivity/lists/${entity}/?${params}`, { credentials: "same-origin" });
      if (!response.ok) throw new Error("Export could not be prepared.");
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `atplcrm-${entity}.${format}`; anchor.click();
      URL.revokeObjectURL(url);
      notify(`${title(entity)} export downloaded.`);
    } catch (error) { notify((error as Error).message); }
    finally { setExporting(""); }
  }
  async function saveView() {
    if (!viewName.trim()) return;
    try {
      const saved = await api<SavedView>("productivity/views/", "POST", {
        entity_type: entity,
        name: viewName.trim(),
        filters,
      });
      setViews([...views, saved].sort((a, b) => a.name.localeCompare(b.name)));
      setViewName("");
      setShowSave(false);
      notify("Personal view saved.");
    } catch (error) {
      notify((error as Error).message);
    }
  }
  async function deleteView(identifier: string) {
    try {
      await api(`productivity/views/${identifier}/`, "DELETE");
      setViews(views.filter((view) => view.id !== identifier));
      notify("Personal view deleted.");
    } catch (error) {
      notify((error as Error).message);
    }
  }
  function applyView(view: SavedView) {
    const next = { ...emptyFilters, ...view.filters };
    setFilters(next);
    setPage(1);
    setSelected([]);
    persist(next, 1);
    void load(1, next);
  }
  async function assign() {
    if (!result || !selected.length) return;
    const pursuits = result.items.filter(
      (item): item is Pursuit =>
        "version" in item && selected.includes(item.id),
    );
    setBusy(true);
    try {
      await api("productivity/pursuits/bulk-assignment/", "POST", {
        pursuit_ids: pursuits.map((item) => item.id),
        versions: Object.fromEntries(
          pursuits.map((item) => [item.id, item.version]),
        ),
        owner_id: newOwner ? Number(newOwner) : undefined,
        holder_id: newHolder ? Number(newHolder) : undefined,
        reason,
      });
      setSelected([]);
      setNewOwner("");
      setNewHolder("");
      setReason("");
      await load();
      onChanged();
      notify(
        `${pursuits.length} pursuit${pursuits.length === 1 ? "" : "s"} assigned.`,
      );
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel record-list-panel">
      <div className="saved-view-bar">
        <span>
          <Bookmark size={15} /> Personal views
        </span>
        {views.map((view) => (
          <span className="saved-view-chip" key={view.id}>
            <button onClick={() => applyView(view)}>{view.name}</button>
            <button
              aria-label={`Delete ${view.name}`}
              onClick={() => deleteView(view.id)}
            >
              <Trash2 size={11} />
            </button>
          </span>
        ))}
        {showSave ? (
          <span className="save-view-form">
            <input
              aria-label="Saved view name"
              value={viewName}
              onChange={(event) => setViewName(event.target.value)}
              placeholder="View name"
              maxLength={80}
              autoFocus
            />
            <button onClick={saveView}>Save</button>
            <button onClick={() => setShowSave(false)}>Cancel</button>
          </span>
        ) : (
          <button className="text-button" onClick={() => setShowSave(true)}>
            + Save current filters
          </button>
        )}
        <span className="list-export-actions">
          <button className="text-button" disabled={Boolean(exporting)} onClick={() => void exportList("csv")}>{exporting === "csv" ? <LoaderCircle className="spin" size={13}/> : <Download size={13} />} CSV</button>
          <button className="text-button" disabled={Boolean(exporting)} onClick={() => void exportList("xlsx")}>{exporting === "xlsx" ? <LoaderCircle className="spin" size={13}/> : <FileSpreadsheet size={13} />} Excel</button>
        </span>
      </div>
      <div className="record-filter-grid">
        <label>
          <span>Search</span>
          <div>
            <Search size={15} />
            <input
              aria-label={`Search ${entity}`}
              value={filters.q}
              onChange={(event) =>
                setFilters({ ...filters, q: event.target.value })
              }
              onKeyDown={(event) =>
                event.key === "Enter" && change("q", filters.q)
              }
              placeholder={`Search ${entity}…`}
            />
          </div>
        </label>
        <label>
          <span>Owner</span>
          <select
            aria-label="List owner"
            value={filters.owner_id}
            onChange={(event) => change("owner_id", event.target.value)}
          >
            <option value="">All owners</option>
            {data.users.map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
              </option>
            ))}
          </select>
        </label>
        {pursuitList && (
          <label>
            <span>{entity === "leads" ? "Status" : "Stage"}</span>
            <select
              aria-label="List status"
              value={filters.status}
              onChange={(event) => change("status", event.target.value)}
            >
              <option value="">All</option>
              {statuses.map(([value, text]) => (
                <option key={value} value={value}>
                  {text}
                </option>
              ))}
            </select>
          </label>
        )}
        {pursuitList && (
          <label>
            <span>Priority</span>
            <select
              aria-label="List priority"
              value={filters.priority}
              onChange={(event) => change("priority", event.target.value)}
            >
              <option value="">All priorities</option>
              {["High", "Medium", "Low"].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
        )}
        <label>
          <span>Country</span>
          <input
            aria-label="List country"
            value={filters.country}
            onChange={(event) =>
              setFilters({ ...filters, country: event.target.value })
            }
            onBlur={() => change("country", filters.country)}
            placeholder="All countries"
          />
        </label>
        <label>
          <span>Sort</span>
          <select
            aria-label="List sort"
            value={filters.sort}
            onChange={(event) => change("sort", event.target.value)}
          >
            <option value="updated">Recently updated</option>
            <option value="name">Name</option>
            {pursuitList && (
              <option value="action_date">Next action date</option>
            )}
            {entity === "opportunities" && (
              <option value="close_date">Expected close</option>
            )}
            {pursuitList && (
              <option value="last_interaction">Last client interaction</option>
            )}
            {entity === "opportunities" && (
              <option value="value">Reporting value</option>
            )}
            <option value="created">Created date</option>
          </select>
        </label>
        <label>
          <span>Direction</span>
          <select
            aria-label="List sort direction"
            value={filters.direction}
            onChange={(event) => change("direction", event.target.value)}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
        <button
          className="button secondary clear-filters"
          onClick={() => {
            setFilters(emptyFilters);
            setPage(1);
            setSelected([]);
            persist(emptyFilters, 1);
            void load(1, emptyFilters);
          }}
        >
          <ListFilter size={15} /> Clear
        </button>
      </div>
      {pursuitList && (
        <details className="advanced-filter-panel">
          <summary>More pipeline filters</summary>
          <div className="advanced-filter-grid">
            <label>
              <span>Ball in Court</span>
              <select
                value={filters.holder_id}
                onChange={(e) => change("holder_id", e.target.value)}
              >
                <option value="">All holders</option>
                {data.users.map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Source</span>
              <select
                value={filters.source}
                onChange={(e) => change("source", e.target.value)}
              >
                <option value="">All sources</option>
                {data.reference.sources.map(([value, text]) => (
                  <option key={value} value={value}>
                    {text}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Next action from</span>
              <input
                type="date"
                value={filters.action_from}
                onChange={(e) => change("action_from", e.target.value)}
              />
            </label>
            <label>
              <span>Next action to</span>
              <input
                type="date"
                value={filters.action_to}
                onChange={(e) => change("action_to", e.target.value)}
              />
            </label>
            <label>
              <span>Last interaction from</span>
              <input
                type="date"
                value={filters.interaction_from}
                onChange={(e) => change("interaction_from", e.target.value)}
              />
            </label>
            <label>
              <span>Last interaction to</span>
              <input
                type="date"
                value={filters.interaction_to}
                onChange={(e) => change("interaction_to", e.target.value)}
              />
            </label>
            {entity === "opportunities" && (
              <>
                <label>
                  <span>Service</span>
                  <select
                    value={filters.service}
                    onChange={(e) => change("service", e.target.value)}
                  >
                    <option value="">All services</option>
                    {data.reference.services.map(([value, text]) => (
                      <option key={value} value={value}>
                        {text}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Blocker</span>
                  <select
                    value={filters.blocker}
                    onChange={(e) => change("blocker", e.target.value)}
                  >
                    <option value="">All blockers</option>
                    {data.reference.blockers.map(([value, text]) => (
                      <option key={value} value={value}>
                        {text}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Partner involvement</span>
                  <select
                    value={filters.partner}
                    onChange={(e) => change("partner", e.target.value)}
                  >
                    <option value="">Any</option>
                    <option value="yes">Has partner</option>
                    <option value="no">No partner</option>
                  </select>
                </label>
                <label>
                  <span>Close period</span>
                  <select
                    value={filters.close_period}
                    onChange={(e) => change("close_period", e.target.value)}
                  >
                    <option value="">Any period</option>
                    <option value="overdue">Passed close date</option>
                    <option value="this_month">This month</option>
                    <option value="this_quarter">This quarter</option>
                    <option value="next_quarter">Next quarter</option>
                  </select>
                </label>
                <label>
                  <span>Close from</span>
                  <input
                    type="date"
                    value={filters.close_from}
                    onChange={(e) => change("close_from", e.target.value)}
                  />
                </label>
                <label>
                  <span>Close to</span>
                  <input
                    type="date"
                    value={filters.close_to}
                    onChange={(e) => change("close_to", e.target.value)}
                  />
                </label>
                <label>
                  <span>Minimum value (USD)</span>
                  <input
                    type="number"
                    min="0"
                    value={filters.value_min}
                    onChange={(e) => change("value_min", e.target.value)}
                  />
                </label>
                <label>
                  <span>Maximum value (USD)</span>
                  <input
                    type="number"
                    min="0"
                    value={filters.value_max}
                    onChange={(e) => change("value_max", e.target.value)}
                  />
                </label>
              </>
            )}
          </div>
        </details>
      )}
      {canBulk && selected.length > 0 && (
        <div className="bulk-bar">
          <strong>{selected.length} selected</strong>
          <label>
            Owner
            <select
              aria-label="New commercial owner"
              value={newOwner}
              onChange={(event) => setNewOwner(event.target.value)}
            >
              <option value="">Keep owner</option>
              {data.users.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Ball in Court
            <select
              aria-label="New Ball in Court holder"
              value={newHolder}
              onChange={(event) => setNewHolder(event.target.value)}
            >
              <option value="">Keep holder</option>
              {data.users.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Reason
            <input
              aria-label="Assignment reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Why is this changing?"
            />
          </label>
          <button
            className="button yellow"
            disabled={busy || (!newOwner && !newHolder) || !reason.trim()}
            onClick={assign}
          >
            <Users size={15} /> Apply assignment
          </button>
        </div>
      )}
      <div className={`table-scroll ${busy && result ? "is-refreshing" : ""}`} aria-busy={busy}>
        {busy && result && <div className="list-progress"><LoaderCircle className="spin" size={15}/> Refreshing records…</div>}
        <table>
          <thead>
            <tr>
              {canBulk && (
                <th>
                  <input
                    type="checkbox"
                    aria-label="Select all visible pursuits"
                    onChange={() =>
                      setSelected(
                        selected.length
                          ? []
                          : (result?.items ?? []).map((item) => item.id),
                      )
                    }
                  />
                </th>
              )}
              <th>
                {entity === "contacts"
                  ? "CONTACT"
                  : entity === "companies"
                    ? "COMPANY"
                    : "PURSUIT"}
              </th>
              <th>{pursuitList ? "STAGE / STATUS" : "COUNTRY / COMPANY"}</th>
              <th>OWNER</th>
              <th>{pursuitList ? "BALL IN COURT" : "DETAIL"}</th>
              <th>{pursuitList ? "NEXT ACTION" : "STATUS"}</th>
            </tr>
          </thead>
          <tbody>
            {busy && !result ? (
              <tr>
                <td colSpan={6}>
                  <div className="list-skeleton" aria-label="Loading records">{Array.from({ length: 5 }, (_, index) => <span key={index}/>)}</div>
                </td>
              </tr>
            ) : (
              result?.items.map((item) => {
                const pursuit = "version" in item ? (item as Pursuit) : null;
                const contact = "first_name" in item ? (item as Contact) : null;
                const company = !pursuit && !contact ? (item as Company) : null;
                return (
                  <tr key={item.id}>
                    {canBulk && (
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Select ${"name" in item ? item.name : "record"}`}
                          checked={selected.includes(item.id)}
                          onChange={() =>
                            setSelected(
                              selected.includes(item.id)
                                ? selected.filter((id) => id !== item.id)
                                : [...selected, item.id],
                            )
                          }
                        />
                      </td>
                    )}
                    <td>
                      <button
                        className="record-name"
                        onClick={() => onOpen(item)}
                      >
                        {pursuit?.name ?? contact?.name ?? company?.name}
                      </button>
                      {contact && <small>{contact.job_title}</small>}
                      {company && <small>{company.industry}</small>}
                    </td>
                    <td>
                      {pursuit
                        ? (pursuit.stage ?? pursuit.status)
                        : contact
                          ? contact.company
                          : company?.country}
                    </td>
                    <td>
                      {pursuit?.owner ?? contact?.owner ?? company?.owner}
                    </td>
                    <td>
                      {pursuit?.holder ?? contact?.email ?? company?.domain}
                    </td>
                    <td>
                      {pursuit ? (
                        <>
                          <strong>{pursuit.next_action}</strong>
                          <small>{pursuit.action_date}</small>
                        </>
                      ) : contact ? (
                        contact.engagement_status
                      ) : (
                        company?.company_type
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      <div className="list-pagination">
        <span>
          {result?.total ?? 0} {title(entity).toLowerCase()} · Page{" "}
          {result?.page ?? 1} of {result?.pages ?? 1}
        </span>
        <div>
          <button
            className="icon-button"
            aria-label="Previous page"
            disabled={!result || result.page <= 1 || busy}
            onClick={() => {
              const next = page - 1;
              setPage(next);
              persist(filters, next);
              void load(next);
            }}
          >
            <ChevronLeft />
          </button>
          <button
            className="icon-button"
            aria-label="Next page"
            disabled={!result || result.page >= result.pages || busy}
            onClick={() => {
              const next = page + 1;
              setPage(next);
              persist(filters, next);
              void load(next);
            }}
          >
            <ChevronRight />
          </button>
        </div>
      </div>
    </section>
  );
}
