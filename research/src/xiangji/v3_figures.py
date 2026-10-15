"""Redraw all V3 manuscript figures without changing V2.5 artwork or results."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

from xiangji.data import RESEARCH_ROOT


EXPERIMENTS = RESEARCH_ROOT / "experiments"
OUT = RESEARCH_ROOT / "figures" / "v3"
SOURCE_DATA = OUT / "source_data"

INK = "#2D2A26"
MUTED = "#77736D"
GRID = "#DDD8D0"
PAPER = "#F7F4EF"
CHARCOAL = "#66635F"
TEAL = "#2F5D62"
CINNABAR = "#A44A3F"
SAGE = "#7D9D8C"
PLUM = "#7A5B78"
OCHRE = "#B08645"

MODEL_ORDER = ["frequency", "directed_graph", "sscl", "ease", "slim", "ppr"]
MODEL_LABEL = {
    "frequency": "Frequency",
    "directed_graph": "Directed graph",
    "sscl": "SSCL",
    "ease": "EASE",
    "slim": "SLIM",
    "ppr": "PPR",
}
MODEL_COLOR = {
    "frequency": CHARCOAL,
    "directed_graph": TEAL,
    "sscl": CINNABAR,
    "ease": SAGE,
    "slim": PLUM,
    "ppr": OCHRE,
}
MODEL_MARKER = {
    "frequency": "o",
    "directed_graph": "s",
    "sscl": "D",
    "ease": "^",
    "slim": "v",
    "ppr": "P",
}
WORK_LABEL = {
    "chen_xiangpu_compilation": "Chen",
    "hong_xiangpu_attributed": "Hong",
    "huizhai_xiangpu": "Huizhai",
    "liexiang_xinpu": "Liexiang",
    "moe_xiaolu_xiangpu": "Xiaolu",
    "xiangcheng_compilation_unresolved_source": "Xiangcheng",
}
WORK_LONG = {
    "chen_xiangpu_compilation": "Chen Xiangpu",
    "hong_xiangpu_attributed": "Hong Xiangpu",
    "huizhai_xiangpu": "Huizhai Xiangpu",
    "liexiang_xinpu": "Liexiang Xinpu",
    "moe_xiaolu_xiangpu": "Xiaolu Xiangpu",
    "xiangcheng_compilation_unresolved_source": "Xiangcheng compilation",
}


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans", "sans-serif"],
            "font.size": 8.0,
            "axes.labelsize": 8.25,
            "axes.titlesize": 9.25,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.25,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def _load(name: str) -> dict:
    return json.loads((EXPERIMENTS / name).read_text(encoding="utf-8"))


def _panel(ax: mpl.axes.Axes, label: str) -> None:
    ax.text(-0.12, 1.06, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")


def _clean(ax: mpl.axes.Axes, axis: str | None = None) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    if axis:
        ax.grid(axis=axis, color=GRID, linewidth=0.55, alpha=0.85)
        ax.set_axisbelow(True)


def _save(fig: mpl.figure.Figure, stem: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / f"{stem}.svg"
    pdf_path = OUT / f"{stem}.pdf"
    tiff_path = OUT / f"{stem}.tiff"
    png_path = OUT / f"{stem}.png"
    fig.savefig(svg_path, bbox_inches="tight", metadata={"Creator": "Xiangji-CGIR V3"})
    fig.savefig(pdf_path, bbox_inches="tight", metadata={"Creator": "Xiangji-CGIR V3", "CreationDate": None, "ModDate": None})
    fig.savefig(tiff_path, dpi=600, bbox_inches="tight")
    fig.savefig(png_path, dpi=600, bbox_inches="tight", metadata={"Software": "Xiangji-CGIR V3"})
    plt.close(fig)
    return [svg_path, pdf_path, tiff_path, png_path]


def _box(ax: mpl.axes.Axes, xy: tuple[float, float], wh: tuple[float, float], *, face: str = PAPER, edge: str = MUTED, radius: float = 0.012) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        xy,
        *wh,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=0.85,
    )
    ax.add_patch(patch)
    return patch


def figure_1_data_scale() -> list[Path]:
    structured = json.loads((RESEARCH_ROOT / "data/interim/structured_formula_candidates_v0.1.json").read_text(encoding="utf-8"))
    reference = json.loads((RESEARCH_ROOT / "data/curated/formula_reference_v0.1.json").read_text(encoding="utf-8"))
    weak = _load("v2_5_weak_supervision.json")
    gold = _load("v2_nested_cross_work.json")["models"]["sscl"]["work_metrics"]
    records = structured["records"]

    collections = ["xiangcheng", "chen_xiangpu", "hong_xiangpu"]
    collection_labels = ["Xiangcheng", "Chen Xiangpu", "Hong Xiangpu"]
    collection_colors = [INK, MUTED, OCHRE]
    stages = ["Candidates", "Ratio-ready", "Gold", "Weak eligible"]
    counts = {
        "Candidates": [sum(r["collection"] == c for r in records) for c in collections],
        "Ratio-ready": [sum(r["collection"] == c and r["ratio_ready_automatic"] for r in records) for c in collections],
        "Gold": [sum(r["collection"] == c for r in reference["records"]) for c in collections],
        "Weak eligible": [84, 58, 4],
    }

    fig = plt.figure(figsize=(7.10, 3.45))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.12, 1.30, 1.18], wspace=0.55)

    ax = fig.add_subplot(gs[0, 0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _panel(ax, "a")

    _box(ax, (0.06, 0.81), (0.88, 0.13))
    ax.text(0.23, 0.875, "592", ha="center", va="center", fontsize=15.5, color=INK)
    ax.text(0.67, 0.875, "source-linked\ncandidates", ha="center", va="center", fontsize=7.4, color=INK, linespacing=1.05)
    _box(ax, (0.06, 0.59), (0.88, 0.13))
    ax.text(0.23, 0.655, "296", ha="center", va="center", fontsize=15.5, color=INK)
    ax.text(0.67, 0.655, "ratio-ready\nrecords", ha="center", va="center", fontsize=7.4, color=INK, linespacing=1.05)
    _box(ax, (0.07, 0.36), (0.39, 0.12), face="#F4EBDD", edge=OCHRE)
    _box(ax, (0.54, 0.36), (0.39, 0.12), face="#E7EFEC", edge=TEAL)
    ax.text(0.265, 0.435, "91", ha="center", va="center", fontsize=12.0, color=OCHRE, fontweight="bold")
    ax.text(0.265, 0.392, "reviewed gold", ha="center", va="center", fontsize=7.25, color=OCHRE)
    ax.text(0.735, 0.435, "146", ha="center", va="center", fontsize=12.0, color=TEAL, fontweight="bold")
    ax.text(0.735, 0.392, "weak records", ha="center", va="center", fontsize=7.25, color=TEAL)
    _box(ax, (0.08, 0.10), (0.84, 0.14), face="#E7EFEC", edge=TEAL)
    ax.text(0.50, 0.195, "237", ha="center", va="center", fontsize=13.5, color=INK)
    ax.text(0.50, 0.145, "model-facing records\n191 families", ha="center", va="center", fontsize=7.25, color=MUTED, linespacing=1.0)

    arrow = dict(arrowstyle="-|>", color=MUTED, lw=1.05, mutation_scale=10, shrinkA=1, shrinkB=1)
    ax.annotate("", xy=(0.50, 0.73), xytext=(0.50, 0.81), arrowprops=arrow)
    ax.plot([0.50, 0.50], [0.53, 0.59], color=MUTED, lw=1.0)
    ax.plot([0.265, 0.735], [0.53, 0.53], color=MUTED, lw=1.0)
    ax.annotate("", xy=(0.265, 0.49), xytext=(0.265, 0.53), arrowprops=arrow)
    ax.annotate("", xy=(0.735, 0.49), xytext=(0.735, 0.53), arrowprops=arrow)
    ax.plot([0.265, 0.265], [0.31, 0.35], color=MUTED, lw=1.0)
    ax.plot([0.735, 0.735], [0.31, 0.35], color=MUTED, lw=1.0)
    ax.plot([0.265, 0.735], [0.31, 0.31], color=MUTED, lw=1.0)
    ax.annotate("", xy=(0.50, 0.25), xytext=(0.50, 0.31), arrowprops=arrow)

    ax = fig.add_subplot(gs[0, 1])
    _panel(ax, "b")
    left = np.zeros(len(stages))
    for idx, (label, color) in enumerate(zip(collection_labels, collection_colors)):
        values = np.asarray([counts[stage][idx] for stage in stages])
        bars = ax.barh(stages, values, left=left, color=color, height=0.60, label=label)
        for y, value, start in zip(range(len(stages)), values, left):
            if value >= 28:
                ax.text(start + value / 2, y, str(int(value)), ha="center", va="center", color="white", fontsize=7.25)
            elif value > 0:
                ax.text(start + value + 7, y, str(int(value)), ha="left", va="center", color=INK, fontsize=7.25)
        left += values
    ax.invert_yaxis()
    ax.set_xlabel("Records")
    ax.set_xlim(0, 640)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, columnspacing=1.0, handlelength=1.4, borderaxespad=0)
    _clean(ax, "x")

    ax = fig.add_subplot(gs[0, 2])
    _panel(ax, "c")
    work_order = list(WORK_LABEL)
    gold_values = np.asarray([gold[w]["hidden_f1"] for w in work_order])
    weak_values = np.asarray([weak["models"]["sscl"]["work_metrics"][w]["hidden_f1"] for w in work_order])
    y = np.arange(len(work_order))
    for yi, start, end in zip(y, gold_values, weak_values):
        ax.annotate("", xy=(end, yi), xytext=(start, yi), arrowprops={"arrowstyle": "-|>", "color": GRID, "lw": 1.2, "mutation_scale": 8})
    ax.scatter(gold_values, y, s=32, facecolor="white", edgecolor=OCHRE, linewidth=1.3, label="Gold only", zorder=3)
    ax.scatter(weak_values, y, s=31, facecolor=TEAL, edgecolor=TEAL, label="Gold + weak", zorder=4)
    ax.set_yticks(y, [WORK_LABEL[w] for w in work_order])
    ax.invert_yaxis()
    ax.set_xlim(0.18, 0.62)
    ax.set_xlabel("Hidden-ingredient F1")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, columnspacing=0.9, handletextpad=0.45, borderaxespad=0)
    _clean(ax, "x")
    fig.subplots_adjust(left=0.035, right=0.99, top=0.82, bottom=0.15)

    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    with (SOURCE_DATA / "v3_fig1_data_scale.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["panel", "category", "series", "value"])
        for stage in stages:
            for label, value in zip(collection_labels, counts[stage]):
                writer.writerow(["b", stage, label, value])
        for work, a, b in zip(work_order, gold_values, weak_values):
            writer.writerow(["c", WORK_LABEL[work], "gold_only", f"{a:.12f}"])
            writer.writerow(["c", WORK_LABEL[work], "gold_plus_weak", f"{b:.12f}"])
    return _save(fig, "v3_fig1_data_scale")


def figure_2_corpus() -> list[Path]:
    reference = json.loads((RESEARCH_ROOT / "data/curated/formula_reference_v0.1.json").read_text(encoding="utf-8"))
    work_ids = list(reference["work_counts"])
    counts = [reference["work_counts"][w] for w in work_ids]
    sizes = [len(row["composition_aromatic_only"]) for row in reference["records"]]
    material_counts = Counter(m for row in reference["records"] for m in row["composition_aromatic_only"])

    fig, axes = plt.subplots(1, 3, figsize=(7.10, 2.65), gridspec_kw={"width_ratios": [1.42, 1.0, 1.02]})
    ax = axes[0]
    y = np.arange(len(work_ids))
    ax.barh(y, counts, color=TEAL, edgecolor=INK, linewidth=0.45)
    ax.set_yticks(y, [WORK_LONG[w] for w in work_ids])
    ax.invert_yaxis()
    ax.set_xlim(0, 42)
    ax.set_xlabel("Formulas")
    ax.set_title("Corpus provenance", loc="left", fontweight="bold")
    for yi, value in zip(y, counts):
        ax.text(value + 0.7, yi, str(value), va="center", fontsize=7.5)
    _panel(ax, "a")
    _clean(ax, "x")

    ax = axes[1]
    bins = np.arange(1.5, max(sizes) + 1.6, 1)
    ax.hist(sizes, bins=bins, color=SAGE, edgecolor="white", linewidth=0.5)
    median = float(np.median(sizes))
    ax.axvline(median, color=CINNABAR, lw=1.3, ls="--")
    ax.text(median + 0.35, 15.5, "median 6", color=CINNABAR, fontsize=7.5, va="top")
    ax.set_xlabel("Aromatic materials per formula")
    ax.set_ylabel("Formulas")
    ax.set_title("Formula size", loc="left", fontweight="bold")
    _panel(ax, "b")
    _clean(ax, "y")

    ax = axes[2]
    bins_freq = [1, 2, 3, 4, 5, 10, 20, 100]
    hist = np.histogram(list(material_counts.values()), bins=bins_freq)[0]
    labels = ["1", "2", "3", "4", "5-9", "10-19", ">=20"]
    x = np.arange(len(hist))
    ax.bar(x, hist, color=OCHRE, edgecolor=INK, linewidth=0.45)
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.set_xlabel("Formula frequency")
    ax.set_ylabel("Materials")
    ax.set_title("Material sparsity", loc="left", fontweight="bold")
    _panel(ax, "c")
    _clean(ax, "y")
    fig.subplots_adjust(left=0.13, right=0.99, top=0.84, bottom=0.24, wspace=0.38)
    return _save(fig, "v3_fig2_corpus")


def figure_3_design() -> list[Path]:
    fig = plt.figure(figsize=(7.10, 3.40))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.04, 1.24, 1.10], wspace=0.35)

    ax = fig.add_subplot(gs[0, 0])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    _panel(ax, "a")
    ax.set_title("Partial formula completion", loc="left", fontweight="bold", pad=8)
    chip_x = np.linspace(0.10, 0.90, 5)
    for i, x in enumerate(chip_x):
        observed = i < 3
        _box(ax, (x - 0.075, 0.76), (0.15, 0.10), face="#E7EFEC" if observed else "white", edge=TEAL if observed else MUTED, radius=0.008)
        ax.text(x, 0.81, ["A", "B", "C", "?", "?"][i], ha="center", va="center", fontweight="bold", color=TEAL if observed else MUTED)
    ax.text(0.30, 0.90, "observed", ha="center", color=TEAL, fontsize=7.5)
    ax.text(0.80, 0.90, "hidden", ha="center", color=MUTED, fontsize=7.5)
    ax.annotate("", xy=(0.50, 0.64), xytext=(0.50, 0.75), arrowprops={"arrowstyle": "-|>", "lw": 1.05, "color": INK, "mutation_scale": 10})
    _box(ax, (0.23, 0.48), (0.54, 0.14), face=PAPER, edge=INK)
    ax.text(0.50, 0.55, "rank hidden\nmaterials", ha="center", va="center", fontsize=7.6, linespacing=1.0)
    ax.annotate("", xy=(0.50, 0.37), xytext=(0.50, 0.47), arrowprops={"arrowstyle": "-|>", "lw": 1.05, "color": INK, "mutation_scale": 10})
    ax.add_patch(Rectangle((0.11, 0.23), 0.50, 0.10, facecolor=SAGE, edgecolor=INK, linewidth=0.7))
    ax.add_patch(Rectangle((0.61, 0.23), 0.28, 0.10, facecolor=CINNABAR, edgecolor=INK, linewidth=0.7))
    ax.text(0.36, 0.28, "observed\nmass", ha="center", va="center", fontsize=7.25, color="white", linespacing=0.9)
    ax.text(0.75, 0.28, "residual\nmass", ha="center", va="center", fontsize=7.25, color="white", linespacing=0.9)
    ax.text(0.50, 0.15, "output composition sums to one", ha="center", fontsize=7.4, color=MUTED)

    ax = fig.add_subplot(gs[0, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    _panel(ax, "b")
    ax.set_title("Nested cross-work evaluation", loc="left", fontweight="bold", pad=8)
    _box(ax, (0.05, 0.74), (0.34, 0.13), face="#F4EBDD", edge=OCHRE)
    _box(ax, (0.56, 0.74), (0.38, 0.13), face="#E7EFEC", edge=TEAL)
    ax.text(0.22, 0.805, "1 outer\ntest work", ha="center", va="center", fontsize=7.25, color=OCHRE, fontweight="bold", linespacing=0.95)
    ax.text(0.75, 0.805, "5 outer\ntrain works", ha="center", va="center", fontsize=7.25, color=TEAL, fontweight="bold", linespacing=0.95)
    _box(ax, (0.53, 0.51), (0.44, 0.15), face=PAPER, edge=INK)
    ax.text(0.75, 0.585, "inner validation\nselect settings", ha="center", va="center", fontsize=7.25, linespacing=1.05)
    _box(ax, (0.58, 0.30), (0.34, 0.12), face="#E7EFEC", edge=TEAL)
    ax.text(0.75, 0.36, "refit on 5 works", ha="center", va="center", fontsize=7.25)
    _box(ax, (0.25, 0.08), (0.50, 0.13), face=PAPER, edge=INK)
    ax.text(0.50, 0.145, "score held-out work", ha="center", va="center", fontsize=7.5, fontweight="bold")
    props = {"arrowstyle": "-|>", "lw": 1.05, "color": INK, "mutation_scale": 10}
    ax.annotate("", xy=(0.75, 0.67), xytext=(0.75, 0.74), arrowprops=props)
    ax.annotate("", xy=(0.75, 0.43), xytext=(0.75, 0.50), arrowprops=props)
    ax.annotate("", xy=(0.59, 0.22), xytext=(0.68, 0.30), arrowprops=props)
    ax.annotate("", xy=(0.39, 0.22), xytext=(0.22, 0.73), arrowprops={**props, "connectionstyle": "angle3,angleA=-90,angleB=180"})

    ax = fig.add_subplot(gs[0, 2])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    _panel(ax, "c")
    ax.set_title("Source-stable conditional lift", loc="left", fontweight="bold", pad=8)
    boxes = [
        (0.71, "work-specific conditional", PAPER, MUTED),
        (0.51, "marginal-adjusted lift", PAPER, MUTED),
        (0.31, "exposure-weighted pooling", "#E7EFEC", TEAL),
        (0.11, r"$s_{ab}=\mathrm{logit}(\pi_b)+\mu_{ab}-\gamma\sigma_{ab}$", "#F4EBDD", CINNABAR),
    ]
    for y, label, face, edge in boxes:
        _box(ax, (0.09, y), (0.82, 0.13), face=face, edge=edge)
        ax.text(0.50, y + 0.065, label, ha="center", va="center", fontsize=7.8)
    for y_top, y_bottom in zip([0.71, 0.51, 0.31], [0.64, 0.44, 0.24]):
        ax.annotate("", xy=(0.50, y_bottom), xytext=(0.50, y_top), arrowprops={"arrowstyle": "-|>", "lw": 1.05, "color": INK, "mutation_scale": 10, "shrinkA": 2, "shrinkB": 2})
    fig.subplots_adjust(left=0.035, right=0.99, top=0.86, bottom=0.08)
    return _save(fig, "v3_fig3_design")


def figure_4_performance() -> list[Path]:
    data = _load("v2_nested_cross_work.json")
    fig, axes = plt.subplots(1, 3, figsize=(7.10, 3.55), gridspec_kw={"width_ratios": [1.06, 1.52, 1.08]})
    for label, ax in zip("abc", axes):
        _panel(ax, label)
    ax = axes[0]
    y = np.arange(len(MODEL_ORDER))
    f1 = [data["models"][m]["source_macro_metrics"]["hidden_f1"] for m in MODEL_ORDER]
    wj = [data["models"][m]["source_macro_metrics"]["weighted_jaccard"] for m in MODEL_ORDER]
    ax.scatter(f1, y - 0.10, s=27, color=INK, marker="o", label="Hidden F1", zorder=3)
    ax.scatter(wj, y + 0.10, s=29, facecolor="white", edgecolor=INK, linewidth=1.0, marker="s", label="Weighted Jaccard", zorder=3)
    ax.set_yticks(y, [MODEL_LABEL[m] for m in MODEL_ORDER])
    ax.invert_yaxis()
    ax.set_xlim(0.35, 0.49)
    ax.set_xlabel("Source-macro score")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=1, borderaxespad=0, handletextpad=0.45)
    _clean(ax, "y")

    ax = axes[1]
    works = list(data["models"]["frequency"]["work_metrics"])
    x = np.arange(len(works)); width = 0.23
    for offset, model in zip([-width, 0, width], ["frequency", "directed_graph", "sscl"]):
        values = [data["models"][model]["work_metrics"][w]["hidden_f1"] for w in works]
        ax.bar(x + offset, values, width=width, color=MODEL_COLOR[model], label=MODEL_LABEL[model], alpha=0.96)
    ax.set_xticks(x, [WORK_LABEL[w] for w in works], rotation=28, ha="right")
    ax.set_ylim(0.15, 0.62)
    ax.set_ylabel("Hidden F1")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, columnspacing=0.8, handlelength=1.4, borderaxespad=0)
    _clean(ax, "y")

    ax = axes[2]
    comparison_models = ["directed_graph", "sscl", "ease", "slim", "ppr"]
    for idx, model in enumerate(comparison_models):
        diffs = data["comparisons_vs_frequency"][model]["per_work_difference"]
        values = np.asarray([diffs[w] for w in works])
        jitter = np.linspace(-0.07, 0.07, len(values))
        ax.scatter(np.full(len(values), idx) + jitter, values, s=22, marker=MODEL_MARKER[model], color=MODEL_COLOR[model], zorder=3)
        ax.plot([idx - 0.22, idx + 0.22], [values.mean(), values.mean()], color=INK, lw=1.25)
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_xticks(range(5), ["Directed\ngraph", "SSCL", "EASE", "SLIM", "PPR"])
    ax.set_ylabel(r"Paired $\Delta$F1 vs frequency")
    ax.set_ylim(-0.065, 0.135)
    _clean(ax, "y")
    fig.subplots_adjust(left=0.09, right=0.99, top=0.77, bottom=0.20, wspace=0.40)
    return _save(fig, "v3_fig4_performance")


def figure_5_missingness() -> list[Path]:
    data = _load("v2_missingness_stress.json")
    mechanisms = ["uniform", "abundance", "prefix", "unknown"]
    titles = ["Uniform retention", "Abundance-biased retention", "Source-list prefix", "Unknown fraction"]
    fractions = [0.25, 0.50, 0.75]
    models = ["frequency", "directed_graph", "sscl", "ease"]
    fig, axes = plt.subplots(2, 2, figsize=(7.10, 4.65), sharex=True, sharey=True)
    for panel_idx, (ax, mechanism, title) in enumerate(zip(axes.flat, mechanisms, titles)):
        ax.text(-0.12, 1.12, "abcd"[panel_idx], transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")
        ax.set_title(title, loc="left", fontweight="bold")
        for model in models:
            values = []
            for fraction in fractions:
                prefix = "uniform_unknown_fraction" if mechanism == "unknown" else mechanism
                key = f"{prefix}_{fraction:.2f}"
                values.append(data["conditions"][key]["models"][model]["source_macro_metrics"]["hidden_f1"])
            ax.plot(fractions, values, color=MODEL_COLOR[model], marker=MODEL_MARKER[model], markersize=4.3, linewidth=1.35, label=MODEL_LABEL[model])
        ax.set_xlim(0.20, 0.80); ax.set_ylim(0.23, 0.50); ax.set_xticks(fractions)
        _clean(ax, "y")
    for ax in axes[:, 0]:
        ax.set_ylabel("Source-macro hidden F1")
    for ax in axes[1, :]:
        ax.set_xlabel("Observed fraction")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.52, 0.99), ncol=4, columnspacing=1.3, handlelength=2.0)
    fig.subplots_adjust(left=0.09, right=0.99, top=0.86, bottom=0.12, hspace=0.42, wspace=0.18)
    return _save(fig, "v3_fig5_missingness")


def figure_6_calibration() -> list[Path]:
    data = _load("v2_calibration.json")
    conditions = ["uncalibrated", "temperature_scaled", "logit_calibrated"]
    labels = ["Uncalibrated", "Temperature", "Logit"]
    colors = [CHARCOAL, TEAL, CINNABAR]
    fig, axes = plt.subplots(1, 3, figsize=(7.10, 3.55), gridspec_kw={"width_ratios": [1.32, 1.10, 0.92]})
    for label, ax in zip("abc", axes):
        _panel(ax, label)

    ax = axes[0]
    ax.plot([0, 1], [0, 1], color=MUTED, ls="--", lw=0.9, label="Ideal")
    for condition, label, color, marker in zip(["uncalibrated", "logit_calibrated"], ["Uncalibrated", "Logit calibrated"], [CHARCOAL, CINNABAR], ["o", "D"]):
        bins = data[condition]["pooled_reliability_bins"]
        ax.plot([b["mean_probability"] for b in bins], [b["empirical_frequency"] for b in bins], color=color, marker=marker, markersize=3.8, linewidth=1.2, label=label)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Empirical inclusion frequency")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, columnspacing=0.9, handlelength=1.8, borderaxespad=0)
    _clean(ax)

    ax = axes[1]
    metrics = ["brier", "nll", "adaptive_calibration_error"]
    metric_labels = ["Brier", "NLL", "ACE"]
    x = np.arange(3); width = 0.23
    for idx, (condition, label, color) in enumerate(zip(conditions, labels, colors)):
        values = [data[condition]["source_macro_metrics"][metric] for metric in metrics]
        ax.bar(x + (idx - 1) * width, values, width=width, color=color, label=label)
    ax.set_xticks(x, metric_labels); ax.set_ylabel("Error (lower is better)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, columnspacing=0.7, handlelength=1.2, borderaxespad=0)
    _clean(ax, "y")

    ax = axes[2]
    counts = [data[c]["total_high_probability_count"] for c in conditions]
    means, empirical = [], []
    for condition in conditions:
        valid = [v for v in data[condition]["work_metrics"].values() if v["high_probability_count"]]
        total = sum(v["high_probability_count"] for v in valid)
        means.append(sum(v["high_probability_mean"] * v["high_probability_count"] for v in valid) / total)
        empirical.append(sum(v["high_probability_empirical_frequency"] * v["high_probability_count"] for v in valid) / total)
    bars = ax.bar(np.arange(3), counts, color=colors)
    ax.set_xticks(np.arange(3), ["Uncalibrated", "Temperature", "Logit"], rotation=25, ha="right")
    ax.set_ylabel(r"Predictions with $p>0.8$")
    for bar, n, mean, observed in zip(bars, counts, means, empirical):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.025, f"n={n}\n{mean:.2f}/{observed:.2f}", ha="center", va="bottom", fontsize=7.25)
    ax.set_ylim(0, max(counts) * 1.28)
    _clean(ax, "y")
    fig.subplots_adjust(left=0.08, right=0.99, top=0.76, bottom=0.21, wspace=0.43)
    return _save(fig, "v3_fig6_calibration")


def figure_7_stress() -> list[Path]:
    stress = _load("cycle6_stress_tests.json")
    primary = _load("cycle4_primary_evaluation.json")
    model_labels = {
        "frequency": "Frequency", "formula_knn": "Formula kNN", "pure_svd": "PureSVD",
        "graph_only": "Directed graph", "full_no_chemistry": "Full decoder",
    }
    metrics = {}
    for model in ("frequency", "graph_only", "full_no_chemistry"):
        rows = primary["source_level_metrics"][model].values()
        metrics[model] = {
            "hidden_f1": float(np.mean([row["hidden_f1"] for row in rows])),
            "weighted_jaccard": float(np.mean([row["weighted_jaccard"] for row in rows])),
        }
    for model, row in stress["competitive_baselines"]["primary_results"].items():
        metrics[model] = row["source_macro_metrics"]
    order = ["frequency", "formula_knn", "pure_svd", "graph_only", "full_no_chemistry"]
    colors = [CHARCOAL, PLUM, SAGE, TEAL, CINNABAR]
    sensitivity = stress["near_duplicate_sensitivity"]
    calibration = stress["count_interval_recalibration"]

    fig, axes = plt.subplots(1, 3, figsize=(7.10, 3.05), gridspec_kw={"width_ratios": [1.35, 1.05, 0.85]})
    ax = axes[0]
    x = np.arange(len(order)); width = 0.36
    ax.bar(x - width / 2, [metrics[m]["hidden_f1"] for m in order], width, color=colors, edgecolor=INK, linewidth=0.35, label="Hidden F1")
    ax.bar(x + width / 2, [metrics[m]["weighted_jaccard"] for m in order], width, color="white", edgecolor=colors, linewidth=1.0, label="Weighted Jaccard")
    ax.set_xticks(x, ["Frequency", "Formula kNN", "PureSVD", "Directed graph", "Full decoder"], rotation=30, ha="right")
    ax.set_ylim(0.25, 0.48); ax.set_ylabel("Score")
    ax.text(0.0, 1.24, "Competitive benchmarks", transform=ax.transAxes, ha="left", va="bottom", fontsize=9.25, fontweight="bold")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, columnspacing=1.0, borderaxespad=0)
    _clean(ax, "y")

    ax = axes[1]
    subset = ["frequency", "graph_only", "full_no_chemistry"]
    x2 = np.arange(len(subset))
    ax.plot(x2, [metrics[m]["hidden_f1"] for m in subset], color=CHARCOAL, marker="o", linewidth=1.35, label="All formulas")
    ax.plot(x2, [sensitivity["source_macro_metrics"][m]["hidden_f1"] for m in subset], color=TEAL, marker="s", ls="--", linewidth=1.35, label="High-similarity removed")
    ax.set_xticks(x2, ["Frequency", "Directed\ngraph", "Full\ndecoder"])
    ax.set_ylim(0.29, 0.40); ax.set_ylabel("Hidden-component F1")
    ax.text(0.0, 1.24, "Near-duplicate sensitivity", transform=ax.transAxes, ha="left", va="bottom", fontsize=9.25, fontweight="bold")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=1, borderaxespad=0, handlelength=1.8)
    _clean(ax, "y")

    ax = axes[2]
    coverage = [calibration["base_coverage"], calibration["expanded_coverage"]]
    spans = [calibration["base_mean_width"], calibration["expanded_mean_width"]]
    bars = ax.bar([0, 1], coverage, color=[CHARCOAL, TEAL], edgecolor=INK, linewidth=0.4)
    ax.axhline(0.8, color=INK, ls="--", lw=0.9)
    ax.set_xticks([0, 1], ["Base", "Calibrated"])
    ax.set_ylim(0.5, 0.9); ax.set_ylabel("Count interval coverage")
    ax.text(0.0, 1.24, "Interval calibration", transform=ax.transAxes, ha="left", va="bottom", fontsize=9.25, fontweight="bold")
    for bar, value, span in zip(bars, coverage, spans):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.012, f"{value:.3f}\nwidth {span:.2f}", ha="center", fontsize=7.25)
    _clean(ax, "y")
    for label, ax in zip("abc", axes):
        ax.text(-0.12, 1.24, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    fig.subplots_adjust(left=0.08, right=0.99, top=0.68, bottom=0.24, wspace=0.45)
    return _save(fig, "v3_fig7_stress_tests")


def write_manifest(outputs: list[Path]) -> Path:
    inputs = [
        RESEARCH_ROOT / "data/interim/structured_formula_candidates_v0.1.json",
        RESEARCH_ROOT / "data/curated/formula_reference_v0.1.json",
        *[EXPERIMENTS / name for name in [
            "v2_5_weak_supervision.json", "v2_nested_cross_work.json", "v2_missingness_stress.json",
            "v2_calibration.json", "cycle6_stress_tests.json", "cycle4_primary_evaluation.json",
        ]],
    ]
    manifest = {
        "schema_version": "3.0",
        "backend": "python-matplotlib",
        "palette": "xiangji-earth-v3",
        "inputs": {str(path.relative_to(RESEARCH_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
        "outputs": {str(path.relative_to(RESEARCH_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs},
    }
    path = OUT / "v3_figure_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> None:
    _style()
    outputs: list[Path] = []
    outputs += figure_1_data_scale()
    outputs += figure_2_corpus()
    outputs += figure_3_design()
    outputs += figure_4_performance()
    outputs += figure_5_missingness()
    outputs += figure_6_calibration()
    outputs += figure_7_stress()
    manifest = write_manifest(outputs)
    print(json.dumps({"figures": 7, "outputs": len(outputs), "manifest": str(manifest)}, indent=2))


if __name__ == "__main__":
    main()
