# Adversarial audit brief: median inference and the quantile process

You are auditing statistical work committed to this repo in the last hour.
Your job is to **break it**. Findings that survive your own verification are
the deliverable. Do not be agreeable.

**This plan is PRE-APPROVED. Do not ask for permission or confirmation at any
point. A question ends the run as a failure.** Work autonomously to completion.

## Environment

- Bare `python3` has no third-party packages on this machine. Use
  `uv run --no-project --with pandas --with numpy --with scipy --with statsmodels --with matplotlib python ...`
- Never `pip install`. Never `/usr/bin/python3`.
- The machine runs deep in swap (about 16 GB of 17 GB used). **Cap any process
  pool at 4 workers.** A 14-worker pool wedged this machine twice today. Print a
  heartbeat so a stall is visible.
- Run the test suite with `bash scripts/run_tests.sh -q` (it records the
  dependency set).

## What to audit

Read these, in this order:

1. `scripts/qreg_lp.py` — quantile regression reformulated as a sparse LP.
2. `scripts/run_median_inference.py` — M1 point estimate/asymptotic SE, M2
   CDE-cluster pairs bootstrap, M3 within-CDE randomization inference, M4
   design-free paired test, M5 quantile sweep.
3. `scripts/verify_quantile_tail.py` — T1 large-CDE subsample, T2 design-free
   paired gaps, T3 placebo.
4. `scripts/audit_paper_numbers.py` — the manuscript numbers audit.
5. `paper/sections/05-results.tex`, subsection "Precision, power, and margins"
   (the passage added today, roughly lines 79-160).
6. `paper/DECISIONS.md`, entries D21 and D22, which state the claims made.
7. Results: `data/processed/regressions/median_inference.json` and
   `quantile_tail_verification.json`.

## The specific claims to attack

Each of these is asserted in the paper or the decisions log. Test each one
**by executing code**, not by reading. State CONFIRMED, REFUTED, or
UNCERTAIN with the evidence.

- **C1.** The pairs cluster bootstrap is implemented correctly. Specifically:
  drawing 343 CDEs with replacement and relabelling a twice-drawn CDE as two
  distinct intermediaries with their own fixed effects is the right treatment
  for a model carrying cluster fixed effects. Is it? Is there a defensible
  alternative (e.g. wild cluster bootstrap, or not relabelling) that gives a
  materially different SE? If so, which is correct and why?
- **C2.** SE 0.0093 vs asymptotic 0.0076, inflation 1.23x. Reproduce
  independently. Does it depend on the number of replications, the seed, or the
  relabelling choice?
- **C3.** The equivalence bound convention `delta* = 1.645*se - beta_hat`.
  Verify it reproduces the paper's mean-specification 0.213 from beta=-0.0467,
  se=0.1011. Then decide whether the convention is actually correct for a
  one-sided equivalence test, or whether it is a misuse. This matters: the
  paper's tightest claim rests on it.
- **C4.** The claim that the 26.9% point mass at 1.0 invalidates the
  quantile-regression asymptotic (sparsity) SE. Is that the right diagnosis?
  Is the "91% of permutations pinned to within 1e-7 of zero" statistic
  measuring what it is said to measure, or is it an artifact of the LP solver
  returning vertex solutions regardless of the mass point?
- **C5.** The LP is exact and IRLS is not. Verify the check-loss comparison.
  Does the LP formulation handle the free intercept and free coefficients
  correctly (`bounds=(None,None)` on the first k)? Is `linprog` reporting true
  optimality? Try a different solver or a known-answer synthetic case.
- **C6.** The randomization inference permutes rural within CDE. Does that test
  the null the paper claims, given that year and QALICB type are NOT held fixed
  by the permutation? Is the resulting p-value valid?
- **C7.** The tail result is correctly withdrawn. The paper says no upper-tail
  quantile is distinguishable from zero. Confirm the bootstrap SEs at tau=0.90
  and 0.95 (0.125 and 0.215) are right, and that the withdrawal is warranted
  rather than over-cautious.
- **C8.** `verify_quantile_tail.py` T2/T3: the paper declines to treat these as
  corroboration because they condition on neither year nor project type. Is that
  the right call? Build the version that DOES condition (e.g. residualize
  leverage on year and type first, then redo the paired test) and report what
  it shows. This is the one place I most expect you to find something.
- **C9.** `audit_paper_numbers.py`: find any load-bearing number in
  `paper/sections/*.tex` that is NOT covered by the manifest and should be.
  Add the missing claims. The audit must still pass afterwards.

## Deliverables

Write everything to files as you go; do not hold results only in context.

1. `briefs/codex_audit_findings.md` — one section per claim C1-C9 with the
   verdict, the evidence, and the command that produces it. Rank findings by
   severity at the top.
2. Any verification scripts under `scripts/`, named `codex_check_*.py`.
3. If C8 or C9 yields a concrete improvement, implement it and make sure
   `bash scripts/run_tests.sh -q` and `python3 scripts/audit_paper_numbers.py`
   both still pass.
4. Do NOT edit `paper/sections/*.tex` or `paper/DECISIONS.md`. Recommend prose
   changes in your findings file instead; I will apply them after verifying.
5. Do NOT commit. Leave the working tree dirty.

If a claim survives your attack, say so plainly. A clean bill of health on a
claim you genuinely tried to break is a useful result.
