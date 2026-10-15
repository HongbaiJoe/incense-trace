"""Audit the evidence behind every family assignment used in the reference set."""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter, defaultdict, deque

from xiangji.data import RESEARCH_ROOT
from xiangji.normalization.genealogy import (
    composition_cosine,
    jaccard,
    material_set,
    ngrams,
    normalize_text,
    normalize_title,
)

LOW_COSINE_EXPLANATIONS = {
    "ff-52bc4a8ba8a8": (
        "The Chen witness compresses or corrupts the Linglingxiang/patchouli line; "
        "the selected Xiangcheng witness retains the complete quantified sequence. "
        "Same normalized title and shared opening quantities justify one conservative leakage group."
    ),
    "ff-a3eedae7a49b": (
        "The witnesses share title, ordered ingredients and method wording. The low cosine is driven by "
        "a historical agarwood-grade identity difference and a divergent Fushouxiang quantity, so they are "
        "kept together conservatively for leakage prevention rather than asserted identical."
    ),
}


def connected(member_ids: list[str], edge_pairs: set[frozenset[str]]) -> bool:
    if len(member_ids) < 2:
        return True
    neighbours: defaultdict[str, set[str]] = defaultdict(set)
    for pair in edge_pairs:
        left, right = tuple(pair)
        neighbours[left].add(right)
        neighbours[right].add(left)
    seen = {member_ids[0]}
    queue = deque([member_ids[0]])
    while queue:
        current = queue.popleft()
        for neighbour in neighbours[current]:
            if neighbour in member_ids and neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return seen == set(member_ids)


def pair_evidence(left: dict, right: dict, direct_edge: dict | None) -> dict:
    left_materials, right_materials = material_set(left), material_set(right)
    return {
        "left_candidate_id": left["candidate_id"],
        "right_candidate_id": right["candidate_id"],
        "left_title": left["formula_title_candidate"],
        "right_title": right["formula_title_candidate"],
        "left_collection": left["collection"],
        "right_collection": right["collection"],
        "same_normalized_title": normalize_title(left["formula_title_candidate"]) == normalize_title(right["formula_title_candidate"]),
        "text_3gram_jaccard": jaccard(ngrams(normalize_text(left["parser_text"])), ngrams(normalize_text(right["parser_text"]))),
        "material_set_jaccard": jaccard(left_materials, right_materials),
        "composition_cosine": composition_cosine(left, right),
        "direct_candidate_edge": direct_edge is not None,
        "direct_edge_reason": direct_edge["reason"] if direct_edge else None,
    }


def build_audit(structured: dict, genealogy: dict, reference: dict) -> dict:
    by_candidate = {row["candidate_id"]: row for row in structured["records"]}
    by_family = {row["formula_family_candidate_id"]: row for row in genealogy["families"]}
    edge_by_pair = {
        frozenset((row["left_candidate_id"], row["right_candidate_id"])): row
        for row in genealogy["edges"]
    }
    selected_family_counts = Counter(row["formula_family_id"] for row in reference["records"])
    if any(count != 1 for count in selected_family_counts.values()):
        raise ValueError("Reference set must contain exactly one representative per selected family")

    family_rows = []
    for reference_row in reference["records"]:
        family_id = reference_row["formula_family_id"]
        family = by_family[family_id]
        members = family["member_candidate_ids"]
        member_rows = [by_candidate[candidate_id] for candidate_id in members]
        pair_rows = [
            pair_evidence(left, right, edge_by_pair.get(frozenset((left["candidate_id"], right["candidate_id"]))))
            for left, right in itertools.combinations(member_rows, 2)
        ]
        direct_pairs = {
            pair for pair in edge_by_pair
            if pair.issubset(set(members))
        }
        is_connected = connected(members, direct_pairs)
        if not is_connected:
            raise ValueError(f"Selected family is not connected by candidate edges: {family_id}")
        min_material = min((row["material_set_jaccard"] for row in pair_rows), default=1.0)
        min_cosine = min((row["composition_cosine"] for row in pair_rows), default=1.0)
        if min_material < 0.5:
            raise ValueError(f"Selected family has material-set Jaccard below 0.5: {family_id}")
        flags = []
        if pair_rows and not all(row["direct_candidate_edge"] for row in pair_rows):
            flags.append("connected_non_clique_cluster")
        if min_cosine < 0.75:
            flags.append("low_pairwise_composition_cosine_reviewed")
        if len({normalize_title(row["formula_title_candidate"]) for row in member_rows}) > 1:
            flags.append("title_variant_reviewed")
        explanation = LOW_COSINE_EXPLANATIONS.get(family_id)
        if "low_pairwise_composition_cosine_reviewed" in flags and not explanation:
            raise ValueError(f"Low-cosine family lacks a documented explanation: {family_id}")
        family_rows.append({
            "formula_family_id": family_id,
            "selected_reference_id": reference_row["reference_id"],
            "selected_candidate_id": reference_row["candidate_id"],
            "member_count": len(members),
            "member_candidate_ids": members,
            "member_titles": [row["formula_title_candidate"] for row in member_rows],
            "member_collections": [row["collection"] for row in member_rows],
            "direct_edge_graph_connected": is_connected,
            "minimum_pairwise_material_set_jaccard": min_material,
            "minimum_pairwise_composition_cosine": min_cosine,
            "audit_flags": flags,
            "review_explanation": explanation,
            "adjudication": "accepted_as_conservative_leakage_group" if len(members) > 1 else "singleton",
            "pair_evidence": pair_rows,
        })

    flag_counts = Counter(flag for row in family_rows for flag in row["audit_flags"])
    return {
        "schema_version": "0.1",
        "purpose": "Evidence audit for the family_assignment_ok gate and leakage grouping; not a claim of textual descent.",
        "reference_record_count": len(reference["records"]),
        "audited_family_count": len(family_rows),
        "singleton_family_count": sum(row["member_count"] == 1 for row in family_rows),
        "multi_member_family_count": sum(row["member_count"] > 1 for row in family_rows),
        "flag_counts": dict(sorted(flag_counts.items())),
        "all_selected_families_connected": True,
        "all_selected_families_minimum_material_jaccard_at_least_0_5": True,
        "one_reference_per_family": True,
        "families": family_rows,
    }


def main() -> None:
    structured_path = RESEARCH_ROOT / "data" / "interim" / "structured_formula_candidates_v0.1.json"
    genealogy_path = RESEARCH_ROOT / "data" / "interim" / "formula_genealogy_candidates_v0.1.json"
    reference_path = RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    genealogy = json.loads(genealogy_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    output = build_audit(structured, genealogy, reference)
    output["source_hashes"] = {
        "structured": hashlib.sha256(structured_path.read_bytes()).hexdigest(),
        "genealogy": hashlib.sha256(genealogy_path.read_bytes()).hexdigest(),
        "reference": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
    }
    target = RESEARCH_ROOT / "reports" / "formula_family_evidence_audit_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "families": output["audited_family_count"],
        "multi_member": output["multi_member_family_count"],
        "flags": output["flag_counts"],
        "output": str(target),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
