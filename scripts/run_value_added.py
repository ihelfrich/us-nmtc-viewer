"""Estimate intermediary value-added and validate its portability.

The estimand is the CDE fixed effect in an additive project-level model of
``leverage_win`` with year and QALICB-type effects.  CDE effects are centered
at their unweighted mean, and their classical pooled-residual sampling
variances feed a standard normal-normal empirical-Bayes decomposition.

Reads:
    data/processed/nmtc_projects.csv

Writes:
    data/processed/regressions/value_added.json
    figures/va_raw_shrunk_distribution.{pdf,png}
    figures/va_portability_scatter.{pdf,png}
    figures/va_split_half_reliability.{pdf,png}
    briefs/value_added_first_pass.md

Run:
    uv run --no-project --with pandas --with numpy --with statsmodels \
      --with matplotlib python scripts/run_value_added.py
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

plt.switch_backend("Agg")


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT = DATA / "regressions"
FIGURES = ROOT / "figures"
BRIEFS = ROOT / "briefs"

OUTCOME = "leverage_win"
GROUP = "cde_name"
CONTROLS = ("year", "qalicb_type")
MIN_PER_BOOK = 3
MIN_SPLIT_TOTAL = 2
SPLIT_REPS = 499
POSTERIOR_DRAWS = 2_000
SEED = 20260814
RAW_GAP_REFERENCE = -0.262

INK = "#16161D"
PENCIL = "#6B6B70"
SIGNAL = "#2852E8"
WASH = "#EEF2FA"
WHITE = "#FFFFFF"
TEXTWIDTH_IN = 4.9

warnings.filterwarnings("ignore", category=FutureWarning)

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 300,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "font.family": "serif",
        "font.serif": ["Palatino", "TeX Gyre Pagella", "DejaVu Serif"],
        "font.size": 8.0,
        "axes.labelsize": 8.0,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": PENCIL,
        "axes.linewidth": 0.6,
        "xtick.color": PENCIL,
        "ytick.color": PENCIL,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "mathtext.fontset": "dejavuserif",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


class CDEFit(NamedTuple):
    effects: pd.DataFrame
    fitted: np.ndarray
    residuals: np.ndarray
    adjusted_outcome: np.ndarray
    n_obs: int
    n_parameters: int
    residual_df: int


def _finish_axes(ax: plt.Axes, *, grid: bool = True) -> None:
    for side in ("left", "bottom"):
        ax.spines[side].set_color(PENCIL)
        ax.spines[side].set_linewidth(0.6)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=PENCIL, linewidth=0.55, alpha=0.12, visible=grid)
    ax.grid(axis="x", visible=False)


def _save_pair(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.55)
    for suffix in ("pdf", "png"):
        fig.savefig(
            FIGURES / f"{stem}.{suffix}",
            bbox_inches="tight",
            pad_inches=0.04,
            facecolor=WHITE,
        )
    plt.close(fig)


def fit_cde_effects(
    frame: pd.DataFrame,
    *,
    outcome: str = OUTCOME,
    group: str = GROUP,
    controls: tuple[str, str] = CONTROLS,
) -> CDEFit:
    """Jointly estimate centered CDE effects and pooled-OLS variances.

    The design includes one column for every CDE and drop-first columns for
    each control.  It therefore has no separate intercept.  Centering the CDE
    coefficients after estimation changes only their arbitrary location, not
    fitted values or their dispersion.
    """
    required = [outcome, group, *controls]
    if frame[required].isna().any().any():
        raise ValueError("fit_cde_effects received missing estimation values")
    if frame[group].nunique() < 2:
        raise ValueError("at least two CDEs are required")

    cde = pd.get_dummies(frame[group].astype(str), dtype=float)
    nuisance = [
        pd.get_dummies(
            frame[control].astype(str), prefix=control, drop_first=True, dtype=float
        )
        for control in controls
    ]
    design = pd.concat([cde, *nuisance], axis=1)
    x = design.to_numpy(float)
    y = frame[outcome].to_numpy(float)
    n, k = x.shape
    rank = int(np.linalg.matrix_rank(x))
    assert rank == k, f"fixed-effect design is rank deficient: rank {rank}, k {k}"
    assert n > k, (
        f"effect covariance requires residual degrees of freedom: n {n}, k {k}"
    )

    # The usual pooled-residual OLS covariance is deliberate. With a CDE fixed
    # effect, HC1 assigns a singleton's own perfectly fitted observation zero
    # residual contribution and can therefore make one-deal effects look almost
    # perfectly reliable. The pooled variance yields the standard sigma^2 / n_j
    # small-cell penalty underlying normal-normal teacher-VA shrinkage.
    fitted_model = sm.OLS(y, x).fit()
    beta = np.asarray(fitted_model.params, dtype=float)
    covariance = np.asarray(fitted_model.cov_params(), dtype=float)
    assert covariance.shape == (k, k)
    assert np.allclose(covariance, covariance.T, atol=1e-10, rtol=1e-10)

    j = cde.shape[1]
    center = np.eye(j) - np.ones((j, j)) / j
    raw_va = center @ beta[:j]
    centered_covariance = center @ covariance[:j, :j] @ center
    centered_covariance = (centered_covariance + centered_covariance.T) / 2
    sampling_variance = np.diag(centered_covariance).copy()
    assert float(sampling_variance.min()) >= -1e-10, "negative OLS effect variance"
    sampling_variance = np.maximum(sampling_variance, 0.0)

    nuisance_contribution = x[:, j:] @ beta[j:] if k > j else np.zeros(n)
    adjusted = y - nuisance_contribution
    alpha_from_adjusted_means = (
        pd.DataFrame({group: frame[group].astype(str).to_numpy(), "adjusted": adjusted})
        .groupby(group, sort=True)["adjusted"]
        .mean()
        .reindex(cde.columns)
        .to_numpy(float)
    )
    # The CDE first-order conditions imply this identity exactly up to solver
    # precision.  It is the load-bearing link between the regression and all
    # leave-out book means below.
    assert np.allclose(alpha_from_adjusted_means, beta[:j], atol=1e-8, rtol=1e-8)
    assert abs(float(raw_va.mean())) < 1e-10, "CDE normalization did not center"

    counts = frame[group].astype(str).value_counts().reindex(cde.columns)
    effects = pd.DataFrame(
        {
            group: cde.columns.astype(str),
            "n_projects": counts.to_numpy(int),
            "raw_va": raw_va,
            "sampling_variance": sampling_variance,
            "sampling_se": np.sqrt(sampling_variance),
        }
    )
    fitted = np.asarray(fitted_model.fittedvalues, dtype=float)
    residuals = y - fitted
    assert np.allclose(fitted + residuals, y, atol=1e-12, rtol=1e-12)
    assert round(float(fitted_model.df_resid)) == n - k
    return CDEFit(effects, fitted, residuals, adjusted, n, k, n - k)


def eb_decompose(theta_hat: np.ndarray, sampling_variance: np.ndarray) -> dict:
    """Apply the standard normal-normal empirical-Bayes decomposition."""
    theta = np.asarray(theta_hat, dtype=float)
    variance = np.asarray(sampling_variance, dtype=float)
    if theta.ndim != 1 or variance.shape != theta.shape or theta.size < 2:
        raise ValueError("effect and sampling-variance vectors must align")
    if not np.isfinite(theta).all() or not np.isfinite(variance).all():
        raise ValueError("EB inputs must be finite")
    assert float(variance.min()) >= -1e-12, "sampling variances must be non-negative"
    variance = np.maximum(variance, 0.0)

    total_variance = float(np.var(theta, ddof=1))
    mean_sampling_variance = float(np.mean(variance))
    unconstrained_signal = total_variance - mean_sampling_variance
    # The non-negative prior-variance constraint is explicit.  A non-positive
    # subtraction is a degenerate EB estimate, not evidence of negative signal.
    signal_variance = max(unconstrained_signal, 0.0)
    degenerate = bool(unconstrained_signal <= 0.0)
    assert signal_variance >= 0.0, "EB signal variance must be non-negative"
    assert math.isclose(
        unconstrained_signal,
        total_variance - mean_sampling_variance,
        abs_tol=1e-14,
        rel_tol=1e-14,
    )
    if degenerate:
        assert signal_variance == 0.0 and unconstrained_signal <= 0.0
    else:
        assert math.isclose(
            total_variance,
            signal_variance + mean_sampling_variance,
            abs_tol=1e-14,
            rel_tol=1e-14,
        )

    denominator = signal_variance + variance
    reliability = np.divide(
        signal_variance,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )
    shrunk = reliability * theta
    posterior_variance = np.divide(
        signal_variance * variance,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )
    assert ((reliability >= 0.0) & (reliability <= 1.0 + 1e-12)).all()
    assert np.allclose(shrunk, reliability * theta, atol=1e-14, rtol=1e-14)
    return {
        "total_variance": total_variance,
        "mean_sampling_variance": mean_sampling_variance,
        "signal_variance_unconstrained": unconstrained_signal,
        "signal_variance": signal_variance,
        "signal_sd": math.sqrt(signal_variance),
        "degenerate": degenerate,
        "reliability": reliability,
        "mean_reliability": float(reliability.mean()),
        "shrunk": shrunk,
        "posterior_variance": posterior_variance,
    }


def reliability_adjusted_correlation(
    raw_correlation: float, reliability_x: float, reliability_y: float
) -> float:
    """Correct a correlation for classical measurement-error attenuation."""
    if reliability_x <= 0.0 or reliability_y <= 0.0:
        return float("nan")
    adjusted = raw_correlation / math.sqrt(reliability_x * reliability_y)
    assert math.isclose(
        adjusted * math.sqrt(reliability_x * reliability_y),
        raw_correlation,
        abs_tol=1e-14,
        rel_tol=1e-14,
    )
    return adjusted


def raw_group_gap(outcome: pd.Series, treated: pd.Series) -> dict:
    """Compute and assert the two-group mean-difference/OLS identity."""
    y = pd.Series(outcome, dtype=float)
    d = pd.Series(treated, dtype=float)
    if len(y) != len(d) or len(y) == 0:
        raise ValueError("outcome and group indicator must be nonempty and aligned")
    if set(d.unique()) != {0.0, 1.0}:
        raise ValueError("group indicator must contain both zero and one")
    control_mean = float(y[d == 0.0].mean())
    treated_mean = float(y[d == 1.0].mean())
    gap = treated_mean - control_mean
    design = sm.add_constant(d.to_numpy())
    params = sm.OLS(y, design).fit().params
    # statsmodels returns a named Series when the endogenous variable is a
    # Series.  Use positional indexing explicitly; params[1] is a label lookup.
    ols_gap = float(params.iloc[1] if hasattr(params, "iloc") else params[1])
    assert math.isclose(gap, ols_gap, abs_tol=1e-12, rel_tol=1e-12)
    return {
        "control_mean": control_mean,
        "treated_mean": treated_mean,
        "gap": gap,
        "ols_gap": ols_gap,
    }


def split_cde_indices(
    frame: pd.DataFrame,
    rng: np.random.Generator,
    *,
    group: str = GROUP,
    min_total: int = MIN_SPLIT_TOTAL,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Randomly make disjoint, balanced halves within every eligible CDE."""
    if min_total < 2:
        raise ValueError("min_total must be at least two")
    counts = frame[group].astype(str).value_counts()
    eligible = sorted(counts[counts >= min_total].index.astype(str).tolist())
    left: list[np.ndarray] = []
    right: list[np.ndarray] = []
    group_as_string = frame[group].astype(str)
    for cde in eligible:
        index = frame.index[group_as_string == cde].to_numpy()
        shuffled = rng.permutation(index)
        cut = len(shuffled) // 2
        left.append(shuffled[:cut])
        right.append(shuffled[cut:])
        assert min(cut, len(shuffled) - cut) >= min_total // 2
        assert abs(cut - (len(shuffled) - cut)) <= 1
    left_index = np.concatenate(left) if left else np.array([], dtype=int)
    right_index = np.concatenate(right) if right else np.array([], dtype=int)
    eligible_index = frame.index[group_as_string.isin(eligible)].to_numpy()
    assert not np.intersect1d(left_index, right_index).size, "split halves overlap"
    assert np.array_equal(
        np.sort(np.concatenate([left_index, right_index])), np.sort(eligible_index)
    ), "split halves do not partition the eligible observations"
    return left_index, right_index, eligible


def counterfactual_reallocation(
    effects: pd.Series,
    dollars: pd.Series,
    *,
    raw_gap: float,
    classification_effects: pd.Series | None = None,
) -> dict:
    """Move all below-median rural dollars pro rata to above-median CDEs."""
    if raw_gap == 0.0:
        raise ValueError("raw gap cannot be zero")
    names = effects.index.union(dollars.index)
    va = effects.reindex(names)
    if va.isna().any():
        raise ValueError("every dollar-holding CDE must have a VA estimate")
    classification = (
        effects if classification_effects is None else classification_effects
    ).reindex(names)
    if classification.isna().any():
        raise ValueError("every CDE must have a classification effect")
    deployed = dollars.reindex(names, fill_value=0.0).astype(float)
    if (deployed < 0.0).any():
        raise ValueError("deployment dollars cannot be negative")
    total = float(deployed.sum())
    if total <= 0.0:
        raise ValueError("positive deployment dollars are required")

    median_va = float(classification.median())
    below = classification < median_va
    above = classification > median_va
    donor_dollars = float(deployed[below].sum())
    existing_recipient_dollars = float(deployed[above].sum())
    if donor_dollars <= 0.0 or existing_recipient_dollars <= 0.0:
        raise ValueError("both donor and recipient groups must hold rural dollars")

    counterfactual = deployed.copy()
    counterfactual.loc[below] = 0.0
    counterfactual.loc[above] += (
        donor_dollars * deployed.loc[above] / existing_recipient_dollars
    )
    counterfactual_total = float(counterfactual.sum())
    assert math.isclose(counterfactual_total, total, abs_tol=1e-6, rel_tol=1e-12)

    observed_weighted_va = float(np.dot(deployed, va) / total)
    counterfactual_weighted_va = float(np.dot(counterfactual, va) / total)
    leverage_gain = counterfactual_weighted_va - observed_weighted_va
    donor_mean_va = float(np.dot(deployed[below], va[below]) / donor_dollars)
    recipient_mean_va = float(
        np.dot(deployed[above], va[above]) / existing_recipient_dollars
    )
    accounting_gain = donor_dollars / total * (recipient_mean_va - donor_mean_va)
    assert math.isclose(leverage_gain, accounting_gain, abs_tol=1e-12, rel_tol=1e-12)
    return {
        "median_va": median_va,
        "n_below_median": int(below.sum()),
        "n_above_median": int(above.sum()),
        "observed_total_dollars": total,
        "counterfactual_total_dollars": counterfactual_total,
        "reallocated_dollars": donor_dollars,
        "reallocated_share": donor_dollars / total,
        "donor_weighted_mean_va": donor_mean_va,
        "recipient_weighted_mean_va": recipient_mean_va,
        "observed_weighted_va": observed_weighted_va,
        "counterfactual_weighted_va": counterfactual_weighted_va,
        "leverage_gain": leverage_gain,
        "share_gap_closed": leverage_gain / abs(raw_gap),
    }


def _distribution(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float)
    q = np.quantile(values, [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
    return {
        "sd": float(np.std(values, ddof=1)),
        "iqr": float(q[4] - q[2]),
        "percentiles": {
            "p05": float(q[0]),
            "p10": float(q[1]),
            "p25": float(q[2]),
            "p50": float(q[3]),
            "p75": float(q[4]),
            "p90": float(q[5]),
            "p95": float(q[6]),
        },
    }


def _variance_reliability(eb: dict) -> float:
    total = float(eb["total_variance"])
    if total <= 0.0:
        return 0.0
    reliability = float(eb["signal_variance"]) / total
    assert 0.0 <= reliability <= 1.0 + 1e-12
    return min(reliability, 1.0)


def _book_portability(frame: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    counts = frame.groupby([GROUP, "metro"]).size().unstack(fill_value=0)
    for column in ("metro", "non_metro"):
        if column not in counts:
            counts[column] = 0
    eligible = counts.index[
        (counts["metro"] >= MIN_PER_BOOK) & (counts["non_metro"] >= MIN_PER_BOOK)
    ]
    book_sample = frame[frame[GROUP].isin(eligible)].copy()
    urban = fit_cde_effects(book_sample[book_sample["metro"] == "metro"])
    rural = fit_cde_effects(book_sample[book_sample["metro"] == "non_metro"])

    urban_effects = urban.effects.set_index(GROUP).sort_index()
    rural_effects = rural.effects.set_index(GROUP).sort_index()
    assert urban_effects.index.equals(rural_effects.index)
    assert len(urban_effects) == len(eligible)
    urban_eb = eb_decompose(
        urban_effects["raw_va"].to_numpy(),
        urban_effects["sampling_variance"].to_numpy(),
    )
    rural_eb = eb_decompose(
        rural_effects["raw_va"].to_numpy(),
        rural_effects["sampling_variance"].to_numpy(),
    )
    raw_correlation = float(
        np.corrcoef(urban_effects["raw_va"], rural_effects["raw_va"])[0, 1]
    )
    urban_reliability = _variance_reliability(urban_eb)
    rural_reliability = _variance_reliability(rural_eb)
    adjusted_correlation = reliability_adjusted_correlation(
        raw_correlation, urban_reliability, rural_reliability
    )
    adjustment_admissible = bool(
        np.isfinite(adjusted_correlation) and abs(adjusted_correlation) <= 1.0
    )

    comparison = pd.DataFrame(
        {
            GROUP: urban_effects.index,
            "urban_n": urban_effects["n_projects"].to_numpy(int),
            "rural_n": rural_effects["n_projects"].to_numpy(int),
            "urban_va": urban_effects["raw_va"].to_numpy(float),
            "rural_va": rural_effects["raw_va"].to_numpy(float),
            "urban_se": urban_effects["sampling_se"].to_numpy(float),
            "rural_se": rural_effects["sampling_se"].to_numpy(float),
            "urban_shrunk_va": urban_eb["shrunk"],
            "rural_shrunk_va": rural_eb["shrunk"],
        }
    )
    result = {
        "minimum_projects_per_book": MIN_PER_BOOK,
        "n_cdes": len(comparison),
        "n_urban_projects": int(comparison["urban_n"].sum()),
        "n_rural_projects": int(comparison["rural_n"].sum()),
        "raw_correlation": raw_correlation,
        "urban_variance_reliability": urban_reliability,
        "rural_variance_reliability": rural_reliability,
        "urban_mean_posterior_reliability": float(urban_eb["mean_reliability"]),
        "rural_mean_posterior_reliability": float(rural_eb["mean_reliability"]),
        "reliability_adjusted_correlation_unbounded": adjusted_correlation,
        "reliability_adjusted_correlation_bounded": (
            float(np.clip(adjusted_correlation, -1.0, 1.0))
            if np.isfinite(adjusted_correlation)
            else float("nan")
        ),
        "reliability_adjustment_admissible": adjustment_admissible,
        "reliability_adjustment_interpretation": (
            "admissible classical disattenuation estimate"
            if adjustment_admissible
            else "inadmissible as a correlation; low estimated reliabilities make the classical correction unstable"
        ),
        "urban_signal_variance_degenerate": bool(urban_eb["degenerate"]),
        "rural_signal_variance_degenerate": bool(rural_eb["degenerate"]),
    }
    return result, comparison


def _split_half_reliability(
    frame: pd.DataFrame, adjusted_outcome: np.ndarray
) -> tuple[dict, np.ndarray]:
    adjusted = np.asarray(adjusted_outcome, dtype=float)
    assert adjusted.shape == (len(frame),)
    grouped_positions = frame.groupby(GROUP, sort=True).indices
    positions_by_cde = {
        str(cde): np.asarray(positions, dtype=int)
        for cde, positions in grouped_positions.items()
        if len(positions) >= MIN_SPLIT_TOTAL
    }
    eligible = sorted(positions_by_cde)
    assert len(eligible) >= 2
    n_cdes = len(eligible)
    n_projects = sum(len(positions_by_cde[cde]) for cde in eligible)
    rng = np.random.default_rng(SEED)
    correlations = np.empty(SPLIT_REPS)
    for rep in range(SPLIT_REPS):
        left_va = np.empty(n_cdes)
        right_va = np.empty(n_cdes)
        for position, cde in enumerate(eligible):
            shuffled = rng.permutation(positions_by_cde[cde])
            cut = len(shuffled) // 2
            assert min(cut, len(shuffled) - cut) >= 1
            assert abs(cut - (len(shuffled) - cut)) <= 1
            left_va[position] = float(adjusted[shuffled[:cut]].mean())
            right_va[position] = float(adjusted[shuffled[cut:]].mean())
        left_va -= left_va.mean()
        right_va -= right_va.mean()
        correlations[rep] = float(np.corrcoef(left_va, right_va)[0, 1])
    assert np.isfinite(correlations).all()
    low, high = np.quantile(correlations, [0.025, 0.975])
    median = float(np.median(correlations))
    spearman_brown = 2 * median / (1 + median) if median > -1 else float("nan")
    return {
        "seed": SEED,
        "repetitions": SPLIT_REPS,
        "minimum_total_projects_per_cde": MIN_SPLIT_TOTAL,
        "n_cdes": int(n_cdes),
        "n_projects": int(n_projects),
        "first_split_correlation": float(correlations[0]),
        "mean_split_correlation": float(correlations.mean()),
        "median_split_correlation": median,
        "split_correlation_interval_95": [float(low), float(high)],
        "spearman_brown_full_sample_reliability_from_median": spearman_brown,
        "interval_definition": (
            "2.5th and 97.5th percentiles across repeated within-CDE random splits; "
            "this is split-assignment variation, not a sampling confidence interval"
        ),
        "risk_adjustment": (
            "year and QALICB-type coefficients are estimated once in the full joint "
            "model and held fixed across halves"
        ),
    }, correlations


def _render_distribution(raw: np.ndarray, shrunk: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN, 2.65))
    for values, color, label, linestyle in (
        (raw, PENCIL, "raw fixed effects", (0, (3, 2))),
        (shrunk, SIGNAL, "empirical-Bayes estimates", "-"),
    ):
        ordered = np.sort(values)
        probability = np.arange(1, len(ordered) + 1) / len(ordered)
        ax.plot(ordered, probability, color=color, lw=1.25, ls=linestyle, label=label)
    ax.axvline(0.0, color=INK, lw=0.7, alpha=0.65)
    ax.set_xlabel("CDE value-added (leverage points, centered)")
    ax.set_ylabel("cumulative share of CDEs")
    ax.legend(frameon=False, fontsize=7.3, loc="lower right", handlelength=2.5)
    _finish_axes(ax)
    _save_pair(fig, "va_raw_shrunk_distribution")


def _render_portability(comparison: pd.DataFrame, result: dict) -> None:
    x = comparison["urban_va"].to_numpy(float)
    y = comparison["rural_va"].to_numpy(float)
    low = float(min(x.min(), y.min()))
    high = float(max(x.max(), y.max()))
    pad = 0.05 * (high - low)
    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN, 3.15))
    ax.plot([low - pad, high + pad], [low - pad, high + pad], color=PENCIL, lw=0.7)
    ax.scatter(
        x,
        y,
        s=18,
        color=SIGNAL,
        alpha=0.72,
        edgecolor=WHITE,
        linewidth=0.35,
        zorder=3,
    )
    ax.set_xlim(low - pad, high + pad)
    ax.set_ylim(low - pad, high + pad)
    ax.set_xlabel("urban-book CDE value-added")
    ax.set_ylabel("rural-book CDE value-added")
    ax.text(
        0.03,
        0.97,
        f"raw r = {result['raw_correlation']:.2f}\n"
        f"{'reliability-adjusted r' if result['reliability_adjustment_admissible'] else 'disattenuation (inadmissible)'} = "
        f"{result['reliability_adjusted_correlation_unbounded']:.2f}\n"
        f"{result['n_cdes']} CDEs; at least {MIN_PER_BOOK} deals per book",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        color=INK,
    )
    _finish_axes(ax)
    _save_pair(fig, "va_portability_scatter")


def _render_split_half(correlations: np.ndarray, result: dict) -> None:
    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN, 2.45))
    ax.hist(
        correlations,
        bins=24,
        color=SIGNAL,
        alpha=0.82,
        edgecolor=WHITE,
        linewidth=0.4,
    )
    ax.axvline(result["median_split_correlation"], color=INK, lw=0.85)
    lo, hi = result["split_correlation_interval_95"]
    ax.axvspan(lo, hi, color=WASH, zorder=0)
    ax.text(
        0.97,
        0.94,
        f"median r = {result['median_split_correlation']:.2f}\n"
        f"split range = [{lo:.2f}, {hi:.2f}]",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.2,
    )
    ax.set_xlabel("correlation between random within-CDE half samples")
    ax.set_ylabel("number of splits")
    _finish_axes(ax)
    _save_pair(fig, "va_split_half_reliability")


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_ready(item) for item in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _portability_reading(correlation: float) -> str:
    if correlation < 0.0:
        return (
            "The urban-rural correlation is negative. That contradicts portable "
            "intermediary quality: CDEs that rank high in one book rank low in the other."
        )
    if correlation < 0.2:
        return (
            "The urban-rural correlation is weak. The data do not support a portable "
            "intermediary-quality interpretation of the within-CDE null."
        )
    if correlation < 0.5:
        return (
            "The urban-rural correlation is positive but moderate. Portability has some "
            "support, but geography-specific noise or performance remains substantial."
        )
    return (
        "The urban-rural correlation is high. CDE performance rankings travel across "
        "books, which turns the within-CDE rural null into evidence consistent with "
        "portable intermediary value-added."
    )


def _write_memo(results: dict) -> None:
    raw = results["raw_value_added"]
    eb = results["empirical_bayes"]
    portability = results["portability"]
    split = results["split_half_reliability"]
    counterfactual = results["counterfactual"]
    p = raw["distribution"]["percentiles"]
    s = eb["shrunk_distribution"]["percentiles"]
    lo, hi = split["split_correlation_interval_95"]
    cf_lo, cf_hi = counterfactual["share_gap_closed_interval_95"]
    portability_text = _portability_reading(portability["raw_correlation"])
    if portability["reliability_adjustment_admissible"]:
        adjustment_text = (
            "The corrected value is within the correlation bounds, although it "
            "remains conditional on the classical-error reliability estimates."
        )
    else:
        adjustment_text = (
            "This corrected value is **inadmissible as a correlation**: the "
            "estimated book reliabilities are so low that classical disattenuation "
            "is unstable. It is reported because it is the requested calculation, "
            "not as an estimate of a latent correlation."
        )
    if portability["raw_correlation"] >= 0.5:
        surprise = (
            "The strongest result is how clearly the ordering survives the geographic "
            "split despite small rural books."
        )
    elif portability["raw_correlation"] >= 0.0:
        surprise = (
            "The main surprise is that the geographic portability test is much weaker "
            "than the between-CDE dispersion alone would suggest."
        )
    else:
        surprise = (
            "The main surprise is the reversal in CDE rankings between urban and rural "
            "books, which cuts against the paper's motivating portability hypothesis."
        )

    memo = f"""# Intermediary value-added: first pass

## Bottom line

The year- and QALICB-adjusted fixed effects are widely dispersed across
{raw["n_cdes"]} CDEs. Their raw standard deviation is {raw["distribution"]["sd"]:.3f}
leverage points (IQR {raw["distribution"]["iqr"]:.3f}; p10 {p["p10"]:+.3f}, p90
{p["p90"]:+.3f}). Removing the mean pooled-OLS sampling variance leaves an estimated
signal standard deviation of {eb["signal_sd"]:.3f}, only
{eb["signal_share_of_total_variance"]:.1%} of the raw effect variance; mean posterior
reliability is {eb["mean_reliability"]:.3f}. The shrunk p10-p90 range is {s["p10"]:+.3f} to
{s["p90"]:+.3f}. The signal-variance estimate is
{"degenerate at zero" if eb["degenerate"] else "strictly positive"}.

The central portability test uses the {portability["n_cdes"]} CDEs with at least
{portability["minimum_projects_per_book"]} urban and
{portability["minimum_projects_per_book"]} rural projects. Urban- and rural-book
VA correlate at **{portability["raw_correlation"]:+.3f}**. The classical
reliability correction is **{portability["reliability_adjusted_correlation_unbounded"]:+.3f}**
(urban variance reliability {portability["urban_variance_reliability"]:.3f}; rural
{portability["rural_variance_reliability"]:.3f}). {adjustment_text} {portability_text}

{surprise} The repeated split-half exercise is a useful check on whether any CDE
ranking is stable at all: the median half-sample correlation is
{split["median_split_correlation"]:+.3f}, with a 95% range across {split["repetitions"]}
random splits of [{lo:+.3f}, {hi:+.3f}]. The corresponding Spearman-Brown
full-sample reliability is {split["spearman_brown_full_sample_reliability_from_median"]:.3f}.
This exercise includes every CDE with at least two projects, so the thinnest books
contribute one project to each half. That range reflects split assignment, not a
confidence interval.

## Counterfactual accounting

Below-median-VA CDEs hold ${counterfactual["reallocated_dollars"] / 1e9:.2f} billion,
or {counterfactual["reallocated_share"]:.1%}, of observed non-metro QLICI. Moving
all of those dollars to above-median CDEs in proportion to the recipients' existing
non-metro books raises the dollar-weighted VA component by
{counterfactual["leverage_gain"]:+.3f} leverage points. Relative to the observed
project-weighted raw rural gap of {results["raw_rural_gap"]["gap"]:+.3f}, that is
{counterfactual["share_gap_closed"]:.1%} of the gap; the normal-normal EB posterior
interval is [{cf_lo:.1%}, {cf_hi:.1%}].

This is an accounting exercise, not a causal estimate. It assumes that CDE VA is
causal and portable to rural projects; year and QALICB composition stays fixed;
all below-median deployment can move; above-median CDEs can absorb it without
diminishing returns; the recipient mix follows existing above-median rural dollar
shares; reallocating intermediaries does not change project selection, prices,
entry, or equilibrium; and a leverage-point VA change can be compared with the
project-weighted -0.262 raw gap even though the reallocation itself is dollar
weighted. The interval propagates EB estimation uncertainty conditional on these
assumptions and the estimated signal variance. It does not cover model uncertainty
or causal uncertainty. The reported interval holds the plug-in donor and recipient
sets fixed, as an implementable ranking would. Re-ranking intermediaries inside each
posterior draw gives the separately recorded sensitivity interval
[{counterfactual["reranked_each_draw_share_gap_closed_interval_95"][0]:.1%},
{counterfactual["reranked_each_draw_share_gap_closed_interval_95"][1]:.1%}], which is
optimistic because every draw selects on its own latent effects.

## What the numbers support

- They support persistent cross-CDE heterogeneity only to the extent that the EB
  signal variance is positive and split-half rankings are stable.
- They support portable intermediary performance only to the extent shown by the
  urban-rural correlation. The disattenuated coefficient can exceed one in finite
  samples; when it does, it signals an imprecise correction rather than a literal
  correlation above one.
- They do not establish that changing the intermediary changes leverage, that
  leverage is social value, or that redirecting allocations would reproduce the
  accounting gain.

## Design weaknesses a referee will attack

1. **Assignment is endogenous.** CDE effects combine intermediary practice with
   persistent borrower, sponsor, local-market, and project selection not absorbed
   by year and four QALICB categories. They are not random-assignment effects.
2. **The outcome is narrow.** `leverage_win` is a winsorized financing multiple on
   subsidized investment, not welfare, additionality, tax expenditure efficiency,
   project survival, or community benefit.
3. **Small and selected books.** The portability sample excludes one-sided and
   thin-book CDEs. Rural-book sampling error is substantial, and the three-deal
   threshold is inherited from the paper's switcher exhibit rather than identified
   by a power calculation.
4. **EB structure is strong.** The normal-normal calculation treats the pooled-OLS
   coefficient variance as known and uses a common signal variance. The pooling is
   what gives thin CDEs a meaningful variance instead of HC1's singleton
   degeneracy, but it imposes homoskedastic project noise. Heavy tails,
   heterogeneous signal variance, correlated coefficient error, and uncertainty in
   the estimated prior variance are only partly represented by the posterior draws.
5. **Portability is correlational.** A positive book correlation could come from
   common deal pipelines, national partners, or persistent sorting; a low one could
   reflect noisier rural books rather than geography-specific technology. The two
   book samples are disjoint, but their nuisance specification is common.
6. **Split-half risk adjustment is shared.** Holding full-sample year/type
   coefficients fixed prevents nuisance re-estimation from dominating the split,
   but their estimation error is shared across halves and can mildly raise the
   correlation. CDEs with only two projects contribute one observation per half,
   which makes the reported reliability deliberately demanding.
7. **The counterfactual has no capacity or equilibrium discipline.** It moves every
   below-median rural dollar, preserves the existing above-median recipient shares,
   and assumes constant VA at expanded scale. It also compares a dollar-weighted
   accounting change with a project-weighted raw gap.
8. **External validity is bounded by the release.** The estimates describe observed
   completed projects and named CDEs in this file, not applicants, rejected projects,
   the full certified-CDE population, or future allocation rounds.
"""
    BRIEFS.mkdir(parents=True, exist_ok=True)
    (BRIEFS / "value_added_first_pass.md").write_text(memo, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Loading project-level analysis data...")
    projects = pd.read_csv(DATA / "nmtc_projects.csv")
    required = [
        OUTCOME,
        GROUP,
        "year",
        "qalicb_type",
        "metro",
        "project_qlici",
    ]
    projects = projects.dropna(subset=required).reset_index(drop=True)
    projects["year"] = projects["year"].astype(int)
    assert projects["metro"].isin(["metro", "non_metro"]).all()
    assert (projects["project_qlici"] >= 0.0).all()
    print(
        f"  N = {len(projects):,}; {projects[GROUP].nunique()} CDEs; "
        f"{int((projects.metro == 'non_metro').sum()):,} non-metro projects"
    )

    print("\n1. Raw CDE value-added")
    raw_fit = fit_cde_effects(projects)
    raw_effects = raw_fit.effects.copy()
    raw_distribution = _distribution(raw_effects["raw_va"].to_numpy())
    print(
        f"  CDEs = {len(raw_effects)}; SD = {raw_distribution['sd']:.4f}; "
        f"IQR = {raw_distribution['iqr']:.4f}; "
        f"p10/p50/p90 = {raw_distribution['percentiles']['p10']:+.4f} / "
        f"{raw_distribution['percentiles']['p50']:+.4f} / "
        f"{raw_distribution['percentiles']['p90']:+.4f}"
    )

    print("\n2. Empirical-Bayes shrinkage")
    raw_eb = eb_decompose(
        raw_effects["raw_va"].to_numpy(),
        raw_effects["sampling_variance"].to_numpy(),
    )
    raw_effects["reliability"] = raw_eb["reliability"]
    raw_effects["shrunk_va"] = raw_eb["shrunk"]
    raw_effects["posterior_variance"] = raw_eb["posterior_variance"]
    shrunk_distribution = _distribution(raw_eb["shrunk"])
    assert raw_eb["signal_variance"] >= 0.0
    print(
        f"  total variance = {raw_eb['total_variance']:.6f}; "
        f"mean sampling variance = {raw_eb['mean_sampling_variance']:.6f}"
    )
    print(
        f"  signal SD = {raw_eb['signal_sd']:.4f}; "
        f"signal share = {raw_eb['signal_variance'] / raw_eb['total_variance']:.1%}; "
        f"mean reliability = {raw_eb['mean_reliability']:.4f}; "
        f"degenerate = {raw_eb['degenerate']}"
    )
    print(
        f"  shrunk SD = {shrunk_distribution['sd']:.4f}; "
        f"shrunk p10/p90 = {shrunk_distribution['percentiles']['p10']:+.4f} / "
        f"{shrunk_distribution['percentiles']['p90']:+.4f}"
    )

    print("\n3. Urban-rural split-sample portability")
    portability, portability_frame = _book_portability(projects)
    print(
        f"  CDEs = {portability['n_cdes']} (>= {MIN_PER_BOOK} projects per book); "
        f"urban N = {portability['n_urban_projects']:,}; "
        f"rural N = {portability['n_rural_projects']:,}"
    )
    print(
        f"  raw r = {portability['raw_correlation']:+.4f}; "
        f"urban/rural reliability = "
        f"{portability['urban_variance_reliability']:.4f} / "
        f"{portability['rural_variance_reliability']:.4f}"
    )
    print(
        "  reliability-adjusted r (unbounded; "
        f"admissible = {portability['reliability_adjustment_admissible']}) = "
        f"{portability['reliability_adjusted_correlation_unbounded']:+.4f}"
    )
    print(f"  reading: {_portability_reading(portability['raw_correlation'])}")

    print("\n4. Repeated within-CDE split-half reliability")
    split_half, split_correlations = _split_half_reliability(
        projects, raw_fit.adjusted_outcome
    )
    split_lo, split_hi = split_half["split_correlation_interval_95"]
    print(
        f"  seed = {SEED}; reps = {SPLIT_REPS}; CDEs = {split_half['n_cdes']}; "
        f"first split r = {split_half['first_split_correlation']:+.4f}"
    )
    print(
        f"  median r = {split_half['median_split_correlation']:+.4f}; "
        f"95% split range = [{split_lo:+.4f}, {split_hi:+.4f}]"
    )

    print("\n5. Reallocation accounting counterfactual")
    raw_gap_result = raw_group_gap(
        projects[OUTCOME], (projects["metro"] == "non_metro").astype(float)
    )
    raw_gap = raw_gap_result["gap"]
    raw_gap_ols = raw_gap_result["ols_gap"]
    assert round(raw_gap, 3) == RAW_GAP_REFERENCE

    effects_by_cde = raw_effects.set_index(GROUP)["shrunk_va"]
    posterior_variance_by_cde = raw_effects.set_index(GROUP)["posterior_variance"]
    rural_dollars = (
        projects[projects["metro"] == "non_metro"].groupby(GROUP)["project_qlici"].sum()
    )
    counterfactual = counterfactual_reallocation(
        effects_by_cde, rural_dollars, raw_gap=raw_gap
    )
    rng = np.random.default_rng(SEED + 1)
    posterior_effect_draws = rng.normal(
        loc=effects_by_cde.to_numpy(float),
        scale=np.sqrt(posterior_variance_by_cde.to_numpy(float)),
        size=(POSTERIOR_DRAWS, len(effects_by_cde)),
    )
    fixed_draw_gain = np.empty(POSTERIOR_DRAWS)
    fixed_draw_share = np.empty(POSTERIOR_DRAWS)
    reranked_draw_gain = np.empty(POSTERIOR_DRAWS)
    reranked_draw_share = np.empty(POSTERIOR_DRAWS)
    for draw in range(POSTERIOR_DRAWS):
        effect_draw = pd.Series(
            posterior_effect_draws[draw], index=effects_by_cde.index
        )
        fixed_result = counterfactual_reallocation(
            effect_draw,
            rural_dollars,
            raw_gap=raw_gap,
            classification_effects=effects_by_cde,
        )
        reranked_result = counterfactual_reallocation(
            effect_draw, rural_dollars, raw_gap=raw_gap
        )
        fixed_draw_gain[draw] = fixed_result["leverage_gain"]
        fixed_draw_share[draw] = fixed_result["share_gap_closed"]
        reranked_draw_gain[draw] = reranked_result["leverage_gain"]
        reranked_draw_share[draw] = reranked_result["share_gap_closed"]
    counterfactual["posterior_draws"] = POSTERIOR_DRAWS
    counterfactual["posterior_seed"] = SEED + 1
    counterfactual["leverage_gain_interval_95"] = np.quantile(
        fixed_draw_gain, [0.025, 0.975]
    ).tolist()
    counterfactual["share_gap_closed_interval_95"] = np.quantile(
        fixed_draw_share, [0.025, 0.975]
    ).tolist()
    counterfactual["interval_definition"] = (
        "2.5th and 97.5th percentiles of independent normal-normal EB posterior "
        "draws, holding the plug-in below/above-median policy groups fixed; fixed "
        "raw gap and fixed observed rural deployment"
    )
    counterfactual["reranked_each_draw_leverage_gain_interval_95"] = np.quantile(
        reranked_draw_gain, [0.025, 0.975]
    ).tolist()
    counterfactual["reranked_each_draw_share_gap_closed_interval_95"] = np.quantile(
        reranked_draw_share, [0.025, 0.975]
    ).tolist()
    counterfactual["reranked_interval_definition"] = (
        "sensitivity that reclassifies CDEs around the median in every posterior "
        "draw; optimistic relative to a fixed implementable ranking because it "
        "selects on each draw's latent effects"
    )
    counterfactual["assumptions"] = [
        "CDE value-added is causal and transfers one-for-one to rural projects",
        "year and QALICB-type composition remains fixed",
        "all below-median rural dollars can be reassigned",
        "above-median CDEs absorb dollars without capacity constraints or diminishing returns",
        "recipient shares follow above-median CDEs' observed rural QLICI shares",
        "project selection, prices, entry, and equilibrium do not respond",
        "dollar-weighted VA changes are compared with the project-weighted raw rural gap",
        "the normal-normal EB model and estimated signal variance are correctly specified",
    ]
    cf_lo, cf_hi = counterfactual["share_gap_closed_interval_95"]
    print(
        f"  raw rural gap = {raw_gap:+.4f}; rural dollars = "
        f"${counterfactual['observed_total_dollars'] / 1e9:.3f}B"
    )
    print(
        f"  reallocated = ${counterfactual['reallocated_dollars'] / 1e9:.3f}B "
        f"({counterfactual['reallocated_share']:.1%}); gain = "
        f"{counterfactual['leverage_gain']:+.4f} leverage points"
    )
    print(
        f"  gap closed = {counterfactual['share_gap_closed']:.1%}; "
        f"EB posterior interval = [{cf_lo:.1%}, {cf_hi:.1%}]"
    )
    print("  interpretation: accounting only, not causal")

    raw_cde_records = raw_effects.sort_values(GROUP).to_dict(orient="records")
    portability_records = portability_frame.sort_values(GROUP).to_dict(orient="records")
    results = {
        "metadata": {
            "outcome": OUTCOME,
            "controls": list(CONTROLS),
            "covariance": "classical OLS using pooled residual variance",
            "normalization": "unweighted mean CDE effect equals zero",
            "eb_model": "normal-normal; signal variance = raw cross-CDE variance minus mean pooled-OLS sampling variance",
            "seed": SEED,
            "input": "data/processed/nmtc_projects.csv",
        },
        "raw_rural_gap": {
            "metro_mean": raw_gap_result["control_mean"],
            "non_metro_mean": raw_gap_result["treated_mean"],
            "gap": raw_gap,
            "ols_identity_gap": raw_gap_ols,
        },
        "raw_value_added": {
            "n_projects": raw_fit.n_obs,
            "n_cdes": len(raw_effects),
            "n_parameters": raw_fit.n_parameters,
            "residual_df": raw_fit.residual_df,
            "distribution": raw_distribution,
        },
        "empirical_bayes": {
            "total_variance": raw_eb["total_variance"],
            "mean_sampling_variance": raw_eb["mean_sampling_variance"],
            "signal_variance_unconstrained": raw_eb["signal_variance_unconstrained"],
            "signal_variance": raw_eb["signal_variance"],
            "signal_sd": raw_eb["signal_sd"],
            "signal_share_of_total_variance": (
                raw_eb["signal_variance"] / raw_eb["total_variance"]
                if raw_eb["total_variance"] > 0
                else 0.0
            ),
            "degenerate": raw_eb["degenerate"],
            "mean_reliability": raw_eb["mean_reliability"],
            "shrunk_distribution": shrunk_distribution,
        },
        "portability": portability,
        "split_half_reliability": split_half,
        "counterfactual": counterfactual,
        "figures": [
            "figures/va_raw_shrunk_distribution.pdf",
            "figures/va_raw_shrunk_distribution.png",
            "figures/va_portability_scatter.pdf",
            "figures/va_portability_scatter.png",
            "figures/va_split_half_reliability.pdf",
            "figures/va_split_half_reliability.png",
        ],
        "cde_estimates": raw_cde_records,
        "portability_estimates": portability_records,
    }

    print("\nWriting figures and outputs...")
    _render_distribution(
        raw_effects["raw_va"].to_numpy(), raw_effects["shrunk_va"].to_numpy()
    )
    _render_portability(portability_frame, portability)
    _render_split_half(split_correlations, split_half)
    ready = _json_ready(results)
    (OUT / "value_added.json").write_text(
        json.dumps(ready, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    _write_memo(ready)
    print("  wrote data/processed/regressions/value_added.json")
    print("  wrote 3 figure pairs under figures/va_*")
    print("  wrote briefs/value_added_first_pass.md")


if __name__ == "__main__":
    main()
