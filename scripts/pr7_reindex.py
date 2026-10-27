#!/usr/bin/env python3
"""Rebuild local semantic vector index. No writes to Obsidian vault."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp_connector.vector_search import EmbeddedVectorIndex, SentenceTransformerProvider, DEFAULT_MODEL
from mcp_connector.search_mode import INDEX_DIR, set_mode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vault', default=os.environ.get('TASK_MANAGER_VAULT_PATH'))
    ap.add_argument('--model', default=DEFAULT_MODEL)
    ap.add_argument('--enable-semantic', action='store_true')
    a = ap.parse_args()
    if not a.vault:
        ap.error('Pass --vault or set TASK_MANAGER_VAULT_PATH')
    index = EmbeddedVectorIndex(Path(a.vault), INDEX_DIR, SentenceTransformerProvider(a.model))
    print(json.dumps(index.rebuild(), ensure_ascii=False, indent=2))
    if a.enable_semantic:
        set_mode('semantic')
        print('Search mode: semantic')

if __name__ == '__main__':
    main()
