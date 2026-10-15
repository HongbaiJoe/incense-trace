"""Generate Cycle 6 stress-test tables and the sixth manuscript figure."""

from __future__ import annotations

import csv
import hashlib
import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from xiangji.data import RESEARCH_ROOT


TABLE_DIR = RESEARCH_ROOT / "manuscript" / "tables"
FIGURE_DIR = RESEARCH_ROOT / "figures"
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
PURPLE = "#CC79A7"
GREY = "#777777"
BLACK = "#111111"


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _normalize_svg(path) -> None:
    """Keep Matplotlib SVG output deterministic and free of trailing spaces."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def build() -> list:
    stress = json.loads((RESEARCH_ROOT / "experiments/cycle6_stress_tests.json").read_text())
    primary = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    model_labels = {
        "frequency": "Frequency",
        "formula_knn": "Formula kNN",
        "pure_svd": "PureSVD",
        "graph_only": "Directed graph",
        "full_no_chemistry": "Full decoder",
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
    order = ("frequency", "formula_knn", "pure_svd", "graph_only", "full_no_chemistry")
    competitive_rows = [
        {"model": model_labels[model], "hidden_f1": metrics[model]["hidden_f1"], "weighted_jaccard": metrics[model]["weighted_jaccard"]}
        for model in order
    ]
    competitive_path = TABLE_DIR / "table10_competitive_baselines.csv"
    _write(competitive_path, competitive_rows)

    sensitivity = stress["near_duplicate_sensitivity"]
    duplicate_rows = []
    for model in ("frequency", "graph_only", "full_no_chemistry"):
        duplicate_rows.append({
            "model": model_labels[model],
            "all_formulas_hidden_f1": metrics[model]["hidden_f1"],
            "after_excluding_high_similarity_hidden_f1": sensitivity["source_macro_metrics"][model]["hidden_f1"],
            "excluded_formula_count": sensitivity["excluded_formula_count"],
            "jaccard_threshold": sensitivity["threshold"],
        })
    duplicate_path = TABLE_DIR / "table11_near_duplicate_sensitivity.csv"
    _write(duplicate_path, duplicate_rows)

    calibration = stress["count_interval_recalibration"]
    calibration_rows = [
        {"interval": "Base posterior", "coverage": calibration["base_coverage"], "mean_width": calibration["base_mean_width"]},
        {"interval": "Development-calibrated", "coverage": calibration["expanded_coverage"], "mean_width": calibration["expanded_mean_width"]},
    ]
    calibration_path = TABLE_DIR / "table12_count_recalibration.csv"
    _write(calibration_path, calibration_rows)

    mpl.rcParams.update({
        "font.family": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 7, "axes.titlesize": 7,
        "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "svg.hashsalt": "xiangji-cgir",
        "savefig.bbox": "tight", "savefig.facecolor": "white",
    })
    fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.35), gridspec_kw={"width_ratios": [1.35, 1.05, 0.85]})
    colors = [GREY, PURPLE, GREEN, BLUE, VERMILLION]
    x = np.arange(len(order))

    ax = axes[0]
    width = 0.36
    ax.bar(x - width / 2, [metrics[m]["hidden_f1"] for m in order], width, color=colors, edgecolor=BLACK, linewidth=0.35, label="Hidden F1")
    ax.bar(x + width / 2, [metrics[m]["weighted_jaccard"] for m in order], width, color="white", edgecolor=colors, linewidth=0.9, label="Weighted Jaccard")
    ax.set_xticks(x, [model_labels[m] for m in order], rotation=38, ha="right")
    ax.set_ylim(0.25, 0.48)
    ax.set_ylabel("Score")
    ax.set_title("Competitive primary benchmarks")
    ax.legend(frameon=False, fontsize=6, loc="upper left")
    ax.text(-0.15, 1.05, "a", transform=ax.transAxes, fontweight="bold", fontsize=7)

    ax = axes[1]
    subset = ("frequency", "graph_only", "full_no_chemistry")
    x2 = np.arange(len(subset))
    ax.plot(x2, [metrics[m]["hidden_f1"] for m in subset], color=GREY, marker="o", label="All formulas")
    ax.plot(x2, [sensitivity["source_macro_metrics"][m]["hidden_f1"] for m in subset], color=BLUE, marker="s", ls="--", label="High-similarity removed")
    ax.set_xticks(x2, [model_labels[m] for m in subset], rotation=32, ha="right")
    ax.set_ylim(0.29, 0.40)
    ax.set_ylabel("Hidden-component F1")
    ax.set_title("Near-duplicate sensitivity")
    ax.legend(frameon=False, fontsize=6)
    ax.text(-0.15, 1.05, "b", transform=ax.transAxes, fontweight="bold", fontsize=7)

    ax = axes[2]
    bars = ax.bar([0, 1], [calibration["base_coverage"], calibration["expanded_coverage"]], color=[GREY, BLUE], edgecolor=BLACK, linewidth=0.4)
    ax.axhline(0.8, color=BLACK, ls="--", lw=0.8)
    ax.set_xticks([0, 1], ["Base", "Calibrated"])
    ax.set_ylim(0.5, 0.9)
    ax.set_ylabel("Count interval coverage")
    ax.set_title("Development calibration")
    for bar, coverage, span in zip(bars, [calibration["base_coverage"], calibration["expanded_coverage"]], [calibration["base_mean_width"], calibration["expanded_mean_width"]]):
        ax.text(bar.get_x() + bar.get_width() / 2, coverage + 0.012, f"{coverage:.3f}\nwidth {span:.2f}", ha="center", fontsize=6)
    ax.text(-0.18, 1.05, "c", transform=ax.transAxes, fontweight="bold", fontsize=7)
    fig.tight_layout(w_pad=1.2)
    pdf = FIGURE_DIR / "fig6_stress_tests.pdf"
    png = FIGURE_DIR / "fig6_stress_tests.png"
    svg = FIGURE_DIR / "fig6_stress_tests.svg"
    fig.savefig(pdf, metadata={"Creator": "Xiangji-CGIR", "CreationDate": None, "ModDate": None})
    fig.savefig(png, dpi=450, metadata={"Software": "Xiangji-CGIR"})
    fig.savefig(svg, metadata={"Creator": "Xiangji-CGIR", "Date": None})
    _normalize_svg(svg)
    plt.close(fig)

    outputs = [competitive_path, duplicate_path, calibration_path, pdf, png, svg]
    manifest = {
        "schema_version": "0.1",
        "generator": "xiangji.cycle6_assets",
        "input": "experiments/cycle6_stress_tests.json",
        "outputs": [
            {"path": str(path.relative_to(RESEARCH_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in outputs
        ],
    }
    manifest_path = FIGURE_DIR / "cycle6_figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return outputs + [manifest_path]


def main() -> None:
    outputs = build()
    print(json.dumps({"outputs": [str(path) for path in outputs]}, indent=2))


if __name__ == "__main__":
    main()
