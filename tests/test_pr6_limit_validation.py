"""PR6 regression checks for VaultConnector.search_notes limit validation.

Reject bool and out-of-range/non-integer limits while accepting integers from
1 through 30, including int subclasses.
"""
from pathlib import Path
import pytest
from mcp_connector.core import VaultConnector, VaultError

@pytest.fixture
def connector(tmp_path: Path):
    (tmp_path / "example.md").write_text("needle needle", encoding="utf-8")
    return VaultConnector(tmp_path, git_sync=False)

@pytest.mark.parametrize("invalid", [True, False, 0, 31, "3", 1.5, None])
def test_rejects_invalid_limit(connector, invalid):
    with pytest.raises(VaultError, match="limit"):
        connector.search_notes("needle", limit=invalid)

@pytest.mark.parametrize("valid", [1, 30])
def test_accepts_boundary_limits(connector, valid):
    assert len(connector.search_notes("needle", limit=valid)) == 1

class IntSubclass(int):
    pass

def test_accepts_int_subclass_without_regression(connector):
    assert len(connector.search_notes("needle", limit=IntSubclass(5))) == 1

def test_preview_output_unchanged(connector):
    assert connector.search_notes("needle")[0] == {
        "path": "example.md", "matches": 2, "preview": "needle needle"
    }
