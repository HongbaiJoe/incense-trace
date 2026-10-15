import hashlib
import json

from xiangji.data import RESEARCH_ROOT
from xiangji.freeze_cycle5 import build_manifest


def test_cycle5_manifest_matches_builder_and_files() -> None:
    expected = build_manifest()
    path = RESEARCH_ROOT / "reports" / "cycle5_release_manifest.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == expected
    assert payload["artifact_count"] >= 35
    assert payload["test_count"] >= 99
    for row in payload["artifacts"]:
        data = (RESEARCH_ROOT / row["path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
