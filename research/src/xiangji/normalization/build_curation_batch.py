"""Build a family-deduplicated, source-stratified formula review batch."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter

from xiangji.data import RESEARCH_ROOT
from xiangji.ingest.audit_candidates import infer_scope, title_flags

TARGET_SIZE = 120
QUOTAS = {
    "huizhai_xiangpu": 12,
    "moe_xiaolu_xiangpu": 6,
    "liexiang_xinpu": 10,
    "hong_xiangpu_attributed": 10,
    "chen_xiangpu_compilation": 37,
    "xiangcheng_compilation_unresolved_source": 37,
}


def work_id(record: dict) -> str:
    if record["collection"] == "hong_xiangpu":
        return "hong_xiangpu_attributed"
    if record["collection"] == "chen_xiangpu":
        return "chen_xiangpu_compilation"
    if record["collection"] == "zunsheng_bajian":
        return "zunsheng_bajian"
    volume = record["page_title"].rsplit("/", 1)[-1]
    return {
        "卷23": "huizhai_xiangpu",
        "卷24": "moe_xiaolu_xiangpu",
        "卷25": "liexiang_xinpu",
    }.get(volume, "xiangcheng_compilation_unresolved_source")


def ranking(record: dict) -> tuple:
    scope = infer_scope(record)
    scope_score = {"burned_incense": 3, "likely_burned_incense": 2, "scope_unresolved": 1}.get(scope, 0)
    component_count = record["aromatic_mention_count"]
    complexity_score = -abs(component_count - 7)
    stable_locator = int(bool(record.get("stable_revision_url")))
    return scope_score, stable_locator, complexity_score, record["candidate_id"]


def select(records: list[dict], family_by_candidate: dict[str, str]) -> list[dict]:
    eligible = []
    for record in records:
        if not record["ratio_ready_automatic"]:
            continue
        if not 2 <= record["aromatic_mention_count"] <= 18:
            continue
        if title_flags(record):
            continue
        if infer_scope(record) == "other_aromatic_preparation":
            continue
        if record["candidate_id"] not in family_by_candidate:
            continue
        eligible.append(record)

    selected, used_families = [], set()
    for group, quota in QUOTAS.items():
        candidates = sorted((record for record in eligible if work_id(record) == group), key=ranking, reverse=True)
        for record in candidates:
            family = family_by_candidate[record["candidate_id"]]
            if family in used_families:
                continue
            selected.append(record)
            used_families.add(family)
            if sum(work_id(item) == group for item in selected) >= quota:
                break
    if len(selected) < TARGET_SIZE:
        for record in sorted(eligible, key=ranking, reverse=True):
            family = family_by_candidate[record["candidate_id"]]
            if family in used_families:
                continue
            selected.append(record)
            used_families.add(family)
            if len(selected) == TARGET_SIZE:
                break
    if len(selected) < TARGET_SIZE:
        raise ValueError(f"Only {len(selected)} family-deduplicated records available")
    return sorted(selected, key=lambda record: (work_id(record), record["page_title"], record["line_start"]))


def main() -> None:
    structured_path = RESEARCH_ROOT / "data" / "interim" / "structured_formula_candidates_v0.1.json"
    genealogy_path = RESEARCH_ROOT / "data" / "interim" / "formula_genealogy_candidates_v0.1.json"
    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    genealogy = json.loads(genealogy_path.read_text(encoding="utf-8"))
    family_by_candidate = {
        candidate_id: family["formula_family_candidate_id"]
        for family in genealogy["families"]
        for candidate_id in family["member_candidate_ids"]
    }
    selected = select(structured["records"], family_by_candidate)
    records = []
    for order, record in enumerate(selected, 1):
        records.append({
            "curation_order": order,
            "candidate_id": record["candidate_id"],
            "formula_family_candidate_id": family_by_candidate[record["candidate_id"]],
            "work_id_provisional": work_id(record),
            "collection": record["collection"],
            "page_title": record["page_title"],
            "stable_revision_url": record["stable_revision_url"],
            "locator_start": record.get("paragraph_start", record["line_start"]),
            "locator_end": record.get("paragraph_end", record["line_end"]),
            "formula_title_candidate": record["formula_title_candidate"],
            "raw_wikitext": record["raw_wikitext"],
            "material_mentions": record["material_mentions"],
            "composition_aromatic_only": record["composition_aromatic_only"],
            "formula_scope_provisional": infer_scope(record),
            "review": {
                "boundary_ok": None,
                "title_ok": None,
                "materials_ok": None,
                "quantities_ok": None,
                "roles_ok": None,
                "scope_ok": None,
                "family_assignment_ok": None,
                "corrected_title": None,
                "corrected_components": None,
                "reviewer": None,
                "review_notes": None,
                "adjudication_status": "pending",
            },
        })
    output = {
        "schema_version": "0.1",
        "selection_rule": "family-deduplicated, source-stratified, ratio-ready candidates prioritized for burned-incense scope",
        "structured_source_sha256": hashlib.sha256(structured_path.read_bytes()).hexdigest(),
        "genealogy_source_sha256": hashlib.sha256(genealogy_path.read_bytes()).hexdigest(),
        "target_size": TARGET_SIZE,
        "record_count": len(records),
        "work_counts": dict(sorted(Counter(record["work_id_provisional"] for record in records).items())),
        "status": "curation queue; no record is gold until all review fields are adjudicated",
        "records": records,
    }
    json_path = RESEARCH_ROOT / "data" / "interim" / "formula_curation_batch_v0.1.json"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = RESEARCH_ROOT / "data" / "interim" / "formula_curation_batch_v0.1.csv"
    fields = [
        "curation_order", "candidate_id", "formula_family_candidate_id", "work_id_provisional",
        "page_title", "locator_start", "locator_end", "formula_title_candidate",
        "formula_scope_provisional", "parsed_components", "raw_wikitext", "boundary_ok", "title_ok",
        "materials_ok", "quantities_ok", "roles_ok", "scope_ok", "family_assignment_ok",
        "corrected_title", "corrected_components", "reviewer", "review_notes", "adjudication_status",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            review = record["review"]
            writer.writerow({
                **{key: record.get(key) for key in fields},
                "parsed_components": json.dumps(record["material_mentions"], ensure_ascii=False),
                **review,
            })
    print(json.dumps({"records": len(records), "work_counts": output["work_counts"], "json": str(json_path), "csv": str(csv_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
