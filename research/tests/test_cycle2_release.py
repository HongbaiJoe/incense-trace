import hashlib
import json

from xiangji.data import RESEARCH_ROOT


def test_cycle2_release_manifest_hashes_match_files():
    path = RESEARCH_ROOT / "reports" / "cycle2_release_manifest.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["artifact_count"] == len(payload["artifacts"]) >= 20
    for row in payload["artifacts"]:
        data = (RESEARCH_ROOT / row["path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
