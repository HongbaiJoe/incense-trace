import copy
import json

from xiangji.data import RESEARCH_ROOT
from xiangji.representations.material_chemistry import validate


def inputs():
    evidence = json.loads((RESEARCH_ROOT / "data" / "curated" / "material_compound_evidence_v0.1.json").read_text())
    ontology = json.loads((RESEARCH_ROOT / "ontology" / "materials_v0.1.json").read_text())
    compounds = json.loads((RESEARCH_ROOT / "data" / "interim" / "pubchem_compounds_v0.1.json").read_text())
    return evidence, ontology, compounds


def test_material_chemistry_evidence_is_internally_valid():
    assert validate(*inputs()) == []


def test_presence_only_evidence_cannot_carry_fake_percentage():
    evidence, ontology, compounds = inputs()
    broken = copy.deepcopy(evidence)
    component = broken["material_profiles"][0]["components"][0]
    component["measurement"] = {"unit": "percent_peak_area", "min": 10.0, "max": 10.0}
    assert any("presence evidence has numeric abundance" in error for error in validate(broken, ontology, compounds))


def test_isolated_presence_cannot_carry_fake_percentage():
    evidence, ontology, compounds = inputs()
    broken = copy.deepcopy(evidence)
    component = next(
        component
        for profile in broken["material_profiles"]
        for component in profile["components"]
        if component["evidence_type"] == "isolated_presence"
    )
    component["measurement"] = {"unit": "percent_peak_area", "min": 1.0, "max": 1.0}
    assert any("presence evidence has numeric abundance" in error for error in validate(broken, ontology, compounds))


def test_unknown_compound_is_rejected():
    evidence, ontology, compounds = inputs()
    broken = copy.deepcopy(evidence)
    broken["material_profiles"][1]["components"][0]["compound_id"] = "invented-molecule"
    assert any("compound absent from molecular vocabulary" in error for error in validate(broken, ontology, compounds))
