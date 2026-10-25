"""Tests of actual file operations and Git synchronization (without calling an IDE)."""
from __future__ import annotations
import subprocess
from pathlib import Path

import pytest

from mcp_connector.core import VaultConnector, VaultError


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def example(**override):
    data = dict(title="Вимоги API", note_type="decision", content="Створено вимоги FR-01…FR-09.",
                source_id="github:65569ae16a9b676cd4f031d6a2498934d23c12ff",
                source="https://github.com/MartinDumas/task-manager-app/commit/65569ae16a9b676cd4f031d6a2498934d23c12ff",
                links=["MOC-Застосунок"], tags=["github", "requirements"])
    return data | override


@pytest.fixture()
def vault(tmp_path: Path):
    path = tmp_path / "vault"
    path.mkdir()
    (path / "MOC-Застосунок.md").write_text("# MOC\n", encoding="utf-8")
    return path


def test_crud_and_idempotency(vault):
    c = VaultConnector(vault, git_sync=False)
    first = c.ingest_note(**example())
    assert first["status"] == "created"
    assert first["commit"] == "local_only"
    again = c.ingest_note(**example())
    assert again["status"] == "unchanged"
    assert len(list((vault / "Decisions").glob("*.md"))) == 1
    note = c.get_note(first["path"])
    assert note["status"] == "ok"
    assert "source_hash" in note["content"]
    assert "[[MOC-Застосунок]]" in note["content"]
    changed = c.ingest_note(**example(content="Документ вимог уточнено."))
    assert changed["status"] == "updated"
    assert changed["path"] == first["path"]
    assert "уточнено" in c.get_note(first["path"])["content"]
    assert c.search_notes("уточнено")[0]["path"] == first["path"]


def test_input_traversal_and_missing(vault):
    c = VaultConnector(vault, git_sync=False)
    for val in ["../secret", "a/b", "a|b", "a]]x"]:
        with pytest.raises(VaultError):
            c.ingest_note(**example(links=[val]))
    with pytest.raises(VaultError):
        c.ingest_note(**example(note_type="../../tmp"))
    with pytest.raises(VaultError):
        c.get_note("../../etc/passwd")
    assert c.get_note("Other") == {"status": "not_found", "query": "Other"}


def test_search(vault):
    c = VaultConnector(vault, git_sync=False)
    c.ingest_note(**example())
    assert c.search_notes("ВИМОГ")
    assert c.search_notes("no-such-phrase") == []
    with pytest.raises(VaultError):
        c.search_notes("x")


def test_search_sorting_and_limit_boundaries(vault):
    c = VaultConnector(vault, git_sync=False)
    notes = {
        "z.md": "needle needle",
        "Decisions/b.md": "needle",
        "Concepts/a.md": "needle",
    }
    for relative, content in notes.items():
        path = vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    expected_paths = ["z.md", "Concepts/a.md", "Decisions/b.md"]
    assert [item["path"] for item in c.search_notes("needle", limit=30)] == expected_paths
    assert [item["path"] for item in c.search_notes("needle", limit=1)] == expected_paths[:1]


def test_search_limit_true_currently_acts_as_one(vault):
    c = VaultConnector(vault, git_sync=False)
    (vault / "a.md").write_text("needle", encoding="utf-8")
    (vault / "b.md").write_text("needle", encoding="utf-8")

    # bool is an int subclass, so True currently passes the limit validation as 1.
    assert c.search_notes("needle", limit=True) == c.search_notes("needle", limit=1)


def test_search_preview_format(vault):
    c = VaultConnector(vault, git_sync=False)
    content = "needle\n" + ("x" * 230)
    (vault / "preview.md").write_text(content, encoding="utf-8")

    result = c.search_notes("needle")

    assert result == [{
        "path": "preview.md",
        "matches": 1,
        "preview": content[:220].replace("\n", " "),
    }]


def test_search_ignores_symlink_files(vault, tmp_path):
    c = VaultConnector(vault, git_sync=False)
    outside_note = tmp_path / "outside.md"
    outside_note.write_text("needle", encoding="utf-8")
    (vault / "linked.md").symlink_to(outside_note)

    assert c.search_notes("needle") == []


def test_git_pull_commit_push_and_noop(tmp_path):
    remote = tmp_path / "remote.git"
    run("init", "--bare", "--initial-branch=main", str(remote), cwd=tmp_path)
    seed = tmp_path / "seed"
    run("clone", str(remote), str(seed), cwd=tmp_path)
    run("config", "user.name", "Course Test", cwd=seed)
    run("config", "user.email", "course-test@example.invalid", cwd=seed)
    (seed / "README.md").write_text("# vault\n", encoding="utf-8")
    run("add", ".", cwd=seed)
    run("commit", "-m", "initial", cwd=seed)
    run("push", "origin", "main", cwd=seed)
    local = tmp_path / "clone"
    run("clone", str(remote), str(local), cwd=tmp_path)
    run("config", "user.name", "Course Test", cwd=local)
    run("config", "user.email", "course-test@example.invalid", cwd=local)
    c = VaultConnector(local, git_sync=True)
    before = run("rev-list", "--count", "HEAD", cwd=local)
    saved = c.ingest_note(**example())
    assert saved["status"] == "created"
    assert len(saved["commit"]) >= 7
    after = run("rev-list", "--count", "HEAD", cwd=local)
    assert int(after) == int(before) + 1
    assert c.ingest_note(**example())["status"] == "unchanged"
    assert run("rev-list", "--count", "HEAD", cwd=local) == after
    fetched = tmp_path / "check"
    run("clone", str(remote), str(fetched), cwd=tmp_path)
    assert (fetched / saved["path"]).exists()
    assert "# Вимоги API" in (fetched / saved["path"]).read_text(encoding="utf-8")


def test_git_dirty_directory_rejected(tmp_path):
    folder = tmp_path / "dirty"
    folder.mkdir()
    run("init", "--initial-branch=main", cwd=folder)
    (folder / "stray.txt").write_text("untracked", encoding="utf-8")
    c = VaultConnector(folder, git_sync=True)
    with pytest.raises(VaultError, match="local modifications"):
        c.ingest_note(**example())
