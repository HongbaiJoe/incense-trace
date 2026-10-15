"""Rebuild Cycle 6 in a fresh locked environment and compare deterministic outputs."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from xiangji.data import RESEARCH_ROOT


COMMANDS = (
    ("uv", "sync", "--frozen", "--all-groups"),
    ("uv", "run", "python", "-m", "xiangji.evaluation.cycle6_stress_tests"),
    ("uv", "run", "python", "-m", "xiangji.evaluation.case_study"),
    ("uv", "run", "python", "-m", "xiangji.cycle6_assets"),
    ("uv", "run", "python", "-m", "xiangji.manuscript_audit"),
    ("uv", "run", "python", "-m", "xiangji.freeze_cycle2"),
    ("uv", "run", "python", "-m", "xiangji.freeze_cycle5"),
    ("uv", "run", "pytest", "-q"),
    ("uv", "run", "python", "-m", "xiangji.manuscript_audit"),
    ("uv", "run", "python", "-m", "xiangji.freeze_cycle2"),
    ("uv", "run", "python", "-m", "xiangji.freeze_cycle5"),
)

DETERMINISTIC_OUTPUTS = (
    "experiments/cycle6_stress_tests.json",
    "experiments/cycle6_case_study.json",
    "manuscript/tables/table8_case_study.csv",
    "manuscript/tables/table9_source_mapping.csv",
    "manuscript/tables/table10_competitive_baselines.csv",
    "manuscript/tables/table11_near_duplicate_sensitivity.csv",
    "manuscript/tables/table12_count_recalibration.csv",
    "figures/fig6_stress_tests.png",
    "figures/fig6_stress_tests.pdf",
    "figures/fig6_stress_tests.svg",
    "figures/cycle6_figure_manifest.json",
    "manuscript/registries/source_manifest.json",
    "manuscript/registries/claims.csv",
    "manuscript/registries/consistency_manifest.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_source(target: Path) -> None:
    ignored = shutil.ignore_patterns(
        ".venv", ".pytest_cache", "__pycache__", "submission", "*.pyc",
        "cycle6_release_manifest.json",
    )
    shutil.copytree(RESEARCH_ROOT, target, ignore=ignored, dirs_exist_ok=True)


def _portable_log(text: str, *, clone: Path, temporary: str) -> str:
    """Remove machine-specific absolute paths from the archived command tails."""
    replacements = (
        (str(clone.resolve()), "<clean-research>"),
        (str(Path(temporary).resolve()), "<temporary>"),
        (str(RESEARCH_ROOT.resolve()), "<working-research>"),
        (str(clone), "<clean-research>"),
        (temporary, "<temporary>"),
        (str(RESEARCH_ROOT), "<working-research>"),
    )
    for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    return text


def _render_report(payload: dict) -> str:
    lines = [
        "# Clean-environment reproduction report",
        "",
        f"Run date: {payload['run_date']}",
        "",
        f"A fresh copy used the locked environment and executed {len(payload['commands'])} commands. "
        f"All commands exited zero. The test suite passed {payload['tests_passed']} tests. "
        f"All {payload['matching_output_count']} checked deterministic outputs matched the working release byte for byte.",
        "",
        "## Commands",
        "",
    ]
    lines.extend(f"- `{' '.join(row['command'])}`: exit {row['exit_code']}" for row in payload["commands"])
    lines.extend(["", "## Environment", ""])
    for key, value in payload["environment"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Hash comparison", "", "| Artifact | Match | SHA-256 |", "|---|---:|---|"])
    for row in payload["outputs"]:
        lines.append(f"| `{row['path']}` | {'yes' if row['match'] else 'no'} | `{row['original_sha256']}` |")
    lines.append("")
    return "\n".join(lines)


def run() -> dict:
    uv = shutil.which("uv")
    if uv is None:
        raise FileNotFoundError("uv executable not found")
    command_rows = []
    with tempfile.TemporaryDirectory(prefix="xiangji-clean-") as temporary:
        clone = Path(temporary) / "research"
        _copy_source(clone)
        environment = dict(os.environ)
        environment["UV_CACHE_DIR"] = str(Path(temporary) / "uv-cache")
        for command in COMMANDS:
            result = subprocess.run(command, cwd=clone, env=environment, text=True, capture_output=True)
            command_rows.append({
                "command": list(command), "exit_code": result.returncode,
                "stdout_tail": _portable_log(result.stdout[-4000:], clone=clone, temporary=temporary),
                "stderr_tail": _portable_log(result.stderr[-4000:], clone=clone, temporary=temporary),
            })
            if result.returncode:
                raise RuntimeError(f"Clean reproduction failed: {command}\n{result.stdout}\n{result.stderr}")
        outputs = []
        for relative in DETERMINISTIC_OUTPUTS:
            original, reproduced = RESEARCH_ROOT / relative, clone / relative
            original_hash, reproduced_hash = _sha256(original), _sha256(reproduced)
            outputs.append({
                "path": relative, "original_sha256": original_hash,
                "reproduced_sha256": reproduced_hash, "match": original_hash == reproduced_hash,
            })
        if not all(row["match"] for row in outputs):
            failed = [row["path"] for row in outputs if not row["match"]]
            for relative in failed:
                debug_name = relative.replace("/", "__")
                shutil.copy2(clone / relative, Path(tempfile.gettempdir()) / f"xiangji_reproduced__{debug_name}")
                shutil.copy2(RESEARCH_ROOT / relative, Path(tempfile.gettempdir()) / f"xiangji_original__{debug_name}")
            raise ValueError(f"Clean output hashes differ: {failed}")
    test_output = next(row["stdout_tail"] for row in command_rows if row["command"][2:3] == ["pytest"])
    match = __import__("re").search(r"(\d+) passed", test_output)
    payload = {
        "schema_version": "0.1", "run_date": date.today().isoformat(),
        "environment": {
            "platform": platform.platform(), "python": platform.python_version(),
            "uv": subprocess.run((uv, "--version"), text=True, capture_output=True, check=True).stdout.strip(),
        },
        "commands": command_rows, "tests_passed": int(match.group(1)) if match else None,
        "matching_output_count": sum(row["match"] for row in outputs), "outputs": outputs,
    }
    json_path = RESEARCH_ROOT / "reports/clean_reproduction_cycle6.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = RESEARCH_ROOT / "reports/clean_reproduction_cycle6.md"
    report_path.write_text(_render_report(payload), encoding="utf-8")
    return payload


def main() -> None:
    payload = run()
    print(json.dumps({"tests_passed": payload["tests_passed"], "matching_output_count": payload["matching_output_count"]}, indent=2))


if __name__ == "__main__":
    main()
