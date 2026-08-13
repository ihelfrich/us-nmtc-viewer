"""Regenerate the paper's four legacy figures in the house style.

Reads the same processed project and transaction files as the original
figure scripts and leaves those original figures untouched.

Writes:
  figures/paper_1_deployment.{pdf,png}
  figures/paper_2_nonmetro_share.{pdf,png}
  figures/paper_3_leverage_dist.{pdf,png}
  figures/paper_6_bunching.{pdf,png}

Run: uv run --with pandas --with numpy --with matplotlib python scripts/make_paper_figures.py
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"

INK = "#16161D"
PENCIL = "#6B6B70"
SIGNAL = "#2852E8"
WASH = "#EEF2FA"
WHITE = "#FFFFFF"
# Figures are drawn at the width they print at (the 4.9in text block), so
# \includegraphics[width=\textwidth] applies no scaling and the labels keep
# the size set here. Drawing wide and shrinking to fit was what made the
# earlier exhibits illegible.
TEXTWIDTH_IN = 4.9
FIGSIZE = (TEXTWIDTH_IN, 3.05)
FIGSIZE_WIDE = (TEXTWIDTH_IN, 2.45)

OUTPUT_STEMS = {
    "deployment": "paper_1_deployment",
    "nonmetro_share": "paper_2_nonmetro_share",
    "leverage": "paper_3_leverage_dist",
    "bunching": "paper_6_bunching",
}


plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 300,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "font.family": "serif",
        "font.serif": ["Palatino", "TeX Gyre Pagella", "DejaVu Serif"],
        "font.size": 8.5,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
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


def _finish_axes(ax: plt.Axes, *, grid: bool = True) -> None:
    """Apply the common hairline frame and restrained horizontal grid."""
    for side in ("left", "bottom"):
        ax.spines[side].set_color(PENCIL)
        ax.spines[side].set_linewidth(0.6)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis="y", color=PENCIL, linewidth=0.55, alpha=0.12)
    ax.grid(axis="x", visible=False)


def _save_pair(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.55)
    for suffix in ("pdf", "png"):
        fig.savefig(
            output_dir / f"{stem}.{suffix}",
            bbox_inches="tight",
            pad_inches=0.04,
            facecolor=WHITE,
        )
    plt.close(fig)


def annual_deployment(transactions: pd.DataFrame) -> pd.DataFrame:
    by_year = (
        transactions.groupby(["year", "metro"])["qlici_amount"]
        .sum()
        .div(1e6)
        .unstack(fill_value=0)
        .sort_index()
    )
    return by_year.reindex(columns=["non_metro", "metro"], fill_value=0)


def compute_bunching(transactions: pd.DataFrame) -> SimpleNamespace:
    """Reproduce the bunching estimator in ``run_regressions.py`` exactly."""
    cde = (
        transactions.groupby("cde_name")
        .agg(
            n_tx=("transaction_id", "count"),
            n_nm=("metro", lambda values: (values == "non_metro").sum()),
        )
        .assign(share=lambda frame: frame.n_nm / frame.n_tx)
        .reset_index()
    )
    active = cde[cde.n_tx >= 5].copy()
    shares = active["share"].to_numpy()

    bins = np.linspace(0, 1, 41)
    midpoints = 0.5 * (bins[:-1] + bins[1:])
    counts, _ = np.histogram(shares, bins=bins)
    density = counts / (counts.sum() * (bins[1] - bins[0]))

    in_window = (midpoints >= 0.175) & (midpoints <= 0.225)
    fit_mask = (~in_window) & (midpoints <= 0.95)
    polynomial = np.polyfit(midpoints[fit_mask], density[fit_mask], deg=3)
    counterfactual = np.polyval(polynomial, midpoints).clip(min=0)

    empirical_mass = float(np.trapezoid(density[in_window], midpoints[in_window]))
    counterfactual_mass = float(
        np.trapezoid(counterfactual[in_window], midpoints[in_window])
    )
    excess_mass = empirical_mass - counterfactual_mass
    excess_mass_pct = 100 * excess_mass / counterfactual_mass

    near_window = ((midpoints >= 0.10) & (midpoints < 0.175)) | (
        (midpoints > 0.225) & (midpoints <= 0.30)
    )
    density_at_20 = float(density[in_window].mean())
    density_near_20 = float(density[near_window].mean())
    ratio_at_to_near = density_at_20 / density_near_20

    return SimpleNamespace(
        n_cde_active=int(len(active)),
        bins=bins,
        midpoints=midpoints,
        density=density,
        counterfactual=counterfactual,
        empirical_mass=empirical_mass,
        counterfactual_mass=counterfactual_mass,
        excess_mass=excess_mass,
        excess_mass_pct=excess_mass_pct,
        density_at_20=density_at_20,
        density_near_20=density_near_20,
        ratio_at_to_near=ratio_at_to_near,
    )


def _plot_deployment(transactions: pd.DataFrame, output_dir: Path) -> str:
    by_year = annual_deployment(transactions)
    years = by_year.index.to_numpy()
    nonmetro = by_year["non_metro"].to_numpy()
    metro = by_year["metro"].to_numpy()

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(years, nonmetro, width=0.78, color=SIGNAL, linewidth=0, zorder=2)
    ax.bar(
        years,
        metro,
        bottom=nonmetro,
        width=0.78,
        color=INK,
        linewidth=0,
        zorder=2,
    )
    ax.set_xlabel("Origination year")
    ax.set_ylabel("QLICI deployed (nominal dollars)")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _: f"${value / 1000:.0f}B")
    )
    ax.set_xticks([2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022])
    ax.set_xlim(years.min() - 0.65, years.max() + 1.65)
    ax.set_ylim(bottom=0)
    last = -1
    ax.text(
        years[last] + 0.55,
        nonmetro[last] / 2,
        "non-metro",
        color=SIGNAL,
        fontsize=7.6,
        va="center",
    )
    ax.text(
        years[last] + 0.55,
        nonmetro[last] + metro[last] * 0.54,
        "metro",
        color=INK,
        fontsize=7.6,
        va="center",
    )
    _finish_axes(ax)
    _save_pair(fig, output_dir, OUTPUT_STEMS["deployment"])

    total_billions = transactions["qlici_amount"].sum() / 1e9
    return (
        f"deployment: n={len(transactions):,} transactions; "
        f"QLICI=${total_billions:.1f}B"
    )


def _plot_nonmetro_share(transactions: pd.DataFrame, output_dir: Path) -> str:
    by_year = annual_deployment(transactions)
    share = by_year["non_metro"].div(by_year.sum(axis=1)).mul(100)
    years = share.index.to_numpy()

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(
        years,
        share.to_numpy(),
        color=SIGNAL,
        linewidth=1.65,
        marker="o",
        markersize=3.2,
        markeredgewidth=0,
        zorder=3,
    )
    ax.axhline(20, color=PENCIL, linewidth=0.75, linestyle=(0, (3, 2)), zorder=1)
    # left-hand placement: the series runs well below the line in the early
    # years, so the label sits clear of the data instead of across it
    ax.text(
        years.min() + 0.3,
        21.0,
        "20% administrative target",
        color=PENCIL,
        fontsize=7.6,
        va="bottom",
        ha="left",
    )
    ax.text(
        years.max() + 0.35,
        share.iloc[-1],
        "non-metro share",
        color=SIGNAL,
        fontsize=7.6,
        va="center",
    )
    ax.set_xlabel("Origination year")
    ax.set_ylabel("Non-metro share of QLICI dollars")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.set_xticks([2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022])
    ax.set_xlim(years.min() - 0.4, years.max() + 2.65)
    ax.set_ylim(0, max(40, float(share.max()) + 5))
    _finish_axes(ax)
    _save_pair(fig, output_dir, OUTPUT_STEMS["nonmetro_share"])

    overall = (
        transactions.loc[transactions.metro == "non_metro", "qlici_amount"].sum()
        / transactions["qlici_amount"].sum()
        * 100
    )
    return f"nonmetro share: n={len(share)} years; overall={overall:.1f}%"


def _plot_leverage(projects: pd.DataFrame, output_dir: Path) -> str:
    metro = projects.loc[projects.metro == "metro", "leverage_win"].dropna()
    nonmetro = projects.loc[
        projects.metro == "non_metro", "leverage_win"
    ].dropna()
    bins = np.linspace(1, 10, 46)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.hist(
        metro,
        bins=bins,
        density=True,
        histtype="stepfilled",
        color=INK,
        alpha=0.18,
        edgecolor=INK,
        linewidth=0.75,
        zorder=2,
    )
    ax.hist(
        nonmetro,
        bins=bins,
        density=True,
        histtype="step",
        color=SIGNAL,
        linewidth=1.35,
        zorder=3,
    )
    metro_median = float(metro.median())
    nonmetro_median = float(nonmetro.median())
    ax.axvline(metro_median, color=INK, linewidth=0.75, linestyle=(0, (2, 2)))
    ax.axvline(
        nonmetro_median, color=SIGNAL, linewidth=0.85, linestyle=(0, (2, 2))
    )
    ax.text(
        0.98,
        0.88,
        f"metro  n={len(metro):,}, median {metro_median:.2f}×",
        transform=ax.transAxes,
        color=INK,
        fontsize=7.6,
        ha="right",
    )
    ax.text(
        0.98,
        0.80,
        f"non-metro  n={len(nonmetro):,}, median {nonmetro_median:.2f}×",
        transform=ax.transAxes,
        color=SIGNAL,
        fontsize=7.6,
        ha="right",
    )
    ax.set_xlabel("Leverage ratio (total project cost / QLICI)")
    ax.set_ylabel("Density")
    ax.set_xlim(1, 10)
    ax.set_ylim(bottom=0)
    _finish_axes(ax)
    _save_pair(fig, output_dir, OUTPUT_STEMS["leverage"])

    return (
        f"leverage: n={len(metro) + len(nonmetro):,} projects; "
        f"medians metro={metro_median:.2f}x, non-metro={nonmetro_median:.2f}x"
    )


def _plot_bunching(transactions: pd.DataFrame, output_dir: Path) -> str:
    result = compute_bunching(transactions)
    width = result.bins[1] - result.bins[0]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    # House rule: the accent marks the focal element, which here is the
    # target and its test window, not the whole empirical distribution.
    ax.axvspan(0.175, 0.225, color=WASH, zorder=0)
    ax.bar(
        result.midpoints,
        result.density,
        width=width * 0.92,
        color=INK,
        alpha=0.62,
        edgecolor=WHITE,
        linewidth=0.35,
        zorder=2,
    )
    ax.plot(
        result.midpoints,
        result.counterfactual,
        color=INK,
        linewidth=1.35,
        linestyle=(0, (4, 2)),
        zorder=3,
    )
    ax.axvline(0.20, color=SIGNAL, linewidth=1.1, zorder=4)
    ax.text(
        0.20,
        0.98,
        "20% target",
        transform=ax.get_xaxis_transform(),
        color=SIGNAL,
        fontsize=7.6,
        ha="center",
        va="top",
    )
    label_index = int(np.argmin(np.abs(result.midpoints - 0.63)))
    ax.annotate(
        "polynomial counterfactual",
        xy=(
            result.midpoints[label_index],
            result.counterfactual[label_index],
        ),
        xytext=(8, 6),
        textcoords="offset points",
        color=INK,
        fontsize=7.6,
    )
    ax.text(
        0.985,
        0.88,
        "empirical density",
        transform=ax.transAxes,
        color=INK,
        fontsize=7.6,
        ha="right",
    )
    ax.set_xlabel("CDE non-metro share of QLICI transactions")
    ax.set_ylabel("Density")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_xlim(0, 1)
    ax.set_ylim(bottom=0)
    _finish_axes(ax)
    _save_pair(fig, output_dir, OUTPUT_STEMS["bunching"])

    return (
        f"bunching: n={result.n_cde_active:,} CDEs; "
        f"B={result.excess_mass:+.4f} ({result.excess_mass_pct:+.1f}%)"
    )


def render_all(output_dir: Path = FIGURES) -> list[str]:
    projects = pd.read_csv(DATA / "nmtc_projects.csv")
    transactions = pd.read_csv(DATA / "nmtc_transactions.csv")
    provenance = [
        _plot_deployment(transactions, output_dir),
        _plot_nonmetro_share(transactions, output_dir),
        _plot_leverage(projects, output_dir),
        _plot_bunching(transactions, output_dir),
    ]
    for line in provenance:
        print(line)
    return provenance


if __name__ == "__main__":
    render_all()
