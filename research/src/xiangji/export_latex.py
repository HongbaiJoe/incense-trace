"""Export the frozen manuscript and supplement as portable LaTeX sources."""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
from pathlib import Path

from xiangji.data import RESEARCH_ROOT
from xiangji.complete_manuscript import build as build_complete_manuscript
from xiangji.export_submission import (
    MAIN_FIGURE_SOURCE,
    MAIN_TABLE_CAPTIONS,
    MAIN_TABLE_SOURCE,
    _romanize_for_portable_pdf,
)


SUBMISSION_DIR = RESEARCH_ROOT / "submission"
MAIN_MD = RESEARCH_ROOT / "manuscript/manuscript_complete.md"
SOURCE_MD = RESEARCH_ROOT / "manuscript/manuscript_v1.md"
SUPPLEMENT_MD = RESEARCH_ROOT / "manuscript/supplementary_v1.md"
FIGURE_DIR = RESEARCH_ROOT / "figures"
TABLE_DIR = RESEARCH_ROOT / "manuscript/tables"
MAIN_TABLE_DIR = RESEARCH_ROOT / "manuscript/main_tables"

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[a4paper,top=23mm,bottom=25mm,left=24mm,right=24mm]{geometry}
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{texgyretermes-regular.otf}[
  BoldFont=texgyretermes-bold.otf,
  ItalicFont=texgyretermes-italic.otf,
  BoldItalicFont=texgyretermes-bolditalic.otf]
\setsansfont{texgyreheros-regular.otf}[BoldFont=texgyreheros-bold.otf]
\setmonofont{lmmono10-regular.otf}[Scale=MatchLowercase]
\setmathfont{latinmodern-math.otf}
\setmathfont{latinmodern-math.otf}[version=bold,FakeBold=1.5]
\usepackage{microtype}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{adjustbox}
\usepackage{pdflscape}
\usepackage{xcolor}
\usepackage{cite}
\usepackage[hidelinks]{hyperref}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf,labelsep=period,justification=justified,singlelinecheck=false}
\setlength{\parindent}{1.4em}
\setlength{\parskip}{0.22em}
\setlength{\emergencystretch}{2em}
\hbadness=2000
\renewcommand{\familydefault}{\rmdefault}
\renewcommand{\baselinestretch}{1.08}
"""

UNNUMBERED_SECTIONS = {
    "Data availability", "Code availability", "Acknowledgements",
    "Author contributions", "Competing interests",
}

MATH_TOKENS = {
    "−": r"\ensuremath{-}",
    "Σ": r"\ensuremath{\Sigma}",
    "π": r"\ensuremath{\pi}",
    "α": r"\ensuremath{\alpha}",
    "Δ": r"\ensuremath{\Delta}",
    "∈": r"\ensuremath{\in}",
    "⊂": r"\ensuremath{\subset}",
    "∩": r"\ensuremath{\cap}",
    "ᵢ": r"\ensuremath{_{i}}",
    "ⱼ": r"\ensuremath{_{j}}",
    "⁻": r"\ensuremath{{}^{-}}",
    "¹": r"\ensuremath{{}^{1}}",
    "²": r"\ensuremath{{}^{2}}",
    "ŵ": r"\ensuremath{\hat{w}}",
}


def _latex_math(value: str) -> str:
    """Normalize commands whose Unicode-math glyph is absent from LM Math."""
    return value.replace(r"\setminus", r"\mathbin{\backslash}")

def _citations(value: str) -> str:
    keys: list[str] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            start, end = (int(part) for part in chunk.split("-", 1))
            keys.extend(f"ref{number}" for number in range(start, end + 1))
        else:
            keys.append(f"ref{int(chunk)}")
    return r"\cite{" + ",".join(keys) + "}"


def _inline(text: str, *, citations: bool = True) -> str:
    text = _romanize_for_portable_pdf(text)
    tokens: list[str] = []

    def hold(value: str) -> str:
        tokens.append(value)
        return f"@@XJ{len(tokens) - 1}@@"

    text = re.sub(r"https?://[^\s)]+", lambda m: hold(r"\nolinkurl{" + m.group(0) + "}"), text)
    if citations:
        text = re.sub(r"\[(\d+(?:[-,]\d+)*)\]", lambda m: hold(_citations(m.group(1))), text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: hold(r"\textbf{" + _inline(m.group(1), citations=False) + "}"), text)
    text = re.sub(r"\*([^*]+)\*", lambda m: hold(r"\emph{" + _inline(m.group(1), citations=False) + "}"), text)
    text = re.sub(r"`([^`]+)`", lambda m: hold(r"\texttt{" + _escape(m.group(1)) + "}"), text)
    text = re.sub(r"\$([^$]+)\$", lambda m: hold(r"\(" + _latex_math(m.group(1)) + r"\)"), text)
    for character, latex in MATH_TOKENS.items():
        text = text.replace(character, hold(latex))
    text = _escape(text)
    for index, token in enumerate(tokens):
        text = text.replace(f"@@XJ{index}@@", token)
    return text


def _escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def _paragraphs(lines: list[str]) -> list[tuple[str, str]]:
    """Return simple Markdown blocks as (kind, value)."""
    blocks: list[tuple[str, str]] = []
    buffer: list[str] = []
    code: list[str] = []
    in_code = False

    def flush() -> None:
        if buffer:
            blocks.append(("paragraph", " ".join(part.strip() for part in buffer)))
            buffer.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush()
            if in_code:
                blocks.append(("code", "\n".join(code)))
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        equation = re.match(r"^\$\$\[([a-z0-9-]+)\]\s*(.+?)\s*\$\$$", line)
        if equation:
            flush()
            blocks.append(("equation", equation.group(1) + "\t" + equation.group(2)))
        elif heading:
            flush()
            blocks.append((f"h{len(heading.group(1))}", heading.group(2)))
        elif re.match(r"^\[\[(FIGURE|TABLE):(\d+)\]\]$", line):
            flush()
            marker = re.match(r"^\[\[(FIGURE|TABLE):(\d+)\]\]$", line)
            assert marker is not None
            blocks.append((marker.group(1).lower(), marker.group(2)))
        elif line.startswith("- "):
            flush()
            blocks.append(("bullet", line[2:]))
        elif not line.strip():
            flush()
        else:
            buffer.append(line)
    flush()
    return blocks


def _body_block(kind: str, value: str) -> str:
    if kind == "equation":
        label, expression = value.split("\t", 1)
        return "\\begin{equation}\n\\label{eq:" + label + "}\n" + _latex_math(expression) + "\n\\end{equation}"
    if kind == "h2":
        command = r"\section*{" if value in UNNUMBERED_SECTIONS else r"\section{"
        return command + _inline(value, citations=False) + "}"
    if kind == "h3":
        return r"\subsection{" + _inline(value, citations=False) + "}"
    if kind == "code":
        return "\\begin{verbatim}\n" + value + "\n\\end{verbatim}"
    if kind == "bullet":
        return r"\begin{itemize}\item " + _inline(value) + r"\end{itemize}"
    return _inline(value)


def _figure_legends() -> dict[int, str]:
    text = SOURCE_MD.read_text(encoding="utf-8")
    legend_text = text.split("## Figure legends", 1)[1]
    legends: dict[int, str] = {}
    pattern = re.compile(r"^\*\*Figure (\d+) \| (.+?)\.\*\*\s*(.*)$", re.MULTILINE)
    for match in pattern.finditer(legend_text):
        legends[int(match.group(1))] = f"{match.group(2)}. {match.group(3)}".strip()
    if set(legends) != set(range(1, 7)):
        raise ValueError(f"Expected six figure legends, found {sorted(legends)}")
    return legends


def _split_main() -> tuple[str, list[tuple[str, str]], list[str]]:
    lines = MAIN_MD.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ")
    reference_index = lines.index("## References")
    blocks = _paragraphs(lines[5:reference_index])
    references = [line for line in lines[reference_index + 1:] if line.strip()]
    return title, blocks, references


def _main_figure_tex(number: int) -> str:
    source_number = MAIN_FIGURE_SOURCE[number]
    path = next(FIGURE_DIR.glob(f"fig{source_number}_*.pdf"))
    return "\n".join([
        r"\begin{figure}[htbp]", r"\centering",
        r"\includegraphics[width=0.98\linewidth]{figures/" + path.name + "}",
        r"\caption{" + _inline(_figure_legends()[source_number]) + "}",
        rf"\label{{fig:{number}}}", r"\end{figure}",
    ])


def _main_table_tex(number: int) -> str:
    path = next(MAIN_TABLE_DIR.glob(f"table{MAIN_TABLE_SOURCE[number]}_*.csv"))
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [[_romanize_for_portable_pdf(value) for value in row] for row in csv.reader(handle)]
    alignment = "@{}" + "l" * len(rows[0]) + "@{}"
    body: list[str] = []
    for row_index, row in enumerate(rows):
        values = []
        for value in row:
            cell = _inline(value, citations=False)
            values.append(r"\textbf{" + cell + "}" if row_index == 0 else cell)
        body.append(" & ".join(values) + r" \\")
        if row_index == 0:
            body.append(r"\midrule")
    return "\n".join([
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{" + _inline(MAIN_TABLE_CAPTIONS[number]) + "}",
        rf"\label{{tab:{number}}}",
        r"\begin{adjustbox}{max width=\linewidth}",
        rf"\begin{{tabular}}{{{alignment}}}", r"\toprule", *body,
        r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}",
    ])


def _main_tex() -> str:
    title, blocks, references = _split_main()
    output = [PREAMBLE, r"\title{" + _inline(title, citations=False) + "}"]
    output.extend([
        r"\author{Author name\\Affiliation, city, country\\Corresponding email}",
        r"\date{}", r"\begin{document}", r"\maketitle",
    ])
    in_abstract = False
    for kind, value in blocks:
        if kind == "h2" and value == "Abstract":
            output.append(r"\begin{abstract}")
            in_abstract = True
            continue
        if in_abstract and kind.startswith("h"):
            output.append(r"\end{abstract}")
            in_abstract = False
        if kind == "figure":
            block = _main_figure_tex(int(value))
        elif kind == "table":
            block = _main_table_tex(int(value))
        else:
            block = _body_block(kind, value)
        output.append(block)
    if in_abstract:
        output.append(r"\end{abstract}")

    output.append(r"\begin{thebibliography}{99}")
    for reference in references:
        match = re.match(r"^(\d+)\.\s+(.+)$", reference)
        if not match:
            raise ValueError(f"Malformed numbered reference: {reference}")
        output.append(r"\bibitem{ref" + match.group(1) + "}" + _inline(match.group(2), citations=False))
    output.append(r"\end{thebibliography}")

    output.extend([r"\clearpage", r"\end{document}"])
    return "\n\n".join(output).rstrip() + "\n"


def _table_tex(number: int) -> str:
    path = next(TABLE_DIR.glob(f"table{number}_*.csv"))
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if number == 8:
        label_column = rows[0].index("label_zh")
        rows = [[value for index, value in enumerate(row) if index != label_column] for row in rows]
    rows = [[_romanize_for_portable_pdf(value) for value in row] for row in rows]
    columns = "@{}" + "l" * len(rows[0]) + "@{}"
    body = []
    for index, row in enumerate(rows):
        if index == 0:
            values = " & ".join(r"\textbf{" + _inline(value, citations=False) + "}" for value in row) + r" \\"
        else:
            values = " & ".join(_inline(value, citations=False) for value in row) + r" \\"
        body.append(values)
        if index == 0:
            body.append(r"\midrule")
    return "\n".join([
        r"\begin{landscape}", r"\begin{table}[p]", r"\centering", r"\scriptsize",
        rf"\caption*{{Supplementary Table S{number}}}",
        r"\resizebox{\linewidth}{!}{%", rf"\begin{{tabular}}{{{columns}}}", r"\toprule",
        *body, r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}", r"\end{landscape}",
    ])


def _supplement_tex() -> str:
    lines = SUPPLEMENT_MD.read_text(encoding="utf-8").splitlines()
    stop = lines.index("### Supplementary Tables")
    blocks = _paragraphs(lines[3:stop])
    output = [PREAMBLE, r"\title{Supplementary Information}",
              r"\author{\parbox{0.82\textwidth}{\centering Probabilistic graph completion of historical Chinese incense formulas under source shift}}",
              r"\date{}", r"\begin{document}", r"\maketitle",
              r"\renewcommand{\theequation}{S\arabic{equation}}"]
    output.extend(_body_block(kind, value) for kind, value in blocks)
    output.extend(_table_tex(number) for number in range(1, 13))
    output.extend([r"\clearpage", r"\section*{Supplementary Data and software inventory}",
                   _inline(lines[-1]), r"\end{document}"])
    return "\n\n".join(output).rstrip() + "\n"


def export() -> list[Path]:
    build_complete_manuscript()
    latex_dir = SUBMISSION_DIR / "latex"
    latex_dir.mkdir(parents=True, exist_ok=True)
    main = latex_dir / "xiangji_cgir_complete_paper.tex"
    supplement = latex_dir / "xiangji_cgir_supplementary.tex"
    main.write_text(_main_tex(), encoding="utf-8")
    supplement.write_text(_supplement_tex(), encoding="utf-8")
    shutil.copy2(RESEARCH_ROOT / "literature/references.bib", latex_dir / "xiangji_cgir_references.bib")
    figure_output = latex_dir / "figures"
    figure_output.mkdir(exist_ok=True)
    for number in range(1, 7):
        source = next(FIGURE_DIR.glob(f"fig{number}_*.pdf"))
        shutil.copy2(source, figure_output / source.name)
    return [main, supplement]


def compile_sources(tectonic: str) -> list[Path]:
    outputs = []
    for source in export():
        subprocess.run([tectonic, "-X", "compile", source.name, "--keep-logs"], cwd=source.parent, check=True)
        outputs.append(source.with_suffix(".pdf"))
    return outputs


def main() -> None:
    for path in export():
        print(path)


if __name__ == "__main__":
    main()
