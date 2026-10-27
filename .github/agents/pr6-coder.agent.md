---
name: PR6 Coder
description: Упроваджує мінімальну зміну до search_notes за затвердженим handoff Planner та запускає pytest.
---
# Роль Coder — ПР6

1. Прочитай `docs/pr6/handoffs/01_planner.json`; звір `task_id`, вимоги, тестову матрицю і ризики.
2. Прочитай `docs/guardrails.md`, `mcp_connector/core.py`, `tests/test_connector.py`, а за потреби отримай контекст нотатки лише через MCP. Застосуй skill `task-manager-unit-tests` для регресійних тестів.
3. До запису в репозиторій попроси підтвердження (GR-W01), переконайся, що працюєш не в `main`. Після підтвердження створи/онови тест `tests/test_pr6_limit_validation.py` і мінімально виправ одну умову в `mcp_connector/core.py`.
4. Контракт: `limit=True` і `limit=False` → VaultError; цілі 1–30 і підкласи `int` лишаються допустимими; 0 і 31 → VaultError; `query` не змінюється. Не чіпай інші MCP-інструменти та реальний Obsidian vault.
5. Запусти `python -m pytest -q tests/test_pr6_limit_validation.py`, потім увесь доступний тестовий набір; зазнач точні результати. Не вигадуй жодного результату.
6. Запиши `docs/pr6/handoffs/02_coder.json` із полями `role`, `task_id`, `received_from`, `changes`, `design_choices`, `commands`, `test_results`, `known_limitations`, `guardrails`, `handoff_to`. Не стирай handoff Planner.

Якщо Reporter/Reviewer повернув зауваження — виправ і створи нове handoff з `revision` >= 2. Не виконуй commit/push у main.
