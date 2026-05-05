/* ============================================================
   NMTC viewer — non-map page logic
   Depends on window.NMTC_HEADLINE, window.NMTC_TOP_CDES.
   ============================================================ */

(function () {
  "use strict";

  // ---------- KPI cards ----------
  const h = window.NMTC_HEADLINE || {};
  const fmt$B = v => `$${v.toFixed(1)} B`;
  const fmtPct = v => `${v.toFixed(1)}%`;
  const fmtX   = v => `${v.toFixed(2)}×`;
  const fmtN   = v => v.toLocaleString("en-US");

  const kpis = [
    { lbl: "Program years", val: `${h.program_years[0]}–${h.program_years[1]}`, sub: `${h.n_transactions_total.toLocaleString()} QLICIs in ${h.n_projects_total.toLocaleString()} projects` },
    { lbl: "Total QLICI deployed", val: fmt$B(h.total_qlici_billion_usd), sub: "nominal USD, CDE → QALICB flow" },
    { lbl: "Total project cost", val: fmt$B(h.total_project_cost_billion_usd), sub: "public + private combined" },
    { lbl: "Mobilization ratio", val: `${((h.total_project_cost_billion_usd - h.total_qlici_billion_usd) / h.total_qlici_billion_usd).toFixed(2)}×`, sub: "private $ per federal $", highlight: true },
    { lbl: "Non-metro $ share", val: fmtPct(h.non_metro_qlici_dollar_share_pct), sub: `vs. ${fmtPct(h.statutory_non_metro_target_pct)} statutory` },
    { lbl: "Median leverage, metro",     val: fmtX(h.median_leverage_metro) },
    { lbl: "Median leverage, non-metro", val: fmtX(h.median_leverage_non_metro) },
    { lbl: "Leverage gap (m − nm)",      val: `+${fmtX(h.leverage_gap_metro_minus_nonmetro)}`, sub: "median", highlight: true },
  ];
  const kgrid = document.getElementById("kpi-cards");
  if (kgrid) {
    kpis.forEach(k => {
      const d = document.createElement("div");
      d.className = "kpi" + (k.highlight ? " highlight" : "");
      d.innerHTML = `<div class="lbl">${k.lbl}</div><div class="val">${k.val}</div>${k.sub ? `<div class="sub">${k.sub}</div>` : ""}`;
      kgrid.appendChild(d);
    });
  }

  // ---------- CDE table ----------
  const cdeTBody = document.querySelector("#cdeTable tbody");
  if (cdeTBody && window.NMTC_TOP_CDES) {
    const rows = window.NMTC_TOP_CDES.slice().sort((a, b) => b.non_metro_share - a.non_metro_share);
    rows.forEach(r => {
      const tr = document.createElement("tr");
      const nonMetroPct = Math.round(r.non_metro_share * 100);
      // bar: gradient from metro → nonmetro, width proportional
      const barW = Math.max(4, nonMetroPct * 1.4);  // visual emphasis
      tr.innerHTML = `
        <td class="name">${r.cde_name}</td>
        <td class="r">$${r.total_qlici_m.toFixed(0)}</td>
        <td class="r">${r.n_tx.toLocaleString()}</td>
        <td class="r">${nonMetroPct}%</td>
        <td>
          <div class="bar-wrap">
            <div class="bar" style="width:${barW}px; background: linear-gradient(to right, var(--metro) 0%, var(--metro) ${100 - nonMetroPct}%, var(--nonmetro) ${100 - nonMetroPct}%);"></div>
          </div>
        </td>`;
      cdeTBody.appendChild(tr);
    });
  }
})();
