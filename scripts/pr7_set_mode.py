#!/usr/bin/env python3
"""Switch search mode for before/after benchmark; do not change MCP configuration."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp_connector.search_mode import set_mode, current_mode

if len(sys.argv) != 2 or sys.argv[1] not in {'lexical', 'semantic'}:
    raise SystemExit('Usage: python scripts/pr7_set_mode.py lexical|semantic')
set_mode(sys.argv[1])
print('Mode:', current_mode())
