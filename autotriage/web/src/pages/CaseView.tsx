import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet } from "../api/client";
import CaseDetail from "../components/CaseDetail";

export default function CaseView() {
  const { caseId } = useParams();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    apiGet<any>(`/api/cases/${caseId}`).then((r) => {
      if (!r.ok) return setError(r.error);
      setData(r.data);
    });
  }, [caseId]);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="muted">Loading…</div>;
  return <CaseDetail data={data} />;
}

