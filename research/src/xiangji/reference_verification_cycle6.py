"""Verify every numbered manuscript reference against a live primary registry."""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from difflib import SequenceMatcher

from xiangji.data import RESEARCH_ROOT
from xiangji.ingest.fetch_reference_metadata import crossref_record, europe_pmc_record, normalized_title


REFERENCE_KEYS = (
    "bembibre2017_smell_heritage", "lisena2022_odeuropa", "paolin2026_historical_smells",
    "lee2023_pom", "gutierrez2018_semantic", "keller2017_dream", "debnath2021_mass_spectra",
    "hamel2024_pyrfume", "sisson2025_blends", "aleixandre2024_scent_creation",
    "sorbi2026_historical_ner", "goel2024_recipe_ner", "zhao2018_bayesian_multilabel",
    "koh2021_wilds", "guo2017_calibration", "cover1967_nearest_neighbor",
    "cremonesi2010_topn", "angelopoulos2023_conformal", "aitchison1982_compositional",
    "rogers2010_morgan", "pedregosa2011_scikit", "ngan2020_agarwood",
    "fatima2019_sandalwood", "distefano2020_frankincense", "benhassine2021_clove",
    "firmino2018_cassia", "hu2017_cyperus", "han2017_ten_oils", "li2019_angelica_aroma",
    "gwari2013_costus", "zou2017_borneol", "li2016_musk", "xue2014_scrophularia",
    "farag2012_licorice", "fernandez2005_storax", "raza2024_fennel",
    "guo2016_camphor_tree", "miyazawa1996_rhubarb",
)

USER_AGENT = "Xiangji-CGIR/0.1 (complete manuscript reference verification)"


def parse_bibtex(text: str) -> dict[str, dict[str, str]]:
    entries = {}
    for match in re.finditer(r"@\w+\{([^,]+),\s*(.*?)\n\}", text, flags=re.DOTALL):
        key, body = match.groups()
        fields = {}
        for field in re.finditer(r"^\s*(\w+)\s*=\s*\{(.*)\},?\s*$", body, flags=re.MULTILINE):
            fields[field.group(1).casefold()] = field.group(2)
        entries[key] = fields
    return entries


def _page_record(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(1_500_000).decode("utf-8", errors="replace")
        final_url = response.geturl()
        status = response.status
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    page_title = html.unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else ""
    return {"provider": "publisher_page", "query_url": url, "resolved_url": final_url, "status_code": status,
            "title": page_title, "body": body}


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalized_title(left), normalized_title(right)).ratio()


def verify_entry(number: int, key: str, fields: dict[str, str]) -> dict:
    expected_title = fields["title"].replace("{{", "").replace("}}", "").replace("{", "").replace("}", "")
    expected_year = int(fields["year"])
    if fields.get("doi"):
        provider = crossref_record(fields["doi"])
        provider_title = provider.get("title") or ""
        provider_year = (provider.get("published_date_parts") or [None])[0]
        similarity = _similarity(expected_title, provider_title)
        identity_ok = similarity >= 0.82 and fields["doi"].casefold() == (provider.get("doi") or "").casefold()
        access_ok = True
    elif "pubmed.ncbi.nlm.nih.gov" in fields.get("url", ""):
        pmid = re.search(r"/(\d+)/?", fields["url"]).group(1)
        provider = europe_pmc_record(pmid)
        provider_title = provider.get("title") or ""
        provider_year = (provider.get("published_date_parts") or [None])[0]
        similarity = _similarity(expected_title, provider_title)
        identity_ok = similarity >= 0.82 and provider.get("pmid") == pmid
        access_ok = True
    else:
        provider = _page_record(fields["url"])
        provider_title = provider["title"]
        page_text = re.sub(r"<[^>]+>", " ", provider.pop("body"))
        similarity = max(_similarity(expected_title, provider_title), _similarity(expected_title, page_text[:10000]))
        identity_ok = normalized_title(expected_title) in normalized_title(page_text)
        provider_year = None
        access_ok = provider["status_code"] == 200
    year_state = "match" if provider_year == expected_year else ("not_exposed" if provider_year is None else "online_first_or_issue_difference")
    status = "verified" if identity_ok and access_ok else "failed"
    return {
        "reference_number": number, "bibtex_key": key, "expected_title": expected_title,
        "expected_year": expected_year, "identifier": fields.get("doi") or fields.get("url"),
        "provider": provider["provider"], "provider_title": provider_title,
        "provider_year": provider_year, "title_similarity": similarity, "year_state": year_state,
        "identity_ok": identity_ok, "access_ok": access_ok, "status": status,
        "query_url": provider["query_url"],
    }


def render_report(payload: dict) -> str:
    lines = [
        "# Complete manuscript reference verification",
        "",
        f"Generated: {payload['access_date']}",
        "",
        f"All {payload['reference_count']} numbered references were checked against Crossref or the cited primary record page. "
        "Title identity uses normalized exact containment for record pages and a declared similarity threshold for Crossref metadata.",
        "",
        "| Ref. | Key | Registry | Title similarity | Year | Status |",
        "|---:|---|---|---:|---|---|",
    ]
    for row in payload["records"]:
        lines.append(
            f"| {row['reference_number']} | `{row['bibtex_key']}` | {row['provider']} | "
            f"{row['title_similarity']:.3f} | {row['year_state']} | {row['status']} |"
        )
    lines.extend([
        "", "## Result", "",
        f"Verified: {payload['verified_count']}/{payload['reference_count']}. Failed: {payload['failed_count']}. "
        f"Year metadata differences: {payload['year_difference_count']}. Differences marked online-first or issue-year do not change reference identity.",
        "", "This audit establishes bibliographic identity and link resolution. Claim-level support is tracked separately in the manuscript claim registry and analytical evidence registry.", "",
    ])
    return "\n".join(lines)


def run(access_date: str) -> dict:
    entries = parse_bibtex((RESEARCH_ROOT / "literature/references.bib").read_text(encoding="utf-8"))
    missing = [key for key in REFERENCE_KEYS if key not in entries]
    if missing:
        raise ValueError(f"Missing manuscript bibliography keys: {missing}")
    records = [verify_entry(number, key, entries[key]) for number, key in enumerate(REFERENCE_KEYS, 1)]
    payload = {
        "schema_version": "0.1", "access_date": access_date, "reference_count": len(records),
        "verified_count": sum(row["status"] == "verified" for row in records),
        "failed_count": sum(row["status"] != "verified" for row in records),
        "year_difference_count": sum(row["year_state"] == "online_first_or_issue_difference" for row in records),
        "records": records,
    }
    output = RESEARCH_ROOT / "data/sources/literature" / f"manuscript_reference_verification_{access_date}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = RESEARCH_ROOT / "reports/reference_verification_cycle6.md"
    report.write_text(render_report(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    payload = run(args.date)
    print(json.dumps({key: payload[key] for key in ("reference_count", "verified_count", "failed_count", "year_difference_count")}, indent=2))


if __name__ == "__main__":
    main()
