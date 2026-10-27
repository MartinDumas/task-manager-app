"""PR7: local, regenerable SQLite vector index over markdown vault notes.

No MCP tool and no external vault access channel is introduced here.
The production encoder runs locally; first model download needs network once.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DB_NAME = "vault_vectors.sqlite3"


class EmbeddingProvider(Protocol):
    model_name: str
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerProvider:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install PR7 embeddings: python -m pip install -r requirements-pr7.txt") from exc
        self.model_name = model_name
        # Downloads model weights on first use; encodes note content locally.
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, batch_size=16, show_progress_bar=False,
                                  normalize_embeddings=True).tolist()


@lru_cache(maxsize=2)
def cached_sentence_transformer(model_name: str = DEFAULT_MODEL) -> SentenceTransformerProvider:
    """Reuse the expensive multilingual embedding model across MCP calls."""
    return SentenceTransformerProvider(model_name)


def safe_markdown_files(vault_path: Path) -> list[tuple[str, str]]:
    vault = Path(vault_path).resolve()
    if not vault.is_dir():
        raise ValueError(f"Vault directory is missing: {vault}")
    out: list[tuple[str, str]] = []
    for p in sorted(vault.rglob("*.md")):
        if p.is_symlink() or any(s in {".git", ".obsidian", ".trash"} for s in p.relative_to(vault).parts):
            continue
        resolved = p.resolve()
        if not resolved.is_relative_to(vault) or not resolved.is_file():
            continue
        out.append((p.relative_to(vault).as_posix(), p.read_text(encoding="utf-8")))
    return out


def corpus_fingerprint(notes: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for path, content in notes:
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content.encode("utf-8")).digest())
    return digest.hexdigest()


def chunk_markdown(content: str, *, max_chars: int = 1100, overlap: int = 100) -> list[str]:
    """Group note content by Markdown headings, then cut oversized sections."""
    if max_chars < 80 or not 0 <= overlap < max_chars // 2:
        raise ValueError("Invalid chunk size/overlap")
    # Frontmatter is searchable context too (tags/description).
    sections: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if re.match(r"^#{1,4}\s+", line) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    result: list[str] = []
    for section in sections:
        if not section:
            continue
        start = 0
        while start < len(section):
            end = min(start + max_chars, len(section))
            piece = section[start:end].strip()
            if piece:
                result.append(piece)
            if end == len(section):
                break
            start = end - overlap
    return result


def _normalized(vector: list[float]) -> list[float]:
    if not vector or any(not math.isfinite(float(v)) for v in vector):
        raise ValueError("Embedding contains no values or non-finite numbers")
    magnitude = math.sqrt(sum(float(v) ** 2 for v in vector))
    if magnitude <= 0:
        raise ValueError("Zero-length embedding")
    return [float(v) / magnitude for v in vector]


@dataclass
class EmbeddedVectorIndex:
    vault_path: Path
    index_dir: Path
    embedder: EmbeddingProvider

    def __post_init__(self):
        self.vault_path = Path(self.vault_path).expanduser().resolve()
        self.index_dir = Path(self.index_dir).expanduser().resolve()
        if self.index_dir.is_relative_to(self.vault_path):
            raise ValueError("Vector index must not be inside the Git-backed vault")

    @property
    def db_path(self) -> Path:
        return self.index_dir / DB_NAME

    def rebuild(self) -> dict[str, object]:
        """Build and atomically replace an embedded index; never alter the vault."""
        notes = safe_markdown_files(self.vault_path)
        fp = corpus_fingerprint(notes)
        chunks = [(path, i, piece)
                  for path, text in notes
                  for i, piece in enumerate(chunk_markdown(text))]
        vectors = self.embedder.encode([piece for _, _, piece in chunks]) if chunks else []
        if len(vectors) != len(chunks):
            raise ValueError("Embedding count differs from chunk count")
        normalized = [_normalized(list(v)) for v in vectors]
        dim = len(normalized[0]) if normalized else 0
        if any(len(v) != dim for v in normalized):
            raise ValueError("Embedding dimensions must be consistent")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix="pr7-", suffix=".sqlite3", dir=self.index_dir)
        os.close(fd)
        try:
            with sqlite3.connect(temp) as db:
                db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("CREATE TABLE chunks (path TEXT NOT NULL, section INTEGER NOT NULL, text TEXT NOT NULL, vector TEXT NOT NULL, PRIMARY KEY (path, section))")
                db.executemany("INSERT INTO meta VALUES (?, ?)", [
                    ("fingerprint", fp), ("model", self.embedder.model_name),
                    ("dimension", str(dim)), ("format", "pr7-v1"),
                ])
                db.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?)", [
                    (path, number, text, json.dumps(v)) for (path, number, text), v in zip(chunks, normalized)
                ])
            os.replace(temp, self.db_path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return {"notes": len(notes), "chunks": len(chunks), "model": self.embedder.model_name,
                "index": str(self.db_path), "fingerprint": fp}

    def search(self, query: str, limit: int) -> list[dict[str, object]]:
        if not self.db_path.exists():
            raise ValueError("Semantic index absent. Run scripts/pr7_reindex.py first")
        current_fp = corpus_fingerprint(safe_markdown_files(self.vault_path))
        try:
            with sqlite3.connect(self.db_path) as db:
                meta = dict(db.execute("SELECT key, value FROM meta"))
                if meta.get("format") != "pr7-v1" or meta.get("model") != self.embedder.model_name:
                    raise ValueError("Index model/format changed; reindex required")
                if meta.get("fingerprint") != current_fp:
                    raise ValueError("Vault notes changed; run reindex before semantic search")
                data = db.execute("SELECT path, section, text, vector FROM chunks").fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError("Vector index corrupted; rebuild it") from exc
        if not data:
            return []
        query_vector = self.embedder.encode([query])
        if len(query_vector) != 1:
            raise ValueError("Embedding encoder returned wrong query dimension")
        q = _normalized(list(query_vector[0]))
        if len(q) != int(meta["dimension"]):
            raise ValueError("Embedding model dimension mismatch; reindex")
        scored = []
        for path, section, text, raw_vector in data:
            v = json.loads(raw_vector)
            score = sum(a * b for a, b in zip(q, v))
            scored.append((score, path, section, text))
        scored.sort(key=lambda v: (-v[0], v[1], v[2]))
        # Keep MCP response keys intact. A semantic match need not contain the literal query.
        return [{"path": path, "matches": text.casefold().count(query.strip().casefold()),
                 "preview": text[:220].replace("\n", " ")}
                for _, path, _, text in scored[:limit]]
