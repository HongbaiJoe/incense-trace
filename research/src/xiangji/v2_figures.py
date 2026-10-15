"""Build the V2 manuscript figures from recorded experiment outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"
FIGURES = ROOT / "figures"
SOURCE_DATA = FIGURES / "source_data"

MODEL_ORDER = ["frequency", "directed_graph", "sscl", "ease", "slim", "ppr"]
MODEL_LABEL = {
    "frequency": "Frequency",
    "directed_graph": "Directed graph",
    "sscl": "SSCL",
    "ease": "EASE",
    "slim": "SLIM",
    "ppr": "PPR",
}
COLORS = {
    "frequency": "#666666",
    "directed_graph": "#0072B2",
    "sscl": "#D55E00",
    "ease": "#009E73",
    "slim": "#CC79A7",
    "ppr": "#E69F00",
}
MARKERS = {
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


def _load(name: str) -> dict:
    return json.loads((EXPERIMENTS / name).read_text(encoding="utf-8"))


def _write_csv(name: str, rows: list[dict]) -> None:
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (SOURCE_DATA / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7,
            "axes.labelsize": 7,
            "axes.titlesize": 8,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def _panel_label(ax: mpl.axes.Axes, label: str) -> None:
    ax.text(-0.11, 1.06, label, transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")


def _clean(ax: mpl.axes.Axes, grid: bool = False) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    if grid:
        ax.grid(axis="y", color="#D7D7D7", linewidth=0.5, alpha=0.8)
        ax.set_axisbelow(True)


def _save(fig: mpl.figure.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure_1() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.02), gridspec_kw={"width_ratios": [1.0, 1.35, 1.15]})
    for ax in axes:
        ax.set_axis_off()
    _panel_label(axes[0], "a")
    _panel_label(axes[1], "b")
    _panel_label(axes[2], "c")

    ax = axes[0]
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.02, 0.93, "Partial formula completion", fontweight="bold")
    ingredients = [(0.18, 0.67, "A", True), (0.50, 0.67, "B", True), (0.82, 0.67, "?", False),
                   (0.18, 0.34, "C", True), (0.50, 0.34, "?", False), (0.82, 0.34, "?", False)]
    for x, y, label, observed in ingredients:
        face = "#E6F2F8" if observed else "white"
        edge = COLORS["directed_graph"] if observed else "#9A9A9A"
        patch = FancyBboxPatch((x - 0.105, y - 0.075), 0.21, 0.15,
                               boxstyle="round,pad=0.015,rounding_size=0.025",
                               facecolor=face, edgecolor=edge, linewidth=1.0,
                               linestyle="-" if observed else "--")
        ax.add_patch(patch); ax.text(x, y, label, ha="center", va="center", fontweight="bold")
    ax.annotate("rank hidden ingredients\nand recover residual mass", xy=(0.82, 0.42), xytext=(0.50, 0.12),
                arrowprops={"arrowstyle": "->", "color": "#444444", "lw": 0.8}, ha="center")

    ax = axes[1]
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.02, 0.93, "Nested cross-work evaluation", fontweight="bold")
    labels = ["Chen", "Xiangcheng", "Huizhai", "Hong", "Liexiang", "Xiaolu"]
    ys = np.linspace(0.77, 0.22, 6)
    for idx, (name, y) in enumerate(zip(labels, ys)):
        x0 = 0.08
        ax.add_patch(FancyBboxPatch((x0, y - 0.03), 0.22, 0.06, boxstyle="round,pad=0.01",
                                    facecolor="#F2F2F2", edgecolor="#B6B6B6", linewidth=0.6))
        ax.text(x0 + 0.11, y, name, ha="center", va="center", fontsize=6.2)
        ax.text(0.39, y, "test" if idx == 0 else "train", color=COLORS["sscl"] if idx == 0 else "#555555",
                va="center", fontweight="bold" if idx == 0 else "normal")
    ax.annotate("inner leave-one-work-out\nmodel selection", xy=(0.72, 0.48), xytext=(0.72, 0.72),
                arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#444444"}, ha="center")
    ax.text(0.72, 0.40, "repeat for all six\nouter test works", ha="center", va="center")
    ax.text(0.50, 0.08, "independent unit: historical work", ha="center", color="#444444")

    ax = axes[2]
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.02, 0.93, "Source-stable conditional lift", fontweight="bold")
    steps = [(0.18, 0.73, "work-specific\nconditional"), (0.50, 0.52, "marginal-adjusted\nlog-odds lift"),
             (0.82, 0.31, "evidence pooling\nand heterogeneity penalty")]
    for x, y, text in steps:
        ax.add_patch(FancyBboxPatch((x - 0.15, y - 0.07), 0.30, 0.14, boxstyle="round,pad=0.014",
                                    facecolor="#FFF3EA" if x > 0.6 else "#F5F5F5", edgecolor="#9A9A9A", linewidth=0.7))
        ax.text(x, y, text, ha="center", va="center")
    ax.annotate("", xy=(0.39, 0.58), xytext=(0.29, 0.67), arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax.annotate("", xy=(0.70, 0.37), xytext=(0.61, 0.46), arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax.text(0.5, 0.10, r"$s_{ab}=\mathrm{logit}(\pi_b)+\mu_{ab}-\gamma\sigma_{ab}$", ha="center", fontsize=8)
    fig.subplots_adjust(left=0.035, right=0.99, top=0.94, bottom=0.06, wspace=0.18)
    _save(fig, "v2_fig1_design")


def figure_2() -> None:
    data = _load("v2_nested_cross_work.json")
    rows = []
    for model in MODEL_ORDER:
        macro = data["models"][model]["source_macro_metrics"]
        rows.append({"model": model, "work": "source_macro", "hidden_f1": macro["hidden_f1"],
                     "weighted_jaccard": macro["weighted_jaccard"]})
        for work, metrics in data["models"][model]["work_metrics"].items():
            rows.append({"model": model, "work": work, "hidden_f1": metrics["hidden_f1"],
                         "weighted_jaccard": metrics["weighted_jaccard"]})
    _write_csv("v2_fig2_performance.csv", rows)

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.65), gridspec_kw={"width_ratios": [1.08, 1.55, 1.0]})
    for label, ax in zip("abc", axes): _panel_label(ax, label)

    ax = axes[0]
    y = np.arange(len(MODEL_ORDER))
    f1 = [data["models"][m]["source_macro_metrics"]["hidden_f1"] for m in MODEL_ORDER]
    wj = [data["models"][m]["source_macro_metrics"]["weighted_jaccard"] for m in MODEL_ORDER]
    ax.scatter(f1, y - 0.10, s=26, marker="o", facecolor="#111111", edgecolor="none", label="Hidden F1")
    ax.scatter(wj, y + 0.10, s=28, marker="s", facecolor="white", edgecolor="#111111", linewidth=0.8, label="Weighted Jaccard")
    ax.set_yticks(y, [MODEL_LABEL[m] for m in MODEL_ORDER]); ax.invert_yaxis(); ax.set_xlim(0.35, 0.49)
    ax.set_xlabel("Source-macro score"); ax.legend(frameon=False, loc="lower right")
    _clean(ax, grid=True)

    ax = axes[1]
    works = list(data["models"]["frequency"]["work_metrics"])
    x = np.arange(len(works)); width = 0.23
    for offset, model in zip([-width, 0, width], ["frequency", "directed_graph", "sscl"]):
        vals = [data["models"][model]["work_metrics"][w]["hidden_f1"] for w in works]
        ax.bar(x + offset, vals, width=width, color=COLORS[model], label=MODEL_LABEL[model], alpha=0.9)
    ax.set_xticks(x, [WORK_LABEL[w] for w in works], rotation=34, ha="right")
    ax.set_ylim(0.15, 0.62); ax.set_ylabel("Hidden F1"); ax.legend(frameon=False, ncol=1, loc="lower right")
    _clean(ax, grid=True)

    ax = axes[2]
    for idx, model in enumerate(["directed_graph", "sscl", "ease", "slim", "ppr"]):
        diffs = data["comparisons_vs_frequency"][model]["per_work_difference"]
        vals = np.array([diffs[w] for w in works])
        jitter = np.linspace(-0.065, 0.065, len(vals))
        ax.scatter(np.full(len(vals), idx) + jitter, vals, s=20, marker=MARKERS[model], color=COLORS[model], zorder=3)
        ax.plot([idx - 0.22, idx + 0.22], [vals.mean(), vals.mean()], color="#111111", lw=1.2)
    ax.axhline(0, color="#777777", lw=0.7, ls="--")
    ax.set_xticks(range(5), [MODEL_LABEL[m] for m in ["directed_graph", "sscl", "ease", "slim", "ppr"]], rotation=38, ha="right")
    ax.set_ylabel(r"Paired $\Delta$F1 vs frequency"); ax.set_ylim(-0.065, 0.135)
    _clean(ax, grid=True)
    fig.subplots_adjust(left=0.09, right=0.99, top=0.93, bottom=0.25, wspace=0.38)
    _save(fig, "v2_fig2_performance")


def figure_3() -> None:
    data = _load("v2_missingness_stress.json")
    mechanisms = ["uniform", "abundance", "prefix", "unknown"]
    titles = ["Uniform retention", "Abundance-biased retention", "Source-list prefix", "Unknown fraction"]
    fractions = [0.25, 0.50, 0.75]
    models = ["frequency", "directed_graph", "sscl", "ease"]
    rows = []
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.55), sharex=True, sharey=True)
    for panel, (ax, mechanism, title) in enumerate(zip(axes.flat, mechanisms, titles)):
        _panel_label(ax, "abcd"[panel]); ax.set_title(title, loc="left", fontweight="bold")
        for model in models:
            vals = []
            for fraction in fractions:
                key_prefix = "uniform_unknown_fraction" if mechanism == "unknown" else mechanism
                key = f"{key_prefix}_{fraction:.2f}"
                score = data["conditions"][key]["models"][model]["source_macro_metrics"]["hidden_f1"]
                vals.append(score)
                rows.append({"mechanism": mechanism, "observed_fraction": fraction, "model": model, "hidden_f1": score})
            ax.plot(fractions, vals, color=COLORS[model], marker=MARKERS[model], markersize=4,
                    linewidth=1.2, label=MODEL_LABEL[model])
        ax.set_xlim(0.20, 0.80); ax.set_ylim(0.23, 0.50); ax.set_xticks(fractions)
        _clean(ax, grid=True)
    for ax in axes[:, 0]: ax.set_ylabel("Source-macro hidden F1")
    for ax in axes[1, :]: ax.set_xlabel("Observed fraction")
    axes[0, 0].legend(frameon=False, ncol=2, loc="lower left")
    _write_csv("v2_fig3_missingness.csv", rows)
    fig.subplots_adjust(left=0.09, right=0.99, top=0.94, bottom=0.12, hspace=0.38, wspace=0.18)
    _save(fig, "v2_fig3_missingness")


def figure_4() -> None:
    data = _load("v2_calibration.json")
    conditions = ["uncalibrated", "temperature_scaled", "logit_calibrated"]
    labels = ["Uncalibrated", "Temperature", "Logit"]
    colors = ["#666666", "#0072B2", "#D55E00"]
    rows = []
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.45), gridspec_kw={"width_ratios": [1.35, 1.05, 0.95]})
    for label, ax in zip("abc", axes): _panel_label(ax, label)

    ax = axes[0]
    ax.plot([0, 1], [0, 1], color="#999999", ls="--", lw=0.8, label="Ideal")
    for condition, label, color, marker in zip(["uncalibrated", "logit_calibrated"], ["Uncalibrated", "Logit calibrated"], [colors[0], colors[2]], ["o", "D"]):
        bins = data[condition]["pooled_reliability_bins"]
        xs = [b["mean_probability"] for b in bins]
        ys = [b["empirical_frequency"] for b in bins]
        ax.plot(xs, ys, color=color, marker=marker, markersize=3.5, linewidth=1.1, label=label)
        for b in bins:
            rows.append({"condition": condition, "bin_lower": b["lower"], "bin_upper": b["upper"],
                         "count": b["count"], "mean_probability": b["mean_probability"],
                         "empirical_frequency": b["empirical_frequency"]})
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Empirical inclusion frequency")
    ax.legend(frameon=False, loc="upper left"); _clean(ax)

    ax = axes[1]
    metrics = ["brier", "nll", "adaptive_calibration_error"]
    metric_labels = ["Brier", "NLL", "ACE"]
    x = np.arange(3); width = 0.23
    for idx, (condition, label, color) in enumerate(zip(conditions, labels, colors)):
        vals = [data[condition]["source_macro_metrics"][m] for m in metrics]
        ax.bar(x + (idx - 1) * width, vals, width=width, color=color, label=label)
    ax.set_xticks(x, metric_labels); ax.set_ylabel("Error (lower is better)")
    ax.legend(frameon=False, fontsize=6, loc="upper right"); _clean(ax, grid=True)

    ax = axes[2]
    counts = [data[c]["total_high_probability_count"] for c in conditions]
    means = []
    empirical = []
    for c in conditions:
        valid = [v for v in data[c]["work_metrics"].values() if v["high_probability_count"]]
        total = sum(v["high_probability_count"] for v in valid)
        means.append(sum(v["high_probability_mean"] * v["high_probability_count"] for v in valid) / total)
        empirical.append(sum(v["high_probability_empirical_frequency"] * v["high_probability_count"] for v in valid) / total)
    bars = ax.bar(np.arange(3), counts, color=colors)
    ax.set_xticks(np.arange(3), labels, rotation=30, ha="right"); ax.set_ylabel("Predictions with $p>0.8$")
    for bar, n, mean, obs in zip(bars, counts, means, empirical):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.025,
                f"n={n}\n{mean:.2f}/{obs:.2f}", ha="center", va="bottom", fontsize=6)
    ax.set_ylim(0, max(counts) * 1.28); _clean(ax, grid=True)
    _write_csv("v2_fig4_calibration.csv", rows)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.92, bottom=0.22, wspace=0.42)
    _save(fig, "v2_fig4_calibration")


def write_manifest() -> None:
    inputs = {}
    for name in ["v2_nested_cross_work.json", "v2_missingness_stress.json", "v2_calibration.json"]:
        raw = (EXPERIMENTS / name).read_bytes()
        inputs[name] = hashlib.sha256(raw).hexdigest()
    outputs = {}
    for path in sorted(FIGURES.glob("v2_fig*.*")):
        outputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "2.0",
        "backend": "python-matplotlib",
        "input_sha256": inputs,
        "output_sha256": outputs,
        "source_data_directory": str(SOURCE_DATA.relative_to(ROOT)),
    }
    (FIGURES / "v2_figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    _style()
    figure_1(); figure_2(); figure_3(); figure_4(); write_manifest()


if __name__ == "__main__":
    main()
