from pathlib import Path

from xiangji.manuscript_assets import build


def test_manuscript_assets_build_complete_release_set() -> None:
    result = build()
    assert result["output_count"] == 22
    manifest = Path(result["manifest"])
    assert manifest.exists()
    assert (manifest.parent / "fig3_primary_performance.pdf").stat().st_size > 1_000
    assert (manifest.parent.parent / "manuscript" / "tables" / "table2_primary_models.csv").exists()
