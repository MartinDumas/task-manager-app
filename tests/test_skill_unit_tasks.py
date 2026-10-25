"""Реальні локальні кейси для демонстрації skill #1 над VaultConnector ПР3.
Не викликає GitHub і не змінює користувацький vault.
"""
from pathlib import Path
import pytest
from mcp_connector.core import VaultConnector, VaultError

@pytest.fixture
def connector(tmp_path: Path):
    (tmp_path / 'MOC-Застосунок.md').write_text('# MOC', encoding='utf-8')
    return VaultConnector(tmp_path, git_sync=False)

def sample(**changes):
    data=dict(title='Перевірка зміни статусу', note_type='decision',
              content='Тестове рішення щодо валідації.',
              source_id='test:pr5:validation', source='docs/pr5-skills.md',
              links=['MOC-Застосунок'], tags=['testing'])
    data.update(changes)
    return data

def test_u1_invalid_source_id_and_title(connector):
    for params in (sample(source_id=''), sample(title='X'*121)):
        with pytest.raises(VaultError):
            connector.ingest_note(**params)
    assert not (connector.vault_path/'Decisions').exists()

def test_u1_invalid_type(connector):
    with pytest.raises(VaultError,match='note_type'):
        connector.ingest_note(**sample(note_type='unknown'))

def test_u2_search_case_and_invalid_limits(connector):
    saved=connector.ingest_note(**sample(content='FASTAPI спрямовує запити до сервісу.'))
    assert connector.search_notes('fastapi')[0]['path']==saved['path']
    assert connector.search_notes('FaStApI')[0]['path']==saved['path']
    for limit in (0,31):
        with pytest.raises(VaultError):
            connector.search_notes('FastAPI', limit=limit)

def test_u2_search_order(connector):
    connector.ingest_note(**sample(content='Пошук Пошук',source_id='test:pr5:sort-1',title='А'))
    connector.ingest_note(**sample(content='Пошук',source_id='test:pr5:sort-2',title='Б'))
    results=connector.search_notes('Пошук')
    assert len(results)>=2
    assert results[0]['matches']>=results[1]['matches']
