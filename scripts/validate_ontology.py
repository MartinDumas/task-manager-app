#!/usr/bin/env python3
"""Validate the PR4 Obsidian taxonomy and frontmatter typed links.
Run from the application repo with: python3 scripts/validate_ontology.py /path/to/vault
Requires PyYAML (already part of the PR3 requirements).
"""
from pathlib import Path
import sys
import yaml

ALLOWED_TYPES = {"concept", "component", "decision", "glossary", "moc", "template", "guide"}
RELATIONS = {"depends_on", "implements", "governed_by", "verifies", "related_to"}
NOTE_FOLDERS = {"concept": "Concepts", "component": "Components", "decision": "Decisions", "glossary": "Glossary", "template": "Templates"}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("no YAML frontmatter")
    chunks = text.split("---\n", 2)
    if len(chunks) < 3 or not chunks[0] == "":
        raise ValueError("malformed YAML")
    data = yaml.safe_load(chunks[1])
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a map")
    return data


def validate(vault):
    vault = Path(vault).expanduser().resolve()
    if not vault.is_dir():
        raise ValueError(f"vault folder not found: {vault}")
    files = sorted(p for p in vault.rglob("*.md") if ".git" not in p.parts and ".obsidian" not in p.parts)
    stems = {}
    for p in files:
        stems.setdefault(p.stem, []).append(p)
    faults = []
    checked = 0
    edges = 0
    for path in files:
        try:
            data = frontmatter(path)
        except (ValueError, yaml.YAMLError) as exc:
            faults.append(f"{path.relative_to(vault)}: {exc}")
            continue
        note_type = data.get("type")
        if note_type not in ALLOWED_TYPES:
            faults.append(f"{path.relative_to(vault)}: invalid type {note_type}")
        if path.parent.name in {"Concepts", "Components", "Decisions", "Glossary", "Templates"}:
            if NOTE_FOLDERS.get(note_type) != path.parent.name:
                faults.append(f"{path.relative_to(vault)}: folder/type mismatch")
        for kind in RELATIONS:
            if kind not in data:
                continue
            targets = data[kind]
            if not isinstance(targets, list):
                faults.append(f"{path.relative_to(vault)}: {kind} must be array")
                continue
            for target in targets:
                if not isinstance(target, str) or not target or "/" in target or target == path.stem:
                    faults.append(f"{path.relative_to(vault)}: invalid {kind} target {target!r}")
                    continue
                if len(stems.get(target, [])) != 1:
                    faults.append(f"{path.relative_to(vault)}: unresolved/ambiguous {kind} -> {target}")
                edges += 1
        checked += 1
    return {"notes": checked, "typed_relations": edges, "errors": faults}


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_ontology.py /absolute/path/to/task-manager-vault")
        return 2
    result = validate(sys.argv[1])
    print(f"Notes: {result['notes']} | typed links: {result['typed_relations']} | errors: {len(result['errors'])}")
    for message in result["errors"]:
        print("ERROR:", message)
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
