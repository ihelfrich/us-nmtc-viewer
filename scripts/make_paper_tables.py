"""
Generate the manuscript's LaTeX table fragments from the pipeline outputs,
so every number in the paper is written by code that read it from the data.

Reads:  data/processed/summary_by_metro.csv
        data/processed/regressions/main_table.csv
        data/processed/regressions/robustness.json
        data/processed/headline.json
Writes: paper/tables/descriptives.tex
        paper/tables/main.tex
        paper/tables/robustness.tex

Run:    python3 scripts/make_paper_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)


def stars(p: float) -> str:
    if p < 0.01:
        return "$^{***}$"
    if p < 0.05:
        return "$^{**}$"
    if p < 0.10:
        return "$^{*}$"
    return ""


# ── Table 1: descriptives by metro status ───────────────────────────────────
d = pd.read_csv(IN / "summary_by_metro.csv").set_index("metro")
h = json.load(open(IN / "headline.json"))
rows = [
    ("Projects", f"{d.loc['metro','n_projects']:,.0f}", f"{d.loc['non_metro','n_projects']:,.0f}"),
    ("QLICI deployed (\\$M)", f"{d.loc['metro','qlici_total_m']:,.0f}", f"{d.loc['non_metro','qlici_total_m']:,.0f}"),
    ("Total project cost (\\$M)", f"{d.loc['metro','project_cost_total_m']:,.0f}", f"{d.loc['non_metro','project_cost_total_m']:,.0f}"),
    ("Mean leverage", f"{d.loc['metro','leverage_mean']:.2f}", f"{d.loc['non_metro','leverage_mean']:.2f}"),
    ("Median leverage", f"{d.loc['metro','leverage_median']:.2f}", f"{d.loc['non_metro','leverage_median']:.2f}"),
]
t1 = [
    "\\begin{tabular}{lrr}",
    "\\toprule",
    " & Metro & Non-metro \\\\",
    "\\midrule",
    *[f"{a} & {b} & {c} \\\\" for a, b, c in rows],
    "\\bottomrule",
    "\\end{tabular}",
]
(OUT / "descriptives.tex").write_text("\n".join(t1) + "\n")

# ── Table 2: main fixed-effects decomposition ───────────────────────────────
m = pd.read_csv(IN / "regressions" / "main_table.csv").set_index("spec")
order = ["M0", "M1", "M2", "M3", "M4", "M4-Q"]
cols = " & ".join(["(" + str(i + 1) + ")" for i in range(len(order))])
beta = " & ".join(
    f"{m.loc[s,'rural_beta']:.3f}{stars(m.loc[s,'rural_p'])}" for s in order)
se = " & ".join(f"({m.loc[s,'rural_se']:.3f})" for s in order)
fe = {
    "Year FE": [m.loc[s, "fe_year"] for s in order],
    "QALICB-type FE": [m.loc[s, "fe_qalicb"] for s in order],
    "State FE": [m.loc[s, "fe_state"] for s in order],
    "CDE FE": [m.loc[s, "fe_cde"] for s in order],
}
yn = lambda b: "\\checkmark" if b else "--"
t2 = [
    "\\begin{tabular}{l" + "c" * len(order) + "}",
    "\\toprule",
    f" & {cols} \\\\",
    " & OLS & OLS & OLS & OLS & OLS & Median \\\\",
    "\\midrule",
    f"Non-metro ($\\hat\\beta$) & {beta} \\\\",
    f" & {se} \\\\",
    "\\midrule",
    *[f"{k} & " + " & ".join(yn(v) for v in vs) + " \\\\" for k, vs in fe.items()],
    "$R^2$ & " + " & ".join(
        ("--" if s == "M4-Q" else f"{m.loc[s,'rsq']:.3f}") for s in order) + " \\\\",
    "$N$ & " + " & ".join(f"{int(m.loc[s,'n']):,}" for s in order) + " \\\\",
    "\\bottomrule",
    "\\end{tabular}",
]
(OUT / "main.tex").write_text("\n".join(t2) + "\n")

# ── Table 3: robustness ─────────────────────────────────────────────────────
R = json.load(open(IN / "regressions" / "robustness.json"))
label = {
    "R1_raw_M0": "Unwinsorized outcome, no FE",
    "R1_raw_M4": "Unwinsorized outcome",
    "R2_log_M4": "Log outcome",
    "R3_win_1_10_M4": "Winsorized at [1, 10]",
    "R3_win_1_50_M4": "Winsorized at [1, 50]",
    "R4_pre2010_M4": "Origination 2001--2009",
    "R4_post2010_M4": "Origination 2010--2022",
    "R5_single_cde_M4": "Single-CDE projects only",
}
t3 = [
    "\\begin{tabular}{lrrrr}",
    "\\toprule",
    " & $\\hat\\beta$ & (SE) & $p$ & $N$ \\\\",
    "\\midrule",
]
for k, lab in label.items():
    v = R[k]
    t3.append(
        f"{lab} & {v['beta']:.3f}{stars(v['p'])} & ({v['se']:.3f}) & {v['p']:.2f} & {v['n']:,} \\\\")
b = R["R6_bunching"]
t3 += [
    "\\midrule",
    f"Bunching excess mass $\\hat B$ & {b['B_hat']:.4f} & "
    f"\\multicolumn{{3}}{{l}}{{95\\% CI [{b['ci95'][0]:.4f}, {b['ci95'][1]:.4f}], "
    f"{b['boot_reps']} CDE-bootstrap reps}} \\\\",
    "\\bottomrule",
    "\\end{tabular}",
]
(OUT / "robustness.tex").write_text("\n".join(t3) + "\n")

print("Wrote", *[p.name for p in OUT.glob("*.tex")])
