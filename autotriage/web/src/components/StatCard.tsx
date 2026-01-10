import React from "react";

export default function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
    </div>
  );
}

