"""Private local mode switch; not an additional MCP channel or agent tool."""
from __future__ import annotations
import json
import os
from pathlib import Path

INDEX_DIR = Path(os.environ.get("TASK_MANAGER_VECTOR_INDEX_DIR", str(Path(__file__).resolve().parents[1] / ".pr7-vector-index"))).expanduser().resolve()
MODE_FILE = INDEX_DIR / "mode.json"


def current_mode() -> str:
    override = os.environ.get("TASK_MANAGER_SEARCH_MODE", "").lower().strip()
    if override in {"semantic", "lexical"}:
        return override
    if MODE_FILE.is_file():
        value = json.loads(MODE_FILE.read_text(encoding="utf-8")).get("mode")
        if value in {"semantic", "lexical"}:
            return value
    return "lexical"


def set_mode(mode: str) -> None:
    if mode not in {"semantic", "lexical"}:
        raise ValueError("Expected semantic or lexical")
    if mode == "semantic" and not (INDEX_DIR / "vault_vectors.sqlite3").is_file():
        raise ValueError("Build index before enabling semantic mode")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(json.dumps({"mode": mode}) + "\n", encoding="utf-8")
