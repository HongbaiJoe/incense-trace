from xiangji.export_latex import _main_tex, _supplement_tex
from xiangji.export_submission import MAIN_MD, SUBMISSION_DIR
from xiangji.figure_submission_audit import audit


def test_submission_source_exists_and_target_is_local() -> None:
    assert MAIN_MD.exists()
    assert SUBMISSION_DIR.parent.name == "research"


def test_six_main_figures_exist() -> None:
    figure_dir = MAIN_MD.parents[1] / "figures"
    assert all(list(figure_dir.glob(f"fig{number}_*.png")) for number in range(1, 7))


def test_twelve_supplementary_tables_exist() -> None:
    table_dir = MAIN_MD.parent / "tables"
    assert all(list(table_dir.glob(f"table{number}_*.csv")) for number in range(1, 13))
    main_tex = _main_tex()
    supplement_tex = _supplement_tex()
    assert main_tex.count(r"\bibitem{ref") == 38
    assert main_tex.count(r"\begin{figure}[htbp]") == 6
    assert main_tex.count(r"\begin{table}[htbp]") == 8
    assert main_tex.count(r"\begin{equation}") == 29
    assert supplement_tex.count(r"\begin{table}[p]") == 12
    assert "印香法" not in supplement_tex
    assert audit(write_report=False)["figure_count"] == 6
