"""Offline static checks for the two PR5 SKILL.md files.
Does NOT pretend that Copilot invoked the skills.
"""
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
SKILLS=('task-manager-unit-tests','task-manager-adr')

def validate():
    problems=[]
    for name in SKILLS:
        path=ROOT/'.github'/'skills'/name/'SKILL.md'
        if not path.is_file():
            problems.append(f'Missing: {path}')
            continue
        raw=path.read_text(encoding='utf-8')
        try:
            _,head,body=raw.split('---',2)
            metadata=yaml.safe_load(head)
        except Exception as e:
            problems.append(f'{name}: invalid frontmatter: {e}')
            continue
        if not isinstance(metadata,dict) or metadata.get('name')!=name or not metadata.get('description'):
            problems.append(f'{name}: name/description incorrect')
        for required in ('guardrails','MCP','Формат','preToolUse'):
            if required.casefold() not in body.casefold():
                problems.append(f'{name}: absent instruction: {required}')
        if 'task-manager-vault' not in body:
            problems.append(f'{name}: no vault MCP reference')
    return problems

if __name__=='__main__':
    issues=validate()
    print(f'Skills: {len(SKILLS)} | static errors: {len(issues)}')
    for x in issues:print('ERROR:',x)
    raise SystemExit(bool(issues))
