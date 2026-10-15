"""Audit manuscript structure, numeric anchors, sources and claim provenance."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from xiangji.data import RESEARCH_ROOT


MANUSCRIPT = RESEARCH_ROOT / "manuscript" / "manuscript_v1.md"
REGISTRY_DIR = RESEARCH_ROOT / "manuscript" / "registries"

SOURCES = {
    "E001": ("data/curated/formula_reference_v0.1.json", "curated formulas and corpus statistics"),
    "E002": ("data/curated/source_blocked_splits_v0.1.json", "development primary and confirmation partitions"),
    "E003": ("experiments/cycle4_primary_evaluation.json", "primary source-blocked metrics and calibration"),
    "E004": ("experiments/cycle4_robustness.json", "context rarity stability and error analyses"),
    "E005": ("experiments/cycle4_hong_confirmation.json", "quarantined-source confirmation"),
    "E006": ("experiments/cycle3_model_selection.json", "development model selection and chemistry ablation"),
    "E007": ("experiments/cycle3_odor_inverse_nested.json", "auxiliary odor inverse evaluation"),
    "E008": ("experiments/cycle3_inference_diagnostics.json", "Laplace and synthetic recovery checks"),
    "E009": ("experiments/cycle5_computational_profile.json", "computational timing"),
    "E010": ("data/processed/material_representations_v0.1.json", "material representation counts and schema"),
    "E011": ("data/curated/material_compound_evidence_v0.1.json", "analytical evidence and PubChem links"),
    "E012": ("literature/references.bib", "bibliographic metadata"),
    "E013": ("figures/figure_manifest.json", "figure provenance and hashes"),
    "E014": ("experiments/cycle6_stress_tests.json", "competitive baselines duplicate sensitivity and count recalibration"),
    "E015": ("experiments/cycle6_case_study.json", "deterministically selected case-level reconstruction"),
    "E016": ("figures/cycle6_figure_manifest.json", "post-freeze stress-test figure provenance"),
}

NUMERIC_ANCHORS = [
    ("N001", "corpus_formula_count", "91", "E001"),
    ("N002", "screened_candidate_count", "120", "E001"),
    ("N003", "excluded_candidate_count", "29", "E001"),
    ("N004", "corpus_work_count", "six work groups", "E001"),
    ("N005", "corpus_material_count", "81 canonical aromatic materials", "E001"),
    ("N006", "development_formula_count", "85 formulas", "E001,E002"),
    ("N007", "development_material_count", "80 materials", "E001,E002"),
    ("N008", "primary_frequency_hidden_f1", "0.339", "E003"),
    ("N009", "primary_graph_hidden_f1", "0.365", "E003"),
    ("N010", "primary_full_hidden_f1", "0.366", "E003"),
    ("N011", "full_minus_frequency_f1", "0.0278", "E003"),
    ("N012", "full_minus_graph_f1", "0.0010", "E003"),
    ("N013", "brier", "0.0429", "E003"),
    ("N014", "ece", "0.0236", "E003"),
    ("N015", "count_mae", "1.190", "E003"),
    ("N016", "count_bias", "0.883", "E003"),
    ("N017", "count_interval_coverage", "64.2%", "E003"),
    ("N018", "ratio_interval_coverage", "91.2%", "E003"),
    ("N019", "common_material_recall", "0.573", "E004"),
    ("N020", "rare_material_recall", "0.056", "E004"),
    ("N021", "hong_full_hidden_f1", "0.577", "E005"),
    ("N022", "t2_odor_knn_wj", "0.2913", "E007"),
    ("N023", "t2_model_wj", "0.2824", "E007"),
    ("N024", "laplace_mh_mae", "0.0016", "E008"),
    ("N025", "fit_median_seconds", "0.115 s", "E009"),
    ("N026", "prediction_median_ms", "1.70 ms", "E009"),
    ("N027", "formula_knn_hidden_f1", "0.343", "E014"),
    ("N028", "puresvd_hidden_f1", "0.334", "E014"),
    ("N029", "high_similarity_excluded_count", "Nine formulas", "E014"),
    ("N030", "sensitivity_graph_hidden_f1", "0.348", "E014"),
    ("N031", "sensitivity_frequency_hidden_f1", "0.322", "E014"),
    ("N032", "calibrated_count_coverage", "82.5%", "E014"),
    ("N033", "mass_constrained_weighted_jaccard", "0.427", "E014"),
    ("N034", "case_hidden_f1", "0.600", "E015"),
]

CLAIM_ANCHORS = [
    ("C001", "The curation pipeline screened 120 candidate formulas", "E001", "descriptive"),
    ("C002", "The directed graph reached F1 0.365", "E003", "primary"),
    ("C003", "The full decoder and graph-only scores were nearly identical", "E003", "primary"),
    ("C004", "Training frequency set a sharp recovery frontier", "E004", "secondary"),
    ("C005", "the highest bin had mean probability 0.931", "E003", "descriptive"),
    ("C006", "Pairwise chemical resemblance did not encode historical co-formulation", "E006,E007", "negative_control"),
    ("C007", "frequency reached hidden F1 0.469", "E005", "confirmation"),
    ("C008", "Training the locked decoder on all 85 development formulas", "E009", "descriptive"),
    ("C009", "A separate 20,000-step Metropolis-Hastings check", "E008", "diagnostic"),
    ("C010", "Formula k-nearest neighbours reached primary hidden F1 0.343", "E014", "post_freeze_baseline"),
    ("C011", "Removing all nine reduced graph F1 to 0.348", "E014", "sensitivity"),
    ("C012", "The expanded interval covered 82.5%", "E014", "recalibration"),
    ("C013", "For *Yinxiang fa*, six of eleven reference materials were observed", "E015", "case_study"),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paragraph_for(text: str, anchor: str) -> str:
    for paragraph in re.split(r"\n\s*\n", text):
        if anchor in paragraph:
            return " ".join(paragraph.split())
    raise ValueError(f"Claim anchor absent: {anchor}")


def _citation_numbers(body: str) -> set[int]:
    """Expand bracketed numeric citations, including en-dash ranges."""
    numbers: set[int] = set()
    for group in re.findall(r"\[([0-9,\-\u2013 ]+)\]", body):
        for token in (part.strip() for part in group.split(",")):
            if not token:
                continue
            match = re.fullmatch(r"(\d+)[\-\u2013](\d+)", token)
            if match:
                start, stop = map(int, match.groups())
                numbers.update(range(start, stop + 1))
            else:
                numbers.add(int(token))
    return numbers


def audit() -> dict:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].removeprefix("# ")
    abstract = text.split("## Abstract\n\n", 1)[1].split("\n\n## Introduction", 1)[0]
    title_words = re.findall(r"\b[\w'-]+\b", title)
    abstract_words = re.findall(r"\b[\w'-]+\b", abstract)
    required = [
        "## Abstract", "## Introduction", "## Results", "## Discussion", "## Methods",
        "## Data availability", "## Code availability", "## Author contributions",
        "## Competing interests", "## References", "## Figure legends",
    ]
    missing_sections = [section for section in required if section not in text]
    discussion = text.split("## Discussion", 1)[1].split("## Methods", 1)[0]
    discussion_subheadings = re.findall(r"^### .+$", discussion, flags=re.MULTILINE)
    cjk = re.findall(r"[\u3400-\u9fff]", text)
    missing_numeric = [identifier for identifier, _, rendered, _ in NUMERIC_ANCHORS if rendered not in text]
    manuscript_body, reference_tail = text.split("## References", 1)
    reference_block = reference_tail.split("## Figure legends", 1)[0]
    reference_numbers = [int(value) for value in re.findall(r"^(\d+)\.", reference_block, re.MULTILINE)]
    if reference_numbers != list(range(1, len(reference_numbers) + 1)):
        raise ValueError("Reference numbering is not sequential")
    cited_numbers = _citation_numbers(manuscript_body)
    missing_references = sorted(cited_numbers - set(reference_numbers))
    uncited_references = sorted(set(reference_numbers) - cited_numbers)

    bib_text = (RESEARCH_ROOT / "literature" / "references.bib").read_text(encoding="utf-8")
    bib_keys = re.findall(r"^@\w+\{([^,]+),", bib_text, flags=re.MULTILINE)
    duplicate_bib_keys = sorted({key for key in bib_keys if bib_keys.count(key) > 1})
    unresolved_bib_fields = re.findall(r"\b(?:Unknown|TBD|TODO)\b", bib_text, flags=re.IGNORECASE)

    source_rows = []
    for evidence_id, (relative, role) in SOURCES.items():
        path = RESEARCH_ROOT / relative
        if not path.exists():
            raise FileNotFoundError(path)
        source_rows.append({
            "evidence_id": evidence_id,
            "path": relative,
            "sha256": _sha256(path),
            "role": role,
            "verification_state": "local_artifact_hash_verified",
        })

    claim_rows = []
    for claim_id, anchor, evidence_ids, intent in CLAIM_ANCHORS:
        paragraph = _paragraph_for(text, anchor)
        claim_rows.append({
            "claim_id": claim_id,
            "claim_sha256": hashlib.sha256(paragraph.encode("utf-8")).hexdigest(),
            "anchor": anchor,
            "evidence_ids": evidence_ids,
            "analysis_intent": intent,
        })

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    source_path = REGISTRY_DIR / "source_manifest.json"
    source_path.write_text(json.dumps({"schema_version": "0.1", "sources": source_rows}, indent=2, sort_keys=True), encoding="utf-8")
    claims_path = REGISTRY_DIR / "claims.csv"
    with claims_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(claim_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(claim_rows)
    consistency_path = REGISTRY_DIR / "consistency_manifest.json"
    consistency_path.write_text(json.dumps({
        "schema_version": "0.1",
        "manuscript_sha256": _sha256(MANUSCRIPT),
        "numeric_facts": [
            {"fact_id": i, "concept": concept, "rendered_value": rendered, "evidence_ids": evidence}
            for i, concept, rendered, evidence in NUMERIC_ANCHORS
        ],
    }, indent=2, sort_keys=True), encoding="utf-8")
    result = {
        "title_word_count": len(title_words),
        "abstract_word_count": len(abstract_words),
        "reference_count": len(reference_numbers),
        "cited_reference_count": len(cited_numbers),
        "missing_references": missing_references,
        "uncited_references": uncited_references,
        "duplicate_bib_keys": duplicate_bib_keys,
        "unresolved_bib_field_count": len(unresolved_bib_fields),
        "missing_sections": missing_sections,
        "discussion_subheadings": discussion_subheadings,
        "cjk_character_count": len(cjk),
        "missing_numeric_anchors": missing_numeric,
        "placeholder_count": text.count("[" + "Insert") + text.count("[" + "Add verified") + text.count("[" + "Author name"),
        "source_count": len(source_rows),
        "claim_count": len(claim_rows),
    }
    if len(title_words) > 15 or len(abstract_words) > 150:
        raise ValueError(f"Venue limits failed: {result}")
    if (missing_sections or discussion_subheadings or cjk or missing_numeric or missing_references
            or uncited_references or duplicate_bib_keys or unresolved_bib_fields):
        raise ValueError(f"Manuscript audit failed: {result}")
    return result


def main() -> None:
    print(json.dumps(audit(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
