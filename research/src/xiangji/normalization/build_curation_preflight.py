"""Build a machine-readable review preflight without assigning gold labels."""

from __future__ import annotations

import json
from collections import Counter

from xiangji.data import RESEARCH_ROOT
from xiangji.normalization.curation import preflight_record


def main() -> None:
    batch_path = RESEARCH_ROOT / "data" / "interim" / "formula_curation_batch_v0.1.json"
    genealogy_path = RESEARCH_ROOT / "data" / "interim" / "formula_genealogy_candidates_v0.1.json"
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    genealogy = json.loads(genealogy_path.read_text(encoding="utf-8"))
    family_sizes = {
        row["formula_family_candidate_id"]: row["member_count"]
        for row in genealogy["families"]
    }
    records = [
        preflight_record(row, family_sizes[row["formula_family_candidate_id"]])
        for row in batch["records"]
    ]
    flag_counts = Counter(flag for row in records for flag in row["flags"])
    output = {
        "schema_version": "0.1",
        "status": "deterministic preflight only; flags are review prompts, not inclusion decisions",
        "record_count": len(records),
        "flag_counts": dict(sorted(flag_counts.items())),
        "records": records,
    }
    target = RESEARCH_ROOT / "reports" / "formula_curation_preflight_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(records), "flag_counts": output["flag_counts"], "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
