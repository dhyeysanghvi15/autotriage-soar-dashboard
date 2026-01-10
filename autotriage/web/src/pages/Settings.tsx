import React, { useEffect, useState } from "react";
import { apiGet } from "../api/client";

export default function Settings() {
  const [cfg, setCfg] = useState<any>(null);
  useEffect(() => {
    apiGet<any>("/api/config").then((r) => {
      if (!r.ok) return;
      setCfg(r.data);
    });
  }, []);

  return (
    <div className="panel">
      <div className="panel-title">Config</div>
      <pre className="code">{cfg ? JSON.stringify(cfg, null, 2) : "Loading…"}</pre>
    </div>
  );
}

