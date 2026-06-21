"""
Self-contained HTML dashboard for the CI/CD Guardian Agent.

Served at GET /dashboard. It fetches GET /dashboard/data (which honors the
optional API key) and renders summary cards, a severity chart, top anomalies,
and a recent-incidents table. Chart.js is loaded from a CDN — no build step.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CI/CD Guardian — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --muted:#94a3b8; --text:#e2e8f0;
          --crit:#ef4444; --high:#f97316; --med:#eab308; --low:#3b82f6; --ok:#22c55e; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         background:var(--bg); color:var(--text); }
  header { padding:20px 28px; border-bottom:1px solid #334155; display:flex;
           align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; }
  header h1 { margin:0; font-size:20px; }
  header .meta { color:var(--muted); font-size:13px; }
  main { padding:24px 28px; max-width:1100px; margin:0 auto; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; }
  .card { background:var(--card); border:1px solid #334155; border-radius:12px; padding:16px; }
  .card .label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
  .card .value { font-size:28px; font-weight:700; margin-top:6px; }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px; }
  @media (max-width:760px){ .grid2 { grid-template-columns:1fr; } }
  .panel { background:var(--card); border:1px solid #334155; border-radius:12px; padding:16px; }
  .panel h2 { margin:0 0 12px; font-size:15px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #334155; }
  th { color:var(--muted); font-weight:600; }
  .pill { padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700; text-transform:uppercase; }
  .s-critical{background:var(--crit);color:#fff} .s-high{background:var(--high);color:#111}
  .s-medium{background:var(--med);color:#111} .s-low{background:var(--low);color:#fff}
  .s-none{background:#334155;color:var(--muted)}
  .blocked{color:var(--crit);font-weight:700} .allowed{color:var(--ok);font-weight:700}
  .empty{color:var(--muted);padding:14px 0}
  code{color:var(--muted)}
</style>
</head>
<body>
<header>
  <h1>🛡️ CI/CD Guardian — Dashboard</h1>
  <div class="meta" id="meta">loading…</div>
</header>
<main>
  <div class="cards" id="cards"></div>
  <div class="grid2">
    <div class="panel"><h2>Severity distribution</h2><canvas id="sevChart" height="200"></canvas></div>
    <div class="panel"><h2>Top anomalies</h2><canvas id="anomChart" height="200"></canvas></div>
  </div>
  <div class="panel" style="margin-top:18px">
    <h2>Recent incidents</h2>
    <div id="recent"></div>
  </div>
</main>
<script>
const KEY = new URLSearchParams(location.search).get("key");
const headers = KEY ? { "X-API-Key": KEY } : {};

function card(label, value){ return `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`; }
function pill(sev){ return `<span class="pill s-${sev}">${sev}</span>`; }

async function load(){
  let data;
  try {
    const res = await fetch("/dashboard/data", { headers });
    if (res.status === 401){ document.getElementById("meta").textContent = "Unauthorized — add ?key=YOUR_API_KEY"; return; }
    data = await res.json();
  } catch (e){ document.getElementById("meta").textContent = "Failed to load data"; return; }

  const m = data.metrics, recent = data.recent || [];
  document.getElementById("meta").textContent =
    `backend: ${m.ltm_backend || "?"} · last analysis: ${m.last_analysis_timestamp || "—"}`;

  document.getElementById("cards").innerHTML = [
    card("Pipelines analyzed", m.total_pipelines_analyzed),
    card("Success rate", m.success_rate_percent + "%"),
    card("Critical", m.critical_incidents),
    card("High", m.high_severity_incidents),
    card("Avg duration", Math.round(m.average_duration_seconds) + "s"),
  ].join("");

  new Chart(document.getElementById("sevChart"), {
    type: "doughnut",
    data: { labels:["Critical","High","Medium","Low"],
      datasets:[{ data:[m.critical_incidents,m.high_severity_incidents,m.medium_severity_incidents,m.low_severity_incidents],
      backgroundColor:["#ef4444","#f97316","#eab308","#3b82f6"] }] },
    options:{ plugins:{ legend:{ labels:{ color:"#e2e8f0" } } } }
  });

  const top = m.top_anomalies || [];
  new Chart(document.getElementById("anomChart"), {
    type: "bar",
    data: { labels: top.map(a=>a.type), datasets:[{ label:"count", data: top.map(a=>a.count), backgroundColor:"#38bdf8" }] },
    options:{ indexAxis:"y", plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:{ color:"#94a3b8" } }, y:{ ticks:{ color:"#94a3b8" } } } }
  });

  if (!recent.length){ document.getElementById("recent").innerHTML = `<div class="empty">No incidents recorded yet.</div>`; return; }
  const rows = recent.map(r => `<tr>
    <td><code>${r.pipeline_id}</code></td>
    <td>${pill(r.severity)}</td>
    <td>${r.status}</td>
    <td>${r.branch}</td>
    <td><code>${r.commit_sha}</code></td>
    <td>${r.anomaly_count}</td>
    <td class="${r.blocked ? "blocked" : "allowed"}">${r.blocked ? "BLOCKED" : "allowed"}</td>
  </tr>`).join("");
  document.getElementById("recent").innerHTML =
    `<table><thead><tr><th>Pipeline</th><th>Severity</th><th>Status</th><th>Branch</th><th>Commit</th><th>Anomalies</th><th>Verdict</th></tr></thead><tbody>${rows}</tbody></table>`;
}
load();
</script>
</body>
</html>
"""
