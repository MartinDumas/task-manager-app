import json
from pathlib import Path
import pytest
from mcp_connector import search_mode


def test_settings_mode_switch(tmp_path, monkeypatch):
    monkeypatch.setattr(search_mode, 'INDEX_DIR', tmp_path)
    monkeypatch.setattr(search_mode, 'MODE_FILE', tmp_path/'mode.json')
    monkeypatch.delenv('TASK_MANAGER_SEARCH_MODE', raising=False)
    assert search_mode.current_mode() == 'lexical'
    with pytest.raises(ValueError): search_mode.set_mode('semantic')
    (tmp_path/'vault_vectors.sqlite3').write_bytes(b'fake for switch-only test')
    search_mode.set_mode('semantic')
    assert search_mode.current_mode() == 'semantic'
    search_mode.set_mode('lexical')
    assert search_mode.current_mode() == 'lexical'
    monkeypatch.setenv('TASK_MANAGER_SEARCH_MODE', 'semantic')
    assert search_mode.current_mode() == 'semantic'
