# Контракт handoff для ПР № 6

**Task ID:** `PR6-STRICT-SEARCH-LIMIT`. Послідовні сесії **Planner → Coder → Reviewer**, а за зауваженнями **Reviewer → Coder → Reviewer**. Це допустимий метод технічної оркестрації за методичкою. Файли агентів містять рольові інструкції; вони не свідчать автоматично про запуск Copilot.

## Спільні обов'язкові поля
- `role`: `planner`, `coder`, `reviewer`.
- `task_id`: `PR6-STRICT-SEARCH-LIMIT`.
- `received_from` або `inputs`: конкретні шляхи/нотатки, версія, стан ADR.
- `decision_rationale` / `design_choices` / `findings`: **чому**, а не лише що зроблено.
- `guardrails`: застосовані правила із `docs/guardrails.md`.
- `handoff_to`: наступна роль і стан.

## Контрольні точки
1. Planner не редагує код; передає вимоги та тести, узгоджує proposed ADR.
2. Coder отримує явне підтвердження для змін (GR-W01), не працює напряму в main (GR-B01), запускає тести, фіксує факти.
3. Reviewer перевіряє edge cases, збереження int-підкласів, відповідність guardrails і факти тестів. Якщо знайдено проблему, створює feedback; Coder реагує і передає нову версію.
4. Жоден агент не читає Obsidian vault файловими інструментами (GR-B03); дозволено лише MCP retrieval.

## Вхідна задача
У `mcp_connector/core.py` було `not isinstance(limit, int)`, що в Python приймає `True` як `1`. У vault є ADR зі статусом **proposed**, отже реалізація не є автоматично схваленою лише фактом наявності ADR.

## Фіксація реального транскрипту
Після кожної Copilot-сесії перенесіть у `docs/pr6/live-transcript.md` фактичні кроки, назву обраного агента, виклики MCP, дозволи, результати команд і зауваження. Не використовуйте приклад offline-rehearsal як доказ реального multi-agent tool-use.
