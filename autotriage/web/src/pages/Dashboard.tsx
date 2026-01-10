import React, { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client";
import StatCard from "../components/StatCard";
import Timeseries from "../charts/Timeseries";

type CaseRow = {
  case_id: string;
  created_at: string;
  severity: number;
  decision: string;
  queue: string;
  summary: string;
};

export default function Dashboard() {
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [overview, setOverview] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    apiGet<any>("/api/overview").then((r) => {
      if (!alive) return;
      if (!r.ok) return setError(r.error);
      setOverview(r.data);
    });
    apiGet<{ items: CaseRow[] }>("/api/cases?time_range=24h").then((r) => {
      if (!alive) return;
      if (!r.ok) return setError(r.error);
      setCases(r.data.items);
    });
    return () => {
      alive = false;
    };
  }, []);

  const stats = useMemo(() => {
    const s = overview?.stats ?? {};
    return {
      ingested: Number(s.ingested ?? 0),
      deduped: Number(s.deduped ?? 0),
      cases: Number(s.cases ?? cases.length),
      autoClosed: Number(s.auto_closed ?? 0),
      tickets: Number(s.tickets ?? 0),
      errors: Number(s.errors ?? 0)
    };
  }, [cases, overview]);

  const points = useMemo(() => {
    const byHour = new Map<string, number>();
    for (const c of cases) {
      const d = new Date(c.created_at);
      const k = `${d.getUTCFullYear()}-${d.getUTCMonth() + 1}-${d.getUTCDate()} ${d.getUTCHours()}:00`;
      byHour.set(k, (byHour.get(k) ?? 0) + 1);
    }
    return Array.from(byHour.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([t, v]) => ({ t, v }));
  }, [cases]);

  return (
    <div className="grid">
      <div className="row">
        <StatCard title="Ingested (24h)" value={stats.ingested} />
        <StatCard title="Deduped (24h)" value={stats.deduped} />
        <StatCard title="Cases (24h)" value={stats.cases} />
        <StatCard title="Tickets (24h)" value={stats.tickets} />
      </div>
      <div className="row">
        <StatCard title="Auto-Closed (24h)" value={stats.autoClosed} />
        <StatCard title="Errors (24h)" value={stats.errors} />
        <div />
        <div />
      </div>

      <div className="panel">
        <div className="panel-title">Cases Over Time</div>
        <Timeseries points={points} />
      </div>

      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}
