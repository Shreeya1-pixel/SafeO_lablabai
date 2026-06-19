import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchFullStats } from "../api";

export default function Logs() {
  const [searchParams] = useSearchParams();
  const source = (searchParams.get("source") || "").toLowerCase();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFullStats()
      .then((stats) => {
        let list = stats?.recent_decisions || [];
        if (source) {
          list = list.filter((r) => {
            const s = (r.source_system || "").toLowerCase();
            if (source === "odoo") return s === "odoo" || s.includes("odoo");
            return s === source || s.includes(source);
          });
        }
        setRows(list);
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [source]);

  return (
    <div className="safeo-page">
      <div className="safeo-page-header">
        <h2>Risk Engine Logs</h2>
        <p>
          {source
            ? `Showing decisions from source: ${source}`
            : "All recent decisions from the SafeO engine"}
        </p>
      </div>
      <div className="safeo-card">
        {loading ? (
          <p className="safeo-muted">Loading…</p>
        ) : !rows.length ? (
          <p className="safeo-muted">No log entries for this filter.</p>
        ) : (
          <table className="safeo-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Request ID</th>
                <th>Source</th>
                <th>Tier</th>
                <th>Risk</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.request_id || row.time}>
                  <td>{formatTime(row.time)}</td>
                  <td className="mono">{(row.request_id || "").slice(0, 12)}</td>
                  <td>{row.source_system || "—"}</td>
                  <td>T{row.tier_used || 1}</td>
                  <td>{Math.round((row.risk_score || 0) * 100)}%</td>
                  <td>
                    <span className={`decision-badge ${decisionClass(row.decision)}`}>{row.decision}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function formatTime(ts) {
  if (!ts) return "—";
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

function decisionClass(d) {
  const v = String(d || "").toLowerCase();
  if (v === "block") return "block";
  if (v === "warn") return "warn";
  return "allow";
}
