#!/usr/bin/env python3
"""Copilot preToolUse guardrails. JSON in stdin -> JSON permission decision in stdout.

Never executes incoming tool command. Tests operate on JSON only.
Target surface: GitHub Copilot hooks (camelCase or compatible PascalCase payload).
"""
import json
import os
import re
import subprocess
import sys

READ_TOOLS = {"view", "read", "grep", "glob", "search_notes", "get_note", "ping", "list_commits"}
MODIFY_TOOLS = {"create", "write", "edit", "apply_patch", "str_replace_editor", "delete", "delete_file", "ingest_note"}
SHELL_TOOLS = {"bash", "shell", "terminal", "run_in_terminal", "execute", "powershell"}


def decision(value, why=""):
    output = {"permissionDecision": value}
    if why:
        output["permissionDecisionReason"] = why
    return output


def parse_args(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"command": value}
        except json.JSONDecodeError:
            return {"command": value}
    return {}


def strings_under(data, names):
    """Only inspect fields that represent commands/paths (not unrelated prose)."""
    values = []
    if not isinstance(data, dict):
        return values
    for key, value in data.items():
        k = str(key).lower()
        if k in names and isinstance(value, str):
            values.append(value)
        if isinstance(value, dict):
            values.extend(strings_under(value, names))
        if isinstance(value, list):
            for child in value:
                if isinstance(child, dict):
                    values.extend(strings_under(child, names))
    return values


def current_branch(cwd):
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, "symbolic-ref", "--quiet", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def classify(payload):
    if not isinstance(payload, dict):
        return decision("deny", "Invalid event payload")
    tool = str(payload.get("toolName") or payload.get("tool_name") or "").strip()
    name = tool.split("/")[-1].lower()
    args = parse_args(payload.get("toolArgs", payload.get("tool_input", {})))
    command_fields = {"command", "cmd", "shellcommand", "commandline", "script"}
    path_fields = {"path", "filepath", "file_path", "target_file", "filename", "file_name", "relativepath", "oldpath", "newpath"}
    commands = strings_under(args, command_fields)
    paths = strings_under(args, path_fields)
    cmd = "\n".join(commands)
    inspected = "\n".join(commands + paths).replace("\\", "/")
    lower = inspected.casefold()

    # Read-only tools may never use filesystem parameters to access the external vault.
    if ("task-manager-vault" in lower or "../vault" in lower) and name not in {"get_note", "search_notes", "ingest_note", "ping"}:
        return decision("deny", "GR-B03: vault files may only be accessed by approved MCP tools")

    # Blocking repository policy: only the app repository is governed by this hook.
    if re.search(r"\bgit\s+(?:-\S+\s+)*(?:push|commit|reset|clean)\b", cmd, re.I):
        if re.search(r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[^\s]*f", cmd, re.I):
            return decision("deny", "GR-B02: destructive git reset/clean forbidden")
        if re.search(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", cmd, re.I):
            return decision("deny", "GR-B02: forced git push forbidden")
        if re.search(r"\bgit\s+push\b[^\n;&|]*(?:\bmain\b|\bmaster\b|HEAD:refs/heads/main|HEAD:main)", cmd, re.I):
            return decision("deny", "GR-B01: direct push to main is prohibited; use PR")
        if re.search(r"\bgit\s+commit\b", cmd, re.I):
            branch = current_branch(str(payload.get("cwd") or os.getcwd()))
            if branch in {"main", "master"}:
                return decision("deny", "GR-B01: commit on main prohibited; create feature branch")
            return decision("ask", "GR-W02: review and approve the commit on a feature branch")

    if re.search(r"(?:^|[\s;&|])(?:sudo\s+)?rm\s+-[^\s]*r[^\s]*f|(?:^|[\s;&|])(?:sudo\s+)?rm\s+-[^\s]*f[^\s]*r", cmd, re.I):
        return decision("deny", "GR-B02: recursive forced deletion prohibited")
    if re.search(r"\bgit\s+rm\b[^\n]*(?:Decisions/|task-manager-vault)", cmd, re.I):
        return decision("deny", "GR-B04: deletion of decision notes prohibited")
    if ("delete" in name or re.search(r"\brm\s+", cmd)) and "decisions/" in lower:
        return decision("deny", "GR-B04: deletion of Decisions notes prohibited")

    if name in READ_TOOLS:
        return decision("allow", "GR-A01: read-only operation")
    if name == "ingest_note":
        return decision("ask", "GR-W03: review MCP ingestion before writing to vault")
    if name in MODIFY_TOOLS:
        return decision("ask", "GR-W01: inspect proposed file modification")
    if name in SHELL_TOOLS or commands:
        if re.fullmatch(r"\s*(?:git\s+(?:status|log|diff|show)(?:\s+[^\n;&|]*)?|pwd|ls(?:\s+[^\n;&|]*)?|pytest(?:\s+[^\n;&|]*)?)\s*", cmd, re.I):
            return decision("allow", "GR-A02: routine read/test command")
        if re.search(r"\b(?:pip3?|uv|npm|brew)\s+(?:install|add|upgrade)\b", cmd, re.I):
            return decision("ask", "GR-W04: dependency changes require approval")
        return decision("ask", "GR-W02: terminal commands require approval unless explicitly safe")
    return decision("ask", "Unrecognized tool; request human approval")


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
        result = classify(payload)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, TypeError, RecursionError) as exc:
        print(json.dumps(decision("deny", "Malformed hook request: " + str(exc)[:150]), ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
