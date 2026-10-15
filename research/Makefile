.PHONY: cycle1 test audit baselines reproduce wikisource-download corpus molecular literature-metadata curation-preflight curated-reference source-splits cycle2-data cycle3-model cycle3-diagnostics cycle4-evaluate cycle5-manuscript cycle6-analysis cycle6-release verify-references export-submission export-latex audit-artwork audit-mathematics complete-paper clean-reproduction

cycle1:
	uv sync --group dev
	uv run python src/xiangji/legacy_v24.py
	uv run python -m xiangji.audit
	uv run python -m xiangji.evaluate
	uv run python -m xiangji.error_analysis
	uv run pytest tests -q

reproduce:
	uv run python src/xiangji/legacy_v24.py

audit:
	uv run python -m xiangji.audit

baselines:
	uv run python -m xiangji.evaluate

test:
	uv run pytest tests -q

wikisource-download:
	uv run python -m xiangji.ingest.fetch_wikisource_dump --collection xiangcheng
	uv run python -m xiangji.ingest.fetch_wikisource_dump --collection hong_xiangpu
	uv run python -m xiangji.ingest.fetch_wikisource_dump --collection chen_xiangpu

corpus:
	uv run python -m xiangji.ingest.extract_candidates --collection xiangcheng
	uv run python -m xiangji.ingest.audit_candidates --collection xiangcheng
	uv run python -m xiangji.ingest.extract_candidates --collection hong_xiangpu
	uv run python -m xiangji.ingest.audit_candidates --collection hong_xiangpu
	uv run python -m xiangji.ingest.extract_candidates --collection chen_xiangpu
	uv run python -m xiangji.ingest.audit_candidates --collection chen_xiangpu
	uv run python -m xiangji.normalization.recipes
	uv run python -m xiangji.normalization.genealogy
	uv run python -m xiangji.normalization.build_curation_batch

molecular:
	uv run python -m xiangji.representations.molecular
	uv run python -m xiangji.representations.material_chemistry
	uv run python -m xiangji.representations.build_material_representations

literature-metadata:
	uv run python -m xiangji.ingest.fetch_reference_metadata --date 2026-09-07
	uv run python -m xiangji.ingest.build_literature_assets

curation-preflight:
	uv run python -m xiangji.normalization.build_curation_preflight

curated-reference:
	uv run python -m xiangji.normalization.build_curated_reference

source-splits:
	uv run python -m xiangji.normalization.build_source_splits

cycle2-data: corpus molecular
	uv run python -m xiangji.ingest.build_literature_assets
	uv run python -m xiangji.normalization.build_curation_preflight
	uv run python -m xiangji.normalization.build_curated_reference
	uv run python -m xiangji.normalization.build_family_evidence_audit
	uv run python -m xiangji.normalization.build_source_splits
	uv run python -m xiangji.freeze_cycle2
	uv run pytest tests -q

cycle3-diagnostics:
	uv run python -m xiangji.evaluation.odor_inverse
	uv run python -m xiangji.evaluation.inference_diagnostics
	uv run python -m xiangji.evaluation.development_diagnostics
	uv run python -m xiangji.freeze_cycle3

cycle3-model:
	uv run python -m xiangji.evaluation.model_selection
	$(MAKE) cycle3-diagnostics
	uv run pytest tests -q

cycle4-evaluate:
	uv run python -m xiangji.evaluation.primary
	uv run python -m xiangji.evaluation.robustness
	uv run python -m xiangji.evaluation.hong_confirmation
	uv run python -m xiangji.freeze_cycle4
	uv run pytest tests -q

cycle5-manuscript:
	uv run python -m xiangji.evaluation.computational_profile
	uv run python -m xiangji.manuscript_assets
	uv run python -m xiangji.manuscript_audit
	uv run python -m xiangji.freeze_cycle2
	uv run python -m xiangji.freeze_cycle5

cycle6-analysis:
	uv run python -m xiangji.evaluation.cycle6_stress_tests
	uv run python -m xiangji.evaluation.case_study
	uv run python -m xiangji.cycle6_assets
	uv run python -m xiangji.manuscript_audit

verify-references:
	uv run python -m xiangji.reference_verification_cycle6 --date 2026-09-08

export-submission:
	uv run python -m xiangji.export_submission

export-latex:
	uv run python -m xiangji.export_latex

audit-artwork:
	uv run python -m xiangji.figure_submission_audit

audit-mathematics:
	uv run python -m xiangji.mathematical_audit

complete-paper:
	uv run python -m xiangji.complete_manuscript
	uv run python -m xiangji.export_submission
	uv run python -m xiangji.export_latex
	uv run python -m xiangji.mathematical_audit

clean-reproduction:
	uv run python -m xiangji.clean_reproduction

cycle6-release: cycle6-analysis
	uv run python -m xiangji.freeze_cycle2
	uv run python -m xiangji.freeze_cycle5
	uv run pytest tests -q
	uv run python -m xiangji.manuscript_audit
	uv run python -m xiangji.freeze_cycle2
	uv run python -m xiangji.freeze_cycle5
	uv run python -m xiangji.freeze_cycle6
