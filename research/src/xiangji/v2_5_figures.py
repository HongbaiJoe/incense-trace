"""Create editable V2.5 manuscript figures from frozen experiment artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from xiangji.data import RESEARCH_ROOT


plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'
mpl.rcParams.update(
    {
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7.5,
        "axes.linewidth": 0.75,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.frameon": False,
    }
)

INK = "#2C2A29"
MUTED = "#AAA5A0"
GOLD = "#B58A4A"
WEAK = "#8FA7A0"
PALE = "#ECE9E4"


def _read() -> tuple[dict, dict, dict]:
    structured = json.loads(
        (
            RESEARCH_ROOT
            / "data"
            / "interim"
            / "structured_formula_candidates_v0.1.json"
        ).read_text(encoding="utf-8")
    )
    reference = json.loads(
        (
            RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
        ).read_text(encoding="utf-8")
    )
    weak = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_5_weak_supervision.json").read_text(
            encoding="utf-8"
        )
    )
    return structured, reference, weak


def _panel_label(ax: plt.Axes, value: str) -> None:
    ax.text(-0.10, 1.05, value, transform=ax.transAxes, weight="bold", fontsize=9)


def _save(fig: plt.Figure, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")


def build_data_scale_figure() -> None:
    structured, reference, weak = _read()
    records = structured["records"]
    collections = ["xiangcheng", "chen_xiangpu", "hong_xiangpu"]
    display = ["Xiangcheng", "Chen Xiangpu", "Hong Xiangpu"]
    stages = ["Candidates", "Ratio-ready", "Gold", "Weak eligible"]
    counts = {
        "Candidates": [sum(r["collection"] == c for r in records) for c in collections],
        "Ratio-ready": [
            sum(r["collection"] == c and r["ratio_ready_automatic"] for r in records)
            for c in collections
        ],
        "Gold": [
            sum(r["collection"] == c for r in reference["records"])
            for c in collections
        ],
        "Weak eligible": [84, 58, 4],
    }

    fig = plt.figure(figsize=(7.09, 3.0), constrained_layout=True)
    grid = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.15, 1.25])

    ax = fig.add_subplot(grid[0, 0])
    ax.set_axis_off()
    _panel_label(ax, "a")
    box_y = [0.84, 0.58, 0.32]
    box_text = [
        ("592", "source-linked candidates"),
        ("296", "ratio-ready records"),
        ("237", "model-facing records"),
    ]
    for y, (number, label) in zip(box_y, box_text):
        face = PALE if number != "237" else "#E7EFEA"
        patch = mpl.patches.FancyBboxPatch(
            (0.12, y - 0.085),
            0.76,
            0.17,
            boxstyle="round,pad=0.015,rounding_size=0.025",
            linewidth=0.8,
            edgecolor=MUTED,
            facecolor=face,
        )
        ax.add_patch(patch)
        ax.text(0.19, y, number, va="center", ha="left", fontsize=15, color=INK)
        ax.text(0.44, y, label, va="center", ha="left", fontsize=7.0, color=INK)
    for y1, y2 in zip(box_y[:-1], box_y[1:]):
        ax.annotate(
            "",
            xy=(0.5, y2 + 0.10),
            xytext=(0.5, y1 - 0.10),
            arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 0.8},
        )
    ax.text(0.21, 0.12, "91 gold", color=GOLD, weight="bold")
    ax.text(0.50, 0.12, "+ 146 weak", color=WEAK, weight="bold")
    ax.text(0.5, 0.02, "191 genealogy families", ha="center", color="#5E5B57")

    ax = fig.add_subplot(grid[0, 1])
    _panel_label(ax, "b")
    left = np.zeros(len(stages))
    colors = ["#4E4A47", "#9A9690", "#C8B38A"]
    for collection, label, color in zip(collections, display, colors):
        values = np.asarray([counts[stage][collections.index(collection)] for stage in stages])
        ax.barh(stages, values, left=left, color=color, height=0.62, label=label)
        for y, value, start in zip(range(len(stages)), values, left):
            if value >= 14:
                ax.text(start + value / 2, y, str(int(value)), ha="center", va="center", color="white", fontsize=6.5)
        left += values
    ax.invert_yaxis()
    ax.set_xlabel("Records")
    ax.set_xlim(0, 620)
    ax.legend(loc="lower left", bbox_to_anchor=(0.02, 0.01), fontsize=6.5)
    ax.grid(axis="x", color="#E7E4E0", linewidth=0.6)
    ax.set_axisbelow(True)

    ax = fig.add_subplot(grid[0, 2])
    _panel_label(ax, "c")
    work_order = [
        "chen_xiangpu_compilation",
        "hong_xiangpu_attributed",
        "huizhai_xiangpu",
        "liexiang_xinpu",
        "moe_xiaolu_xiangpu",
        "xiangcheng_compilation_unresolved_source",
    ]
    short = ["Chen", "Hong", "Huizhai", "Liexiang", "Xiaolu", "Xiangcheng"]
    gold = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json").read_text(
            encoding="utf-8"
        )
    )["models"]["sscl"]["work_metrics"]
    augmented = weak["models"]["sscl"]["work_metrics"]
    y = np.arange(len(work_order))
    gold_value = np.asarray([gold[w]["hidden_f1"] for w in work_order])
    weak_value = np.asarray([augmented[w]["hidden_f1"] for w in work_order])
    for k in range(len(y)):
        ax.plot([gold_value[k], weak_value[k]], [k, k], color=MUTED, lw=1.0, zorder=1)
    ax.scatter(gold_value, y, s=26, facecolors="white", edgecolors=GOLD, linewidths=1.2, label="Gold only", zorder=2)
    ax.scatter(weak_value, y, s=26, color=WEAK, label="Gold + weak", zorder=3)
    ax.set_yticks(y, short)
    ax.invert_yaxis()
    ax.set_xlim(0.18, 0.62)
    ax.set_xlabel("Hidden-ingredient F1")
    ax.grid(axis="x", color="#E7E4E0", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=6.5)

    output = RESEARCH_ROOT / "figures" / "v2_5_fig1_data_scale"
    _save(fig, output)

    source_data = RESEARCH_ROOT / "figures" / "v2_5_fig1_source_data.csv"
    with source_data.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["panel", "category", "series", "value"])
        for stage in stages:
            for label, value in zip(display, counts[stage]):
                writer.writerow(["b", stage, label, value])
        for work, label, a, b in zip(work_order, short, gold_value, weak_value):
            writer.writerow(["c", label, "gold_only", f"{a:.12f}"])
            writer.writerow(["c", label, "gold_plus_weak", f"{b:.12f}"])


def main() -> None:
    build_data_scale_figure()
    print(RESEARCH_ROOT / "figures" / "v2_5_fig1_data_scale.pdf")


if __name__ == "__main__":
    main()
