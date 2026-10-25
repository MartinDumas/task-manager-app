# Тестові кейси політики guardrails (ПР4)

| Кейс | Категорія | Вхідний інструмент / аргумент | Очікується |
|---|---|---|---|
| TC-A01 | allow | view docs/app-requirements.md | allow |
| TC-A02 | allow | bash git status | allow |
| TC-A03 | allow | search_notes TaskStatus | allow |
| TC-W01 | ask | edit src/services.py | ask |
| TC-W02 | ask | bash pip install fastapi | ask |
| TC-W03 | ask | ingest_note в Decisions/ через MCP | ask |
| TC-B01 | block | bash git push origin main | deny |
| TC-B02 | block | bash rm -rf docs | deny |
| TC-B03 | block | bash cat /Users/.../task-manager-vault/Decisions/... | deny |
| TC-B04 | block | delete Decisions/ADR-001-LocalRESTAPI.md | deny |

Негативні тести не виконують видалення/пуш насправді: вони подають JSON подій у preToolUse hook та перевіряють рішення. Реальний hook у JetBrains Agent має бути перевірений викликом **безпечної імітації** (без фактичного виконання руйнівних операцій) і скріншотом повідомлення `deny`. Git pre-push окремо тестується синтетичним stdin.
