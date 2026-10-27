# ПР7 — Context Engineering: RAG через чинний MCP-конектор

Проєкт: `MartinDumas/task-manager-app`, WebStorm / Copilot, vault — окремий Git-репозиторій. Джерело істини: Markdown-нотатки vault; індекс — локальний похідний файл SQLite.

## Що додано

- `mcp_connector/vector_search.py`: читання безпечних `.md`, chunking за Markdown-заголовками, multilingual sentence embeddings, зберігання та ранжування cosine similarity у локальному SQLite.
- `mcp_connector/search_mode.py`: локальний перемикач `lexical` / `semantic` без зміни конфігурації MCP у WebStorm.
- Мінімальне оновлення `mcp_connector/core.py` і `mcp_connector/server.py`: agent-facing `search_notes(query, limit=10)` не змінюється, `get_note/ingest_note/ping` працюють як раніше.
- `scripts/pr7_reindex.py`, `scripts/pr7_set_mode.py`, `scripts/pr7_compare.py` та регресійні тести.
- `docs/pr7/benchmark_10.json` — 10 ідентичних контрольних питань для реального порівняння агента до/після.

## Встановлення до WebStorm (Mac)

1. Переконайся, що працюєш у feature-гілці, а локальний `.github/hooks/guardrails.json` збережений. Не використовуй `git add .`.
2. Розпакуй ZIP та з теки архіву виконай:

   ```bash
   python3 INSTALL_PR7.py ~/Documents/Data-Engineering --dry-run
   python3 INSTALL_PR7.py ~/Documents/Data-Engineering
   ```

   Інсталятор робить мінімальні правки тільки в `mcp_connector/core.py` та `server.py`, додає нові файли й правило `.gitignore`. Не змінює hooks, MCP-облікові дані, існуючі профілі агентів та vault; відмовляється перезаписувати чужі файли.

3. У терміналі WebStorm:

   ```bash
   cd ~/Documents/Data-Engineering
   source .venv312/bin/activate
   python -m pytest -q tests/test_pr7_*.py
   python -m pytest -q
   ```

   Якщо `pytest` відсутній, встанови існуючі залежності проєкту відповідно до його `requirements-mcp.txt`.

4. Перед порівнянням зроби **lexical baseline**, не встановлюючи модель:

   ```bash
   python scripts/pr7_set_mode.py lexical
   ```

   Відкрий нову сесію Copilot Agent та постав усі 10 питань із `docs/pr7/benchmark_10.json` через MCP `task-manager-vault.search_notes`. Для кожного зафіксуй отримані джерела й оцінку 0–2 у копії `results_template.json`.

5. Для семантичного пошуку встанови optional runtime (без Homebrew):

   ```bash
   python -m pip install -r requirements-pr7.txt
   python scripts/pr7_reindex.py --vault "$HOME/Documents/task-manager-vault" --enable-semantic
   ```

   Перший запуск `sentence-transformers` завантажує ваги моделі; це може вимагати Інтернету та місця на диску. Надалі embeddings будуються локально. Не вставляй секрети в нотатки, які будуть індексуватися.

6. **Не потрібно редагувати `mcp.json`** і не потрібно додавати окремі tools. Якщо у WebStorm MCP-сервер уже запущений зі старим Python-модулем, перезапусти сервер `task-manager-vault` через Agent Customizations → MCP Servers → Restart Server.
7. З нової сесії Copilot повтори *ті самі* 10 запитів; оцінки й джерела запиши в `docs/pr7/results_actual.json` (створи копію шаблону, не включай конфіденційні дані). Підсумок:

   ```bash
   python scripts/pr7_compare.py docs/pr7/results_actual.json
   ```

## Як оціночувати

- `0` — немає відповіді/джерела або факт неправильний;
- `1` — частково правильна відповідь, не підтверджено всі твердження;
- `2` — правильна відповідь з посиланням на релевантний документ vault.

Для чесного A/B утримуй незмінними питання, підказки агента, доступні MCP tools і версію vault. Запускай **нову сесію Copilot** після перемикання режиму, щоб попередні retrieval-відповіді не потрапили у контекст.

## Guardrails та зміни vault

- Агенти читають знання лише через наявний MCP `task-manager-vault`.
- `get_note` і `ingest_note` не змінено; `git_sync` і підтвердження guardrails залишаються як у ПР3–ПР6.
- Індекс зберігається у `.pr7-vector-index/` у репозиторії застосунку; додано до `.gitignore`, не комітиться і не є джерелом істини.
- Після запису нової нотатки індекс позначається застарілим. Повторно запусти `scripts/pr7_reindex.py` (як вище) — не використовується тихий, застарілий індекс.
- `matches` у semantic-режимі відображає *буквальну* кількість входжень у chunk і може дорівнювати 0, навіть якщо chunk семантично релевантний. Ранжування визначають embeddings, а формат результату зберігає `path`, `matches`, `preview`.
- Семантичний результат — підказка, не підтверджений факт: для критичного твердження слід прочитати нотатку `get_note`.

## Публікація

Після перевірки реальних результатів створи PR із нової feature-гілки в `main`. До індексу Git додай тільки код, документацію, реальні знеособлені результати і тести. Не додавай `.pr7-vector-index/`, `.venv312/`, `.idea/`, `mcp.json` і локально змінений `.github/hooks/guardrails.json`.

**Статус стартового комплекту:** структурні та regression тести виконані локально зі штучним тестовим embedder; реальна якість multilingual-моделі та відповіді Copilot не перевірені до запуску на Mac.
