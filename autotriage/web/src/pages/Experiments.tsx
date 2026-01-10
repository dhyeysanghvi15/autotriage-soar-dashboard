import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";
import ReductionBar from "../charts/ReductionBar";
import RuleDiffViewer from "../components/RuleDiffViewer";

type ExperimentRow = { experiment_id: string; created_at: string; since: string; until: string };

export default function Experiments() {
  const [items, setItems] = useState<ExperimentRow[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    apiGet<{ items: ExperimentRow[] }>("/api/experiments").then((r) => {
      if (!r.ok) return setError(r.error);
      setItems(r.data.items);
    });
  };

  useEffect(() => refresh(), []);

  const run = async () => {
    const until = new Date().toISOString();
    const since = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const r = await apiPost<{ experiment_id: string }>("/api/replay", {
      since,
      until,
      config_overrides: { scoring: { weights: { "signal.ip_rep.bad": 35 } } }
    });
    if (!r.ok) return setError(r.error);
    refresh();
  };

  const load = async (id: string) => {
    const r = await apiGet<any>(`/api/experiments/${id}`);
    if (!r.ok) return setError(r.error);
    setSelected(r.data);
  };

  return (
    <div className="grid">
      <div className="row">
        <button className="btn" onClick={run}>
          Run Replay (last 60m)
        </button>
        {error ? <div className="error">{error}</div> : null}
      </div>

      <div className="panel">
        <div className="panel-title">Experiments</div>
        <div className="split">
          <div>
            <div className="muted">Click an experiment to view results.</div>
            <ul className="list">
              {items.map((x) => (
                <li key={x.experiment_id}>
                  <button className="link" onClick={() => load(x.experiment_id)}>
                    {x.experiment_id.slice(0, 8)} · {new Date(x.created_at).toLocaleString()}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            {selected ? (
              <>
                <div className="panel-title">Before / After</div>
                <div className="row">
                  <ReductionBar
                    title="Ticket Reduction %"
                    before={selected.before?.tickets ?? 0}
                    after={selected.after?.tickets ?? 0}
                  />
                  <ReductionBar
                    title="Auto-close Rate %"
                    before={selected.before?.auto_close_rate_pct ?? 0}
                    after={selected.after?.auto_close_rate_pct ?? 0}
                    percent
                  />
                </div>
                <div className="panel-title">Rule Overrides</div>
                <RuleDiffViewer />
              </>
            ) : (
              <div className="muted">No experiment selected.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

