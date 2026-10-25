# Сценарії перевірки skills (ПР5)

Сценарії U1–U2 й A1–A2 обрано із фактичних модулів/архітектури Task Manager API. **У звіті** окремо позначаються локальні тести і перевірки, які належить виконати у Copilot на Mac.

## U1 — unit-тести валідації `VaultConnector` (skill `task-manager-unit-tests`)
Промпт: «Використай skill `task-manager-unit-tests`. Через MCP `search_notes` знайди нотатки про валідацію, прочитай потрібні `get_note`, потім перевір `VaultConnector.ingest_note`: порожній source_id, довгий title і недопустимий note_type. Додай тести в новий файл, не змінюй продуктивний код. Попроси схвалення на запис, запусти pytest і подай звіт.»
Критерій: негативні випадки породжують `VaultError`; фактичний запуск pytest успішний; є MCP retrieval у логу.

## U2 — регресійний тест `search_notes` (skill `task-manager-unit-tests`)
Промпт: «Використай skill `task-manager-unit-tests` для пошуку в `VaultConnector.search_notes`: перевір нечутливість до регістру, порядок сортування та недопустимі limit=0/31. Звернися до Obsidian vault лише через MCP, отримай схвалення перед записом тестів та покажи результат pytest.»
Критерій: правила пошуку перевірені автоматизованим тестом; немає реальної мережі.

## A1 — ADR розташування skills (skill `task-manager-adr`)
Промпт: «Використай skill `task-manager-adr`. Через MCP знайди ADR і MOC, запропонуй прийняте у цьому проєкті рішення про зберігання skills у `.github/skills/`. source_id=`adr:pr5:skills-location`, source=`docs/pr5-skills.md`, links=`["MOC-Застосунок"]`, tags=`["adr", "skills", "copilot"]`. Покажи чернетку для підтвердження, потім `ingest_note` через MCP і `get_note`. Без direct file writes у vault.»
Критерій: створено/оновлено одну ADR-нотатку; повернено фактичний шлях/коміт; нема дублікатів.

## A2 — ADR перевірки перед PR (skill `task-manager-adr`)
Промпт: «Використай skill `task-manager-adr` для ADR: запуск unit-тестів і guardrails до Pull Request. Через MCP знайди відповідні ADR і прочитай нотатку; source_id=`adr:pr5:test-before-pr`, source=`docs/pr5-skills.md`, links=`["MOC-Застосунок", "ADR-005-OntologyGuardrails"]`, tags=`["adr", "testing", "guardrails"]`. Запроси затвердження, запиши через `ingest_note` й повтори той самий запит для перевірки `unchanged`.»
Критерій: спершу `created` або `updated`, повторно `unchanged`; в логу є запит на дозвіл.

## Ручне втручання — журнал для заповнення
| Кейс | Очікувана реакція | Фактичний результат у Copilot | Скріншот |
|---|---|---|---|
| U1 | MCP read → approval → pytest | заповнити після запуску | |
| U2 | MCP read → approval → pytest | заповнити після запуску | |
| A1 | MCP read → approval → ingest | заповнити після запуску | |
| A2 | MCP read → approval → ingest → unchanged | заповнити після запуску | |
