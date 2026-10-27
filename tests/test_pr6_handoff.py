import sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pr6_orchestration import TASK_ID, validate, REQUIRED

def _record(role):
    d={k:['evidence'] for k in REQUIRED[role]}
    d.update(role=role,task_id=TASK_ID,guardrails=['GR-W01'])
    if role == 'planner': d['inputs']=['vault ADR proposed'];d['handoff_to']='coder'
    if role == 'reviewer': d['decision']='changes_requested'
    return d

@pytest.mark.parametrize('role', ['planner','coder','reviewer'])
def test_handoff_valid(role):
    assert validate(_record(role),role)

def test_handoff_rejects_missing_rationale():
    d=_record('planner');d.pop('decision_rationale')
    with pytest.raises(ValueError, match='missing keys'): validate(d,'planner')

def test_handoff_rejects_wrong_task_id():
    d=_record('coder');d['task_id']='OTHER'
    with pytest.raises(ValueError,match='mismatch'):validate(d,'coder')

def test_review_requires_explicit_decision():
    d=_record('reviewer');d['decision']='maybe'
    with pytest.raises(ValueError, match='invalid decision'):validate(d,'reviewer')

def test_planner_must_preserve_proposed_adr_status():
    d=_record('planner');d['inputs']=['approved ADR']
    with pytest.raises(ValueError, match='approval status'):validate(d,'planner')
