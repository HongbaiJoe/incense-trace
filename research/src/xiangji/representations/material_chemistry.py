"""Validate source-backed material-to-compound analytical evidence."""

from __future__ import annotations

import json
from collections import Counter

from xiangji.data import RESEARCH_ROOT


PRESENCE_EVIDENCE_TYPES = {"presence_across_samples", "isolated_presence"}


def validate(evidence: dict, ontology: dict, compounds: dict) -> list[str]:
    errors: list[str] = []
    source_ids = {row["source_id"] for row in evidence["sources"]}
    if len(source_ids) != len(evidence["sources"]):
        errors.append("duplicate source_id")
    material_ids = {row["id"] for row in ontology["entities"]}
    compound_ids = {row["query_name"] for row in compounds["records"]}
    profile_ids: set[str] = set()
    for profile in evidence["material_profiles"]:
        if profile["profile_id"] in profile_ids:
            errors.append(f"duplicate profile_id: {profile['profile_id']}")
        profile_ids.add(profile["profile_id"])
        if profile["source_id"] not in source_ids:
            errors.append(f"unknown source: {profile['source_id']}")
        if profile["ontology_material_id"] not in material_ids:
            errors.append(f"unknown material: {profile['ontology_material_id']}")
        if not profile.get("source_locator"):
            errors.append(f"missing source locator: {profile['profile_id']}")
        seen_compounds: set[str] = set()
        for component in profile["components"]:
            compound_id = component["compound_id"]
            if compound_id in seen_compounds:
                errors.append(f"duplicate compound in profile: {profile['profile_id']}:{compound_id}")
            seen_compounds.add(compound_id)
            if compound_id not in compound_ids:
                errors.append(f"compound absent from molecular vocabulary: {compound_id}")
            measurement = component["measurement"]
            if component["evidence_type"] in PRESENCE_EVIDENCE_TYPES:
                if measurement is not None:
                    errors.append(f"presence evidence has numeric abundance: {profile['profile_id']}:{compound_id}")
            elif measurement is None:
                errors.append(f"numeric evidence lacks measurement: {profile['profile_id']}:{compound_id}")
            else:
                lower, upper, unit = measurement.get("min"), measurement.get("max"), measurement.get("unit")
                if unit not in {"percent_peak_area", "concentration_ng_g"}:
                    errors.append(f"unsupported measurement unit: {profile['profile_id']}:{compound_id}")
                elif lower is None or upper is None or not 0 <= lower <= upper:
                    errors.append(f"invalid measurement interval: {profile['profile_id']}:{compound_id}")
                elif unit == "percent_peak_area" and upper > 100:
                    errors.append(f"percentage exceeds 100: {profile['profile_id']}:{compound_id}")
    return errors


def coverage_report(evidence: dict, structured: dict) -> dict:
    covered = {profile["ontology_material_id"] for profile in evidence["material_profiles"]}
    formula_counts: Counter[str] = Counter()
    for record in structured["records"]:
        if not record["ratio_ready_automatic"]:
            continue
        formula_counts.update({mention["entity_id"] for mention in record["material_mentions"] if mention["role"] == "aromatic_material"})
    total = sum(formula_counts.values())
    covered_mentions = sum(count for material, count in formula_counts.items() if material in covered)
    top = [
        {"ontology_material_id": material, "formula_count": count, "has_analytical_profile": material in covered}
        for material, count in formula_counts.most_common(20)
    ]
    return {
        "profile_count": len(evidence["material_profiles"]),
        "covered_material_count": len(covered),
        "numeric_component_edge_count": sum(
            component["evidence_type"] not in PRESENCE_EVIDENCE_TYPES
            for profile in evidence["material_profiles"]
            for component in profile["components"]
        ),
        "presence_only_edge_count": sum(
            component["evidence_type"] in PRESENCE_EVIDENCE_TYPES
            for profile in evidence["material_profiles"]
            for component in profile["components"]
        ),
        "automatic_ratio_ready_aromatic_mention_coverage": covered_mentions / total if total else 0.0,
        "top_20_materials": top,
        "interpretation": "Coverage is diagnostic only because the formula corpus is not yet gold and one modern profile cannot represent all historical grades or chemotypes.",
    }


def main() -> None:
    evidence_path = RESEARCH_ROOT / "data" / "curated" / "material_compound_evidence_v0.1.json"
    ontology_path = RESEARCH_ROOT / "ontology" / "materials_v0.1.json"
    compounds_path = RESEARCH_ROOT / "data" / "interim" / "pubchem_compounds_v0.1.json"
    structured_path = RESEARCH_ROOT / "data" / "interim" / "structured_formula_candidates_v0.1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
    compounds = json.loads(compounds_path.read_text(encoding="utf-8"))
    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    errors = validate(evidence, ontology, compounds)
    report = {"validation_errors": errors, **coverage_report(evidence, structured)}
    target = RESEARCH_ROOT / "reports" / "material_chemistry_audit_v0.1.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors:
        raise ValueError("; ".join(errors))
    print(json.dumps({"audit": str(target), **{key: report[key] for key in ("profile_count", "covered_material_count", "numeric_component_edge_count", "automatic_ratio_ready_aromatic_mention_coverage")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
