import React from "react";
import { Link } from "react-router-dom";

type CaseRow = {
  case_id: string;
  created_at: string;
  severity: number;
  decision: string;
  queue: string;
  summary: string;
};

export default function CaseTable({ items }: { items: CaseRow[] }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>When</th>
          <th>Severity</th>
          <th>Decision</th>
          <th>Queue</th>
          <th>Summary</th>
        </tr>
      </thead>
      <tbody>
        {items.map((c) => (
          <tr key={c.case_id}>
            <td className="muted">{new Date(c.created_at).toLocaleString()}</td>
            <td>{c.severity}</td>
            <td>
              <span className={`pill pill-${c.decision.toLowerCase()}`}>{c.decision}</span>
            </td>
            <td>{c.queue}</td>
            <td>
              <Link className="link" to={`/cases/${c.case_id}`}>
                {c.summary}
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

