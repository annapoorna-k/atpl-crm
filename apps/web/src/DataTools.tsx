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
  rank: number;
};
type RecentSearch = {
  id: string;
  query: string;
  entity_type: string;
  filters: { owner_id: number | null; status_filter: string; country: string };
  use_count: number;
  last_used_at: string;
};
type ImportError = { row: number; field: string; message: string };
type ImportWarning = ImportError & { record_id: string; confidence: number };
type Preview = {
  headers: string[];
  suggested_mapping: Record<string, string | null>;
  sample: Record<string, string>[];
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: ImportError[];
  truncated_errors: boolean;
  warnings: ImportWarning[];
  truncated_warnings: boolean;
};
type ImportJob = {
  id: string;
  filename: string;
  file_type: string;
  entity_type: string;
  status: string;
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
  errors: ImportError[];
  warnings: ImportWarning[];
  created_at: string;
};
type DuplicateGroup = {
  entity_type: "companies" | "contacts";
  match_type: string;
  match_value: string;
  confidence: number;
  match_reasons: string[];
  records: {
    id: string;
    name: string;
    detail: string;
    fields: Record<string, string>;
  }[];
};
type Quality = {
  score: number;
  records_checked: number;
  issue_count: number;
  filtered_issue_count: number;
  duplicate_group_count: number;
  duplicate_record_count: number;
  metrics: Record<string, number>;
  severity_counts: Record<string, number>;
  page: number;
  pages: number;
  page_size: number;
  issues: {
    type: string;
    id: string;
    name: string;
    reason: string;
    code: string;
    severity: string;
    route: string;
    recommended_action: string;
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
    "sourced_by_email",
    "email",
    "job_title",
    "seniority",
    "phone",
    "mobile",
    "linkedin_url",
    "city",
    "source_channel",
    "source_detail",
    "engagement_status",
    "do_not_contact",
    "consent_basis",
    "notes",
  ],
  leads: [
    "name",
    "company_name",
    "owner_email",
    "holder_email",
    "sourced_by_email",
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

const base64File = (buffer: ArrayBuffer) => {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 32768) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768));
  }
  return btoa(binary);
};

export function DataTools({
  data,
  notify,
  onChanged,
  onOpen,
}: {
  data: Data;
  notify: (message: string) => void;
  onChanged: () => void;
  onOpen: (type: string, id: string) => void;
}) {
  const [tab, setTab] = useState("search");
  const [busy, setBusy] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [searchType, setSearchType] = useState("all");
  const [owner, setOwner] = useState("");
  const [searchCountry, setSearchCountry] = useState("");
  const [searchStatus, setSearchStatus] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchPage, setSearchPage] = useState(1);
  const [searchPages, setSearchPages] = useState(1);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [entity, setEntity] = useState("companies");
  const [filename, setFilename] = useState("");
  const [csvText, setCsvText] = useState("");
  const [fileContent, setFileContent] = useState("");
  const [fileType, setFileType] = useState<"csv" | "xlsx">("csv");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<Preview | null>(null);
  const [warningsConfirmed, setWarningsConfirmed] = useState(false);
  const [history, setHistory] = useState<ImportJob[]>([]);
  const [duplicates, setDuplicates] = useState<DuplicateGroup[]>([]);
  const [quality, setQuality] = useState<Quality | null>(null);
  const [qualitySeverity, setQualitySeverity] = useState("all");
  const [qualityType, setQualityType] = useState("all");
  const [mergeReview, setMergeReview] = useState<DuplicateGroup | null>(null);
  const [mergePrimary, setMergePrimary] = useState("");
  const [mergeSources, setMergeSources] = useState<Record<string, string>>({});
  const [dismissReasons, setDismissReasons] = useState<Record<string, string>>(
    {},
  );
  const canManage = ["Manager", "Executive", "Administrator"].includes(
    data.user.level,
  );

  const refreshInsights = async () => {
    const [jobs, duplicateData, qualityData] = await Promise.all([
      api<ImportJob[]>("data/imports/"),
      api<{ groups: DuplicateGroup[] }>("data/duplicates/"),
      api<Quality>(
        `data/quality/?severity=${qualitySeverity}&entity_type=${qualityType}&page=1&page_size=50`,
      ),
    ]);
    setHistory(jobs);
    setDuplicates(duplicateData.groups);
    setQuality(qualityData);
  };
  useEffect(() => {
    if (canManage) refreshInsights().catch((error) => notify((error as Error).message));
    api<RecentSearch[]>("data/search/recent/").then(setRecentSearches).catch((error) => notify((error as Error).message));
  }, []);

  async function runSearch(
    query = searchText,
    type = searchType,
    ownerId = owner,
    country = searchCountry,
    status = searchStatus,
    requestedPage = 1,
    remember = true,
  ) {
    if (query.trim().length < 2) return;
    setBusy(true);
    try {
      const params = new URLSearchParams({
        q: query,
        entity_type: type,
        page: String(requestedPage),
      });
      if (ownerId) params.set("owner_id", ownerId);
      if (country) params.set("country", country);
      if (status) params.set("status_filter", status);
      const response = await api<{ total: number; page: number; pages: number; results: SearchResult[] }>(
        `data/search/?${params}`,
      );
      setResults(response.results);
      setSearchTotal(response.total);
      setSearchPage(response.page);
      setSearchPages(response.pages);
      if (remember && requestedPage === 1) {
        await api<RecentSearch>("data/search/recent/", "POST", {
          query, entity_type: type, owner_id: ownerId ? Number(ownerId) : null,
          country, status_filter: status,
        });
        setRecentSearches(await api<RecentSearch[]>("data/search/recent/"));
      }
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function search(event: FormEvent) {
    event.preventDefault();
    await runSearch();
  }
  async function clearRecent() {
    await api("data/search/recent/", "DELETE");
    setRecentSearches([]);
    notify("Recent searches cleared.");
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
    if (!csvText && !fileContent)
      return notify("Choose a CSV or Excel file first.");
    setBusy(true);
    try {
      const result = await api<Preview>("data/imports/preview/", "POST", {
        entity_type: entity,
        filename,
        csv_text: csvText,
        file_content: fileContent,
        file_type: fileType,
        mapping,
      });
      setPreview(result);
      setWarningsConfirmed(false);
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
        file_content: fileContent,
        file_type: fileType,
        mapping,
        confirm_warnings: warningsConfirmed,
      });
      notify(
        `${job.imported_rows} rows imported; ${job.skipped_rows} skipped.`,
      );
      setPreview(null);
      setCsvText("");
      setFileContent("");
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
  function reviewMerge(group: DuplicateGroup) {
    const primary = group.records[0];
    setMergeReview(group);
    setMergePrimary(primary.id);
    setMergeSources(
      Object.fromEntries(
        Object.keys(primary.fields).map((field) => [field, primary.id]),
      ),
    );
  }
  async function mergeGroup() {
    if (!mergeReview || !mergePrimary) return;
    const duplicate = mergeReview.records.find(
      (record) => record.id !== mergePrimary,
    );
    if (!duplicate) return;
    setBusy(true);
    try {
      await api(`data/duplicates/${mergeReview.entity_type}/merge/`, "POST", {
        primary_id: mergePrimary,
        duplicate_id: duplicate.id,
        field_sources: mergeSources,
      });
      const primary = mergeReview.records.find(
        (record) => record.id === mergePrimary,
      );
      notify(`Merged the reviewed records into ${primary?.name}.`);
      setMergeReview(null);
      await refreshInsights();
      onChanged();
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function dismissGroup(group: DuplicateGroup) {
    const reason = dismissReasons[group.match_value]?.trim();
    if (!reason) return notify("Enter why these records are distinct.");
    setBusy(true);
    try {
      await api(`data/duplicates/${group.entity_type}/dismiss/`, "POST", {
        first_id: group.records[0].id,
        second_id: group.records[1].id,
        reason,
      });
      notify("The suggestion was reviewed and dismissed.");
      await refreshInsights();
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function loadQuality(
    severity = qualitySeverity,
    kind = qualityType,
    page = 1,
  ) {
    setBusy(true);
    try {
      const response = await api<Quality>(
        `data/quality/?severity=${severity}&entity_type=${kind}&page=${page}&page_size=50`,
      );
      setQuality(response);
    } catch (error) {
      notify((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function downloadQuality() {
    if (!quality) return;
    const safe = (value: string | number) =>
      `"${String(value).replaceAll('"', '""')}"`;
    const rows = [
      ["severity", "record_type", "record", "issue", "recommended_action"],
      ...quality.issues.map((issue) => [
        issue.severity,
        issue.type,
        issue.name,
        issue.reason,
        issue.recommended_action,
      ]),
    ];
    const url = URL.createObjectURL(
      new Blob([rows.map((row) => row.map(safe).join(",")).join("\r\n")], {
        type: "text/csv;charset=utf-8",
      }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "atplcrm-data-quality.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="data-tools">
      <div className="data-tabs" role="tablist" aria-label="Data tools">
        {[
          ["search", "Global search", Search],
          ["import", "Import center", Upload],
          ["duplicates", `Duplicates (${duplicates.length})`, Merge],
          ["quality", "Data quality", CheckCircle2],
        ].filter(([key]) => key === "search" || canManage).map(([key, text, Icon]) => (
          <button
            key={String(key)}
            className={tab === key ? "active" : ""}
            onClick={() => setTab(String(key))}
            role="tab"
            aria-selected={tab === key}
            aria-controls={`data-panel-${key}`}
          >
            <Icon size={17} /> {String(text)}
          </button>
        ))}
      </div>

      {tab === "search" && (
        <section className="panel data-panel" id="data-panel-search" role="tabpanel">
          <div className="panel-heading">
            <div>
              <h2>Search the whole workspace</h2>
              <p>
                Find relationships and pursuits with tenant-safe server search.
              </p>
            </div>
          </div>
          {recentSearches.length > 0 && (
            <div className="recent-searches" aria-label="Recent searches">
              <span>Recent</span>
              {recentSearches.map((recent) => (
                <button key={recent.id} type="button" onClick={() => {
                  const ownerId = recent.filters.owner_id ? String(recent.filters.owner_id) : "";
                  setSearchText(recent.query); setSearchType(recent.entity_type); setOwner(ownerId);
                  setSearchCountry(recent.filters.country || ""); setSearchStatus(recent.filters.status_filter || "");
                  void runSearch(recent.query, recent.entity_type, ownerId, recent.filters.country || "", recent.filters.status_filter || "", 1, false);
                }}>{recent.query}<small>{recent.entity_type === "all" ? "All records" : label(recent.entity_type)}</small></button>
              ))}
              <button type="button" className="text-button" onClick={() => void clearRecent()}>Clear history</button>
            </div>
          )}
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
            <label>
              <span>Country</span>
              <input value={searchCountry} onChange={(event) => setSearchCountry(event.target.value)} placeholder="Any country" />
            </label>
            {(searchType === "leads" || searchType === "opportunities") && (
              <label>
                <span>{searchType === "leads" ? "Status" : "Stage"}</span>
                <select value={searchStatus} onChange={(event) => setSearchStatus(event.target.value)}>
                  <option value="">All</option>
                  {(searchType === "leads" ? data.reference.lead_statuses : data.reference.stages).map(([value, text]) => <option key={value} value={value}>{text}</option>)}
                </select>
              </label>
            )}
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
            <p className="result-summary" role="status" aria-live="polite">
              {searchTotal} result{searchTotal === 1 ? "" : "s"}
            </p>
          )}
          <div className="search-results">
            {results.map((result) => (
              <button
                type="button"
                className="search-result"
                key={`${result.type}-${result.id}`}
                onClick={() => onOpen(result.type, result.id)}
                aria-label={`Open ${result.type} ${result.title}`}
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
              </button>
            ))}
          </div>
          {searchPages > 1 && (
            <div className="list-pagination" aria-label="Search result pages">
              <button className="button secondary" disabled={searchPage <= 1 || busy} onClick={() => void runSearch(searchText, searchType, owner, searchCountry, searchStatus, searchPage - 1, false)}>Previous</button>
              <span>Page {searchPage} of {searchPages}</span>
              <button className="button secondary" disabled={searchPage >= searchPages || busy} onClick={() => void runSearch(searchText, searchType, owner, searchCountry, searchStatus, searchPage + 1, false)}>Next</button>
            </div>
          )}
        </section>
      )}

      {tab === "import" && (
        <>
          <section className="panel data-panel">
            <div className="panel-heading">
              <div>
                <h2>CSV and Excel import center</h2>
                <p>
                  Map columns and dry-run every row before writing to ATPLCRM.
                </p>
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
                      {filename || "Choose a UTF-8 CSV or .xlsx file"}
                      <small>
                        Maximum 20,000 rows and 8 MB · first worksheet is used
                      </small>
                    </span>
                    <input
                      type="file"
                      accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                      onChange={async (event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        if (file.size > 8_000_000) {
                          notify("Choose a file no larger than 8 MB.");
                          event.target.value = "";
                          return;
                        }
                        setFilename(file.name);
                        if (file.name.toLowerCase().endsWith(".xlsx")) {
                          setFileType("xlsx");
                          setFileContent(base64File(await file.arrayBuffer()));
                          setCsvText("");
                        } else {
                          setFileType("csv");
                          setCsvText(await file.text());
                          setFileContent("");
                        }
                        setPreview(null);
                        setMapping({});
                        setWarningsConfirmed(false);
                      }}
                    />
                  </label>
                  <button
                    className="button primary"
                    onClick={validateImport}
                    disabled={busy || (!csvText && !fileContent)}
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
                    {preview.warnings.length > 0 && (
                      <div className="import-warnings">
                        <div className="import-error-heading">
                          <h3>Possible duplicates to review</h3>
                          <span className="badge yellow">
                            {preview.warnings.length} warnings
                          </span>
                        </div>
                        {preview.warnings.slice(0, 12).map((warning, index) => (
                          <div
                            key={`${warning.row}-${warning.record_id}-${index}`}
                          >
                            <b>{warning.confidence}%</b>
                            <span>Row {warning.row}</span>
                            <em>{warning.message}</em>
                          </div>
                        ))}
                        <label className="warning-confirmation">
                          <input
                            type="checkbox"
                            checked={warningsConfirmed}
                            onChange={(event) =>
                              setWarningsConfirmed(event.target.checked)
                            }
                          />
                          I reviewed these suggestions and confirm that the
                          valid rows should be created as separate records.
                        </label>
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
                        disabled={
                          !preview.valid_rows ||
                          busy ||
                          (preview.warnings.length > 0 && !warningsConfirmed)
                        }
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
                        <td>
                          {label(job.entity_type)} ·{" "}
                          {job.file_type.toUpperCase()}
                        </td>
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
                Exact and high-confidence fuzzy matches use company names,
                domains, contact names, email addresses and phone numbers.
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
                    <h3>{group.confidence}% match confidence</h3>
                  </div>
                  <div className="duplicate-records">
                    {group.records.map((record, index) => (
                      <div key={record.id}>
                        <span>{index === 0 ? "RECORD A" : "RECORD B"}</span>
                        <strong>{record.name}</strong>
                        <small>{record.detail}</small>
                      </div>
                    ))}
                  </div>
                  {canManage && (
                    <div className="duplicate-actions">
                      <button
                        className="button secondary"
                        onClick={() => reviewMerge(group)}
                        disabled={busy}
                      >
                        <Merge size={16} /> Review and merge
                      </button>
                      <div>
                        <input
                          aria-label={`Reason these ${group.records[0].name} records are distinct`}
                          placeholder="Why are these distinct?"
                          value={dismissReasons[group.match_value] ?? ""}
                          onChange={(event) =>
                            setDismissReasons({
                              ...dismissReasons,
                              [group.match_value]: event.target.value,
                            })
                          }
                        />
                        <button
                          className="text-button"
                          onClick={() => void dismissGroup(group)}
                          disabled={busy}
                        >
                          Not duplicates
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="data-empty">
              <CheckCircle2 size={30} /> No unresolved duplicate suggestions
              found.
            </div>
          )}
          {mergeReview && (
            <div
              className="merge-review"
              role="region"
              aria-label="Field by field merge review"
            >
              <div className="merge-review-heading">
                <div>
                  <small>MANUAL RESOLUTION</small>
                  <h2>Choose the surviving record and every retained value</h2>
                </div>
                <button
                  className="text-button"
                  onClick={() => setMergeReview(null)}
                >
                  Cancel
                </button>
              </div>
              <label className="merge-primary">
                Surviving record
                <select
                  value={mergePrimary}
                  onChange={(event) => {
                    const id = event.target.value;
                    setMergePrimary(id);
                    const record = mergeReview.records.find(
                      (item) => item.id === id,
                    )!;
                    setMergeSources(
                      Object.fromEntries(
                        Object.keys(record.fields).map((field) => [field, id]),
                      ),
                    );
                  }}
                >
                  {mergeReview.records.map((record) => (
                    <option value={record.id} key={record.id}>
                      {record.name} · {record.detail}
                    </option>
                  ))}
                </select>
              </label>
              <div className="merge-fields">
                {Object.keys(mergeReview.records[0].fields).map((field) => (
                  <div key={field}>
                    <strong>{label(field.replace(/_id$/, ""))}</strong>
                    {mergeReview.records.map((record) => (
                      <label
                        key={record.id}
                        className={
                          mergeSources[field] === record.id ? "selected" : ""
                        }
                      >
                        <input
                          type="radio"
                          name={`merge-${field}`}
                          value={record.id}
                          checked={mergeSources[field] === record.id}
                          onChange={() =>
                            setMergeSources({
                              ...mergeSources,
                              [field]: record.id,
                            })
                          }
                        />
                        <span>{record.fields[field] || "Not provided"}</span>
                        <small>{record.name}</small>
                      </label>
                    ))}
                  </div>
                ))}
              </div>
              <div className="merge-footer">
                <p>
                  All linked contacts, pursuits, activities, stakeholders and
                  partner references move to the surviving record. The other
                  record is archived.
                </p>
                <button
                  className="button primary"
                  onClick={() => void mergeGroup()}
                  disabled={busy}
                >
                  <Merge size={16} /> Confirm reviewed merge
                </button>
              </div>
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
              <div className="quality-actions">
                <select
                  aria-label="Quality severity"
                  value={qualitySeverity}
                  onChange={(event) => {
                    setQualitySeverity(event.target.value);
                    void loadQuality(event.target.value, qualityType);
                  }}
                >
                  <option value="all">All severities</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <select
                  aria-label="Quality record type"
                  value={qualityType}
                  onChange={(event) => {
                    setQualityType(event.target.value);
                    void loadQuality(qualitySeverity, event.target.value);
                  }}
                >
                  <option value="all">All records</option>
                  <option value="company">Companies</option>
                  <option value="contact">Contacts</option>
                  <option value="pursuit">Pursuits</option>
                </select>
                <button className="button secondary" onClick={downloadQuality}>
                  <Download size={15} /> Export displayed
                </button>
                <span className="badge yellow">
                  {quality.filtered_issue_count} issues
                </span>
              </div>
            </div>
            {quality.issues.length ? (
              <div className="quality-list">
                {quality.issues.map((issue, index) => (
                  <button
                    type="button"
                    onClick={() => onOpen(issue.type, issue.id)}
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
                    <span>
                      <em>{issue.reason}</em>
                      <small>{issue.recommended_action}</small>
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="data-empty">
                <CheckCircle2 size={30} /> All checked records meet the current
                quality rules.
              </div>
            )}
            {quality.pages > 1 && (
              <div className="quality-pagination">
                <span>
                  Page {quality.page} of {quality.pages}
                </span>
                <div>
                  <button
                    className="button secondary"
                    disabled={quality.page <= 1 || busy}
                    onClick={() =>
                      void loadQuality(
                        qualitySeverity,
                        qualityType,
                        quality.page - 1,
                      )
                    }
                  >
                    Previous
                  </button>
                  <button
                    className="button secondary"
                    disabled={quality.page >= quality.pages || busy}
                    onClick={() =>
                      void loadQuality(
                        qualitySeverity,
                        qualityType,
                        quality.page + 1,
                      )
                    }
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
