"""Stdio MCP server for controlled Obsidian vault access (Python MCP SDK v1)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running this file by its absolute path from JetBrains' MCP configuration.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp_connector.core import VaultConnector, VaultError  # noqa: E402

mcp = FastMCP("task-manager-vault", instructions="Read and write Obsidian knowledge via typed tools only.")


def _connector() -> VaultConnector:
    vault = os.environ.get("TASK_MANAGER_VAULT_PATH")
    if not vault:
        raise VaultError("TASK_MANAGER_VAULT_PATH environment variable is required")
    return VaultConnector(Path(vault), git_sync=os.environ.get("VAULT_GIT_SYNC", "true").lower() == "true")


@mcp.tool()
def ping() -> dict:
    """Confirm the local vault MCP server is responding (no data changes)."""
    return {"status": "ok", "service": "task-manager-vault"}


@mcp.tool()
def get_note(note_name: str) -> dict:
    """Read an Obsidian note by stem (Task) or relative name (Concepts/Task)."""
    return _connector().get_note(note_name)


@mcp.tool()
def search_notes(query: str, limit: int = 10) -> list[dict]:
    """Find matching notes in vault by case-insensitive text search."""
    return _connector().search_notes(query, limit)


@mcp.tool()
def ingest_note(
    title: str,
    note_type: str,
    content: str,
    source_id: str,
    source: str,
    links: list[str] | None = None,
    tags: list[str] | None = None,
    status: str = "documented",
) -> dict:
    """Idempotently create/update a vault note; with git sync enabled, pull/commit/push."""
    return _connector().ingest_note(title, note_type, content, source_id, source, links, tags, status)


if __name__ == "__main__":
    # stdout reserved for MCP JSON-RPC frames; log diagnostics only to stderr.
    mcp.run(transport="stdio")
