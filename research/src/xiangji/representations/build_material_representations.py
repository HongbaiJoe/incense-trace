"""Build three profile-level material views without pooling incompatible assays."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from xiangji.data import RESEARCH_ROOT


def conditional_weights(components: list[dict]) -> tuple[dict[str, float], str]:
    units = {
        row["measurement"]["unit"]
        for row in components
        if row.get("measurement") is not None
    }
    if not units:
        weight = 1.0 / len(components)
        return {row["compound_id"]: weight for row in components}, "uniform_over_presence_only_compounds"
    if len(units) != 1 or any(row.get("measurement") is None for row in components):
        raise ValueError("A profile cannot mix measurement units or numeric and presence-only evidence")
    midpoints = {
        row["compound_id"]: (row["measurement"]["min"] + row["measurement"]["max"]) / 2
        for row in components
    }
    total = sum(midpoints.values())
    if total <= 0:
        raise ValueError("Measured component midpoints must sum to a positive value")
    unit = next(iter(units))
    return {key: value / total for key, value in midpoints.items()}, f"midpoint_normalized_within_reported_{unit}"


def weighted_dict(rows: list[tuple[dict[str, float], float]]) -> dict[str, float]:
    values: defaultdict[str, float] = defaultdict(float)
    for vector, weight in rows:
        for key, value in vector.items():
            values[key] += weight * value
    return dict(sorted(values.items()))


def build_profile(profile: dict, molecular_by_name: dict, tags_by_name: dict) -> dict:
    weights, weight_basis = conditional_weights(profile["components"])
    compounds = []
    descriptor_rows = []
    physicochemical_rows = []
    bit_rows = []
    for component in profile["components"]:
        name = component["compound_id"]
        molecular = molecular_by_name[name]
        weight = weights[name]
        tags = tags_by_name[name]
        descriptor_rows.append(({tag: 1.0 for tag in tags}, weight))
        physicochemical_rows.append((molecular["descriptors"], weight))
        bit_rows.append(({str(bit): 1.0 for bit in molecular["morgan_on_bits"]}, weight))
        compounds.append({
            "compound_id": name,
            "cid": molecular["cid"],
            "inchikey": molecular["inchikey"],
            "conditional_weight": weight,
            "evidence_type": component["evidence_type"],
            "measurement": component["measurement"],
        })
    return {
        "profile_id": profile["profile_id"],
        "ontology_material_id": profile["ontology_material_id"],
        "context": {
            key: profile[key]
            for key in ("taxon", "part", "preparation", "analytical_method", "source_id", "source_locator", "sample_scope")
        },
        "weight_basis": weight_basis,
        "coverage_note": "Vectors are conditional on reported compounds and are not a complete volatile composition.",
        "compound_set_molecular_view": {
            "fingerprint": "Morgan radius 2, 2048 bits",
            "compounds": compounds,
            "weighted_morgan_bits": weighted_dict(bit_rows),
        },
        "physicochemical_view": weighted_dict(physicochemical_rows),
        "odor_tag_view": {
            "provenance": "controlled seed metadata used as a descriptor vocabulary; not analytical occurrence evidence",
            "weights": weighted_dict(descriptor_rows),
        },
    }


def main() -> None:
    evidence_path = RESEARCH_ROOT / "data" / "curated" / "material_compound_evidence_v0.1.json"
    molecular_path = RESEARCH_ROOT / "data" / "processed" / "molecular_features_v0.1.json"
    seed_path = RESEARCH_ROOT / "data" / "raw" / "compound_seeds.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    molecular = json.loads(molecular_path.read_text(encoding="utf-8"))
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))
    molecular_by_name = {row["query_name"]: row for row in molecular["records"]}
    tags_by_name = {row["name"]: row["tags"] for row in seeds["compounds"]}
    profiles = [
        build_profile(profile, molecular_by_name, tags_by_name)
        for profile in evidence["material_profiles"]
    ]
    output = {
        "schema_version": "0.1",
        "status": "frozen Cycle 2 profile-level representations",
        "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "molecular_features_sha256": hashlib.sha256(molecular_path.read_bytes()).hexdigest(),
        "profile_count": len(profiles),
        "material_count": len({row["ontology_material_id"] for row in profiles}),
        "aggregation_policy": "Keep specimen, preparation and assay profiles separate; never pool incompatible units across sources.",
        "views": ["odor_tag_view", "compound_set_molecular_view", "physicochemical_view"],
        "profiles": profiles,
    }
    target = RESEARCH_ROOT / "data" / "processed" / "material_representations_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"profiles": output["profile_count"], "materials": output["material_count"], "views": output["views"], "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
