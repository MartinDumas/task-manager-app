"""Git-backed vault ingestion and retrieval. No MCP runtime dependency here."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Fixed folders; never trust a model-provided filesystem path.
NOTE_FOLDERS = {
    "concept": "Concepts",
    "component": "Components",
    "decision": "Decisions",
    "glossary": "Glossary",
}
ALLOWED_STATUSES = {"documented", "proposed", "accepted", "deprecated"}
MAX_CONTENT = 16_000
MAX_NOTE = 40_000


class VaultError(ValueError):
    """Input, vault configuration or Git synchronization error."""


def _git(directory: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(directory), "-c", "core.quotepath=false", *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if cp.returncode:
        raise VaultError(f"git {args[0]} failed: {cp.stderr.strip()[:500]}")
    return cp.stdout.strip()


def _key(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 180:
        raise VaultError("source_id must be a non-empty string up to 180 characters")
    # Stable ID derived from the source, regardless of changing display title.
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _safe_title(value: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value.strip()) <= 120):
        raise VaultError("title must contain 1..120 characters")
    if any(ch in value for ch in "\x00\r\n"):
        raise VaultError("title contains a control character")
    return value.strip()


def _stem(title: str) -> str:
    cleaned = re.sub(r"[^\w-]+", "-", title, flags=re.UNICODE)
    return (cleaned.strip("-_")[:58] or "Note")


def _link(value: str) -> str:
    if not isinstance(value, str):
        raise VaultError("links must be a list of note names")
    # No traversal, embedded markdown, aliases, folders, or arbitrary external paths.
    if not re.fullmatch(r"[\w()\- ]{1,100}", value, flags=re.UNICODE) or value in (".", ".."):
        raise VaultError(f"invalid wiki link: {value!r}")
    return value


def _split_note(raw: str) -> tuple[dict[str, Any], str]:
    parts = raw.split("---\n", 2)
    if len(parts) != 3 or parts[0] != "":
        raise VaultError("existing note has no YAML frontmatter")
    fields = yaml.safe_load(parts[1])
    if not isinstance(fields, dict):
        raise VaultError("invalid YAML frontmatter")
    return fields, parts[2]


@dataclass
class VaultConnector:
    vault_path: Path
    git_sync: bool = True
    branch: str = "main"

    def __post_init__(self) -> None:
        self.vault_path = Path(self.vault_path).expanduser().resolve()
        if not self.vault_path.is_dir():
            raise VaultError(f"vault directory not found: {self.vault_path}")
        if self.branch not in {"main", "master"}:
            raise VaultError("unsupported branch")
        if self.git_sync and not (self.vault_path / ".git").exists():
            raise VaultError("vault must be its own git clone when git_sync is enabled")

    def _git_prepare(self) -> None:
        if not self.git_sync:
            return
        if _git(self.vault_path, "status", "--porcelain"):
            raise VaultError("vault clone has local modifications: commit or stash them first")
        _git(self.vault_path, "pull", "--ff-only", "origin", self.branch)

    def _git_commit_push(self, relative: Path, message: str) -> str:
        if not self.git_sync:
            return "local_only"
        _git(self.vault_path, "add", "--", relative.as_posix())
        staged = _git(self.vault_path, "diff", "--cached", "--name-only")
        if staged.strip() != relative.as_posix():
            raise VaultError("unexpected staged files; aborting commit")
        _git(self.vault_path, "commit", "-m", message)
        _git(self.vault_path, "push", "origin", self.branch)
        return _git(self.vault_path, "rev-parse", "--short", "HEAD")

    def ingest_note(
        self,
        title: str,
        note_type: str,
        content: str,
        source_id: str,
        source: str,
        links: list[str] | None = None,
        tags: list[str] | None = None,
        status: str = "documented",
    ) -> dict[str, Any]:
        """Upsert by source_id, commit and push only changed notes."""
        title = _safe_title(title)
        if note_type not in NOTE_FOLDERS:
            raise VaultError("note_type must be concept/component/decision/glossary")
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_CONTENT:
            raise VaultError("content must be non-empty and <= 16000 characters")
        if not isinstance(source, str) or not source.strip() or len(source) > 1000:
            raise VaultError("source must describe a real document or GitHub URL")
        if status not in ALLOWED_STATUSES:
            raise VaultError("unsupported status")
        if links is None:
            links = []
        if tags is None:
            tags = []
        if not isinstance(links, list) or len(links) > 12:
            raise VaultError("links must be an array with at most 12 values")
        if not isinstance(tags, list) or len(tags) > 12:
            raise VaultError("tags must be an array with at most 12 values")
        links = list(dict.fromkeys(_link(item) for item in links))
        tags = list(dict.fromkeys(tags))
        if not all(isinstance(t, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", t) for t in tags):
            raise VaultError("tags must use lowercase latin letters, digits, _ or -")
        source_id = source_id.strip()
        suffix = _key(source_id)
        relative = Path(NOTE_FOLDERS[note_type]) / f"{_stem(title)}-{suffix}.md"
        path = (self.vault_path / relative).resolve()
        if not path.is_relative_to(self.vault_path):
            raise VaultError("invalid path")

        # Validate everything before touching Git or the working tree.
        self._git_prepare()
        folder = self.vault_path / NOTE_FOLDERS[note_type]
        folder.mkdir(exist_ok=True)
        # Source identity is not tied to the title: find prior note if it was renamed.
        matches: list[Path] = []
        for other in folder.glob(f"*-{suffix}.md"):
            fields, _ = _split_note(other.read_text(encoding="utf-8"))
            if fields.get("source_id") == source_id:
                matches.append(other)
        if len(matches) > 1:
            raise VaultError("duplicate source_id in vault; manual cleanup needed")
        if matches:
            path = matches[0]
            relative = path.relative_to(self.vault_path)

        payload = {
            "title": title,
            "type": note_type,
            "content": content.strip(),
            "source": source.strip(),
            "source_id": source_id,
            "links": links,
            "tags": tags,
            "status": status,
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        existing: dict[str, Any] = {}
        if path.exists():
            existing, _ = _split_note(path.read_text(encoding="utf-8"))
            if existing.get("source_id") != source_id:
                raise VaultError("existing note has different source_id")
            if existing.get("source_hash") == digest:
                return {"status": "unchanged", "path": relative.as_posix(), "commit": None}

        today = date.today().isoformat()
        fields = {
            "type": note_type,
            "title": title,
            "created": str(existing.get("created", today)),
            "updated": today,
            "tags": tags,
            "source": source.strip(),
            "source_id": source_id,
            "source_hash": digest,
            "status": status,
        }
        wiki = "\n".join(f"- [[{name}]]" for name in links)
        body = f"# {title}\n\n{content.strip()}\n"
        if wiki:
            body += f"\n## Пов'язані нотатки\n\n{wiki}\n"
        generated = "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True) + "---\n\n" + body
        action = "updated" if path.exists() else "created"
        path.write_text(generated, encoding="utf-8")
        commit = self._git_commit_push(relative, f"docs(vault): {action} {note_type} {suffix}")
        return {"status": action, "path": relative.as_posix(), "commit": commit}

    def get_note(self, note_name: str) -> dict[str, Any]:
        """Read by filename stem or relative path; do not accept arbitrary paths."""
        if not isinstance(note_name, str) or not note_name.strip() or len(note_name) > 180:
            raise VaultError("note_name must be non-empty")
        value = note_name.removesuffix(".md")
        if "/" in value:
            parent, _, stem = value.partition("/")
            if parent not in {*NOTE_FOLDERS.values(), "Templates"}:
                raise VaultError("invalid note folder")
            if not re.fullmatch(r"[\w()\- ]{1,120}", stem, flags=re.UNICODE):
                raise VaultError("invalid note filename")
            names = [self.vault_path / parent / (stem + ".md")]
        else:
            if not re.fullmatch(r"[\w()\- ]{1,120}", value, flags=re.UNICODE):
                raise VaultError("invalid note filename")
            names = list(self.vault_path.rglob(value + ".md"))
        safe = []
        for path in names:
            rp = path.resolve()
            if rp.is_relative_to(self.vault_path) and rp.suffix == ".md" and rp.is_file():
                safe.append(rp)
        if len(safe) != 1:
            return {"status": "not_found" if not safe else "ambiguous", "query": note_name}
        raw = safe[0].read_text(encoding="utf-8")
        if len(raw) > MAX_NOTE:
            raise VaultError("note too large")
        return {"status": "ok", "path": safe[0].relative_to(self.vault_path).as_posix(), "content": raw}

    def search_notes(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Case-insensitive substring search; no embeddings or unverified claims."""
        if not isinstance(query, str) or not (2 <= len(query.strip()) <= 100):
            raise VaultError("query length must be 2..100")
        if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= 30):
            raise VaultError("limit must be 1..30")
        matches = []
        term = query.casefold().strip()
        for path in sorted(self.vault_path.rglob("*.md")):
            if ".git" in path.parts or path.is_symlink():
                continue
            if not path.resolve().is_relative_to(self.vault_path):
                continue
            text = path.read_text(encoding="utf-8")
            hits = text.casefold().count(term)
            if hits:
                matches.append({"path": path.relative_to(self.vault_path).as_posix(),
                                "matches": hits, "preview": text[:220].replace("\n", " ")})
        return sorted(matches, key=lambda x: (-x["matches"], x["path"]))[:limit]
