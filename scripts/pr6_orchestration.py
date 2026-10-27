#!/usr/bin/env python3
"""PR6 handoff validator and OFFLINE role rehearsal (not an LLM or IDE)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TASK_ID = "PR6-STRICT-SEARCH-LIMIT"
REQUIRED = {
    "planner": {"role", "task_id", "inputs", "requirements", "decision_rationale", "risks", "tests", "guardrails", "open_questions", "handoff_to"},
    "coder": {"role", "task_id", "received_from", "changes", "design_choices", "commands", "test_results", "known_limitations", "guardrails", "handoff_to"},
    "reviewer": {"role", "task_id", "received_from", "decision", "findings", "evidence", "context_retained", "guardrails", "handoff_to"},
}

def validate(data: dict, role: str):
    if not isinstance(data, dict):
        raise ValueError(f"{role}: expected JSON object")
    missing = REQUIRED[role] - data.keys()
    if missing:
        raise ValueError(f"{role}: missing keys {sorted(missing)}")
    if data['role'] != role or data['task_id'] != TASK_ID:
        raise ValueError(f"{role}: role/task_id mismatch")
    if role == 'reviewer' and data['decision'] not in {'approved','changes_requested'}:
        raise ValueError('reviewer: invalid decision')
    if not data.get('guardrails'):
        raise ValueError(f'{role}: missing guardrails context')
    if role == 'planner' and 'proposed' not in json.dumps(data,ensure_ascii=False).lower():
        raise ValueError('planner: ADR approval status was lost')
    return True

def validate_files(base: Path):
    names={'planner':'01_planner.json', 'coder':'02_coder.json','reviewer':'03_reviewer.json'}
    for role,file in names.items():
        data=json.loads((base/file).read_text(encoding='utf-8'))
        validate(data,role)
        print(f'PASS {role}: {file}; guardrails={len(data["guardrails"])}')
    print('PASS handoff chain: planner -> coder -> reviewer')

def rehearse(root:Path):
    """Generate deterministic offline illustrative handoffs; no IDE/LLM claims."""
    base=root/'docs'/'pr6'/'offline-example';base.mkdir(parents=True,exist_ok=True)
    planner={"role":"planner","task_id":TASK_ID,"inputs":["mcp_connector/core.py","vault ADR proposed: limit bool","docs/guardrails.md"],"requirements":["reject True and False", "preserve 1..30 and int subclasses","do not change query"],"decision_rationale":"bool є підкласом int, тому ізольована перевірка isinstance(limit, bool) перед isinstance(limit, int) відповідає ADR proposed; потрібна згода людини", "risks":["Зміна контракту limit=True", "type(limit) is int відхилить int підкласи"],"tests":["True/False", "1/30", "IntSubclass(5)", "0/31", "unchanged search output"],"guardrails":["GR-A01", "GR-W01", "GR-B01", "GR-B03"],"open_questions":["Людина має схвалити зміну, бо ADR proposed"],"handoff_to":"coder"}
    coder={"role":"coder","task_id":TASK_ID,"received_from":"01_planner.json","changes":["candidate: type(limit) is int (навмисна офлайн-модель регресії)"],"design_choices":"Наївна сувора перевірка типу; не відповідає вимозі інтерфейсу щодо int-підкласів", "commands":["pytest tests/test_pr6_limit_validation.py — offline simulated design review"],"test_results":{"status":"review_required", "int_subclass":"fails"},"known_limitations":["IntSubclass(5) отримує помилку"],"guardrails":["GR-W01 (approval required)", "GR-B01"],"handoff_to":"reviewer"}
    reviewer={"role":"reviewer","task_id":TASK_ID,"received_from":["01_planner.json", "02_coder.json"],"decision":"changes_requested","findings":["Заміна на type(limit) is int заборонить IntSubclass(5)"],"evidence":["issubclass(IntSubclass, int) == True", "План вимагав збереження підкласів"],"context_retained":True,"guardrails":["GR-W01", "GR-B01", "GR-B03"],"handoff_to":"coder: use isinstance(limit, bool) or not isinstance(limit, int)"}
    for name,record in [('01_planner.json',planner),('02_coder.json',coder),('03_reviewer.json',reviewer)]:
        (base/name).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    validate_files(base)
    (base/'transcript.md').write_text("""# Офлайн-репетиція ролей — НЕ Copilot Agent\n\nPlanner: ADR `proposed`; зберегти int-підкласи, заборонити bool; потрібна згода.\n\nCoder (перший кандидат): запропонував `type(limit) is int`.\n\nReviewer: `changes_requested`, помилка — `IntSubclass(5)` стає недопустимим; handoff назад Coder.\n\nCoder (скоригована пропозиція): `isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= 30)`; тести для int-підкласів.\n\nReviewer (контроль прикладу): логіка відповідає контракту; справжня перевірка змін у WebStorm та `pytest` потрібні після застосування патча.\n\nЦей транскрипт створений скриптом детерміновано та **не свідчить** про LLM-виклики чи дозвіл людини на зміни.\n""",encoding='utf-8')
    print('Created OFFLINE rehearsal only in',base)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['validate','rehearse']);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--allow-example',action='store_true')
    a=p.parse_args();root=a.root.resolve()
    if a.action=='rehearse': rehearse(root)
    else:
        base=root/'docs/pr6/offline-example' if a.allow_example else root/'docs/pr6/handoffs'
        validate_files(base)
if __name__=='__main__': main()
