"""Materialize the v0.1 exact-composition reference set from reviewed decisions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

from xiangji.data import RESEARCH_ROOT
from xiangji.normalization.curation import validate_decision

GATE_KEYS = (
    "boundary_ok",
    "title_ok",
    "materials_ok",
    "quantities_ok",
    "roles_ok",
    "scope_ok",
    "family_assignment_ok",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def aromatic_mass_vector(record: dict) -> dict[str, float]:
    masses: defaultdict[str, float] = defaultdict(float)
    for mention in record["material_mentions"]:
        if mention["role"] != "aromatic_material":
            continue
        quantity = mention.get("quantity") or {}
        if quantity.get("basis") != "mass_qian" or quantity.get("value_qian") is None:
            raise ValueError(
                f"Included record {record['candidate_id']} has a non-mass aromatic quantity: "
                f"{mention['surface']}"
            )
        masses[mention["entity_id"]] += float(quantity["value_qian"])
    if not masses or sum(masses.values()) <= 0:
        raise ValueError(f"Included record {record['candidate_id']} has no positive aromatic mass")
    return dict(sorted(masses.items()))


def close_composition(masses: dict[str, float]) -> dict[str, float]:
    total = sum(masses.values())
    return {entity_id: value / total for entity_id, value in masses.items()}


def assert_same_composition(left: dict[str, float], right: dict[str, float], tolerance: float = 1e-10) -> None:
    if set(left) != set(right):
        raise ValueError(f"Composition entities differ: {sorted(left)} != {sorted(right)}")
    if any(abs(left[key] - right[key]) > tolerance for key in left):
        raise ValueError("Stored and recomputed aromatic compositions differ")


def build_decisions(batch: dict, manifest: dict) -> list[dict]:
    records_by_id = {row["candidate_id"]: row for row in batch["records"]}
    exclusions = manifest["exclusions"]
    unknown = set(exclusions) - set(records_by_id)
    if unknown:
        raise ValueError(f"Manifest contains unknown candidate IDs: {sorted(unknown)}")

    decisions = []
    for record in batch["records"]:
        candidate_id = record["candidate_id"]
        exclusion = exclusions.get(candidate_id)
        failed = set(exclusion.get("failed_gates", [])) if exclusion else set()
        invalid_gates = failed - set(GATE_KEYS)
        if invalid_gates:
            raise ValueError(f"Unknown failed gates for {candidate_id}: {sorted(invalid_gates)}")
        if exclusion:
            if exclusion["curation_order"] != record["curation_order"]:
                raise ValueError(f"Curation-order mismatch for {candidate_id}")
            if exclusion["expected_title"] != record["formula_title_candidate"]:
                raise ValueError(f"Title mismatch for {candidate_id}")
        release_ok = exclusion.get("release_ok", True) if exclusion else True
        included = exclusion is None
        decision = {
            "curation_order": record["curation_order"],
            "candidate_id": candidate_id,
            "formula_title": record["formula_title_candidate"],
            **{gate: gate not in failed for gate in GATE_KEYS},
            "release_ok": release_ok,
            "decision": "included_reference" if included else "excluded_reference",
            "reviewer": manifest["reviewer"],
            "review_date": manifest["review_date"],
            "review_mode": manifest["review_mode"],
            "review_notes": (
                exclusion["review_notes"] if exclusion else manifest["default_review_notes"]
            ),
            "reason_codes": exclusion.get("reason_codes", []) if exclusion else [],
        }
        validate_decision(decision)
        if included and not release_ok:
            raise ValueError(f"Included record {candidate_id} is not release-eligible")
        decisions.append(decision)
    return decisions


def make_reference_record(record: dict, decision: dict) -> dict:
    masses = aromatic_mass_vector(record)
    composition = close_composition(masses)
    assert_same_composition(composition, record["composition_aromatic_only"])
    raw_text = record["raw_wikitext"]
    return {
        "reference_id": f"xjfr-{record['candidate_id']}",
        "candidate_id": record["candidate_id"],
        "formula_family_id": record["formula_family_candidate_id"],
        "work_id": record["work_id_provisional"],
        "collection": record["collection"],
        "formula_title_verbatim": record["formula_title_candidate"],
        "source": {
            "page_title": record["page_title"],
            "stable_revision_url": record["stable_revision_url"],
            "locator_start": record["locator_start"],
            "locator_end": record["locator_end"],
            "raw_wikitext_sha256": sha256_bytes(raw_text.encode("utf-8")),
            "rights": "public-domain historical text; Wikisource transcription CC BY-SA 4.0",
        },
        "raw_wikitext": raw_text,
        "material_mentions": record["material_mentions"],
        "target_definition": "relative dry mass of aromatic materials only",
        "aromatic_mass_qian_by_entity": masses,
        "aromatic_mass_qian_total": sum(masses.values()),
        "composition_aromatic_only": composition,
        "component_count": len(composition),
        "curation": {
            key: decision[key]
            for key in (
                *GATE_KEYS,
                "release_ok",
                "decision",
                "reviewer",
                "review_date",
                "review_mode",
                "review_notes",
            )
        },
    }


def materialize(batch: dict, manifest: dict) -> tuple[dict, dict]:
    decisions = build_decisions(batch, manifest)
    decision_by_id = {row["candidate_id"]: row for row in decisions}
    included_records = [
        make_reference_record(row, decision_by_id[row["candidate_id"]])
        for row in batch["records"]
        if decision_by_id[row["candidate_id"]]["decision"] == "included_reference"
    ]
    if len(included_records) < 80:
        raise ValueError(f"Reference set has only {len(included_records)} records; minimum is 80")
    families = [row["formula_family_id"] for row in included_records]
    if len(families) != len(set(families)):
        raise ValueError("Included reference records are not family-unique")
    if any(abs(sum(row["composition_aromatic_only"].values()) - 1.0) > 1e-10 for row in included_records):
        raise ValueError("At least one included composition does not close to one")
    if any(not all(row["curation"][gate] is True for gate in GATE_KEYS) for row in included_records):
        raise ValueError("At least one included record failed a curation gate")

    work_counts = Counter(row["work_id"] for row in included_records)
    component_counts = Counter(row["component_count"] for row in included_records)
    exclusion_counts = Counter(
        code for row in decisions if row["decision"] == "excluded_reference" for code in row["reason_codes"]
    )
    reference = {
        "schema_version": "0.1",
        "name": "Xiangji Formula Reference v0.1",
        "status": "curated exact-composition reference set; independent second review pending",
        "target_definition": "relative dry-mass composition of aromatic materials in one burned or fumigating incense formula",
        "selection_notes": "One representative per checked provisional formula family; no missing aromatic quantity is imputed.",
        "batch_sha256": manifest["batch_sha256"],
        "manifest_sha256": None,
        "record_count": len(included_records),
        "work_count": len(work_counts),
        "work_counts": dict(sorted(work_counts.items())),
        "records": included_records,
    }
    audit = {
        "schema_version": "0.1",
        "batch_record_count": len(batch["records"]),
        "included_record_count": len(included_records),
        "excluded_record_count": len(decisions) - len(included_records),
        "included_family_count": len(set(families)),
        "included_work_count": len(work_counts),
        "included_work_counts": dict(sorted(work_counts.items())),
        "component_count_distribution": {
            str(key): value for key, value in sorted(component_counts.items())
        },
        "component_count_min": min(component_counts),
        "component_count_max": max(component_counts),
        "component_count_mean": sum(row["component_count"] for row in included_records) / len(included_records),
        "exclusion_reason_counts": dict(sorted(exclusion_counts.items())),
        "all_included_compositions_close_to_one": True,
        "all_included_records_pass_seven_gates": True,
        "included_families_are_unique": True,
        "independent_second_review_complete": False,
        "decisions": decisions,
    }
    return reference, audit


def main() -> None:
    batch_path = RESEARCH_ROOT / "data" / "interim" / "formula_curation_batch_v0.1.json"
    manifest_path = RESEARCH_ROOT / "data" / "curated" / "formula_curation_manifest_v0.1.json"
    batch_bytes = batch_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    batch = json.loads(batch_bytes)
    manifest = json.loads(manifest_bytes)
    observed_batch_hash = sha256_bytes(batch_bytes)
    if observed_batch_hash != manifest["batch_sha256"]:
        raise ValueError(
            f"Frozen batch hash mismatch: {observed_batch_hash} != {manifest['batch_sha256']}"
        )
    reference, audit = materialize(batch, manifest)
    reference["manifest_sha256"] = sha256_bytes(manifest_bytes)

    reference_path = RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    audit_path = RESEARCH_ROOT / "reports" / "formula_reference_audit_v0.1.json"
    reference_path.write_text(json.dumps(reference, ensure_ascii=False, indent=2), encoding="utf-8")
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "included": audit["included_record_count"],
        "excluded": audit["excluded_record_count"],
        "families": audit["included_family_count"],
        "works": audit["included_work_count"],
        "reference": str(reference_path),
        "audit": str(audit_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
