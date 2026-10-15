import hashlib
import json

from xiangji.cycle6_assets import build
from xiangji.data import RESEARCH_ROOT


def test_cycle6_assets_are_generated_and_hashed() -> None:
    outputs = build()
    assert len(outputs) == 7
    manifest = json.loads((RESEARCH_ROOT / "figures/cycle6_figure_manifest.json").read_text())
    assert len(manifest["outputs"]) == 6
    for row in manifest["outputs"]:
        path = RESEARCH_ROOT / row["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
