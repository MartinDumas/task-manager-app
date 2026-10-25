# Практична № 5 — два Agent Skills для Task Manager API

| Skill | Призначення | Місце | Залежності |
|---|---|---|---|
| `task-manager-unit-tests` | генерація стабільних pytest-тестів | `.github/skills/task-manager-unit-tests/SKILL.md` | docs/app-requirements.md, guardrails, MCP retrieval |
| `task-manager-adr` | оформлення ADR у зовнішньому vault | `.github/skills/task-manager-adr/SKILL.md` | guardrails, MCP search/get/ingest, GitHub MCP |

## Модель виклику
GitHub Copilot Agent може вибрати skill за його `description`, або користувач явно просить **використати skill з конкретною назвою**. Skill — інструкція для агента; він **не є самостійним Python-скриптом** і не гарантує, що агент справді викличе MCP без перевірки журналу.

## Межі доступу
- В IDE відкритий лише застосунок `Data-Engineering` (локальний клон `task-manager-app`).
- `task-manager-vault` фізично зберігається поза workspace.
- `search_notes` / `get_note` / `ingest_note` викликаються через MCP, а не напряму з файлової системи.
- До редагування тестів і ingestion застосовуються `ask` та `deny` правила `docs/guardrails.md` і `preToolUse` hook.

## Як зафіксувати перевірку у WebStorm
1. Скопіюй файли skills, створи нову сесію Copilot Agent, перевір у **Agent Customizations → Skills**, що видно обидва skills. Якщо не видно — Settings → Tools → GitHub Copilot → Chat → Agent → Enable Skills; перезапусти сесію.
2. Виконай запити зі `docs/pr5-test-cases.md` та збережи скріншоти: skill selected/loaded, MCP calls, `ask` перед зміною, результати `pytest` / `ingest_note`.
3. Звітуй лише про дійсно виконані Copilot-кроки. Якщо Copilot не викликав skill автоматично, попроси явно використати його за назвою та зафіксуй ручне втручання.
4. Не запускай повторний ingestion до перевірки стану Git у vault, якщо є незавершений push.
