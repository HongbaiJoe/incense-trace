import json

from xiangji.data import RESEARCH_ROOT
from xiangji.representations.molecular import FP_SIZE, featurize


def test_pubchem_manifest_has_unique_resolved_structures():
    payload = json.loads((RESEARCH_ROOT / "data" / "interim" / "pubchem_compounds_v0.1.json").read_text())
    records = payload["records"]
    assert payload["record_count"] == 40
    assert len(records) == payload["record_count"]
    assert len({record["cid"] for record in records}) == payload["record_count"]
    assert len({record["inchikey"] for record in records}) == payload["record_count"]
    assert all(record["synonym_match"] for record in records)


def test_rdkit_feature_shape_and_identity():
    record = {
        "cid": 3314,
        "query_name": "eugenol",
        "inchikey": "RRAFCDWBNXTKKO-UHFFFAOYSA-N",
        "canonical_smiles": "COC1=C(C=CC(=C1)CC=C)O",
    }
    features = featurize(record)
    assert features["morgan_size"] == FP_SIZE
    assert features["morgan_on_bits"]
    assert min(features["morgan_on_bits"]) >= 0
    assert max(features["morgan_on_bits"]) < FP_SIZE
    assert features["canonical_isomeric_smiles_rdkit"]


def test_molecular_audit_has_no_identity_failures():
    audit_path = RESEARCH_ROOT / "reports" / "molecular_feature_audit_v0.1.json"
    if not audit_path.exists():
        return
    audit = json.loads(audit_path.read_text())
    assert audit["records_with_identity_failures"] == 0
