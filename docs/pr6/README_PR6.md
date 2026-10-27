# Практична №6 — Оркестрація Planner → Coder → Reviewer

## Як встановити без втрати файлів попередніх практичних

1. Розпакуйте архів у довільну теку, наприклад `~/Downloads/pr6_delivery`.
2. У терміналі з цієї теки виконайте `python3 INSTALL_PR6.py ~/Documents/Data-Engineering`.
3. Скрипт розмістить видимі `agents/*.agent.md` у прихованій `.github/agents/` та додасть решту у `docs/pr6/`, `tests/`, `scripts/`. Він **не переписує** наявні файли та не змінює `mcp_connector/core.py`.
4. Перевірте: `python3 scripts/pr6_orchestration.py rehearse --root .` (для локального прикладу; перевірка реального ланцюга після Copilot).
5. Створіть робочу гілку (`git switch -c feature/pr6-orchestration`, якщо зараз main). Не запускайте `git push origin main`.
6. У WebStorm → Agent Customizations → Agents переконайтеся, що є PR6 Planner, PR6 Coder, PR6 Reviewer (за потреби нова Copilot-сесія). Виконання — **послідовні сесії**; автоматичного переходу IDE не гарантується.

## Запити для Copilot

**Planner:** «Обери агента PR6 Planner. Сплануй виправлення PR6-STRICT-SEARCH-LIMIT у `VaultConnector.search_notes` за ADR proposed, перевір знання тільки через MCP та запиши `docs/pr6/handoffs/01_planner.json`. Жодного коду не редагуй. Показуй рішення та ризики».

**Coder:** «Обери PR6 Coder; прочитай `01_planner.json`, запроси підтвердження для змін коду, реалізуй тільки валідацію bool і тести `tests/test_pr6_limit_validation.py`, запусти pytest, запиши `02_coder.json`. Не змінюй vault, не коміть».

**Reviewer:** «Обери PR6 Reviewer; незалежно звір `01_planner.json`, `02_coder.json`, diff і фактичні тести, перевір підклас int, bool, межі, guardrails. Створи `03_reviewer.json` з рішенням і аргументами. За дефекту поверни Coder».

**Повтор:** якщо `changes_requested`, нова сесія PR6 Coder виправляє код; PR6 Reviewer проводить повторне рев'ю.

## Демонстрація, тести, handoff

- `python3 scripts/pr6_orchestration.py rehearse --root .` — **локальна контрольна демонстрація ролей без LLM**, що створює приклад транскрипту у `docs/pr6/offline-example/`. Не є реальним викликом Copilot.
- `python3 scripts/pr6_orchestration.py validate --root . --allow-example` — перевіряє приклад handoff.
- `python3 -m pytest -q tests/test_pr6_handoff.py` — перевіряє схеми передачі, критичний підклас int і обов'язкові поля.
- У `patches/pr6_limit_validation.patch` є **пропозиція**, а не застосована до живого проєкту зміна. Для демонстрації застосовуйте в окремій feature-гілці після перевірки `git diff --check` і запиту на схвалення.

## Зафіксувати для звіту
Зберегти скріншоти вибору Planner/Coder/Reviewer, `get_note` (MCP), `ask` перед редагуванням, передачі JSON, `pytest`, рішення `changes_requested/approved`, Pull Request. Фактичний транскрипт заповнювати лише за реальними викликами.
