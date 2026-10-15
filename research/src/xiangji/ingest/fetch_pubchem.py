"""Fetch a versioned molecular vocabulary through the approved PubChem wrapper."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

from xiangji.data import RESEARCH_ROOT


def run_wrapper(wrapper: Path, command: str, value: str, output: Path) -> None:
    if output.exists():
        return
    args = ["uv", "run", str(wrapper), command]
    args.extend((["--name", value] if command == "resolve" else ["--cid", value]))
    args.extend(["--output", str(output)])
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wrapper", type=Path, required=True)
    args = parser.parse_args()
    wrapper = args.wrapper.resolve()
    if not wrapper.is_file():
        raise FileNotFoundError(wrapper)

    seed_path = RESEARCH_ROOT / "data" / "raw" / "compound_seeds.json"
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))["compounds"]
    output_dir = RESEARCH_ROOT / "data" / "sources" / "pubchem" / "2026-09-06"
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, seed in enumerate(seeds, 1):
        stem = f"{index:03d}"
        resolve_path = output_dir / f"{stem}_resolve.json"
        run_wrapper(wrapper, "resolve", seed["name"], resolve_path)
        resolution = json.loads(resolve_path.read_text(encoding="utf-8"))
        properties = resolution["properties"]["PropertyTable"]["Properties"][0]
        cid = str(properties["CID"])
        property_path = output_dir / f"{stem}_properties.json"
        synonym_path = output_dir / f"{stem}_synonyms.json"
        run_wrapper(wrapper, "properties", cid, property_path)
        run_wrapper(wrapper, "synonyms", cid, synonym_path)
        property_row = json.loads(property_path.read_text(encoding="utf-8"))["PropertyTable"]["Properties"][0]
        synonym_data = json.loads(synonym_path.read_text(encoding="utf-8"))
        synonyms = synonym_data["InformationList"]["Information"][0].get("Synonym", [])
        records.append({
            "query_name": seed["name"],
            "tags": seed["tags"],
            "cid": int(cid),
            "canonical_smiles": properties.get("SMILES"),
            "connectivity_smiles": properties.get("ConnectivitySMILES"),
            "inchikey": properties.get("InChIKey"),
            "molecular_formula": property_row.get("MolecularFormula"),
            "molecular_weight": property_row.get("MolecularWeight"),
            "xlogp": property_row.get("XLogP"),
            "exact_mass": property_row.get("ExactMass"),
            "tpsa": property_row.get("TPSA"),
            "hbond_donor_count": property_row.get("HBondDonorCount"),
            "hbond_acceptor_count": property_row.get("HBondAcceptorCount"),
            "rotatable_bond_count": property_row.get("RotatableBondCount"),
            "synonym_match": seed["name"].casefold() in {str(value).casefold() for value in synonyms},
            "raw_files": [resolve_path.name, property_path.name, synonym_path.name],
        })

    manifest = {
        "schema_version": "0.1",
        "source": "PubChem PUG REST via pubchem_database skill wrapper",
        "source_url": "https://pubchem.ncbi.nlm.nih.gov/",
        "access_date": str(date.today()),
        "wrapper_sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        "seed_sha256": hashlib.sha256(seed_path.read_bytes()).hexdigest(),
        "record_count": len(records),
        "scope_note": "Tags are vocabulary seeds, not material abundance evidence.",
        "records": records,
    }
    target = RESEARCH_ROOT / "data" / "interim" / "pubchem_compounds_v0.1.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
