# ПР3 — MCP-конектори для Task Manager API

Цей каталог треба **влити у корінь існуючого** репозиторію
`https://github.com/MartinDumas/task-manager-app`; це не новий Git-репозиторій.

Склад:

- `mcp_connector/core.py` — ingestion/retrieval + git pull/commit/push + перевірка ідемпотентності;
- `mcp_connector/server.py` — власний stdio MCP-сервер (`ping`, `get_note`, `search_notes`, `ingest_note`);
- `tests/test_connector.py` — локальні автоматичні тести (включно з git bare remote);
- `config/mcp.jetbrains.example.json` — **лише шаблон**, не готова приватна конфігурація;
- `requirements-mcp.txt` — залежності MCP SDK 1.x, PyYAML, pytest.

На macOS:

```bash
# у корені task-manager-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-mcp.txt
PYTHONPATH=. python -m pytest -v tests/
```

**Два окремі клони:** наприклад, `~/Documents/task-manager-app` (відкрито у WebStorm)
і `~/Documents/task-manager-vault` (НЕ додавати у workspace IDE).

Налаштування в GitHub Copilot → Settings → Model Context Protocol → Configure.
У конфігурації заміни `ABSOLUTE/PATH` на **фактичні абсолютні шляхи Mac**.
GitHub PAT створюй із мінімальними правами на `task-manager-app`; вставляй
**тільки в локальний mcp.json Copilot**, не у Git-репозиторій і не у чат.

Важливо: у цьому пакеті **не стверджується, що GitHub MCP уже підключено
до твого WebStorm**: це потрібно перевірити локально у режимі Agent.

Для `ingest_note` налаштування `VAULT_GIT_SYNC=true` вимагає git-клон vault
із налаштованим origin та правом push, а також чисте дерево перед записом.
Щоб безпечно перевірити локальні нотатки без комітів, постав `false`.

Конфігурація не встановлює справжню OS-пісочницю: агент із довільними
shell-командами може мати ширші права. Практична №4 присвячена технічному
посиленню guardrails і обмеженню доступу.

Детальні дії та підказки для Copilot — у файлі `ІНСТРУКЦІЯ_ЗАПУСКУ_ПР3.md` поряд з архівом.
