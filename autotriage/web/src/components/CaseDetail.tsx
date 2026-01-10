import React, { useMemo } from "react";
import CaseGraph from "./CaseGraph";

export default function CaseDetail({ data }: { data: any }) {
  const c = data.case ?? {};
  const graph = data.graph ?? { nodes: [], edges: [] };
  const enrichments = data.enrichments ?? {};
  const scoring = data.scoring ?? {};
  const actions = data.recommended_actions ?? [];

  const contributions = useMemo(() => scoring.contributions ?? [], [scoring]);

  return (
    <div className="grid">
      <div className="row">
        <div className="panel">
          <div className="panel-title">Case</div>
          <div className="kv">
            <div>Case ID</div>
            <div className="mono">{c.case_id}</div>
            <div>Decision</div>
            <div>{c.decision}</div>
            <div>Queue</div>
            <div>{c.queue}</div>
            <div>Severity</div>
            <div>{c.severity}</div>
            <div>Confidence</div>
            <div>{Number(scoring.confidence ?? 0).toFixed(2)}</div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-title">Recommended Actions</div>
          <ul className="list">
            {actions.map((a: any, i: number) => (
              <li key={i}>
                <a className="link" href={a.playbook} target="_blank" rel="noreferrer">
                  {a.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="row">
        <div className="panel">
          <div className="panel-title">Entity Graph</div>
          <CaseGraph graph={graph} />
        </div>
      </div>

      <div className="row">
        <div className="panel">
          <div className="panel-title">Timeline</div>
          <ul className="list">
            {(data.timeline ?? []).map((e: any) => (
              <li key={e.event_id}>
                <span className="mono">{e.created_at}</span> · <span className="pill">{e.stage}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <div className="panel-title">Enrichments</div>
          <pre className="code">{JSON.stringify(enrichments, null, 2)}</pre>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">Score Explainability</div>
        <table className="table">
          <thead>
            <tr>
              <th>Signal</th>
              <th>Weight</th>
              <th>Value</th>
              <th>Points</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {contributions.map((x: any, i: number) => (
              <tr key={i}>
                <td className="mono">{x.name}</td>
                <td>{x.weight}</td>
                <td>{x.value}</td>
                <td>{Number(x.points).toFixed(1)}</td>
                <td className="muted">{x.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

