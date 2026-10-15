import json

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.case_study import build


def test_case_study_selection_and_rows_are_deterministic() -> None:
    result = build()
    assert result["seed"] == 17
    assert result["reference_id"] == "xjfr-526789359594ac3e"
    assert result["formula_title_verbatim"] == "印香法"
    assert len(result["material_rows"]) == 13
    assert {row["outcome"] for row in result["material_rows"]} == {
        "observed input", "recovered hidden", "missed hidden", "false positive"
    }


def test_generated_case_study_matches_builder() -> None:
    path = RESEARCH_ROOT / "experiments" / "cycle6_case_study.json"
    if path.exists():
        assert json.loads(path.read_text(encoding="utf-8")) == build()
