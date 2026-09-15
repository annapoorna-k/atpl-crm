import { useEffect, useMemo, useState } from "react";
import { ArrowDownToLine, BarChart3, ChevronRight, FileSpreadsheet, Filter, LoaderCircle, X } from "lucide-react";
import { api } from "./api";
import type { Data, Pursuit } from "./types";

type Row = Record<string, string | number | null | string[]> & { record_ids?: string[] };
type ReportRecord = { id: string; name: string; company: string; owner: string; stage_label: string; net_value_usd: string | null; expected_close_date: string | null };
type Analytics = {
  pipeline_total_usd: string;
  pipeline: Row[]; forecast_month: Row[]; forecast_quarter: Row[];
  lead_funnel: Row[]; lead_by_source: Row[]; lead_by_user: Row[];
  blockers_by_type: Row[]; blockers_by_owner: Row[]; outcomes: Row[];
  loss_reasons: Row[]; value_erosion: Row[]; movement: Row[];
  performance: Row[]; milestones: Row[]; records: ReportRecord[];
};

const tabs = [
  ["pipeline", "Pipeline & forecast"], ["leads", "Lead funnel"], ["bottlenecks", "Bottlenecks"],
  ["blockers", "Blockers"], ["outcomes", "Win/loss"], ["erosion", "Value erosion"],
  ["movement", "Movement"], ["people", "People"],
] as const;
const money = (value: string | number | null | undefined) => value == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(Number(value));

function ReportRows({ rows, label, value, onSelect, empty = "No matching data." }: { rows: Row[]; label: (row: Row) => string; value: (row: Row) => string; onSelect: (row: Row, title: string) => void; empty?: string }) {
  if (!rows.length) return <p className="settings-note">{empty}</p>;
  const maximum = Math.max(...rows.map((row) => Number(row.count ?? row.closed ?? row.deal_count ?? 0)), 1);
  return <div className="analytics-rows">{rows.map((row, index) => {
    const title = label(row); const amount = Number(row.count ?? row.closed ?? row.deal_count ?? 0);
    return <button key={`${title}-${index}`} onClick={() => onSelect(row, title)}>
      <span><strong>{title}</strong><small>{value(row)}</small><i style={{ width: `${Math.max(3, amount / maximum * 100)}%` }}/></span><ChevronRight size={17}/>
    </button>;
  })}</div>;
}

export function ReportsCenter({ data, onOpen }: { data: Data; onOpen: (pursuit: Pursuit) => void }) {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [tab, setTab] = useState<(typeof tabs)[number][0]>("pipeline");
  const [period, setPeriod] = useState("365d");
  const [fromDate, setFromDate] = useState(""); const [toDate, setToDate] = useState("");
  const [owner, setOwner] = useState(""); const [service, setService] = useState(""); const [source, setSource] = useState("");
  const [country, setCountry] = useState(""); const [opportunityType, setOpportunityType] = useState(""); const [groupBy, setGroupBy] = useState("service_line");
  const [drilldown, setDrilldown] = useState<{ title: string; ids: string[] } | null>(null); const [error, setError] = useState("");
  const services = useMemo(() => [...new Set(data.opportunities.map((row) => row.service_line).filter(Boolean))].sort(), [data]);
  const countryValues = useMemo(() => [...new Set(data.companies.map((row) => row.country).filter(Boolean))].sort(), [data]);
  const opportunityTypes = useMemo(() => [...new Set(data.opportunities.map((row) => row.opportunity_type).filter(Boolean))].sort(), [data]);
  const params = useMemo(() => {
    const value = new URLSearchParams({ period, group_by: groupBy });
    if (period === "custom") { if (fromDate) value.set("from_date", fromDate); if (toDate) value.set("to_date", toDate); }
    if (owner) value.set("owner_id", owner); if (service) value.set("service_line", service); if (source) value.set("source", source);
    if (country) value.set("country", country); if (opportunityType) value.set("opportunity_type", opportunityType);
    return value;
  }, [period, fromDate, toDate, owner, service, source, country, opportunityType, groupBy]);

  useEffect(() => {
    if (period === "custom" && (!fromDate || !toDate)) return;
    setAnalytics(null); setError(""); setDrilldown(null);
    api<Analytics>(`reports/analytics/?${params}`).then(setAnalytics).catch((reason) => setError((reason as Error).message));
  }, [params, period, fromDate, toDate]);
  const select = (row: Row, title: string) => setDrilldown({ title, ids: row.record_ids ?? [] });
  const drillRows = drilldown && analytics ? analytics.records.filter((row) => drilldown.ids.includes(row.id)) : [];
  const pursuitFor = (id: string) => [...data.opportunities, ...data.leads].find((row) => row.id === id);
  const reportName = tab === "pipeline" ? "pipeline" : tab === "leads" ? "lead_funnel" : tab === "bottlenecks" ? "milestones" : tab === "blockers" ? "blockers_by_type" : tab === "outcomes" ? "outcomes" : tab === "erosion" ? "value_erosion" : tab === "movement" ? "movement" : "performance";
  const download = (format: "csv" | "xlsx") => { location.href = `/api/v1/reports/export/?report=${reportName}&format=${format}&${params}`; };

  return <section className="panel analytics-center">
    <div className="panel-heading"><div><h2>Management analytics</h2><p>Server-calculated net USD reporting with filters, record drill-down and governed exports.</p></div><div className="report-export"><button className="button secondary" onClick={() => download("csv")}><ArrowDownToLine size={15}/> CSV</button><button className="button secondary" onClick={() => download("xlsx")}><FileSpreadsheet size={15}/> Excel</button></div></div>
    <div className="report-filters"><span><Filter size={16}/> Filters</span><label>Period<select value={period} onChange={(e) => setPeriod(e.target.value)}><option value="30d">Last 30 days</option><option value="90d">Last 90 days</option><option value="365d">Last year</option><option value="24m">Last 24 months</option><option value="all">All history</option><option value="custom">Custom</option></select></label>{period === "custom" && <><label>From<input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)}/></label><label>To<input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)}/></label></>}<label>Owner<select value={owner} onChange={(e) => setOwner(e.target.value)}><option value="">All owners</option>{data.users.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label><label>Service<select value={service} onChange={(e) => setService(e.target.value)}><option value="">All services</option>{services.map((value) => <option key={value}>{value}</option>)}</select></label><label>Source<select value={source} onChange={(e) => setSource(e.target.value)}><option value="">All sources</option>{data.reference.sources.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Country<select value={country} onChange={(e) => setCountry(e.target.value)}><option value="">All countries</option>{countryValues.map((value) => <option key={value}>{value}</option>)}</select></label><label>Opportunity type<select value={opportunityType} onChange={(e) => setOpportunityType(e.target.value)}><option value="">All types</option>{opportunityTypes.map((value) => <option key={value}>{value}</option>)}</select></label></div>
    <div className="analytics-tabs">{tabs.map(([key, label]) => <button className={tab === key ? "active" : ""} onClick={() => { setTab(key); setDrilldown(null); }} key={key}>{label}</button>)}</div>
    {error && <p className="error">{error}</p>}
    {!analytics && !error ? <div className="document-loading"><LoaderCircle className="spin"/> Calculating report…</div> : analytics && <div className="analytics-body">
      {tab === "pipeline" && <div className="analytics-columns"><div><h3>Current pipeline by stage</h3><button className="analytics-total" onClick={() => setDrilldown({ title: "Open pipeline", ids: analytics.pipeline.flatMap((row) => row.record_ids ?? []) })}><BarChart3/><span><small>NET OPEN PIPELINE</small><strong>{money(analytics.pipeline_total_usd)}</strong></span></button><ReportRows rows={analytics.pipeline} label={(r) => String(r.label)} value={(r) => `${r.count} opportunities · ${money(r.net_value_usd as string)}`} onSelect={select}/></div><div><h3>Weighted forecast by month</h3><ReportRows rows={analytics.forecast_month} label={(r) => String(r.period)} value={(r) => `${r.count} opportunities · ${money(r.weighted_value_usd as string)} weighted`} onSelect={select}/><h3 className="spaced">Weighted forecast by quarter</h3><ReportRows rows={analytics.forecast_quarter} label={(r) => String(r.period)} value={(r) => `${money(r.weighted_value_usd as string)} weighted`} onSelect={select}/></div></div>}
      {tab === "leads" && <div className="analytics-columns three"><div><h3>Lifecycle funnel</h3><ReportRows rows={analytics.lead_funnel} label={(r) => String(r.stage)} value={(r) => `${r.count} leads`} onSelect={select}/></div><div><h3>By source</h3><ReportRows rows={analytics.lead_by_source} label={(r) => String(r.key)} value={(r) => `${r.created} created · ${r.converted} converted`} onSelect={select}/></div><div><h3>By sourced user</h3><ReportRows rows={analytics.lead_by_user} label={(r) => String(r.key)} value={(r) => `${r.engaged} engaged · ${r.converted} converted`} onSelect={select}/></div></div>}
      {tab === "bottlenecks" && <div><h3>Seven-transition bottleneck funnel</h3><ReportRows rows={analytics.milestones} label={(r) => String(r.label)} value={(r) => `${r.count} completed · ${r.median_working_days ?? "—"} median working days`} onSelect={select}/></div>}
      {tab === "blockers" && <div className="analytics-columns"><div><h3>By blocker type</h3><ReportRows rows={analytics.blockers_by_type} label={(r) => String(r.key)} value={(r) => `${r.count} open · median ${r.median_days}d · oldest ${r.oldest_days}d`} onSelect={select}/></div><div><h3>By blocker owner</h3><ReportRows rows={analytics.blockers_by_owner} label={(r) => String(r.key)} value={(r) => `${r.count} open · oldest ${r.oldest_days}d`} onSelect={select}/></div></div>}
      {tab === "outcomes" && <><div className="group-control"><label>Group outcomes by<select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}><option value="service_line">Service line</option><option value="source">Source</option><option value="country">Country</option><option value="opportunity_type">Opportunity type</option><option value="owner">Owner</option></select></label></div><div className="analytics-columns"><div><h3>Win rate, deal size and cycle</h3><ReportRows rows={analytics.outcomes} label={(r) => String(r.key)} value={(r) => `${r.win_rate_pct}% win · ${money(r.average_deal_size_usd as string)} average · ${r.median_cycle_working_days ?? "—"}d cycle`} onSelect={select}/></div><div><h3>Loss reason distribution</h3><ReportRows rows={analytics.loss_reasons} label={(r) => String(r.key)} value={(r) => `${r.count} losses`} onSelect={select}/></div></div></>}
      {tab === "erosion" && <><div className="group-control"><label>View value erosion by<select value={groupBy === "owner" ? "owner" : "service_line"} onChange={(e) => setGroupBy(e.target.value)}><option value="service_line">Service line</option><option value="owner">Owner</option></select></label></div><ReportRows rows={analytics.value_erosion} label={(r) => String(r.key)} value={(r) => `${r.deal_count} won · ${money(r.initial_usd as string)} initial → ${money(r.final_usd as string)} final · ${r.erosion_pct}%`} onSelect={select}/></>}
      {tab === "movement" && <ReportRows rows={analytics.movement} label={(r) => String(r.key).replaceAll("_", " ").replace(/^./, (v) => v.toUpperCase())} value={(r) => `${r.count} pursuits in selected dates`} onSelect={select}/>} 
      {tab === "people" && <div className="people-report"><table><thead><tr><th>PERSON</th><th>LEADS GENERATED</th><th>OPPORTUNITIES OWNED</th><th>PRE-SALES DELIVERED</th><th>BALL IN COURT</th><th>BLOCKERS OWNED</th></tr></thead><tbody>{analytics.performance.map((row) => <tr key={String(row.user_id)}><td><strong>{row.user}</strong></td>{[["leads_generated","leads_generated_ids"],["opportunities_owned","opportunities_owned_ids"],["presales_delivered","presales_delivered_ids"],["ball_in_court","ball_in_court_ids"],["blockers_owned","blockers_owned_ids"]].map(([value, ids]) => <td key={value}><button className="table-number" onClick={() => setDrilldown({ title: `${row.user} · ${value.replaceAll("_", " ")}`, ids: row[ids] as string[] })}>{row[value]}</button></td>)}</tr>)}</tbody></table></div>}
      {drilldown && <aside className="report-drilldown"><div className="panel-heading"><div><h3>{drilldown.title}</h3><p>{drillRows.length} underlying record{drillRows.length === 1 ? "" : "s"}</p></div><button className="icon-button" onClick={() => setDrilldown(null)}><X size={18}/></button></div>{drillRows.map((row) => <button key={row.id} onClick={() => { const pursuit = pursuitFor(row.id); if (pursuit) onOpen(pursuit); }}><span><strong>{row.name}</strong><small>{row.company} · {row.owner} · {row.stage_label}</small></span><span>{money(row.net_value_usd)}<ChevronRight size={16}/></span></button>)}{!drillRows.length && <p className="settings-note">No records in your visible dataset.</p>}</aside>}
    </div>}
  </section>;
}
