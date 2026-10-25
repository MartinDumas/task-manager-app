import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pre_tool_guard import classify


def evt(tool, args, cwd="."):
    return {"toolName": tool, "toolArgs": args, "cwd": cwd}


def val(tool, args, cwd="."):
    return classify(evt(tool, args, cwd))["permissionDecision"]


def test_allowed_cases():
    assert val("view", {"path": "docs/app-requirements.md"}) == "allow"
    assert val("bash", {"command": "git status"}) == "allow"
    assert val("search_notes", {"query": "TaskStatus"}) == "allow"
    assert val("bash", {"command": "pytest -q"}) == "allow"


def test_approval_cases():
    assert val("edit", {"path": "src/services.py", "newText": "pass"}) == "ask"
    assert val("bash", {"command": "pip install fastapi"}) == "ask"
    assert val("ingest_note", {"title": "ADR"}) == "ask"
    assert val("bash", {"command": "git push origin feature/work"}) == "ask"


def test_block_cases():
    assert val("bash", {"command": "git push origin main"}) == "deny"
    assert val("bash", {"command": "rm -rf docs"}) == "deny"
    assert val("bash", {"command": "cat /Users/demo/Documents/task-manager-vault/Decisions/ADR-004.md"}) == "deny"
    assert val("delete_file", {"path": "Decisions/ADR-001-LocalRESTAPI.md"}) == "deny"
    assert val("bash", {"command": "git reset --hard HEAD~1"}) == "deny"
    assert val("bash", {"command": "git clean -fd"}) == "deny"
    assert val("bash", {"command": "git push --force origin feature/work"}) == "deny"


def test_camelcase_and_string_args():
    d = classify({"toolName": "bash", "toolArgs": json.dumps({"command": "git push origin main"})})
    assert d["permissionDecision"] == "deny"
    d = classify({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    assert d["permissionDecision"] == "allow"


def test_malformed_input_denied():
    assert classify(None)["permissionDecision"] == "deny"
    cmd = subprocess.run([sys.executable, str(ROOT / "scripts/pre_tool_guard.py")], input="not json", capture_output=True, text=True)
    assert cmd.returncode == 0
    assert json.loads(cmd.stdout)["permissionDecision"] == "deny"


def test_script_emits_parseable_decision():
    cmd = subprocess.run([sys.executable, str(ROOT / "scripts/pre_tool_guard.py")], input=json.dumps(evt("bash", {"command":"git push origin main"})), capture_output=True, text=True)
    assert cmd.returncode == 0
    assert json.loads(cmd.stdout)["permissionDecision"] == "deny"


def test_commit_on_main_blocked(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    assert val("bash", {"command": "git commit -m docs"}, str(tmp_path)) == "deny"
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", "feature/guardrails"], check=True)
    assert val("bash", {"command": "git commit -m docs"}, str(tmp_path)) == "ask"


def test_git_pre_push_blocks_main():
    script = ROOT / ".githooks/pre-push"
    for line, expected in [
        ("refs/heads/main abc refs/heads/main def\n", 1),
        ("refs/heads/feature abc refs/heads/feature def\n", 0),
    ]:
        cp = subprocess.run([sys.executable, str(script)], input=line, capture_output=True, text=True)
        assert cp.returncode == expected
