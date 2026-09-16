import { useEffect, useRef, useState } from "react";
import { Building2, ContactRound, LoaderCircle, Search, Target, X } from "lucide-react";
import { api } from "./api";

export type GlobalSearchResult = {
  type: "Company" | "Contact" | "Lead" | "Opportunity";
  id: string;
  title: string;
  subtitle: string;
  status: string;
  owner: string;
  route: string;
  rank: number;
};

const icon = (type: GlobalSearchResult["type"]) => {
  if (type === "Company") return <Building2 size={17} />;
  if (type === "Contact") return <ContactRound size={17} />;
  return <Target size={17} />;
};

export function GlobalSearch({
  onOpen,
  onAllResults,
}: {
  onOpen: (result: GlobalSearchResult) => void;
  onAllResults: (query: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GlobalSearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const wrapper = useRef<HTMLDivElement>(null);
  const sequence = useRef(0);

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
        input.current?.focus();
      }
      if (event.key === "Escape") setOpen(false);
    };
    const outside = (event: MouseEvent) => {
      if (!wrapper.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("keydown", shortcut);
    document.addEventListener("mousedown", outside);
    return () => {
      window.removeEventListener("keydown", shortcut);
      document.removeEventListener("mousedown", outside);
    };
  }, []);

  useEffect(() => {
    const normalized = query.trim();
    if (normalized.length < 2) {
      setResults([]);
      setTotal(0);
      setBusy(false);
      setError("");
      return;
    }
    const current = ++sequence.current;
    setBusy(true);
    const timer = window.setTimeout(() => {
      api<{ total: number; results: GlobalSearchResult[] }>(
        `data/search/?q=${encodeURIComponent(normalized)}&entity_type=all&page=1&page_size=8`,
      )
        .then((response) => {
          if (current !== sequence.current) return;
          setResults(response.results);
          setTotal(response.total);
          setError("");
        })
        .catch((reason) => {
          if (current === sequence.current) setError((reason as Error).message);
        })
        .finally(() => {
          if (current === sequence.current) setBusy(false);
        });
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const select = (result: GlobalSearchResult) => {
    void api("data/search/recent/", "POST", {
      query: query.trim(),
      entity_type: "all",
      owner_id: null,
      country: "",
      status_filter: "",
    });
    onOpen(result);
    setOpen(false);
  };

  return (
    <div className="command-search" ref={wrapper}>
      <label className={`search ${open ? "is-open" : ""}`}>
        <Search size={16} />
        <input
          ref={input}
          value={query}
          onFocus={() => setOpen(true)}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          placeholder="Search all records…"
          aria-label="Search all companies, contacts, leads and opportunities"
          aria-expanded={open}
          aria-controls="command-search-results"
        />
        {busy ? (
          <LoaderCircle className="spin" size={14} />
        ) : query ? (
          <button
            type="button"
            className="icon-button"
            onClick={() => setQuery("")}
            aria-label="Clear global search"
          >
            <X size={13} />
          </button>
        ) : (
          <kbd>⌘K</kbd>
        )}
      </label>
      {open && (
        <section
          className="command-results"
          id="command-search-results"
          aria-label="Global search results"
          aria-live="polite"
        >
          {query.trim().length < 2 ? (
            <div className="command-hint">
              <Search size={20} />
              <span><strong>Search the whole workspace</strong><small>Companies, people, leads and opportunities</small></span>
            </div>
          ) : error ? (
            <p className="command-error">{error}</p>
          ) : !busy && !results.length ? (
            <div className="command-hint"><span><strong>No matching records</strong><small>Try a name, email, company or pursuit.</small></span></div>
          ) : (
            <>
              <div className="command-result-list">
                {results.map((result) => (
                  <button key={`${result.type}-${result.id}`} onClick={() => select(result)}>
                    <span className="command-result-icon">{icon(result.type)}</span>
                    <span><small>{result.type}</small><strong>{result.title}</strong><em>{result.subtitle}</em></span>
                    <span><b>{result.status}</b><small>{result.owner}</small></span>
                  </button>
                ))}
              </div>
              {total > results.length && (
                <button className="command-all" onClick={() => { onAllResults(query.trim()); setOpen(false); }}>
                  View all {total} results <span>→</span>
                </button>
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
