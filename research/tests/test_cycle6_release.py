import json

from xiangji.data import RESEARCH_ROOT
from xiangji.freeze_cycle6 import build_manifest


def test_cycle6_release_manifest_matches_builder_and_files() -> None:
    path = RESEARCH_ROOT / "reports/cycle6_release_manifest.json"
    if not path.exists():
        return
    expected = build_manifest()
    assert json.loads(path.read_text(encoding="utf-8")) == expected
