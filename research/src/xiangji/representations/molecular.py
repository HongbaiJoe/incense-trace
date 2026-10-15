"""Generate reproducible molecular descriptors and sparse Morgan fingerprints."""

from __future__ import annotations

import hashlib
import json

from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, rdFingerprintGenerator, rdMolDescriptors

from xiangji.data import RESEARCH_ROOT

FP_RADIUS = 2
FP_SIZE = 2048


def featurize(record: dict) -> dict:
    molecule = Chem.MolFromSmiles(record["canonical_smiles"])
    if molecule is None:
        raise ValueError(f"RDKit failed to parse CID {record['cid']}")
    Chem.SanitizeMol(molecule)
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS, fpSize=FP_SIZE)
    fingerprint = generator.GetFingerprint(molecule)
    canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    return {
        "cid": record["cid"],
        "query_name": record["query_name"],
        "inchikey": record["inchikey"],
        "inchikey_rdkit": Chem.MolToInchiKey(molecule),
        "molecular_formula_rdkit": rdMolDescriptors.CalcMolFormula(molecule),
        "canonical_isomeric_smiles_rdkit": canonical,
        "canonical_smiles_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "descriptors": {
            "MolWt": Descriptors.MolWt(molecule),
            "ExactMolWt": Descriptors.ExactMolWt(molecule),
            "MolLogP": Descriptors.MolLogP(molecule),
            "TPSA": Descriptors.TPSA(molecule),
            "NumHDonors": Descriptors.NumHDonors(molecule),
            "NumHAcceptors": Descriptors.NumHAcceptors(molecule),
            "NumRotatableBonds": Descriptors.NumRotatableBonds(molecule),
            "NumAromaticRings": Descriptors.NumAromaticRings(molecule),
            "FractionCSP3": Descriptors.FractionCSP3(molecule),
            "HeavyAtomCount": Descriptors.HeavyAtomCount(molecule),
        },
        "morgan_radius": FP_RADIUS,
        "morgan_size": FP_SIZE,
        "morgan_on_bits": list(fingerprint.GetOnBits()),
    }


def comparison(record: dict, features: dict) -> dict:
    rdkit_values = features["descriptors"]
    identity_checks = {
        "molecular_formula": record["molecular_formula"] == features["molecular_formula_rdkit"],
        "inchikey": record["inchikey"] == features["inchikey_rdkit"],
        "molecular_weight": abs(float(record["molecular_weight"]) - rdkit_values["MolWt"]) <= 0.15,
        "exact_mass": abs(float(record["exact_mass"]) - rdkit_values["ExactMolWt"]) <= 1e-5,
    }
    definition_sensitive_pairs = {
        "xlogp": (float(record["xlogp"]), rdkit_values["MolLogP"]),
        "tpsa": (float(record["tpsa"]), rdkit_values["TPSA"]),
        "hbond_donor_count": (float(record["hbond_donor_count"]), rdkit_values["NumHDonors"]),
        "hbond_acceptor_count": (float(record["hbond_acceptor_count"]), rdkit_values["NumHAcceptors"]),
        "rotatable_bond_count": (float(record["rotatable_bond_count"]), rdkit_values["NumRotatableBonds"]),
    }
    differences = {
        field: {"pubchem": expected, "rdkit": observed, "absolute_difference": abs(expected - observed)}
        for field, (expected, observed) in definition_sensitive_pairs.items()
    }
    failures = [field for field, passed in identity_checks.items() if not passed]
    return {
        "cid": record["cid"],
        "query_name": record["query_name"],
        "identity_checks": identity_checks,
        "identity_failures": failures,
        "definition_sensitive_differences": differences,
    }


def main() -> None:
    source_path = RESEARCH_ROOT / "data" / "interim" / "pubchem_compounds_v0.1.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    features = [featurize(record) for record in source["records"]]
    comparisons = [comparison(record, feature) for record, feature in zip(source["records"], features, strict=True)]
    output = {
        "schema_version": "0.1",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rdkit_version": rdBase.rdkitVersion,
        "fingerprint": {"algorithm": "Morgan", "radius": FP_RADIUS, "size": FP_SIZE, "representation": "on-bit indices"},
        "record_count": len(features),
        "records": features,
    }
    output_path = RESEARCH_ROOT / "data" / "processed" / "molecular_features_v0.1.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "record_count": len(comparisons),
        "records_with_identity_failures": sum(bool(row["identity_failures"]) for row in comparisons),
        "interpretation": (
            "Identity checks must pass. PubChem and RDKit values for XlogP, TPSA, hydrogen-bond counts, "
            "and rotatable bonds are retained as method-dependent comparisons, not identity tests. "
            "Downstream features use the pinned RDKit version consistently."
        ),
        "comparisons": comparisons,
    }
    audit_path = RESEARCH_ROOT / "reports" / "molecular_feature_audit_v0.1.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"features": str(output_path), "audit": str(audit_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
