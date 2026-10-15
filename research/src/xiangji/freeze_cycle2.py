"""Create a deterministic checksum manifest for the Cycle 2 release."""

from __future__ import annotations

import hashlib
import json

from xiangji.data import RESEARCH_ROOT

ARTIFACTS = [
    "ontology/materials_v0.1.json",
    "ontology/skchar_resolutions_v0.1.json",
    "protocol/formula_curation_protocol_v0.1.md",
    "data/interim/structured_formula_candidates_v0.1.json",
    "data/interim/formula_genealogy_candidates_v0.1.json",
    "data/interim/formula_curation_batch_v0.1.json",
    "data/curated/formula_curation_manifest_v0.1.json",
    "data/curated/formula_reference_v0.1.json",
    "data/curated/source_blocked_splits_v0.1.json",
    "data/interim/pubchem_compounds_v0.1.json",
    "data/processed/molecular_features_v0.1.json",
    "data/curated/material_compound_evidence_v0.1.json",
    "data/processed/material_representations_v0.1.json",
    "literature/search_log.csv",
    "literature/screening.csv",
    "literature/evidence_matrix.csv",
    "literature/novelty_matrix.csv",
    "literature/references.bib",
    "reports/formula_reference_audit_v0.1.json",
    "reports/formula_family_evidence_audit_v0.1.json",
    "reports/material_chemistry_audit_v0.1.json",
]


def main() -> None:
    rows = []
    for relative in ARTIFACTS:
        path = RESEARCH_ROOT / relative
        data = path.read_bytes()
        rows.append({
            "path": relative,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    output = {
        "schema_version": "0.1",
        "release": "xiangji-cycle2-v0.1",
        "freeze_date": "2026-09-07",
        "artifact_count": len(rows),
        "artifacts": rows,
    }
    target = RESEARCH_ROOT / "reports" / "cycle2_release_manifest.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"release": output["release"], "artifacts": len(rows), "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
