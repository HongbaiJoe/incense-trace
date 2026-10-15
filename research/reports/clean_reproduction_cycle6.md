# Clean-environment reproduction report

Run date: 2026-09-08

A fresh copy used the locked environment and executed 11 commands. All commands exited zero. The test suite passed 112 tests. All 14 checked deterministic outputs matched the working release byte for byte.

## Commands

- `uv sync --frozen --all-groups`: exit 0
- `uv run python -m xiangji.evaluation.cycle6_stress_tests`: exit 0
- `uv run python -m xiangji.evaluation.case_study`: exit 0
- `uv run python -m xiangji.cycle6_assets`: exit 0
- `uv run python -m xiangji.manuscript_audit`: exit 0
- `uv run python -m xiangji.freeze_cycle2`: exit 0
- `uv run python -m xiangji.freeze_cycle5`: exit 0
- `uv run pytest -q`: exit 0
- `uv run python -m xiangji.manuscript_audit`: exit 0
- `uv run python -m xiangji.freeze_cycle2`: exit 0
- `uv run python -m xiangji.freeze_cycle5`: exit 0

## Environment

- platform: `macOS-14.5-arm64-arm-64bit-Mach-O`
- python: `3.14.6`
- uv: `uv 0.11.33 (fece32fc5 2026-07-28 aarch64-apple-darwin)`

## Hash comparison

| Artifact | Match | SHA-256 |
|---|---:|---|
| `experiments/cycle6_stress_tests.json` | yes | `c39e596b561213940c68c9112699b11bbf340b9798b6904d8945072fdc9af452` |
| `experiments/cycle6_case_study.json` | yes | `c2dec647e339f323a6d700a6fe30f0ee66d32758067a3f1bd9524059859e20b5` |
| `manuscript/tables/table8_case_study.csv` | yes | `eef31b4d1f388b2930bf549cab01dd9c33dab5597e924ee04d886c90e44658ce` |
| `manuscript/tables/table9_source_mapping.csv` | yes | `e94800b81aba26a8b26e508671a18c15c0c47e4f70d07da8f1afab8c98759fa4` |
| `manuscript/tables/table10_competitive_baselines.csv` | yes | `d50c57a72cea19c5ff84816b549eeb6e91b23e85f6cdcf112fdd4b3671735083` |
| `manuscript/tables/table11_near_duplicate_sensitivity.csv` | yes | `bf79661da6ff0057759c2b286455286b1ccfdc39903e368b989f6a0bb767e7f5` |
| `manuscript/tables/table12_count_recalibration.csv` | yes | `429adb802d27be86db3290d033de3229ee65887d98105ac0379ba667506481e4` |
| `figures/fig6_stress_tests.png` | yes | `b57efa4561e0f77d9fb93967d07d2b13ae8e4be3eae196bf23d4965f41938a28` |
| `figures/fig6_stress_tests.pdf` | yes | `4ae8ba1cf70209680a0d4b515bb88338a364c192179a59baa835a38ec5d3929e` |
| `figures/fig6_stress_tests.svg` | yes | `9bfd0e6ec058cbbc89a3af6bcf8139fa2e568d1bc387c4f6b75bb59c8b985eb6` |
| `figures/cycle6_figure_manifest.json` | yes | `6fbdd92a327f2bde3d750fefe6c76547b9ff29fecd2f8d16bc795a9952306bed` |
| `manuscript/registries/source_manifest.json` | yes | `2a2bc8446cc06a77b527d8e4c3819d352decb703de28d4b40de5ea6b4b65fcd9` |
| `manuscript/registries/claims.csv` | yes | `bae78a6d8b14297062e8d4cce16928781d05940559c006bec70ecfd42c3641b1` |
| `manuscript/registries/consistency_manifest.json` | yes | `57dd5552715bc283395fe897012df9a8fec122667dd68f74f1353722425efb03` |
