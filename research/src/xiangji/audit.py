"""Dataset audit with explicit source-validation limitations."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from xiangji.data import RESEARCH_ROOT, load_corpus


def build_audit() -> dict:
    corpus = load_corpus()
    recipe_ids = [r["id"] for r in corpus.recipes]
    families = Counter(r["family"] for r in corpus.recipes)
    materials = Counter(m for r in corpus.recipes for m in r["ingredients"])
    source_ids = [r.get("source_id") for r in corpus.recipes]
    source_locators = [r.get("source_locator") for r in corpus.recipes]
    return {
        "recipe_count": len(corpus.recipes),
        "material_catalogue_count": len(corpus.materials),
        "observed_material_count": len(materials),
        "odor_dimension_count": len(corpus.dimensions),
        "family_counts": dict(sorted(families.items())),
        "ingredient_count_distribution": dict(sorted(Counter(len(r["ingredients"]) for r in corpus.recipes).items())),
        "duplicate_recipe_ids": sorted([rid for rid, count in Counter(recipe_ids).items() if count > 1]),
        "recipes_with_source_id": sum(value is not None for value in source_ids),
        "recipes_with_source_locator": sum(value is not None for value in source_locators),
        "cross_document_evaluation_available": len(set(v for v in source_ids if v)) >= 2,
        "validation_flag_counts": dict(Counter(str(r.get("validation", False)).lower() for r in corpus.recipes)),
        "known_limitations": [
            "All 44 records currently lack document identifiers and page or folio locators.",
            "The provided odor targets are curated labels, not instrumental measurements.",
            "Leave-one-family-out evaluates style-family extrapolation; it must not be described as cross-document validation.",
            "A true cross-document test requires independently sourced recipes with provenance metadata.",
        ],
    }


def main() -> None:
    output = RESEARCH_ROOT / "reports" / "cycle1_data_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_audit()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
