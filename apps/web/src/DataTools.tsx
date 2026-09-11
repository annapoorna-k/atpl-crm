import { useEffect, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  FileSearch,
  LoaderCircle,
  Merge,
  Search,
  Upload,
} from "lucide-react";
import { api } from "./api";
import type { Data } from "./types";

type SearchResult = {
  type: string;
  id: string;
  title: string;
  subtitle: string;
  status: string;
  owner: string;
  route: string;
};
type ImportError = { row: number; field: string; message: string };
type Preview = {
  headers: string[];
  suggested_mapping: Record<string, string | null>;
  sample: Record<string, string>[];
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: ImportError[];
  truncated_errors: boolean;
};
type ImportJob = {
  id: string;
  filename: string;
  entity_type: string;
  status: string;
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
  errors: ImportError[];
  created_at: string;
};
type DuplicateGroup = {
  entity_type: "companies" | "contacts";
  match_type: string;
  match_value: string;
  records: { id: string; name: string; detail: string }[];
};
type Quality = {
  score: number;
  records_checked: number;
  issue_count: number;
  duplicate_group_count: number;
  metrics: Record<string, number>;
  issues: {
    type: string;
    id: string;
    name: string;
    reason: string;
    severity: string;
    route: string;
  }[];
};

const fields: Record<string, string[]> = {
  companies: [
    "name",
    "country",
    "owner_email",
    "domain",
    "industry",
    "company_type",
    "primary_region",
    "global_account_name",
  ],
  contacts: [
    "company_name",
    "first_name",
    "last_name",
    "country",
    "owner_email",
    "email",
    "job_title",
    "phone",
    "mobile",
    "city",
    "source_channel",
  ],
  leads: [
    "name",
    "company_name",
    "owner_email",
    "next_action",
    "action_type",
    "action_date",
    "source_channel",
    "source_detail",
    "priority",
    "area_of_interest",
  ],
};
const required: Record<string, string[]> = {
  companies: ["name", "country", "owner_email"],
  contacts: [
    "company_name",
    "first_name",
    "last_name",
    "country",
    "owner_email",
  ],
  leads: [
    "name",
    "company_name",
    "owner_email",
    "next_action",
    "action_type",
    "action_date",
    "source_channel",
  ],
};
const label = (value: string) =>
  value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());

export function DataTools({
  data,
  notify,
  onChanged,
}: {
  data: Data;
  notify: (message: string) => void;
  onChanged: () => void;
}) {
  const [tab, setTab] = useState("search");
  const [busy, setBusy] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [searchType, setSearchType] = useState("all");
  const [owner, setOwner] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [entity, setEntity] = useState("companies");
  const [filename, setFilename] = useState("");
  const [csvText, setCsvText] = useState("");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<Preview | null>(null);
  const [history, setHistory] = useState<ImportJob[]>([]);
  const [duplicates, setDuplicates] = useState<DuplicateGroup[]>([]);
  const [quality, setQuality] = useState<Quality | null>(null);
  const canManage = ["Manager", "Executive", "Administrator"].includes(
    data.user.level,
  );

  const refreshInsights = async () => {
    const [jobs, duplicateData, qualityData] = await Promise.all([
      api<ImportJob[]>("data/imports/"),
      api<{ groups: DuplicateGroup[] }>("data/duplicates/"),
      api<Quality>("data/quality/"),
    ]);
    setHistory(jobs);
    setDuplicates(duplicateData.groups);
    setQuality(qualityData);
  };
  useEffect(() => {
    refreshInsights().catch((error) => notify((error as Error).message));
  }, []);

  async function search(event: FormEvent) {
    event.preventDefault();
    if (searchText.trim().length < 2) return;
    setBusy(true);
    try {
      const params = new URLSearchParams({
        q: searchText,
        entity_type: searchType,
      });
      if (owner) params.set("owner_id", owner);
      const response = await api<{ total: number; results: SearchResult[] }>(
        `data/search/?${params}`,
      );
      setResults(response.results);
      setSearchTotal(response.total);
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function downloadTemplate() {
    const template = await api<{ filename: string; csv_text: string }>(
      `data/templates/${entity}/`,
    );
    const url = URL.createObjectURL(
      new Blob([template.csv_text], { type: "text/csv;charset=utf-8" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = template.filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }
  async function validateImport() {
    if (!csvText) return notify("Choose a CSV file first.");
    setBusy(true);
    try {
      const result = await api<Preview>("data/imports/preview/", "POST", {
        entity_type: entity,
        filename,
        csv_text: csvText,
        mapping,
      });
      setPreview(result);
      setMapping(
        Object.fromEntries(
          Object.entries(result.suggested_mapping).filter(
            (entry): entry is [string, string] => Boolean(entry[1]),
          ),
        ),
      );
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function runImport() {
    setBusy(true);
    try {
      const job = await api<ImportJob>("data/imports/", "POST", {
        entity_type: entity,
        filename,
        csv_text: csvText,
        mapping,
      });
      notify(
        `${job.imported_rows} rows imported; ${job.skipped_rows} skipped.`,
      );
      setPreview(null);
      setCsvText("");
      setFilename("");
      await refreshInsights();
      onChanged();
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function downloadErrors(errors: ImportError[], name = filename) {
    const safe = (value: string | number) =>
      `"${String(value).replaceAll('"', '""')}"`;
    const rows = [
      ["row", "field", "message"],
      ...errors.map((error) => [error.row, error.field, error.message]),
    ];
    const url = URL.createObjectURL(
      new Blob([rows.map((row) => row.map(safe).join(",")).join("\r\n")], {
        type: "text/csv;charset=utf-8",
      }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${name.replace(/\.csv$/i, "")}-errors.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }
  async function mergeGroup(group: DuplicateGroup) {
    if (group.records.length < 2) return;
    setBusy(true);
    try {
      const [primary, ...rest] = group.records;
      for (const duplicate of rest) {
        await api(`data/duplicates/${group.entity_type}/merge/`, "POST", {
          primary_id: primary.id,
          duplicate_id: duplicate.id,
        });
      }
      notify(
        `Merged ${rest.length} record${rest.length === 1 ? "" : "s"} into ${primary.name}.`,
      );
      await refreshInsights();
      onChanged();
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="data-tools">
      <div className="data-tabs" role="tablist" aria-label="Data tools">
        {[
          ["search", "Global search", Search],
          ["import", "Import center", Upload],
          ["duplicates", `Duplicates (${duplicates.length})`, Merge],
          ["quality", "Data quality", CheckCircle2],
        ].map(([key, text, Icon]) => (
          <button
            key={String(key)}
            className={tab === key ? "active" : ""}
            onClick={() => setTab(String(key))}
            role="tab"
          >
            <Icon size={17} /> {String(text)}
          </button>
        ))}
      </div>

      {tab === "search" && (
        <section className="panel data-panel">
          <div className="panel-heading">
            <div>
              <h2>Search the whole workspace</h2>
              <p>
                Find relationships and pursuits with tenant-safe server search.
              </p>
            </div>
          </div>
          <form className="global-search-form" onSubmit={search}>
            <label>
              <span>Search terms</span>
              <div className="search-box">
                <Search size={18} />
                <input
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  placeholder="Name, email, domain, phone or pursuit…"
                  minLength={2}
                  required
                />
              </div>
            </label>
            <label>
              <span>Record type</span>
              <select
                value={searchType}
                onChange={(event) => setSearchType(event.target.value)}
              >
                <option value="all">All records</option>
                <option value="companies">Companies</option>
                <option value="contacts">Contacts</option>
                <option value="leads">Leads</option>
                <option value="opportunities">Opportunities</option>
              </select>
            </label>
            <label>
              <span>Owner</span>
              <select
                value={owner}
                onChange={(event) => setOwner(event.target.value)}
              >
                <option value="">All owners</option>
                {data.users.map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="button primary" disabled={busy}>
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <Search size={17} />
              )}{" "}
              Search
            </button>
          </form>
          {searchText && (
            <p className="result-summary">
              {searchTotal} result{searchTotal === 1 ? "" : "s"}
            </p>
          )}
          <div className="search-results">
            {results.map((result) => (
              <a
                className="search-result"
                href={`#${result.route}`}
                key={`${result.type}-${result.id}`}
              >
                <span className="result-icon">
                  <Database size={18} />
                </span>
                <span>
                  <small>{result.type}</small>
                  <strong>{result.title}</strong>
                  <em>{result.subtitle}</em>
                </span>
                <span>
                  <b>{result.status}</b>
                  <em>{result.owner}</em>
                </span>
              </a>
            ))}
          </div>
        </section>
      )}

      {tab === "import" && (
        <>
          <section className="panel data-panel">
            <div className="panel-heading">
              <div>
                <h2>CSV import center</h2>
                <p>Validate every row before writing it to ATPLCRM.</p>
              </div>
              <button className="button secondary" onClick={downloadTemplate}>
                <Download size={16} /> Download template
              </button>
            </div>
            {!canManage ? (
              <div className="data-access-note">
                <AlertTriangle size={20} /> Manager, Executive or Administrator
                access is required to import records.
              </div>
            ) : (
              <>
                <div className="import-controls">
                  <label>
                    <span>Record type</span>
                    <select
                      value={entity}
                      onChange={(event) => {
                        setEntity(event.target.value);
                        setPreview(null);
                        setMapping({});
                      }}
                    >
                      <option value="companies">Companies</option>
                      <option value="contacts">Contacts</option>
                      <option value="leads">Leads</option>
                    </select>
                  </label>
                  <label className="file-picker">
                    <Upload size={22} />
                    <span>
                      {filename || "Choose a UTF-8 CSV file"}
                      <small>Maximum 5,000 rows and 2 MB</small>
                    </span>
                    <input
                      type="file"
                      accept=".csv,text/csv"
                      onChange={async (event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        setFilename(file.name);
                        setCsvText(await file.text());
                        setPreview(null);
                        setMapping({});
                      }}
                    />
                  </label>
                  <button
                    className="button primary"
                    onClick={validateImport}
                    disabled={busy || !csvText}
                  >
                    {busy ? (
                      <LoaderCircle className="spin" size={17} />
                    ) : (
                      <FileSearch size={17} />
                    )}{" "}
                    Validate file
                  </button>
                </div>
                {preview && (
                  <div className="import-preview">
                    <div className="import-score">
                      <strong>{preview.valid_rows}</strong>
                      <span>valid rows</span>
                      <strong className={preview.invalid_rows ? "warn" : ""}>
                        {preview.invalid_rows}
                      </strong>
                      <span>rows with errors</span>
                    </div>
                    <h3>Column mapping</h3>
                    <div className="mapping-grid">
                      {fields[entity].map((field) => (
                        <label key={field}>
                          <span>
                            {label(field)}{" "}
                            {required[entity].includes(field) && <b>*</b>}
                          </span>
                          <select
                            value={mapping[field] ?? ""}
                            onChange={(event) =>
                              setMapping({
                                ...mapping,
                                [field]: event.target.value,
                              })
                            }
                          >
                            <option value="">Not mapped</option>
                            {preview.headers.map((header) => (
                              <option key={header}>{header}</option>
                            ))}
                          </select>
                        </label>
                      ))}
                    </div>
                    {preview.errors.length > 0 && (
                      <div className="import-errors">
                        <div className="import-error-heading">
                          <h3>Validation report</h3>
                          <button
                            className="text-button"
                            onClick={() => downloadErrors(preview.errors)}
                          >
                            <Download size={14} /> Download error CSV
                          </button>
                        </div>
                        {preview.errors.slice(0, 12).map((error, index) => (
                          <div key={`${error.row}-${error.field}-${index}`}>
                            <b>Row {error.row}</b>
                            <span>{label(error.field)}</span>
                            <em>{error.message}</em>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="import-actions">
                      <button
                        className="button secondary"
                        onClick={validateImport}
                      >
                        Revalidate mapping
                      </button>
                      <button
                        className="button primary"
                        onClick={runImport}
                        disabled={!preview.valid_rows || busy}
                      >
                        Import {preview.valid_rows} valid row
                        {preview.valid_rows === 1 ? "" : "s"}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
          <section className="panel data-panel">
            <div className="panel-heading">
              <h2>Import history</h2>
              <span className="badge">{history.length} runs</span>
            </div>
            {history.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>FILE</th>
                      <th>TYPE</th>
                      <th>STATUS</th>
                      <th>IMPORTED</th>
                      <th>SKIPPED</th>
                      <th>DATE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((job) => (
                      <tr key={job.id}>
                        <td>
                          <strong>{job.filename}</strong>
                        </td>
                        <td>{label(job.entity_type)}</td>
                        <td>
                          <span
                            className={`badge ${job.skipped_rows ? "yellow" : "green"}`}
                          >
                            {job.status}
                          </span>
                        </td>
                        <td>
                          {job.imported_rows} / {job.total_rows}
                        </td>
                        <td>{job.skipped_rows}</td>
                        <td>{new Date(job.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="data-empty">
                No imports have run in this workspace.
              </div>
            )}
          </section>
        </>
      )}

      {tab === "duplicates" && (
        <section className="panel data-panel">
          <div className="panel-heading">
            <div>
              <h2>Possible duplicate records</h2>
              <p>
                Matches use normalized company names, domains, email addresses
                and phone numbers.
              </p>
            </div>
            <span className="badge yellow">{duplicates.length} groups</span>
          </div>
          {duplicates.length ? (
            <div className="duplicate-list">
              {duplicates.map((group) => (
                <article
                  key={`${group.entity_type}-${group.match_type}-${group.match_value}`}
                >
                  <div>
                    <small>{group.match_type}</small>
                    <h3>{group.records.length} possible matches</h3>
                  </div>
                  <div className="duplicate-records">
                    {group.records.map((record, index) => (
                      <div key={record.id}>
                        <span>{index === 0 ? "KEEP" : "MERGE"}</span>
                        <strong>{record.name}</strong>
                        <small>{record.detail}</small>
                      </div>
                    ))}
                  </div>
                  {canManage && (
                    <button
                      className="button secondary"
                      onClick={() => mergeGroup(group)}
                      disabled={busy}
                    >
                      <Merge size={16} /> Keep first and merge others
                    </button>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="data-empty">
              <CheckCircle2 size={30} /> No exact duplicate groups found.
            </div>
          )}
        </section>
      )}

      {tab === "quality" && quality && (
        <>
          <div className="quality-metrics">
            <section className="quality-score">
              <span
                style={
                  { "--score": `${quality.score * 3.6}deg` } as CSSProperties
                }
              >
                <b>{quality.score}</b>
                <small>/ 100</small>
              </span>
              <div>
                <small>WORKSPACE QUALITY</small>
                <h2>
                  {quality.score >= 90
                    ? "Excellent"
                    : quality.score >= 70
                      ? "Good, with gaps"
                      : "Needs attention"}
                </h2>
                <p>{quality.records_checked} records checked</p>
              </div>
            </section>
            {Object.entries(quality.metrics).map(([key, value]) => (
              <section className="quality-stat" key={key}>
                <strong>{value}</strong>
                <span>{label(key)}</span>
              </section>
            ))}
          </div>
          <section className="panel data-panel">
            <div className="panel-heading">
              <div>
                <h2>Records requiring attention</h2>
                <p>
                  Resolve high-impact gaps first to keep follow-up and reporting
                  reliable.
                </p>
              </div>
              <span className="badge yellow">{quality.issue_count} issues</span>
            </div>
            {quality.issues.length ? (
              <div className="quality-list">
                {quality.issues.map((issue, index) => (
                  <a
                    href={`#${issue.route}`}
                    key={`${issue.type}-${issue.id}-${index}`}
                  >
                    <span
                      className={`severity ${issue.severity.toLowerCase()}`}
                    >
                      {issue.severity}
                    </span>
                    <span>
                      <strong>{issue.name}</strong>
                      <small>{issue.type}</small>
                    </span>
                    <em>{issue.reason}</em>
                  </a>
                ))}
              </div>
            ) : (
              <div className="data-empty">
                <CheckCircle2 size={30} /> All checked records meet the current
                quality rules.
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
