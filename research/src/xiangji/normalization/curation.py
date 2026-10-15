"""Deterministic preflight and validation helpers for formula adjudication."""

from __future__ import annotations

import re

from xiangji.normalization.recipes import (
    SKCHAR_CAPTURE,
    ingredient_body,
    load_skchar_resolutions,
)

ALTERNATIVE_MARKER = re.compile(r"別一方|别一方|又一方|又方|一方加|别本有|別本有")
OPTIONAL_MARKER = re.compile(r"不用亦可|不拘多少|隨意|随意|任意|或作|亦可")
NON_EXACT_MARKER = re.compile(
    r"少許|少许|不拘多少|"
    r"[一二三四五六七八九十百千廿卅半]+(?:餘|余)?(?:字|枚|粒|顆|颗|箇|個|个|朶|朵|升|合|盞|盏|撮)"
)
UNSPECIFIED_PREMIX = re.compile(r"用料[一二三四五六七八九十百千廿卅]+(?:兩|两|斤|觔)")


def unresolved_skchar_ids(text: str) -> list[str]:
    resolved = load_skchar_resolutions()
    return sorted({match.group(1) for match in SKCHAR_CAPTURE.finditer(text) if match.group(1) not in resolved})


def preflight_record(record: dict, family_size: int) -> dict:
    raw = record["raw_wikitext"]
    body = ingredient_body(raw.splitlines())
    aromatic = [row for row in record["material_mentions"] if row["role"] == "aromatic_material"]
    unresolved_identity = sorted({
        row["entity_id"] for row in aromatic
        if "unresolved" in row["identity_status"]
    })
    flags = []
    if ALTERNATIVE_MARKER.search(raw):
        flags.append("alternative_or_variant_marker")
    if OPTIONAL_MARKER.search(raw):
        flags.append("optional_or_non_exact_language")
    if NON_EXACT_MARKER.search(raw):
        flags.append("count_volume_or_qualitative_quantity_present")
    if UNSPECIFIED_PREMIX.search(raw):
        flags.append("unspecified_premix_present")
    body_skchars = unresolved_skchar_ids(body)
    if body_skchars:
        flags.append("unresolved_skchar_in_ingredient_span")
    if record["formula_scope_provisional"] not in {"burned_incense", "likely_burned_incense"}:
        flags.append("scope_requires_review")
    if family_size > 1:
        flags.append("multi_witness_family_requires_review")
    if any(row["source_zone"] == "method_quantified_addition" for row in record["material_mentions"]):
        flags.append("method_addition_requires_retention_check")
    if any(row["source_zone"] == "note_quantified_addition" for row in record["material_mentions"]):
        flags.append("note_addition_requires_retention_check")
    composition = record.get("composition_aromatic_only") or {}
    total = sum(composition.values())
    if not composition or abs(total - 1.0) > 1e-9:
        flags.append("invalid_automatic_composition")
    return {
        "curation_order": record["curation_order"],
        "candidate_id": record["candidate_id"],
        "formula_family_candidate_id": record["formula_family_candidate_id"],
        "formula_title_candidate": record["formula_title_candidate"],
        "family_size": family_size,
        "flags": flags,
        "unresolved_skchar_ids_in_ingredient_span": body_skchars,
        "unresolved_identity_entity_ids": unresolved_identity,
        "aromatic_component_count": len(composition),
        "composition_sum": total,
        "automatic_status": "preflight_only_not_an_adjudication",
    }


def validate_decision(decision: dict) -> None:
    required = {
        "candidate_id", "boundary_ok", "title_ok", "materials_ok", "quantities_ok",
        "roles_ok", "scope_ok", "family_assignment_ok", "decision", "reviewer",
        "review_notes", "reason_codes",
    }
    missing = required - set(decision)
    if missing:
        raise ValueError(f"Decision missing fields: {sorted(missing)}")
    if decision["decision"] not in {"included_reference", "excluded_reference", "requires_correction"}:
        raise ValueError(f"Unknown decision: {decision['decision']}")
    gates = [
        decision[key] for key in (
            "boundary_ok", "title_ok", "materials_ok", "quantities_ok",
            "roles_ok", "scope_ok", "family_assignment_ok",
        )
    ]
    if decision["decision"] == "included_reference" and not all(value is True for value in gates):
        raise ValueError("Included reference requires all seven gates to be true")
    if decision["decision"] == "excluded_reference" and not decision["reason_codes"]:
        raise ValueError("Excluded reference requires at least one reason code")
