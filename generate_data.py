"""Одноразовый скрипт генерации тестового CSV с метриками процесса разработки ПО.

Запуск:  python generate_data.py
Результат: data/dev_metrics.csv (воспроизводимо, random.seed(42))
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_ROWS = 280
START = date(2024, 1, 1)
END = date(2024, 6, 30)
SPRINT_DAYS = 14

TEAMS = ["Backend", "Frontend", "QA", "DevOps"]
ISSUE_TYPES = ["Feature", "Bug", "Task"]
ISSUE_WEIGHTS = [0.40, 0.30, 0.30]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
PRIORITY_WEIGHTS = [0.20, 0.45, 0.25, 0.10]
STATUSES = ["Done", "In Progress", "Blocked"]
STATUS_WEIGHTS = [0.80, 0.14, 0.06]
STORY_POINTS = [1, 2, 3, 5, 8, 13]
STORY_POINT_WEIGHTS = [0.20, 0.25, 0.25, 0.17, 0.09, 0.04]

COLUMNS = [
    "date", "sprint", "team", "issue_type", "priority", "status",
    "story_points", "lead_time_days", "cycle_time_days", "bugs_fixed", "commits",
]


def sprint_name(d: date) -> str:
    """Спринт по 2 недели, отсчёт от START: Sprint 1 ... Sprint 13."""
    return f"Sprint {(d - START).days // SPRINT_DAYS + 1}"


def build_row(d: date) -> dict:
    issue_type = random.choices(ISSUE_TYPES, ISSUE_WEIGHTS)[0]
    story_points = random.choices(STORY_POINTS, STORY_POINT_WEIGHTS)[0]

    # lead time растёт вместе со story points, диапазон 0.5..10
    base = 0.5 + story_points * 0.55
    lead_time = round(min(10.0, max(0.5, random.gauss(base, 1.2))), 1)
    # cycle time всегда <= lead time
    cycle_time = round(max(0.5, min(lead_time, lead_time * random.uniform(0.4, 1.0))), 1)

    if issue_type == "Bug":
        bugs_fixed = random.randint(1, 10)
    else:
        bugs_fixed = random.choices([0, 1, 2, 3], [0.60, 0.20, 0.12, 0.08])[0]

    return {
        "date": d.isoformat(),
        "sprint": sprint_name(d),
        "team": random.choice(TEAMS),
        "issue_type": issue_type,
        "priority": random.choices(PRIORITIES, PRIORITY_WEIGHTS)[0],
        "status": random.choices(STATUSES, STATUS_WEIGHTS)[0],
        "story_points": story_points,
        "lead_time_days": lead_time,
        "cycle_time_days": cycle_time,
        "bugs_fixed": bugs_fixed,
        "commits": random.randint(0, 40),
    }


def main() -> None:
    random.seed(SEED)
    total_days = (END - START).days
    dates = sorted(START + timedelta(days=random.randint(0, total_days)) for _ in range(N_ROWS))
    rows = [build_row(d) for d in dates]

    out_path = Path(__file__).parent / "data" / "dev_metrics.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
