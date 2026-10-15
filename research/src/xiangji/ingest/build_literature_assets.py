"""Build the bounded Cycle 2 evidence map from verified local source records."""

from __future__ import annotations

import csv
import json
import re

from xiangji.data import RESEARCH_ROOT

METHOD_SOURCES = [
    {
        "source_id": "aleixandre2024_scent_creation", "year": 2024,
        "title": "Automatic scent creation by cheminformatics method",
        "doi": "10.1038/s41598-024-82654-7", "stream": "inverse_scent_design",
        "task": "odor descriptors to essential-oil component ratios",
        "method": "mass-spectral components, forward DNN and gradient inverse optimization",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "sisson2025_blends", "year": 2025,
        "title": "Deep Learning for Odor Prediction on Aroma-Chemical Blends",
        "doi": "10.1021/acsomega.4c07078", "stream": "odor_mixtures",
        "task": "two molecular graphs to blend descriptors",
        "method": "permutation-invariant graph neural networks",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "lee2023_pom", "year": 2023,
        "title": "A Principal Odor Map Unifies Diverse Tasks in Olfactory Perception",
        "doi": "10.1126/science.ade4401", "stream": "computational_olfaction",
        "task": "molecular graph to perceptual embedding and descriptors",
        "method": "message-passing graph neural network with prospective validation",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "hamel2024_pyrfume", "year": 2024,
        "title": "Pyrfume: A Window to the World's Olfactory Data",
        "doi": "10.1038/s41597-024-04051-z", "stream": "olfactory_data",
        "task": "heterogeneous olfactory datasets to standardized archive",
        "method": "data model, provenance and curation",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "gutierrez2018_semantic", "year": 2018,
        "title": "Predicting natural language descriptions of mono-molecular odorants",
        "doi": "10.1038/s41467-018-07439-9", "stream": "computational_olfaction",
        "task": "molecular features to natural-language odor descriptions",
        "method": "semantic and psychophysical prediction",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "keller2017_dream", "year": 2017,
        "title": "Predicting human olfactory perception from chemical features of odor molecules",
        "doi": "10.1126/science.aal2014", "stream": "computational_olfaction",
        "task": "molecular features to perceptual ratings",
        "method": "crowdsourced challenge and ensemble prediction",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "debnath2021_mass_spectra", "year": 2021,
        "title": "Predicting Odor Perception of Mixed Scent from Mass Spectrometry",
        "doi": "10.1149/1945-7111/ac33e0", "stream": "computational_olfaction",
        "task": "mass spectra to odor descriptors",
        "method": "spectral feature prediction",
        "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "thomasdanguin2014_mixtures", "year": 2014,
        "title": "The perception of odor objects in everyday life: a review on the processing of odor mixtures",
        "doi": "10.3389/fpsyg.2014.00504", "stream": "odor_mixtures",
        "task": "odor-mixture perception synthesis",
        "method": "review of configural and elemental mixture processing",
        "historical_text": 0, "chemistry": 0, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "sorbi2026_historical_ner", "year": 2026,
        "title": "Weakly Supervised Named Entity Recognition for Low-Resource Historical Texts",
        "url": "https://aclanthology.org/2026.latechclfl-1.6/", "stream": "historical_nlp",
        "task": "low-resource historical text to entity spans",
        "method": "weak supervision for historical named-entity recognition",
        "historical_text": 1, "chemistry": 0, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 1,
    },
    {
        "source_id": "goel2024_recipe_ner", "year": 2024,
        "title": "Deep Learning Based Named Entity Recognition Models for Recipes",
        "url": "https://aclanthology.org/2024.lrec-main.406/", "stream": "recipe_information_extraction",
        "task": "recipe phrases to ingredient, quantity, unit and state entities",
        "method": "supervised NER with augmented annotations",
        "historical_text": 0, "chemistry": 0, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
    },
    {
        "source_id": "tyagi2023_conformal", "year": 2023,
        "title": "Multi-label Classification under Uncertainty: A Tree-based Conformal Prediction Approach",
        "url": "https://proceedings.mlr.press/v204/tyagi23a.html", "stream": "uncertainty_quantification",
        "task": "multilabel scores to calibrated prediction sets",
        "method": "split conformal inference with hierarchical testing",
        "historical_text": 0, "chemistry": 0, "name_uncertainty": 0, "posterior_output": 1, "source_shift": 0,
    },
]


def safe_bib(value: str) -> str:
    return re.sub(r"[{}]", "", value).replace("&", "\\&")


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    literature_dir = RESEARCH_ROOT / "literature"
    literature_dir.mkdir(exist_ok=True)
    metadata_path = RESEARCH_ROOT / "data" / "sources" / "literature" / "crossref_europepmc_2026-09-07.json"
    registry_path = RESEARCH_ROOT / "data" / "curated" / "material_compound_evidence_v0.1.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    analytical = []
    for row in registry["sources"]:
        analytical.append({
            "source_id": row["source_id"], "year": row["year"], "title": row["title"],
            "doi": row.get("doi", ""), "url": row["url"], "stream": "material_analytical_chemistry",
            "task": "material specimen to identified volatile components",
            "method": "source-specific GC-MS, GC-O or isolation evidence; see evidence registry",
            "historical_text": 0, "chemistry": 1, "name_uncertainty": 0, "posterior_output": 0, "source_shift": 0,
            "evidence_access": row["evidence_access"],
        })
    included = METHOD_SOURCES + analytical
    screening_rows = [{
        "source_id": row["source_id"], "title": row["title"], "year": row["year"],
        "stream": row["stream"], "decision": "included", "exclusion_reason": "",
        "identifier": row.get("doi", ""), "url": row.get("url") or f"https://doi.org/{row['doi']}",
        "evidence_access": row.get("evidence_access", "method_or_results_checked_in_seed_map"),
    } for row in included]
    screening_rows.extend([
        {"source_id": "frontiers2026_excluded", "title": "Candidate analytical paper with insufficient identification evidence", "year": 2026, "stream": "material_analytical_chemistry", "decision": "excluded", "exclusion_reason": "compound identifications lacked sufficient retention-index or identifier support for current schema", "identifier": "10.3389/fnut.2026.1764021", "url": "https://doi.org/10.3389/fnut.2026.1764021", "evidence_access": "full_text_checked"},
        {"source_id": "song_incense_database_excluded", "title": "song-incense-database repository", "year": "", "stream": "historical_formula_data", "decision": "excluded", "exclusion_reason": "no standard license and contains model-inferred formula records", "identifier": "", "url": "", "evidence_access": "repository_audited"},
    ])
    write_csv(literature_dir / "screening.csv", list(screening_rows[0]), screening_rows)

    evidence_rows = [{key: row.get(key, "") for key in (
        "source_id", "stream", "task", "method", "historical_text", "chemistry",
        "name_uncertainty", "posterior_output", "source_shift",
    )} for row in included]
    write_csv(literature_dir / "evidence_matrix.csv", list(evidence_rows[0]), evidence_rows)
    novelty_rows = [{key: row[key] for key in (
        "source_id", "title", "historical_text", "chemistry", "name_uncertainty", "posterior_output", "source_shift"
    )} for row in METHOD_SOURCES]
    novelty_rows.append({
        "source_id": "xiangji_cgir_proposed", "title": "Xiangji-CGIR proposed full method",
        "historical_text": 1, "chemistry": 1, "name_uncertainty": 1, "posterior_output": 1, "source_shift": 1,
    })
    write_csv(literature_dir / "novelty_matrix.csv", list(novelty_rows[0]), novelty_rows)

    query_rows = [
        {"date": "2026-09-06", "provider": "Crossref and publisher/DOI resolution", "theme": "computational olfaction and inverse scent design", "query_or_method": "seed DOI resolution plus backward/forward citation leads from closest prior art", "records_retained": 8, "scope": "bounded method map; total hit count not retained"},
        {"date": "2026-09-06", "provider": "ACL Anthology and PMLR", "theme": "historical NLP, recipe NER and conformal multilabel prediction", "query_or_method": "venue search and direct record verification", "records_retained": 3, "scope": "bounded method map; total hit count not retained"},
        {"date": "2026-09-07", "provider": "Europe PMC", "theme": "material analytical chemistry", "query_or_method": "17 material-specific GC-MS/GC-O queries preserved in protocol/literature_search_log_2026-09-07.md", "records_retained": 17, "scope": "targeted evidence search"},
        {"date": "2026-09-07", "provider": "Crossref", "theme": "bibliographic verification", "query_or_method": "exact DOI metadata retrieval for analytical sources", "records_retained": 16, "scope": "metadata verification, not discovery"},
    ]
    write_csv(literature_dir / "search_log.csv", list(query_rows[0]), query_rows)

    metadata_by_id = {row["source"]["source_id"]: row["metadata"] for row in metadata["records"]}
    bib_entries = []
    for row in included:
        meta = metadata_by_id.get(row["source_id"], {})
        authors = " and ".join(
            (
                " ".join(filter(None, [author.get("given"), author.get("family")]))
                if isinstance(author, dict)
                else str(author)
            )
            for author in meta.get("authors", [])
        ) or "Unknown"
        fields = [
            f"  title = {{{safe_bib(row['title'])}}}", f"  year = {{{row['year']}}}",
            f"  author = {{{safe_bib(authors)}}}",
        ]
        if row.get("doi"):
            fields.append(f"  doi = {{{row['doi']}}}")
        if row.get("url"):
            fields.append(f"  url = {{{row['url']}}}")
        bib_entries.append("@article{" + row["source_id"] + ",\n" + ",\n".join(fields) + "\n}")
    # Keep the evidence-map export separate from the curated manuscript
    # bibliography. Rebuilding Cycle 2 must not erase later reference work.
    (literature_dir / "evidence_sources.bib").write_text("\n\n".join(bib_entries) + "\n", encoding="utf-8")

    flow = f"""# Cycle 2 evidence-map flow\n\nThis is a bounded, reproducible evidence map—not a PRISMA systematic review. Database-wide hit counts and a complete deduplication denominator were not retained during the seed search, so a PRISMA diagram would imply a search completeness that the present record cannot support.\n\n- Method papers retained after topic and methods checking: {len(METHOD_SOURCES)}\n- Primary analytical sources retained after statement-level evidence checking: {len(analytical)}\n- Explicit exclusions retained: 2\n- Total included records in the Cycle 2 evidence matrix: {len(included)}\n- Records with verified analytical-source metadata: {len(metadata['records'])}\n\nA submission-grade systematic review requires fresh, frozen searches in at least three comprehensive indexes, complete hit counts, deduplication IDs, title/abstract decisions, full-text exclusion reasons and backward/forward citation tracking. Institutional Web of Science, Scopus and CNKI coverage remains an external gate rather than being fabricated here.\n"""
    (literature_dir / "evidence_map_flow.md").write_text(flow, encoding="utf-8")
    print(json.dumps({"included": len(included), "excluded": 2, "method_sources": len(METHOD_SOURCES), "analytical_sources": len(analytical), "output": str(literature_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
