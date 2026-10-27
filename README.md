# Task Manager API — інженерія даних та знань

Навчальний проєкт практичних робіт № 1–7 із дисципліни **«Інженерія даних та знань»**. Предметна область — менеджер завдань (Task Manager API).

Цей репозиторій містить **специфікації майбутнього API**, MCP-конектор до окремої бази знань Obsidian, правила безпеки для агентів, навички Copilot, профілі агентів, RAG-пошук та автоматизовані тести. **Повноцінний REST API на FastAPI тут ще не реалізовано**: його модель і вимоги описано в [документації](docs/app-requirements.md).

## Виконані практичні роботи

| Робота | Результат |
| --- | --- |
| ПР1 | Вимоги до Task Manager API та агентного середовища |
| ПР2 | Окремий Obsidian knowledge vault (інший GitHub-репозиторій) |
| ПР3 | MCP-сервер: `ping`, `get_note`, `search_notes`, `ingest_note` |
| ПР4 | Онтологія знань, guardrails і Git / preToolUse hooks |
| ПР5 | Copilot skills для unit-тестування та ADR |
| ПР6 | Planner → Coder → Reviewer, структуровані handoff і регресійні тести |
| ПР7 | Семантичний RAG над Markdown-нотками: chunking, embeddings, SQLite та порівняння пошуку |

## Структура репозиторію

- `docs/` — вимоги, онтологія, guardrails, сценарії перевірки, документи оркестрації й результати RAG.
- `mcp_connector/` — реалізація контрольованого доступу до Obsidian і двох режимів пошуку.
- `.github/skills/` — дві навички Copilot для тестів та ADR.
- `.github/agents/` — профілі Planner, Coder і Reviewer.
- `.github/hooks/`, `.githooks/` — правила та Git hooks.
- `scripts/` — валідація, переіндексація, перемикання режиму, оцінювання експерименту.
- `tests/` — ізольовані unit- та регресійні тести.
- `config/mcp.jetbrains.example.json` — **шаблон**, не приватна MCP-конфігурація.

Ключові документи: [вимоги до API](docs/app-requirements.md), [вимоги до harness](docs/harness-requirements.md), [онтологія](docs/ontology.md), [guardrails](docs/guardrails.md), [контракт handoff](docs/pr6/handoff-contract.md), [план RAG-експерименту](docs/pr7/TEST_PLAN.md).

## Швидкий запуск і тести

Потрібні Python 3.12+ та Git. Наприклад, на macOS:

```bash
python3 -m venv .venv312
source .venv312/bin/activate
python -m pip install -r requirements-mcp.txt
python -m pytest -q
```

Під час виконання ПР7 повний набір містив **54 успішні тести**. Усі тести виконуються на тимчасових даних: для звичайної перевірки не потрібно відкривати особистий Obsidian vault.

## MCP та Obsidian

База знань живе **в окремому репозиторії** `MartinDumas/task-manager-vault`, поза робочим деревом цього проєкту. Конектор `mcp_connector/server.py` надає типізовані MCP-інструменти; шлях до vault визначається локально змінною `TASK_MANAGER_VAULT_PATH`. Для операцій запису діють окремі дозволи й Git-перевірки.

Для налаштування WebStorm орієнтуйтеся на `config/mcp.jetbrains.example.json`, **замінюючи всі прикладні шляхи/облікові дані локально**. Не додавайте токени, `mcp.json`, віртуальні середовища або реальний vault до Git.

## RAG: lexical і semantic

```bash
# Додаткові залежності для реальної multilingual-моделі
python -m pip install -r requirements-pr7.txt

# Індекс створюється локально поза Obsidian vault; перший запуск завантажує модель
python scripts/pr7_reindex.py --vault "$HOME/Documents/task-manager-vault" --enable-semantic

# За потреби можна повернутися до буквального пошуку
python scripts/pr7_set_mode.py lexical
```

У режимі semantic використовується модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` і локальний SQLite-індекс `.pr7-vector-index/`. API MCP `search_notes(query, limit)` залишається незмінним. Після зміни нотаток індекс треба побудувати повторно.

**Експеримент ПР7:** десять однакових запитань через Copilot і MCP дали **0/20 балів** у буквальному режимі та **11/20** у семантичному. Це оцінки відповідей, перевірених за нотатками, а не загальний показник точності моделі: довгі запитання створювали складні умови для пошуку точного підрядка. [Питання](docs/pr7/benchmark_10.json) · [Фактичні оцінки](docs/pr7/results_actual.json) · [Методика](docs/pr7/TEST_PLAN.md).

Підсумок обчислюється з уже перевірених оцінок:

```bash
python scripts/pr7_compare.py docs/pr7/results_actual.json
```

## Безпека й відтворюваність

- Агент звертається до бази знань **через MCP**, а не через прямий доступ до файлів vault.
- Запис у vault і редагування коду потребують відповідного підтвердження; прямий push до `main` заборонений правилами проєкту.
- Векторний індекс `.pr7-vector-index/`, локальні середовища, IDE-налаштування та `mcp.json` виключені з Git.
- `docs/pr6/offline-example/` — **навчальна офлайн-репетиція**, не запис реальних сесій Copilot; реальні зафіксовані кроки й handoff зберігаються окремо у `docs/pr6/`.

Репозиторій зберігає вихідний код і результати практичних робіт, а оформлені звіти DOCX подаються окремо.
