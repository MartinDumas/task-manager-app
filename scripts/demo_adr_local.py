"""Local reproducible demonstration of two ADR cases on a TEMP vault.
NOT an MCP/IDE call and NOT published to actual GitHub.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp_connector.core import VaultConnector

CASES=[
 ('A1','Розташування skills Task Manager API','adr:pr5:skills-location',
  'Контекст: повторювані задачі мають однакову процедуру.\nВаріанти: дублювати запити чи зберігати skills у репозиторії.\nРішення: skills зберігати в .github/skills/.\nНаслідок: версіонування і повторне використання.'),
 ('A2','Запуск тестів перед Pull Request','adr:pr5:test-before-pr',
  'Контекст: агент змінює код.\nВаріанти: тести після merge чи до Pull Request.\nРішення: запускати pytest та guardrails до PR.\nНаслідок: менше регресій, додаткова перевірка.'),
]
with TemporaryDirectory(prefix='pr5-adr-demo-') as directory:
    root=Path(directory)
    (root/'MOC-Застосунок.md').write_text('# MOC',encoding='utf-8')
    c=VaultConnector(root,git_sync=False)
    for key,title,sid,content in CASES:
        inp=dict(title=title,note_type='decision',content=content,source_id=sid,
                 source='docs/pr5-skills.md',links=['MOC-Застосунок'],tags=['adr','skills'])
        first=c.ingest_note(**inp)
        second=c.ingest_note(**inp)
        got=c.get_note(first['path'])
        assert first['status']=='created' and first['commit']=='local_only'
        assert second['status']=='unchanged' and got['status']=='ok'
        print(key,'created -> unchanged;',first['path'],'(test-only local vault)')
    assert len(list((root/'Decisions').glob('*.md')))==2
    print('ADR cases: 2 | idempotency checks: 2 | duplicates: 0')
