# Release verification

Date: 2026-10-15. Checks were performed on an independent copy; the existing website and original repository were not changed.

| Check | Result |
| --- | --- |
| Locked website dependency installation | Passed |
| Production website build and data checks | Passed; 3 data tests |
| TypeScript checking (`npx tsc --noEmit`) | Passed |
| Browser-engine unit tests | Passed; 2 tests |
| Python tests after removing the restricted transcription candidate file | Passed; 141 tests |
| Python/TypeScript agreement | Eight fixture predictions agree within 1e-10 |
| Reference-data fingerprint | Matches the SHA-256 embedded in the website model |
| Research source preservation | All 79 files under `research/src/` match the source snapshot |
| Publication scan | No known credential pattern, private database, cache path, machine-specific absolute path, symlink, or file at or above 100 MiB found in staged files |

The scan checks common credential patterns; it is not a general security audit. Fresh visual browser tests, production database integration tests, full nested retraining, and manuscript compilation were not run for this packaging release. Their existing source scripts and archived results are included.

## Source snapshot

- Website: latest published version 15, last updated 2026-09-30; source commit `498eb8fe0d0642dd6b4fdf3fc48bf2e86df1653f`.
- Research: working files accompanying commit `eb36bf7f3be471acc360531d4032ebd1b237cc3a`, including the later V5 files present in that working tree. This is a file snapshot, not a claim that every included file was tracked in that commit.
- Exported model: `xiangji-v5-20260929`, 91 formulas, 81 material identifiers.

`SHA256_MANIFEST.json` records file fingerprints for the public snapshot, excluding the manifest itself. Archive tests may regenerate historical reports when rerun.

## Packaging changes

The public copy has a project-specific package name and README, an explicit engine-test command and dependency, portable optional browser-test paths, and portable manuscript input paths. The original hosting project identifier is omitted. Application components, numerical algorithms, fitted model data, images, and the current PDF are unchanged.

Excluded: dependencies, caches, visitor databases, internal design plans, private teacher-comment matrices, redundant high-resolution TIFF exports and rendered-page previews, and a CText transcription candidate file whose redistribution status is unresolved. Vector figures and their source data remain included.
