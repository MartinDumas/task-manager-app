"""Offline tests using deterministic fake embeddings (not model quality claims)."""
from __future__ import annotations
from pathlib import Path
import pytest
from mcp_connector.core import VaultConnector, VaultError
from mcp_connector.vector_search import (EmbeddedVectorIndex, chunk_markdown,
    safe_markdown_files, corpus_fingerprint)


class ExampleEmbedding:
    model_name = 'test-intent-v1'
    def encode(self, texts):
        def vec(text):
            lower = text.casefold()
            if any(t in lower for t in ('термін', 'deadline', 'дедлайн', 'строк', 'коли заверш')):
                return [1., 0., 0.]
            if any(t in lower for t in ('безпека', 'guardrails', 'захист')):
                return [0., 1., 0.]
            return [0., 0., 1.]
        return [vec(t) for t in texts]


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / 'vault';v.mkdir()
    (v/'Deadline.md').write_text('# Дедлайн\nСтрок завершення роботи задається due_date.', encoding='utf-8')
    (v/'Guard.md').write_text('# Безпека\nGuardrails забороняють прямий push у main.', encoding='utf-8')
    return v


def test_chunking_sections_and_overlong():
    chunks = chunk_markdown('# Вступ\nТекст\n## Друге\n' + 'A' * 340, max_chars=100, overlap=20)
    assert chunks[0].startswith('# Вступ')
    assert any('## Друге' in s for s in chunks)
    assert all(0 < len(s) <= 100 for s in chunks)


def test_rebuild_and_semantic_synonym(vault, tmp_path):
    provider = ExampleEmbedding()
    index = EmbeddedVectorIndex(vault, tmp_path / 'index', provider)
    info = index.rebuild()
    assert info['notes'] == 2 and info['chunks'] == 2
    assert index.db_path.exists()
    # Baseline substring fails to find phrase absent from notes.
    baseline = VaultConnector(vault, git_sync=False)
    assert baseline.search_notes('коли завершити') == []
    improved = VaultConnector(vault, git_sync=False, search_mode='semantic',
                              vector_index_dir=index.index_dir, embedding_provider=provider)
    hit = improved.search_notes('коли завершити')[0]
    assert hit['path'] == 'Deadline.md' and set(hit) == {'path','matches','preview'}
    assert hit['matches'] == 0  # semantic relevance despite no literal match


def test_model_change_requires_rebuild(vault, tmp_path):
    ix = EmbeddedVectorIndex(vault, tmp_path/'idx', ExampleEmbedding()); ix.rebuild()
    class Another(ExampleEmbedding): model_name = 'different-model'
    with pytest.raises(ValueError, match='model/format'):
        EmbeddedVectorIndex(vault, tmp_path/'idx', Another()).search('дедлайн',1)


def test_stale_index_detected_and_rebuildable(vault, tmp_path):
    ix = EmbeddedVectorIndex(vault,tmp_path/'idx',ExampleEmbedding()); ix.rebuild()
    (vault/'Guard.md').write_text('# Безпека\nОновлено',encoding='utf-8')
    with pytest.raises(ValueError, match='reindex'):
        ix.search('безпека',2)
    ix.rebuild()
    assert len(ix.search('безпека',2)) == 2


def test_symlinks_and_git_files_ignored(vault, tmp_path):
    outside = tmp_path/'secret.md';outside.write_text('захист',encoding='utf-8')
    (vault/'link.md').symlink_to(outside)
    (vault/'.git').mkdir()
    (vault/'.git'/'ignore.md').write_text('захист',encoding='utf-8')
    assert set(p for p, _ in safe_markdown_files(vault)) == {'Deadline.md','Guard.md'}


def test_reject_bool_and_invalid_limit_in_semantic_mode(vault, tmp_path):
    idx=EmbeddedVectorIndex(vault,tmp_path/'idx',ExampleEmbedding());idx.rebuild()
    c=VaultConnector(vault,git_sync=False,search_mode='semantic',
                     vector_index_dir=idx.index_dir,embedding_provider=ExampleEmbedding())
    for v in (True,False,0,31,'1',1.5,None):
        with pytest.raises(VaultError, match='limit'): c.search_notes('дедлайн',v)
    assert c.search_notes('дедлайн',1)
    assert c.search_notes('дедлайн',30)
    class IntSubclass(int): pass
    assert c.search_notes('дедлайн',IntSubclass(2))


def test_no_index_inside_vault(vault):
    with pytest.raises(ValueError, match='inside'):
        EmbeddedVectorIndex(vault, vault/'.vector', ExampleEmbedding())


def test_index_persistence_without_provider_write(vault,tmp_path):
    i=EmbeddedVectorIndex(vault,tmp_path/'idx',ExampleEmbedding());i.rebuild()
    j=EmbeddedVectorIndex(vault,tmp_path/'idx',ExampleEmbedding())
    assert j.search('захист',1)[0]['path']=='Guard.md'
    assert not (vault/'vault_vectors.sqlite3').exists()
