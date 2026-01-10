import React, { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client";
import CaseTable from "../components/CaseTable";

type CaseRow = {
  case_id: string;
  created_at: string;
  severity: number;
  decision: string;
  queue: string;
  summary: string;
};

export default function Cases() {
  const [items, setItems] = useState<CaseRow[]>([]);
  const [q, setQ] = useState("");
  const [decision, setDecision] = useState("");
  const [severityMin, setSeverityMin] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams();
    params.set("time_range", "24h");
    if (q) params.set("q", q);
    if (decision) params.set("decision", decision);
    if (severityMin) params.set("severity_min", String(severityMin));
    apiGet<{ items: CaseRow[] }>(`/api/cases?${params.toString()}`).then((r) => {
      if (!r.ok) return;
      setItems(r.data.items);
    });
  }, [q, decision, severityMin]);

  const counts = useMemo(() => items.length, [items]);

  return (
    <div className="grid">
      <div className="panel">
        <div className="panel-title">Cases</div>
        <div className="filters">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search (entity/case/summary)" />
          <select value={decision} onChange={(e) => setDecision(e.target.value)}>
            <option value="">Decision: any</option>
            <option value="AUTO_CLOSE">AUTO_CLOSE</option>
            <option value="CREATE_TICKET">CREATE_TICKET</option>
            <option value="ESCALATE">ESCALATE</option>
          </select>
          <input
            type="number"
            value={severityMin}
            onChange={(e) => setSeverityMin(Number(e.target.value))}
            min={0}
            max={100}
            placeholder="Severity min"
          />
          <div className="muted">{counts} results</div>
        </div>
        <CaseTable items={items} />
      </div>
    </div>
  );
}

