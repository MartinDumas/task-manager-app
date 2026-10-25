import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_ontology import validate


def test_schema_links_vault_in_snapshot():
    snapshot = Path(__file__).resolve().parents[2] / "task-manager-vault"
    # Integration test when both delivery folders are side by side.
    assert snapshot.exists(), "Place app/ and vault/ together as delivered"
    result = validate(snapshot)
    assert not result["errors"], result["errors"]
    assert result["typed_relations"] >= 10


def test_ontology_checks_bad_links(tmp_path):
    p = tmp_path / "Components" / "Thing.md"
    p.parent.mkdir()
    p.write_text("---\ntype: component\ndepends_on: [Missing]\n---\n# T\n", encoding="utf-8")
    results = validate(tmp_path)
    assert any("Missing" in issue for issue in results["errors"])
