from xiangji.reference_verification_cycle6 import REFERENCE_KEYS, parse_bibtex
from xiangji.data import RESEARCH_ROOT


def test_complete_numbered_reference_key_registry() -> None:
    assert len(REFERENCE_KEYS) == 38
    assert len(set(REFERENCE_KEYS)) == 38


def test_every_numbered_reference_has_required_bibtex_fields() -> None:
    entries = parse_bibtex((RESEARCH_ROOT / "literature/references.bib").read_text(encoding="utf-8"))
    for key in REFERENCE_KEYS:
        assert {"title", "year", "author"} <= entries[key].keys()
        assert entries[key].get("doi") or entries[key].get("url")
