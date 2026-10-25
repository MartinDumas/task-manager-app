# Практична № 5 — навички агента

**Репозиторій:** `MartinDumas/task-manager-app` (локальний каталог `Data-Engineering`).

1. Скопіюй вміст `task-manager-app/` з цього архіву **поверх** локального клонованого проєкту. Не видаляй наявні `.github/hooks`, `docs`, `mcp_connector`, `tests`.
2. Перевір `Agent Customizations → Skills` у WebStorm. При потребі увімкни `Enable Skills` у Copilot Agent Settings та створи нову сесію. Використай явні промпти з `docs/pr5-test-cases.md`.
3. Для тестів: `source .venv312/bin/activate` і `python -m pytest -q tests/test_skill_unit_tasks.py tests/test_skill_manifest.py`.
4. Для локальної симуляції ADR: `python scripts/demo_adr_local.py`. Ця команда не звертається до Copilot, не запускає MCP і не пушить до GitHub.
5. Лише Copilot із запущеним `task-manager-vault` MCP має виконати справжні `ingest_note`; перед записом потрібна згода на guardrails `ask`. Не вводь PAT у файли/чат.
6. Коміт у feature-гілку та PR до main (GR-B01); не використовуй прямий push main.

**Примітка.** Перші 2 тести демонструють код реалізації сценарію U1/U2; перевірка того, що агент сам застосував skill, здійснюється на Mac та підтверджується журналом Copilot.
