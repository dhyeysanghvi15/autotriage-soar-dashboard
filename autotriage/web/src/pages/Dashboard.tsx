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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
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
    const byDecision = new Map<string, number>();
    for (const c of cases) byDecision.set(c.decision, (byDecision.get(c.decision) ?? 0) + 1);
    return {
      cases: cases.length,
      autoClose: byDecision.get("AUTO_CLOSE") ?? 0,
      tickets: (byDecision.get("CREATE_TICKET") ?? 0) + (byDecision.get("ESCALATE") ?? 0),
      escalations: byDecision.get("ESCALATE") ?? 0
    };
  }, [cases]);

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
        <StatCard title="Cases (24h)" value={stats.cases} />
        <StatCard title="Tickets" value={stats.tickets} />
        <StatCard title="Auto-Closed" value={stats.autoClose} />
        <StatCard title="Escalations" value={stats.escalations} />
      </div>

      <div className="panel">
        <div className="panel-title">Cases Over Time</div>
        <Timeseries points={points} />
      </div>

      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}

