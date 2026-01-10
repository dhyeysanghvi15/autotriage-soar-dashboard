import React from "react";

export default function Timeseries({ points }: { points: { t: string; v: number }[] }) {
  const max = Math.max(1, ...points.map((p) => p.v));
  const w = 820;
  const h = 180;
  const pad = 16;
  const step = points.length > 1 ? (w - pad * 2) / (points.length - 1) : 0;
  const d = points
    .map((p, i) => {
      const x = pad + i * step;
      const y = h - pad - (p.v / max) * (h - pad * 2);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart">
      <path d={d} fill="none" stroke="#38bdf8" strokeWidth="2" />
    </svg>
  );
}

