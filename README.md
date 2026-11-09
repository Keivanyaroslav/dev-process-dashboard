# dev-process-dashboard

Дашборд анализа процесса разработки программного обеспечения на **Dash (Python)**.
Инструмент для визуального анализа метрик задач, багов, коммитов, спринтов, story points и lead time.
CSV-файл с данными загружается пользователем через веб-интерфейс — не из кода.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.17.0-blue.svg)](https://dash.plotly.com/)
[![dash-bootstrap-components](https://img.shields.io/badge/dbc-1.6.0-blue.svg)](https://dash-bootstrap-components.opensource.faculty.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Установка и запуск

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Keivanyaroslav/dev-process-dashboard.git
cd dev-process-dashboard

# 2. Создайте и активируйте виртуальное окружение
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS:
python -m venv .venv
source .venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Запустите дашборд
python app.py
```

Дашборд откроется по адресу: http://127.0.0.1:8050

## Формат CSV

CSV-файл загружается через компонент `dcc.Upload` на странице дашборда.
Ожидаются следующие колонки:

| Колонка | Описание | Пример |
|---------|----------|--------|
| `date` | Дата записи | 2024-01-15 |
| `sprint` | Название спринта | Sprint 1 |
| `team` | Команда разработки | Backend, Frontend, QA, DevOps |
| `issue_type` | Тип задачи | Feature, Bug, Task |
| `priority` | Приоритет | Low, Medium, High, Critical |
| `status` | Статус | Done, In Progress, Blocked |
| `story_points` | Story points (сложность) | 1, 2, 3, 5, 8, 13 |
| `lead_time_days` | Lead time, дни | 0.5 – 10 |
| `cycle_time_days` | Cycle time, дни (≤ lead_time) | 0.5 – 10 |
| `bugs_fixed` | Количество исправленных багов | 0 – 10 |
| `commits` | Количество коммитов | 0 – 40 |

Тестовый файл уже сгенерирован: `data/dev_metrics.csv` (280 строк, период 2024-01-01 … 2024-06-30).
Скрипт генерации: `generate_data.py` (воспроизводимо, `random.seed(42)`).

## Элементы интерфейса

| Элемент | Назначение |
|---------|------------|
| `dcc.Upload` | Загрузка CSV-файла через веб-интерфейс |
| Dropdown (команда) | Мультивыбор одной или нескольких команд (Backend, Frontend, QA, DevOps) |
| RadioItems (тип задачи) | Фильтр по типу задачи: Feature / Bug / Task / Все |
| DatePickerRange | Выбор временного периода (дата начала и конца) |
| RangeSlider (story points) | Диапазон фильтрации по story points (1–13) |
| Линейный график | Динамика количества задач и коммитов по дням (две оси Y) |
| Круговая диаграмма | Распределение задач по типам (donut, hole=0.4) |
| Гистограмма | Распределение lead time по дням |
| Scatter-график | Story points vs lead time с цветовой кодировкой и hover-подсказками |
| DataTable | Метрики по спринтам с нативной сортировкой |
| KPI-карточки (6 шт.) | Задач, закрыто, багов, story points, средний lead time, коммитов |

Все элементы работают совместно: при изменении любого фильтра все графики, KPI и таблица пересчитываются в реальном времени.

## Структура проекта

```
dev-process-dashboard/
├── app.py                 # Основной файл дашборда (Dash)
├── generate_data.py       # Скрипт генерации тестового CSV
├── requirements.txt       # Зависимости Python
├── README.md              # Этот файл
├── data/
│   └── dev_metrics.csv    # Тестовый CSV с метриками (280 строк)
└── assets/
    └── style.css          # Пользовательская стилизация
```

## Используемые технологии

- Python 3.10+
- Dash 2.17.0
- dash-bootstrap-components 1.6.0 (тема FLATLY)
- pandas 2.2.2
- plotly 5.22.0

## Ветки и релиз

- `main` — главная ветка (стабильная версия)
- `test` — ветка разработки
- `release` — релизная ветка (формируется путем слияния из `test`)

Для создания релиза отправьте Pull Request из `test` в `release` через веб-интерфейс GitHub:
https://github.com/Keivanyaroslav/dev-process-dashboard/compare/release...test
