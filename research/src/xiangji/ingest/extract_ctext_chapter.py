"""Extract a manually scoped set of public-domain formulas from one saved CText page."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

from xiangji.data import RESEARCH_ROOT

SOURCE_URL = "https://ctext.org/wiki.pl?chapter=360607&if=gb"
SOURCE_URN = "ctp:ws360607"
FORMULA_RANGES = {
    126: 128,
    129: 132,
    133: 134,
    135: 136,
    137: 138,
    139: 141,
    142: 143,
    144: 145,
    146: 147,
    148: 150,
    155: 156,
}


def parse_rows(document: str) -> dict[int, str]:
    rows = {}
    for paragraph, block in re.findall(r'<tr class="result" id="p(\d+)">(.*?)</tr>', document, re.S):
        cells = re.findall(r'<td class="ctext"[^>]*>(.*?)</td>', block, re.S)
        if not cells:
            continue
        text = html.unescape(re.sub(r"<[^>]+>", "", cells[-1])).strip()
        rows[int(paragraph)] = text
    return rows


def extract_records(rows: dict[int, str]) -> list[dict]:
    records = []
    for start, end in FORMULA_RANGES.items():
        missing = [paragraph for paragraph in range(start, end + 1) if paragraph not in rows]
        if missing:
            raise ValueError(f"Missing CText paragraphs: {missing}")
        title = rows[start]
        raw = "\n".join(rows[paragraph] for paragraph in range(start, end + 1))
        key = f"{SOURCE_URN}:p{start}-p{end}:{title}"
        records.append({
            "candidate_id": hashlib.sha1(key.encode()).hexdigest()[:16],
            "page_title": "遵生八箋/燕閒清賞箋中卷",
            "revision_id": None,
            "paragraph_start": start,
            "paragraph_end": end,
            "line_start": start,
            "line_end": end,
            "formula_title_candidate": title,
            "raw_wikitext": raw,
            "anchor_count": None,
            "quantity_expression_count": None,
            "status": "candidate_unverified",
            "collection": "zunsheng_bajian",
            "witness_id": "ctext-ctp-ws360607-access-20260906",
            "source_path": None,
            "source_url": SOURCE_URL,
            "stable_revision_url": f"{SOURCE_URL}#p{start}",
            "source_urn": SOURCE_URN,
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path, required=True, help="One manually downloaded CText chapter page")
    args = parser.parse_args()
    rows = parse_rows(args.html.read_text(encoding="utf-8"))
    records = extract_records(rows)
    output = {
        "generator": "xiangji.ingest.extract_ctext_chapter v0.1",
        "candidate_count": len(records),
        "source": "Chinese Text Project, one manually scoped chapter page",
        "source_url": SOURCE_URL,
        "source_urn": SOURCE_URN,
        "access_date": "2026-09-06",
        "rights_note": (
            "Underlying historical text is public domain. CText requests citation and prohibits bulk automated downloading; "
            "redistribution status of this digital transcription must be reviewed before dataset release."
        ),
        "raw_html_sha256": hashlib.sha256(args.html.read_bytes()).hexdigest(),
        "status": "manually scoped candidate records; not gold data",
        "records": records,
    }
    target = RESEARCH_ROOT / "data" / "interim" / "zunsheng_bajian_formula_candidates.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
