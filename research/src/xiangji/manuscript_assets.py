"""Build manuscript tables and publication figures from frozen artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from xiangji.data import RESEARCH_ROOT


FIGURE_DIR = RESEARCH_ROOT / "figures"
TABLE_DIR = RESEARCH_ROOT / "manuscript" / "tables"

BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
PURPLE = "#CC79A7"
BLACK = "#111111"
GREY = "#777777"
LIGHT_GREY = "#E6E3DE"

WORK_LABELS = {
    "chen_xiangpu_compilation": "Chen Xiangpu",
    "huizhai_xiangpu": "Huizhai Xiangpu",
    "liexiang_xinpu": "Liexiang Xinpu",
    "moe_xiaolu_xiangpu": "Xiaolu Xiangpu",
    "xiangcheng_compilation_unresolved_source": "Xiangcheng compilation",
    "hong_xiangpu_attributed": "Hong Xiangpu",
}
MODEL_LABELS = {
    "frequency": "Frequency",
    "graph_only": "Directed graph",
    "full_no_chemistry": "Full decoder",
}
MODEL_STYLES = {
    "frequency": (GREY, "o", ":"),
    "graph_only": (BLUE, "s", "--"),
    "full_no_chemistry": (VERMILLION, "^", "-"),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _style() -> None:
    mpl.rcParams.update({
        "font.family": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "xiangji-cgir",
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    })


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.14, 1.06, label, transform=ax.transAxes, fontweight="bold", fontsize=7)


def _normalize_svg(path: Path) -> None:
    """Keep Matplotlib SVG output deterministic and free of trailing spaces."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def _save(fig: plt.Figure, stem: str) -> list[Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    pdf = FIGURE_DIR / f"{stem}.pdf"
    png = FIGURE_DIR / f"{stem}.png"
    svg = FIGURE_DIR / f"{stem}.svg"
    fig.savefig(pdf, metadata={"Creator": "Xiangji-CGIR", "CreationDate": None, "ModDate": None})
    fig.savefig(png, dpi=450, metadata={"Software": "Xiangji-CGIR"})
    fig.savefig(svg, metadata={"Creator": "Xiangji-CGIR", "Date": None})
    _normalize_svg(svg)
    plt.close(fig)
    return [pdf, png, svg]


def build_tables(reference: dict, primary: dict, robustness: dict, hong: dict) -> list[Path]:
    sealed_ids = set(
        _load(RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json")
        ["sealed_evaluation"]["reference_ids"]
    )
    development = [row for row in reference["records"] if row["reference_id"] not in sealed_ids]
    source_rows = []
    for work_id, count in reference["work_counts"].items():
        rows = [row for row in reference["records"] if row["work_id"] == work_id]
        materials = {m for row in rows for m in row["composition_aromatic_only"]}
        sizes = [len(row["composition_aromatic_only"]) for row in rows]
        source_rows.append({
            "work_id": work_id,
            "work": WORK_LABELS[work_id],
            "formula_count": count,
            "unique_materials": len(materials),
            "median_formula_size": float(np.median(sizes)),
            "role": "confirmation" if work_id == "hong_xiangpu_attributed" else "development_and_primary",
        })
    source_path = TABLE_DIR / "table1_corpus_by_source.csv"
    _write_csv(source_path, source_rows, list(source_rows[0]))

    main_rows = []
    for model in ("frequency", "graph_only", "full_no_chemistry"):
        metrics = primary["source_level_metrics"][model]
        main_rows.append({
            "model": MODEL_LABELS[model],
            "hidden_f1_source_macro": float(np.mean([x["hidden_f1"] for x in metrics.values()])),
            "weighted_jaccard_source_macro": float(np.mean([x["weighted_jaccard"] for x in metrics.values()])),
            "aitchison_distance_source_macro": float(np.mean([x["aitchison_distance"] for x in metrics.values()])),
            "development_formula_count": len(development),
            "held_out_work_groups": len(metrics),
            "mask_seeds": len(primary["seeds"]),
        })
    main_path = TABLE_DIR / "table2_primary_models.csv"
    _write_csv(main_path, main_rows, list(main_rows[0]))

    source_metric_rows = []
    for work_id in WORK_LABELS:
        if work_id == "hong_xiangpu_attributed":
            continue
        for model in ("frequency", "graph_only", "full_no_chemistry"):
            values = primary["source_level_metrics"][model][work_id]
            source_metric_rows.append({
                "work_id": work_id,
                "work": WORK_LABELS[work_id],
                "model": MODEL_LABELS[model],
                **values,
            })
    source_metrics_path = TABLE_DIR / "table3_source_metrics.csv"
    _write_csv(source_metrics_path, source_metric_rows, list(source_metric_rows[0]))

    sensitivity_rows = []
    for fraction, payload in robustness["observation_fraction_sensitivity"].items():
        for model in ("frequency", "graph_only", "full_no_chemistry"):
            sensitivity_rows.append({
                "observed_fraction": float(fraction),
                "model": MODEL_LABELS[model],
                **payload["model_metrics"][model],
            })
    sensitivity_path = TABLE_DIR / "table4_context_sensitivity.csv"
    _write_csv(sensitivity_path, sensitivity_rows, list(sensitivity_rows[0]))

    error = robustness["locked_model_error_analysis"]
    rarity_rows = [
        {"frequency_class": key, **value}
        for key, value in error["hidden_recall_by_training_frequency"].items()
    ]
    rarity_path = TABLE_DIR / "table5_rarity_recall.csv"
    _write_csv(rarity_path, rarity_rows, list(rarity_rows[0]))

    calibration_rows = primary["selected_model_calibration"]["reliability_bins"]
    calibration_path = TABLE_DIR / "table6_reliability_bins.csv"
    _write_csv(calibration_path, calibration_rows, list(calibration_rows[0]))

    hong_rows = []
    for model in ("frequency", "graph_only", "full_no_chemistry"):
        values = hong["results"][model]["mean_across_seeds"]
        hong_rows.append({"model": MODEL_LABELS[model], **values})
    hong_path = TABLE_DIR / "table7_hong_confirmation.csv"
    _write_csv(hong_path, hong_rows, list(hong_rows[0]))
    return [source_path, main_path, source_metrics_path, sensitivity_path, rarity_path, calibration_path, hong_path]


def figure1_workflow() -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.9, 2.35))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (0.02, 0.30, 0.16, 0.42, "Historical formula\nwith observed materials", "91 formulas\n6 work groups"),
        (0.23, 0.30, 0.16, 0.42, "Training-fold\nconditional graph", r"$P(m_j\mid m_i)$"),
        (0.44, 0.30, 0.16, 0.42, "Bayesian inclusion\ndecoder", r"$p(y_j=1\mid x)$"),
        (0.65, 0.30, 0.16, 0.42, "Count and ratio\nposteriors", r"$K,\;\mathbf{w}\in\Delta^{M-1}$"),
        (0.86, 0.30, 0.12, 0.42, "Ranked\ncompletion", "materials\nratios\nintervals"),
    ]
    for index, (x, y, w, h, title, detail) in enumerate(boxes):
        edge = BLUE if index in (1, 2) else BLACK
        rect = mpl.patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=1.0, edgecolor=edge, facecolor="white"
        )
        ax.add_patch(rect)
        title_size = 6.8 if index == 0 else 7
        ax.text(x + w / 2, y + 0.27, title, ha="center", va="center", fontsize=title_size, weight="bold")
        ax.text(x + w / 2, y + 0.10, detail, ha="center", va="center", fontsize=7, color=GREY)
        if index < len(boxes) - 1:
            next_x = boxes[index + 1][0]
            ax.annotate("", (next_x - 0.01, 0.51), (x + w + 0.01, 0.51),
                        arrowprops={"arrowstyle": "-|>", "lw": 0.9, "color": GREY})
    ax.text(0.50, 0.88, "Source-blocked evaluation", ha="center", fontsize=7, weight="bold")
    ax.text(0.50, 0.80, "all statistics rebuilt within each training fold", ha="center", fontsize=7, color=GREY)
    ax.annotate("", (0.10, 0.22), (0.92, 0.22), arrowprops={"arrowstyle": "<|-|>", "lw": 0.9, "color": VERMILLION})
    ax.text(0.51, 0.08, "Two unseen works per primary fold   •   five deterministic masks   •   one quarantined confirmation work", ha="center", fontsize=7)
    fig.tight_layout(pad=0.2)
    return _save(fig, "fig1_workflow")


def figure2_corpus(reference: dict) -> list[Path]:
    work_ids = list(reference["work_counts"])
    labels = [WORK_LABELS[x] for x in work_ids]
    counts = [reference["work_counts"][x] for x in work_ids]
    sizes = [len(row["composition_aromatic_only"]) for row in reference["records"]]
    material_counts = Counter(m for row in reference["records"] for m in row["composition_aromatic_only"])

    fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.25), gridspec_kw={"width_ratios": [1.25, 1, 1]})
    ax = axes[0]
    colors = [VERMILLION if x == "hong_xiangpu_attributed" else BLUE for x in work_ids]
    positions = np.arange(len(labels))
    ax.barh(positions, counts, color=colors, edgecolor=BLACK, linewidth=0.45)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Formulas")
    ax.set_title("Corpus provenance")
    for y, value in zip(positions, counts):
        ax.text(value + 0.6, y, str(value), va="center", fontsize=7)
    _panel_label(ax, "a")

    ax = axes[1]
    bins = np.arange(1.5, max(sizes) + 1.6, 1)
    ax.hist(sizes, bins=bins, color=GREEN, edgecolor="white", linewidth=0.5)
    ax.axvline(np.median(sizes), color=BLACK, lw=1, ls="--", label=f"median = {np.median(sizes):.0f}")
    ax.set_xlabel("Aromatic materials per formula")
    ax.set_ylabel("Formulas")
    ax.set_title("Formula size")
    ax.legend(frameon=False, loc="upper right")
    _panel_label(ax, "b")

    ax = axes[2]
    frequency_bins = [1, 2, 3, 4, 5, 10, 20, 100]
    hist = np.histogram(list(material_counts.values()), bins=frequency_bins)[0]
    bin_labels = ["1", "2", "3", "4", "5–9", "10–19", "≥20"]
    ax.bar(np.arange(len(hist)), hist, color=PURPLE, edgecolor=BLACK, linewidth=0.45)
    ax.set_xticks(np.arange(len(hist)), bin_labels, rotation=45, ha="right")
    ax.set_xlabel("Formula frequency")
    ax.set_ylabel("Materials")
    ax.set_title("Material sparsity")
    _panel_label(ax, "c")
    fig.tight_layout(w_pad=1.2)
    return _save(fig, "fig2_corpus")


def figure3_primary(primary: dict) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.55))
    work_ids = list(primary["source_level_metrics"]["frequency"])
    positions = np.arange(len(work_ids))
    width = 0.23
    for offset, model in enumerate(("frequency", "graph_only", "full_no_chemistry")):
        color, marker, _ = MODEL_STYLES[model]
        values = [primary["source_level_metrics"][model][w]["hidden_f1"] for w in work_ids]
        axes[0].bar(positions + (offset - 1) * width, values, width,
                    color=color, alpha=0.88, edgecolor=BLACK, linewidth=0.35,
                    label=MODEL_LABELS[model])
        macro = float(np.mean(values))
        axes[1].scatter(offset, macro, s=38, color=color, marker=marker, edgecolor=BLACK, linewidth=0.45, zorder=3)
        for value in values:
            axes[1].scatter(offset, value, s=17, facecolor="white", edgecolor=color, marker=marker, linewidth=0.8, zorder=2)
    axes[0].set_xticks(positions, [WORK_LABELS[w] for w in work_ids], rotation=28, ha="right")
    axes[0].set_ylim(0, 0.52)
    axes[0].set_ylabel("Hidden-component F1")
    axes[0].set_title("Transfer to unseen works")
    _panel_label(axes[0], "a")

    axes[1].plot([0, 1, 2], [
        np.mean([primary["source_level_metrics"][m][w]["hidden_f1"] for w in work_ids])
        for m in ("frequency", "graph_only", "full_no_chemistry")
    ], color=LIGHT_GREY, lw=1, zorder=1)
    axes[1].set_xticks([0, 1, 2], ["Frequency", "Directed\ngraph", "Full\ndecoder"])
    axes[1].set_ylim(0.15, 0.48)
    axes[1].set_ylabel("Hidden-component F1")
    axes[1].set_title("Work-level distribution")
    _panel_label(axes[1], "b")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(w_pad=2.0, rect=[0, 0, 1, 0.88])
    return _save(fig, "fig3_primary_performance")


def figure4_robustness(robustness: dict) -> list[Path]:
    sensitivity = robustness["observation_fraction_sensitivity"]
    fraction_keys = sorted(sensitivity, key=float)
    fractions = np.array([float(x) for x in fraction_keys])
    error = robustness["locked_model_error_analysis"]
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.45))
    for model in ("frequency", "graph_only", "full_no_chemistry"):
        color, marker, line = MODEL_STYLES[model]
        values = [sensitivity[key]["model_metrics"][model]["hidden_f1"] for key in fraction_keys]
        axes[0].plot(fractions, values, color=color, marker=marker, ls=line, lw=1.0,
                     ms=4, label=MODEL_LABELS[model])
    axes[0].set_xticks(fractions, [f"{x:.0%}" for x in fractions])
    axes[0].set_ylim(0.20, 0.43)
    axes[0].set_xlabel("Observed fraction of true formula")
    axes[0].set_ylabel("Hidden-component F1")
    axes[0].set_title("Context sensitivity")
    axes[0].legend(frameon=False)
    _panel_label(axes[0], "a")

    order = ["common_5_plus", "rare_2_to_4", "singleton", "out_of_vocabulary"]
    labels = ["≥5", "2–4", "1", "0"]
    values = [error["hidden_recall_by_training_frequency"][x]["recall"] for x in order]
    totals = [error["hidden_recall_by_training_frequency"][x]["total"] for x in order]
    bars = axes[1].bar(np.arange(4), values, color=[BLUE, GREEN, PURPLE, GREY], edgecolor=BLACK, linewidth=0.45)
    axes[1].set_xticks(np.arange(4), labels)
    axes[1].set_ylim(0, 0.62)
    axes[1].set_xlabel("Training formulas containing material")
    axes[1].set_ylabel("Hidden-material recall")
    axes[1].set_title("Frequency controls recoverability")
    for bar, value, total in zip(bars, values, totals):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.018, f"{value:.2f}\n(n={total})", ha="center", fontsize=6.5)
    _panel_label(axes[1], "b")
    fig.tight_layout(w_pad=2.2)
    return _save(fig, "fig4_robustness")


def figure5_uncertainty(primary: dict, hong: dict) -> list[Path]:
    calibration = primary["selected_model_calibration"]
    bins = calibration["reliability_bins"]
    x = np.array([row["mean_probability"] for row in bins])
    y = np.array([row["empirical_frequency"] for row in bins])
    n = np.array([row["n"] for row in bins])
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.45))
    axes[0].plot([0, 1], [0, 1], color=GREY, lw=0.8, ls="--")
    axes[0].scatter(x, y, s=18 + 42 * np.sqrt(n / n.max()), color=BLUE, edgecolor=BLACK, linewidth=0.4)
    axes[0].plot(x, y, color=BLUE, lw=1)
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1)
    axes[0].set_xlabel("Mean predicted inclusion probability")
    axes[0].set_ylabel("Empirical inclusion frequency")
    axes[0].set_title("Reliability under source shift")
    axes[0].text(0.03, 0.94, f"ECE = {calibration['hidden_candidate_ece']:.3f}\nBrier = {calibration['hidden_candidate_brier']:.3f}", transform=axes[0].transAxes, va="top", fontsize=7)
    _panel_label(axes[0], "a")

    models = ("frequency", "graph_only", "full_no_chemistry")
    values = [hong["results"][m]["mean_across_seeds"]["hidden_f1"] for m in models]
    standard_deviations = [hong["results"][m]["sd_across_seeds"]["hidden_f1"] for m in models]
    colors = [MODEL_STYLES[m][0] for m in models]
    bars = axes[1].bar(np.arange(3), values, yerr=standard_deviations, capsize=3,
                       color=colors, edgecolor=BLACK, linewidth=0.45)
    axes[1].set_xticks(np.arange(3), [MODEL_LABELS[m].replace(" ", "\n") for m in models])
    axes[1].set_ylim(0, 0.68)
    axes[1].set_ylabel("Hidden-component F1")
    axes[1].set_title("Hong-source confirmation")
    for bar, value in zip(bars, values):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.055, f"{value:.3f}", ha="center", fontsize=7)
    _panel_label(axes[1], "b")
    fig.tight_layout(w_pad=2.0)
    return _save(fig, "fig5_uncertainty_confirmation")


def build() -> dict:
    _style()
    paths = {
        "reference": RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json",
        "splits": RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json",
        "primary": RESEARCH_ROOT / "experiments" / "cycle4_primary_evaluation.json",
        "robustness": RESEARCH_ROOT / "experiments" / "cycle4_robustness.json",
        "hong": RESEARCH_ROOT / "experiments" / "cycle4_hong_confirmation.json",
    }
    reference = _load(paths["reference"])
    primary = _load(paths["primary"])
    robustness = _load(paths["robustness"])
    hong = _load(paths["hong"])
    outputs = build_tables(reference, primary, robustness, hong)
    outputs += figure1_workflow()
    outputs += figure2_corpus(reference)
    outputs += figure3_primary(primary)
    outputs += figure4_robustness(robustness)
    outputs += figure5_uncertainty(primary, hong)
    manifest = {
        "schema_version": "0.1",
        "generated_by": "xiangji.manuscript_assets",
        "figure_standard": {
            "formats": ["PDF vector with Type 42 fonts", "SVG editable text", "PNG 450 dpi"],
            "color_space": "sRGB",
            "font_embedding": "TrueType Type 42 in PDF",
            "palette": "Okabe-Ito subset with redundant markers and line styles",
        },
        "sources": {name: {"path": str(path.relative_to(RESEARCH_ROOT)), "sha256": _sha256(path)} for name, path in paths.items()},
        "outputs": [
            {"path": str(path.relative_to(RESEARCH_ROOT)), "sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in outputs
        ],
    }
    manifest_path = FIGURE_DIR / "figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"manifest": str(manifest_path), "output_count": len(outputs)}


def main() -> None:
    print(json.dumps(build(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
