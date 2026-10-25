# Онтологія Task Manager API (ПР4)

## Таксономія сутностей

| Тип YAML `type` | Каталог | Приклад | Семантика |
|---|---|---|---|
| concept | Concepts/ | Task, TaskStatus | Предметні сутності та правила |
| component | Components/ | ApiRouter, ServiceLayer | Технічні модулі (частина ще запланована) |
| decision | Decisions/ | ADR-002-SeparateKnowledgeVault | Архітектурні рішення |
| glossary | Glossary/ | DomainGlossary | Визначення термінів |
| moc | Корінь vault | MOC-Застосунок | Навігаційний вузол |
| template | Templates/ | Template-Decision | Шаблон нотатки |
| guide | Корінь vault | README | Інструкція користування сховищем |

## Типізовані відношення (5)

| Предикат | Зміст | Приклад |
|---|---|---|
| `depends_on` | Компонент потребує іншого компонента | `ApiRouter → ServiceLayer` |
| `implements` | Компонент реалізує доменну концепцію | `ServiceLayer → TaskWorkflow` |
| `governed_by` | Компонент підпорядкований архітектурному рішенню | `RepositoryLayer → ADR-003-StorageAndORM` |
| `verifies` | Тестовий компонент перевіряє інший | `TestSuite → ApiRouter` |
| `related_to` | Змістовний симетричний зв'язок без напрямку реалізації | `Task → TaskStatus` |

## Формат запису

Файли Markdown з YAML frontmatter. Значення предикатів — масив точних **stem** (назв файлів без `.md`), не мітки користувача; перевіряються скриптом `scripts/validate_ontology.py`. Wiki-посилання в тексті залишаються для навігації в Obsidian.

```yaml
---
type: component
title: API Router
depends_on: [ServiceLayer]
implements: [Task]
governed_by: [ADR-001-LocalRESTAPI]
---
```

Семантичні ребра є додатковими до wiki-посилань; вони не змінюють фактичну бізнес-архітектуру з ПР1.

## Теги

`domain`, `task`, `status` — предметна область; `architecture`, `api`, `service`, `repository` — компоненти; `adr`, `security`, `knowledge` — рішення; `glossary`, `navigation` — довідкові та MOC. Нові теги за потреби не змінюють визначені типи.

## Перевірка

`python3 scripts/validate_ontology.py /absolute/path/to/task-manager-vault`

Скрипт перевіряє типи, директорії, існування цілей зв'язків, відсутність самопосилань та дублікатів назв. Це легковаге семантичне представлення, а не OWL/RDF-онтологія.
