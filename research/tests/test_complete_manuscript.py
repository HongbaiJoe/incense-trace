import re
import zipfile

from xiangji.complete_manuscript import OUTPUT, build
from xiangji.data import RESEARCH_ROOT
from xiangji.mathematical_audit import TEX, WORD


def test_complete_manuscript_has_standard_section_order_and_inline_assets() -> None:
    build()
    text = OUTPUT.read_text(encoding="utf-8")
    sections = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    expected = [
        "Abstract", "Introduction", "Related Work", "Problem Formulation and Dataset",
        "Xiangji-CGIR Method", "Experimental Design", "Results", "Discussion",
        "Limitations", "Conclusion",
    ]
    assert [section for section in sections if section in expected] == expected
    assert len(re.findall(r"^\$\$\[[a-z0-9-]+\]", text, flags=re.MULTILINE)) == 29
    assert re.findall(r"^\[\[FIGURE:(\d+)\]\]$", text, flags=re.MULTILINE) == [str(n) for n in range(1, 7)]
    assert re.findall(r"^\[\[TABLE:(\d+)\]\]$", text, flags=re.MULTILINE) == [str(n) for n in range(1, 9)]


def test_complete_exports_preserve_math_and_main_assets() -> None:
    tex = TEX.read_text(encoding="utf-8")
    assert tex.count(r"\begin{equation}") == 29
    assert tex.count(r"\begin{figure}[htbp]") == 6
    assert tex.count(r"\begin{table}[htbp]") == 8
    with zipfile.ZipFile(WORD) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert document_xml.count("<m:oMath") >= 29


def test_main_tables_are_eight_well_formed_csv_files() -> None:
    paths = sorted((RESEARCH_ROOT / "manuscript" / "main_tables").glob("table*.csv"))
    assert len(paths) == 8
    assert all(path.read_text(encoding="utf-8").count("\n") >= 2 for path in paths)
