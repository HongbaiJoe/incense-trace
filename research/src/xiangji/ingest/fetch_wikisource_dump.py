"""Fetch a bounded official Wikisource dump stream and preserve page revisions."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from xiangji.data import RESEARCH_ROOT

DUMP_DATE = "20260901"
DUMP_URL = (
    "https://dumps.wikimedia.org/zhwikisource/20260901/"
    "zhwikisource-20260901-pages-articles-multistream.xml.bz2"
)
INDEX_URL = (
    "https://dumps.wikimedia.org/zhwikisource/20260901/"
    "zhwikisource-20260901-pages-articles-multistream-index.txt.bz2"
)
INDEX_SHA256 = "28bc1f75468f53d25b4eae2de07420f9a2f2005e2e7f4d3f0b645b10aec5d0c5"
INDEX_SIZE_BYTES = 62_835_312
COLLECTIONS = {
    "xiangcheng": {
        "byte_start": 738_317_443,
        "byte_end": 738_880_946,
        "archive_sha256": "02c17c3e24f7638a0c3d4e895b33244f2740c66bac21b5ddbbdd53c9ea910014",
        "target_titles": {f"香乘 (四庫全書本)/卷{i:02d}" for i in range(14, 26)} | {"香乘 (四庫全書本)"},
        "default_dir": "xiangcheng_20260901",
        "catalog_note": "Ming compilation by Zhou Jiazhou; embedded works require work-level segmentation.",
    },
    "hong_xiangpu": {
        "byte_start": 738_317_443,
        "byte_end": 738_880_946,
        "archive_sha256": "02c17c3e24f7638a0c3d4e895b33244f2740c66bac21b5ddbbdd53c9ea910014",
        "target_titles": {
            "香譜 (四庫全書本)/卷上", "香譜 (四庫全書本)/卷下",
            "香譜 (四庫全書本)/全覽", "香譜 (四庫全書本)",
        },
        "default_dir": "hong_xiangpu_20260901",
        "catalog_note": "Traditionally attributed to Hong Chu; attribution is disputed and retained as metadata uncertainty.",
    },
    "chen_xiangpu": {
        "byte_start": 737_161_266,
        "byte_end": 737_579_793,
        "archive_sha256": "6c79dcb299f22961bcb59b03df31be009159bca4d590e7727b03230d5b7558b2",
        "target_titles": {f"陳氏香譜 (四庫全書本)/卷{i}" for i in range(1, 5)} | {
            "陳氏香譜 (四庫全書本)/全覽", "陳氏香譜 (四庫全書本)",
        },
        "default_dir": "chen_xiangpu_20260901",
        "catalog_note": "Four-volume Siku Quanshu witness attributed to Chen Jing.",
    },
}


def fetch_range(spec: dict) -> bytes:
    request = urllib.request.Request(
        DUMP_URL,
        headers={
            "Range": f"bytes={spec['byte_start']}-{spec['byte_end']}",
            "User-Agent": "Xiangji-CGIR/0.1 academic-research",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 206:
            raise RuntimeError(f"Server did not honor byte range; HTTP {response.status}")
        return response.read()


def parse_pages(archive: bytes, spec: dict) -> list[dict]:
    digest = hashlib.sha256(archive).hexdigest()
    if digest != spec["archive_sha256"]:
        raise ValueError(f"Dump stream checksum mismatch: {digest}")
    xml = bz2.decompress(archive).decode("utf-8")
    root = ET.fromstring(f"<dump>{xml}</dump>")
    pages = []
    for page in root.findall("page"):
        title = page.findtext("title")
        if title not in spec["target_titles"]:
            continue
        revision = page.find("revision")
        assert revision is not None
        pages.append({
            "title": title,
            "page_id": int(page.findtext("id", "0")),
            "revision_id": int(revision.findtext("id", "0")),
            "parent_revision_id": int(revision.findtext("parentid", "0")),
            "timestamp": revision.findtext("timestamp"),
            "wikimedia_sha1": revision.findtext("sha1"),
            "wikitext": revision.findtext("text", ""),
        })
    if {page["title"] for page in pages} != spec["target_titles"]:
        missing = spec["target_titles"] - {page["title"] for page in pages}
        raise ValueError(f"Expected Wikisource pages missing from dump stream: {sorted(missing)}")
    return pages


def write_snapshot(pages: list[dict], output_dir: Path, collection: str, spec: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_pages = []
    for page in sorted(pages, key=lambda row: row["title"]):
        slug = page["title"].split("/")[-1].replace(" ", "_")
        path = output_dir / f"{slug}.wiki"
        path.write_text(page["wikitext"], encoding="utf-8")
        metadata = {key: value for key, value in page.items() if key != "wikitext"}
        metadata["path"] = str(path.relative_to(RESEARCH_ROOT))
        base_url = "https://zh.wikisource.org/wiki/" + urllib.parse.quote(page["title"])
        metadata["source_url"] = base_url
        metadata["stable_revision_url"] = f"{base_url}?oldid={page['revision_id']}"
        manifest_pages.append(metadata)
    manifest = {
        "source": "Chinese Wikisource official multistream dump",
        "collection": collection,
        "dump_date": DUMP_DATE,
        "dump_url": DUMP_URL,
        "multistream_index_url": INDEX_URL,
        "multistream_index_sha256": INDEX_SHA256,
        "multistream_index_size_bytes": INDEX_SIZE_BYTES,
        "byte_range_inclusive": [spec["byte_start"], spec["byte_end"]],
        "compressed_stream_sha256": spec["archive_sha256"],
        "catalog_note": spec["catalog_note"],
        "rights": "Underlying historical work is public domain; Wikisource transcription is CC BY-SA 4.0.",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "pages": manifest_pages,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", choices=sorted(COLLECTIONS), default="xiangcheng")
    parser.add_argument("--archive", type=Path, help="Use an already downloaded bounded bzip2 stream")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    spec = COLLECTIONS[args.collection]
    output_dir = args.output_dir or (
        RESEARCH_ROOT / "data" / "sources" / "wikisource" / spec["default_dir"]
    )
    archive = args.archive.read_bytes() if args.archive else fetch_range(spec)
    pages = parse_pages(archive, spec)
    write_snapshot(pages, output_dir, args.collection, spec)
    print(json.dumps({"collection": args.collection, "pages": len(pages), "output_dir": str(output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
