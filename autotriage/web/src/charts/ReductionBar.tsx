import React from "react";

export default function ReductionBar({
  title,
  before,
  after,
  percent
}: {
  title: string;
  before: number;
  after: number;
  percent?: boolean;
}) {
  const b = Number(before) || 0;
  const a = Number(after) || 0;
  const denom = Math.max(1, b);
  const reduction = Math.max(0, (b - a) / denom);
  const pct = Math.round(reduction * 100);
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="card-value">{percent ? `${a.toFixed(1)}%` : `${a}`}</div>
      <div className="bar">
        <div className="bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="muted">Reduction: {pct}%</div>
    </div>
  );
}

