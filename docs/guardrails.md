# Guardrails — Task Manager API (ПР4)

**Підстава:** ЗАВДАННЯ.md, docs/harness-requirements.md (ПР1); Obsidian vault (ПР2–ПР3).  
**Платформа:** WebStorm + GitHub Copilot Agent; hook-конфігурація `.github/hooks/guardrails.json` (JetBrains public preview / Copilot CLI).  
**Сфера:** лише застосунок `task-manager-app`; окремий `task-manager-vault` обслуговує власний MCP-конектор.

## Рівні рішень

| ID | Рівень | Конкретна операція | Технічна реакція |
|---|---|---|---|
| GR-A01 | allow | Читання `docs/*.md`, code review, `get_note`, `search_notes`, `ping` | `allow` |
| GR-A02 | allow | `git status`, `git log`, `git diff`, `pytest` | `allow` (якщо проста команда) |
| GR-A03 | allow | Аналіз структури `Concepts/` через MCP без запису | `allow` |
| GR-W01 | ask | `create`, `edit`, `apply_patch` у коді та документації | `ask` |
| GR-W02 | ask | `git commit` у робочій гілці; інші команди оболонки | `ask` |
| GR-W03 | ask | `ingest_note` — запис у vault через MCP | `ask` |
| GR-W04 | ask | `pip install`, `npm install`, `uv add` | `ask` |
| GR-B01 | block | Прямий `git push origin main`; коміт у main; push до master | `deny` |
| GR-B02 | block | `rm -rf ...`, `git reset --hard`, `git clean -fd`, `git push --force` | `deny` |
| GR-B03 | block | Пряме читання/запис `task-manager-vault` через bash або file tool | `deny` |
| GR-B04 | block | Видалення файлів у `Decisions/` | `deny` |

## Межі гарантій

1. Hook запускає агентна IDE до інструмента, а не до довільних системних процесів. Працює тільки за ввімкнених hooks у підтримуваному агентному середовищі.
2. Інструмент може мати іншу назву чи аргументи; невідомі запити переводяться до `ask`. Shell-рівень без ізоляції не дає абсолютного захисту. Встановлення залежностей та довільне виконання тестів може запускати сторонній код.
3. Додатковий `.githooks/pre-push` блокує прямий push у `main` **лише після локального встановлення** в репозиторії застосунку.
4. Для vault не встановлювати цей git hook: автоматичний `ingest_note` у ПР3 законно робить commit/push до main vault через MCP.
5. Користувач перевіряє результат і схвалює зміни. Після запровадження блокування main розробка ведеться через feature branch та pull request.
6. Тести `tests/test_guardrails.py` перевіряють JSON-рішення скрипта без запуску небезпечних команд; реальний preToolUse у WebStorm потрібно додатково підтвердити скріншотом.

## Увімкнення

Скопіювати файли до кореня `task-manager-app`, зберегти, перевірити `python3 -m pytest -q tests/test_guardrails.py`, перевірити вкладку Agent Customizations → Hooks у WebStorm та створити нову Agent-сесію. Для Git: `sh scripts/install_git_hooks.sh` лише після огляду наявних локальних hooks.
