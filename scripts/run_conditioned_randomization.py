"""
Randomization inference that respects the covariates, after a cross-model
audit showed the production version does not.

`run_median_inference.py` M3 permutes the rural label inside each
intermediary and reports a two-sided p of 0.085. Its docstring, and an
earlier version of Section 5.2, described this as holding "every book
composition" fixed. That is wrong. Permuting within CDE fixes each
intermediary's rural *count* and nothing else, and rural status is strongly
associated with origination year and QALICB type. The permutation therefore
destroys structure the specification conditions on, and the resulting
p-value is valid only under exchangeability conditional on intermediary
alone, which is an assumption about the assignment mechanism that this
observational setting does not deliver.

The diagnostic that shows it: under the within-CDE permutation null, the
observed year-level rural shares sit as far as 3.3 standard deviations from
the reference distribution. Real assignment is not exchangeable within
intermediary.

This script reports the stricter test alongside it.

  N1  Reproduce the within-CDE permutation p as a stated sensitivity.

  N2  The covariate-preserving version: permute the rural label only inside
      exact intermediary-by-year-by-QALICB-type strata, so that every
      margin the specification conditions on is held fixed by construction.

  N3  The cost of that strictness, reported rather than buried. Most exact
      strata are homogeneous in rural status and contribute no permutable
      variation, so N2 rests on a subset of the sample. The count and
      coverage are recorded.

Neither test rejects, so the paper's conclusion is unchanged; what changes
is which number may be called design-valid and under what assumption.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/conditioned_randomization.json / .md

Run:    uv run --no-project --with pandas --with numpy --with scipy \
            python scripts/run_conditioned_randomization.py
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qreg_lp import fit_quantile          # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"

B_WITHIN = int(os.environ.get("NMTC_B_WITHIN", 400))
B_STRATA = int(os.environ.get("NMTC_B_STRATA", 400))
B_BALANCE = int(os.environ.get("NMTC_B_BALANCE", 200))
N_WORKERS = int(os.environ.get("NMTC_WORKERS", 4))
SEED = 20260815


def load() -> pd.DataFrame:
    pr = pd.read_csv(IN / "nmtc_projects.csv")
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                           "cde_name"]).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)
    return pr


def main() -> None:
    pr = load()
    b_hat = fit_quantile(pr, "leverage_win", 0.5)
    R: dict = {"observed_beta": round(float(b_hat), 6),
               "n_projects": int(len(pr)), "seed": SEED}
    print(f"observed median rural coefficient {b_hat:+.6f}")

    cde_groups = [g.index.to_numpy() for _, g in pr.groupby("cde_name")]
    strata_all = [g.index.to_numpy() for _, g
                  in pr.groupby(["cde_name", "year", "qalicb_type"])]
    mixed = [i for i in strata_all
             if len(i) > 1 and pr.loc[i, "rural"].nunique() > 1]
    R["n_exact_strata"] = int(len(strata_all))
    R["n_exact_strata_mixed"] = int(len(mixed))
    R["n_projects_in_mixed_strata"] = int(sum(len(i) for i in mixed))
    R["share_projects_in_mixed_strata"] = round(
        R["n_projects_in_mixed_strata"] / len(pr), 4)
    print(f"N3 exact CDE x year x type strata: {len(mixed):,} of "
          f"{len(strata_all):,} are mixed, covering "
          f"{R['n_projects_in_mixed_strata']:,} projects "
          f"({100*R['share_projects_in_mixed_strata']:.1f}%)")

    # ── the balance diagnostic that motivates all of this ──────────────
    rng = np.random.default_rng(SEED)
    obs_year = pr.groupby("year")["rural"].mean()
    obs_type = pr.groupby("qalicb_type")["rural"].mean()
    draws_year, draws_type = [], []
    for _ in range(B_BALANCE):
        r = pr["rural"].to_numpy().copy()
        for idx in cde_groups:
            if len(idx) > 1:
                r[idx] = rng.permutation(r[idx])
        tmp = pr.assign(x=r)
        draws_year.append(tmp.groupby("year")["x"].mean())
        draws_type.append(tmp.groupby("qalicb_type")["x"].mean())
    DY, DT = pd.concat(draws_year, axis=1), pd.concat(draws_type, axis=1)
    z_year = ((obs_year - DY.mean(axis=1)) / DY.std(axis=1)).abs().max()
    z_type = ((obs_type - DT.mean(axis=1)) / DT.std(axis=1)).abs().max()
    R["balance_max_abs_z_year"] = round(float(z_year), 3)
    R["balance_max_abs_z_qalicb_type"] = round(float(z_type), 3)
    print(f"   within-CDE permutation null vs observed covariate balance: "
          f"max |z| year {z_year:.2f}, type {z_type:.2f}")

    def run(groups: list[np.ndarray], n: int, base: int, label: str) -> dict:
        def one(k: int) -> float | None:
            g = np.random.default_rng(base + k)
            r = pr["rural"].to_numpy().copy()
            for idx in groups:
                if len(idx) > 1:
                    r[idx] = g.permutation(r[idx])
            if len(np.unique(r)) < 2:
                return None
            try:
                return fit_quantile(pr.assign(rural=r), "leverage_win", 0.5)
            except Exception:                                   # noqa: BLE001
                return None

        vals, done = [], 0
        with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
            for v in ex.map(one, range(n)):
                done += 1
                if v is not None:
                    vals.append(v)
                if done % 50 == 0:
                    print(f"   [{label}] {done}/{n}", flush=True)
        arr = np.array(vals, dtype=float)
        extreme = int((np.abs(arr) >= abs(b_hat)).sum())
        return {"draws_used": int(len(arr)), "n_extreme": extreme,
                "p_two_sided": round((extreme + 1) / (len(arr) + 1), 4),
                "null_sd": round(float(arr.std(ddof=1)), 6),
                "null_ci95": [round(float(np.percentile(arr, 2.5)), 5),
                              round(float(np.percentile(arr, 97.5)), 5)]}

    print(f"N1 within-CDE permutation, {B_WITHIN} draws")
    R["N1_within_cde"] = run(cde_groups, B_WITHIN, SEED + 1000, "N1")
    print(f"   p = {R['N1_within_cde']['p_two_sided']:.4f}")

    print(f"N2 exact CDE x year x type strata, {B_STRATA} draws")
    R["N2_exact_strata"] = run(mixed, B_STRATA, SEED + 5000, "N2")
    print(f"   p = {R['N2_exact_strata']['p_two_sided']:.4f}")

    R["verdict"] = (
        "Permuting within intermediary alone does not preserve the rural "
        "association with year or project type, so its p-value is a "
        "sensitivity under an assumption of exchangeability conditional on "
        "intermediary. Restricting permutations to exact "
        "intermediary-by-year-by-type strata preserves every conditioned "
        "margin and is the stricter test, at the cost of resting on the "
        f"{R['share_projects_in_mixed_strata']:.0%} of projects that sit in "
        "mixed strata. Neither test rejects the null.")

    (OUT / "conditioned_randomization.json").write_text(json.dumps(R, indent=2))
    md = ["# Randomization inference, conditioned on the covariates", "",
          "_Generated by `scripts/run_conditioned_randomization.py`._", "",
          "| quantity | value |", "|---|---:|",
          f"| observed median rural coefficient | {b_hat:+.6f} |",
          f"| within-CDE permutation p | {R['N1_within_cde']['p_two_sided']:.4f} |",
          f"| exact-strata permutation p | {R['N2_exact_strata']['p_two_sided']:.4f} |",
          f"| exact strata, mixed / total | {R['n_exact_strata_mixed']:,} / "
          f"{R['n_exact_strata']:,} |",
          f"| projects in mixed strata | {R['n_projects_in_mixed_strata']:,} "
          f"({100*R['share_projects_in_mixed_strata']:.1f}%) |",
          f"| covariate balance, max abs z (year) | {R['balance_max_abs_z_year']:.2f} |",
          f"| covariate balance, max abs z (type) | {R['balance_max_abs_z_qalicb_type']:.2f} |",
          "", R["verdict"], ""]
    (OUT / "conditioned_randomization.md").write_text("\n".join(md))
    print(f"\nWrote {OUT/'conditioned_randomization.json'} and .md")


if __name__ == "__main__":
    main()
