"""Assemble the field-neutral complete-paper manuscript used by both exporters.

The scientific prose remains in ``manuscript_v1.md``.  This module changes only
presentation order: problem formulation and methods precede experiments, and
the compact main-text tables and figures are inserted where they are discussed.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

from xiangji.data import RESEARCH_ROOT
from xiangji.presentation_tables import build as build_presentation_tables


SOURCE = RESEARCH_ROOT / "manuscript" / "manuscript_v1.md"
OUTPUT = RESEARCH_ROOT / "manuscript" / "manuscript_complete.md"


def _h2_sections(text: str) -> tuple[list[str], OrderedDict[str, list[str]]]:
    lines = text.splitlines()
    first = next(index for index, line in enumerate(lines) if line.startswith("## "))
    front = lines[:first]
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None
    for line in lines[first:]:
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return front, sections


def _h3_sections(lines: list[str]) -> OrderedDict[str, list[str]]:
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None
    for line in lines:
        if line.startswith("### "):
            current = line[4:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def _trim(lines: list[str]) -> list[str]:
    values = list(lines)
    while values and not values[0].strip():
        values.pop(0)
    while values and not values[-1].strip():
        values.pop()
    return values


def _subsection(title: str, lines: list[str]) -> list[str]:
    return [f"### {title}", "", *_trim(lines), ""]


def _section(title: str, lines: list[str]) -> list[str]:
    return [f"## {title}", "", *_trim(lines), ""]


def _with_marker(lines: list[str], marker: str) -> list[str]:
    return [*_trim(lines), "", marker]


def _replace_main_text_references(text: str) -> str:
    replacements = {
        "(Fig. 2a; Supplementary Table S1)": "(Fig. 2a; Table 3)",
        "(Fig. 3; Supplementary Table S2)": "(Fig. 3; Tables 4 and 5)",
        "(Fig. 3a; Supplementary Table S3)": "(Fig. 3a; Table 5)",
        "(Fig. 6a; Supplementary Table S10)": "(Fig. 4a; Table 4)",
        "(Fig. 6b; Supplementary Table S11)": "(Fig. 4b)",
        "(Fig. 4a; Supplementary Table S4)": "(Fig. 5a; Table 6)",
        "(Fig. 4b; Supplementary Table S5)": "(Fig. 5b)",
        "(Fig. 5a; Supplementary Table S6)": "(Fig. 6a; Table 7)",
        "(Fig. 6c; Supplementary Table S12)": "(Fig. 4c; Table 7)",
        "(Fig. 5b; Supplementary Table S7)": "(Fig. 6b)",
        "(Supplementary Table S8)": "(Table 8)",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def build() -> Path:
    build_presentation_tables()
    front, sections = _h2_sections(SOURCE.read_text(encoding="utf-8"))
    methods = _h3_sections(sections["Methods"])
    results = _h3_sections(sections["Results"])

    output: list[str] = [*_trim(front), ""]
    output.extend(_section("Abstract", sections["Abstract"]))
    output.extend(_section("Introduction", sections["Introduction"]))
    output.extend(_section("Related Work", sections["Related work"]))

    problem: list[str] = []
    problem.extend(_subsection("Corpus Construction and Provenance", methods["Corpus construction and provenance"]))
    problem.extend(_subsection("Prediction Task and Observation Mechanism", methods["Prediction task and observation mechanism"]))
    problem.extend(_subsection("Source-Blocked Splits", _with_marker(methods["Source-blocked splits"], "[[TABLE:1]]")))
    output.extend(_section("Problem Formulation and Dataset", problem))

    model: list[str] = []
    model.extend(_subsection("Model Overview", [
        "Xiangji-CGIR separates formula completion into candidate inclusion, total ingredient count and composition. Figure 1 summarizes the training-only information flow and the source-blocked evaluation design.",
        "",
        "[[FIGURE:1]]",
    ]))
    model.extend(_subsection("Directed Posterior-Predictive Material Graph", methods["Directed posterior-predictive material graph"]))
    model.extend(_subsection("Generalized Bayesian Inclusion Decoder", methods["Inclusion decoder"]))
    model.extend(_subsection("Ingredient Count and Composition Uncertainty", methods["Ingredient count and composition uncertainty"]))
    model.extend(_subsection("Chemoinformatic Evidence Layer", methods["Chemoinformatic evidence layer"]))
    output.extend(_section("Xiangji-CGIR Method", model))

    experiments: list[str] = []
    experiments.extend(_subsection("Model Selection, Ablations and Negative Controls", _with_marker(
        methods["Model selection baselines and negative controls"], "[[TABLE:2]]"
    )))
    experiments.extend(_subsection("Competitive Set-Completion Baselines", methods["Competitive set-completion baselines"]))
    experiments.extend(_subsection("Cross-Work Similarity Sensitivity and Case Selection", methods["Cross-work similarity sensitivity and case selection"]))
    experiments.extend(_subsection("Evaluation Metrics and Statistical Analysis", methods["Evaluation and statistical analysis"]))
    experiments.extend(_subsection("Software and Computational Profiling", methods["Software and computational profiling"]))
    output.extend(_section("Experimental Design", experiments))

    result_markers = {
        "A source-blocked benchmark exposes material and document sparsity": ["[[TABLE:3]]", "[[FIGURE:2]]"],
        "A directed material graph carries the cross-document gain": ["[[TABLE:4]]", "[[TABLE:5]]", "[[FIGURE:3]]", "[[FIGURE:4]]"],
        "Context amount changes the residual task": ["[[TABLE:6]]", "[[FIGURE:5]]"],
        "Uncertainty outputs are informative but high probabilities remain overconfident": ["[[TABLE:7]]", "[[FIGURE:6]]"],
        "Quarantined-source confirmation reproduces the ranking": ["[[TABLE:8]]"],
    }
    result_lines: list[str] = []
    for title, lines in results.items():
        body = _trim(lines)
        for marker in result_markers.get(title, []):
            body.extend(["", marker])
        result_lines.extend(_subsection(title, body))
    output.extend(_section("Results", result_lines))

    for title in ("Discussion", "Limitations", "Conclusion", "Data availability", "Code availability", "Acknowledgements", "Author contributions", "Competing interests"):
        output.extend(_section(title.title() if title[0].islower() else title, sections[title]))
    output.extend(_section("References", sections["References"]))

    rendered = _replace_main_text_references("\n".join(output).rstrip() + "\n")
    expected_figures = [f"[[FIGURE:{number}]]" for number in range(1, 7)]
    expected_tables = [f"[[TABLE:{number}]]" for number in range(1, 9)]
    for marker in expected_figures + expected_tables:
        if rendered.count(marker) != 1:
            raise ValueError(f"Expected exactly one manuscript marker: {marker}")
    equation_labels = re.findall(r"^\$\$\[([a-z0-9-]+)\]", rendered, flags=re.MULTILINE)
    if len(equation_labels) != 29 or len(set(equation_labels)) != 29:
        raise ValueError(f"Expected 29 unique main-text equations, found {len(equation_labels)}")
    OUTPUT.write_text(rendered, encoding="utf-8")
    return OUTPUT


def main() -> None:
    print(build())


if __name__ == "__main__":
    main()
