import { getApiKey } from "./utils/connections";

const API = "/api";

export async function fetchBackendHealth() {
  const res = await fetch(`${API}/v1/health`, {
    headers: { Authorization: `Bearer ${getApiKey()}` },
  });
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

export async function fetchOdooHealth() {
  try {
    const res = await fetch("/odoo-health", { signal: AbortSignal.timeout(4000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchFullStats() {
  const res = await fetch(`${API}/ml/full-stats`);
  if (!res.ok) throw new Error("Metrics unavailable");
  return res.json();
}

export function odooMetricsFromStats(stats) {
  const rows = stats?.recent_decisions || [];
  const odooRows = rows.filter((r) => {
    const src = (r.source_system || "").toLowerCase();
    return src === "odoo" || src.includes("odoo");
  });

  const today = new Date().toISOString().slice(0, 10);
  const blockedToday = odooRows.filter(
    (r) => r.decision === "BLOCK" && String(r.time || "").startsWith(today)
  ).length;

  const last = odooRows[0];
  return {
    lastScan: last?.time || null,
    blockedToday,
    totalOdoo: odooRows.length,
  };
}

export async function testEndpoint(url) {
  try {
    const res = await fetch(url, { method: "GET", signal: AbortSignal.timeout(5000) });
    return res.ok;
  } catch {
    return false;
  }
}
