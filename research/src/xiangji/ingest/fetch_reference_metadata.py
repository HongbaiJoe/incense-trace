"""Fetch and verify bibliographic metadata for analytical-evidence sources.

This networked command is intentionally separate from the offline data build.
It creates a normalized metadata snapshot and a compact verification report.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from xiangji.data import RESEARCH_ROOT

USER_AGENT = "Xiangji-CGIR/0.1 (bibliographic verification; research prototype)"


def normalized_title(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return "".join(character.casefold() for character in value if character.isalnum())


def request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def crossref_record(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    message = request_json(url)["message"]
    published = message.get("published", {}).get("date-parts", [[]])[0]
    return {
        "provider": "Crossref",
        "query_url": url,
        "doi": message.get("DOI"),
        "title": (message.get("title") or [None])[0],
        "authors": [
            {"given": author.get("given"), "family": author.get("family")}
            for author in message.get("author", [])
        ],
        "published_date_parts": published,
        "journal": (message.get("container-title") or [None])[0],
        "volume": message.get("volume"),
        "issue": message.get("issue"),
        "page": message.get("page") or message.get("article-number"),
    }


def europe_pmc_record(pmid: str) -> dict:
    query = urllib.parse.urlencode(
        {"query": f"EXT_ID:{pmid}", "format": "json", "pageSize": 3, "resultType": "core"}
    )
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query
    results = request_json(url)["resultList"]["result"]
    exact = next((record for record in results if record.get("pmid") == str(pmid)), None)
    if exact is None:
        raise LookupError(f"Europe PMC returned no exact PMID match for {pmid}")
    return {
        "provider": "Europe PMC",
        "query_url": url,
        "doi": exact.get("doi"),
        "pmid": exact.get("pmid"),
        "pmcid": exact.get("pmcid"),
        "title": exact.get("title"),
        "authors": exact.get("authorString"),
        "published_date_parts": [int(exact["pubYear"])],
        "journal": exact.get("journalTitle"),
        "volume": exact.get("journalVolume"),
        "issue": exact.get("issue"),
        "page": exact.get("pageInfo"),
    }


def compare(source: dict, metadata: dict) -> dict:
    metadata_year = metadata["published_date_parts"][0] if metadata["published_date_parts"] else None
    title_match = normalized_title(source["title"]) == normalized_title(metadata["title"] or "")
    year_match = source["year"] == metadata_year
    return {
        "source_id": source["source_id"],
        "identifier": source.get("doi") or f"PMID:{source.get('pmid')}",
        "title_exact_after_normalization": title_match,
        "source_year": source["year"],
        "metadata_year": metadata_year,
        "year_match": year_match,
        "status": "verified" if title_match and year_match else "warning",
        "warning": None
        if year_match
        else "Source uses issue/citation year while provider metadata records an earlier online-first year."
    }


def render_report(records: list[dict]) -> str:
    lines = [
        "# Analytical-source bibliographic verification v0.1",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Titles are compared after Unicode case folding, HTML removal and punctuation removal. "
        "A year warning is retained when Crossref records an online-first year earlier than the citation/issue year.",
        "",
        "| Source | Identifier | Title | Year | Status |",
        "|---|---|---:|---:|---|",
    ]
    for record in records:
        check = record["verification"]
        year = "match" if check["year_match"] else f"{check['source_year']} vs {check['metadata_year']}"
        lines.append(
            f"| {check['source_id']} | `{check['identifier']}` | "
            f"{'match' if check['title_exact_after_normalization'] else 'mismatch'} | {year} | {check['status']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A verified row confirms bibliographic identity, not the scientific validity of every analytical result. "
            "Statement-level evidence remains tied to the locator, specimen, preparation and analytical method stored "
            "in `material_compound_evidence_v0.1.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    source_path = RESEARCH_ROOT / "data" / "curated" / "material_compound_evidence_v0.1.json"
    sources = json.loads(source_path.read_text(encoding="utf-8"))["sources"]
    records = []
    for source in sources:
        if source.get("doi"):
            metadata = crossref_record(source["doi"])
        elif source.get("pmid"):
            metadata = europe_pmc_record(source["pmid"])
        else:
            raise ValueError(f"source lacks DOI and PMID: {source['source_id']}")
        records.append({"source": source, "metadata": metadata, "verification": compare(source, metadata)})

    snapshot = {
        "schema_version": "0.1",
        "access_date": args.date,
        "source_registry": str(source_path.relative_to(RESEARCH_ROOT)),
        "record_count": len(records),
        "records": records,
    }
    target_dir = RESEARCH_ROOT / "data" / "sources" / "literature"
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = target_dir / f"crossref_europepmc_{args.date}.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = RESEARCH_ROOT / "reports" / "reference_verification_v0.1.md"
    report_path.write_text(render_report(records), encoding="utf-8")
    warnings = sum(record["verification"]["status"] == "warning" for record in records)
    print(json.dumps({"records": len(records), "warnings": warnings, "snapshot": str(snapshot_path), "report": str(report_path)}))


if __name__ == "__main__":
    main()
