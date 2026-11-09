"""Дашборд анализа процесса разработки ПО (Dash).

Запуск: python app.py  ->  http://127.0.0.1:8050
CSV с метриками загружается пользователем через веб-интерфейс (dcc.Upload).
"""
import base64
import io

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html

REQUIRED_COLUMNS = [
    "date", "sprint", "team", "issue_type", "priority", "status",
    "story_points", "lead_time_days", "cycle_time_days", "bugs_fixed", "commits",
]

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Дашборд процесса разработки ПО"


def parse_contents(contents: str) -> pd.DataFrame:
    """Декодирует содержимое dcc.Upload (data:...;base64,...) в DataFrame."""
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"В CSV отсутствуют колонки: {', '.join(missing)}")
    df["date"] = pd.to_datetime(df["date"])
    return df


def empty_fig(msg: str = "Загрузите CSV-файл") -> go.Figure:
    """График-заглушка с текстовым сообщением по центру."""
    fig = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": msg,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 16, "color": "#7b8a8b"},
        }],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


def graph_card(title: str, graph_id: str, md: int = 6) -> dbc.Col:
    """Карточка с заголовком и пустым графиком-заглушкой."""
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody(dcc.Graph(id=graph_id, figure=empty_fig(), style={"height": "340px"})),
        ]),
        md=md,
        className="mb-4",
    )


app.layout = dbc.Container(
    [
        html.H1("Дашборд процесса разработки ПО", className="dashboard-title mt-4"),
        html.P(
            "Анализ метрик разработки: задачи, баги, коммиты, спринты, story points и lead time. "
            "Загрузите CSV-файл с метриками, чтобы начать работу.",
            className="lead dashboard-subtitle",
        ),
        dbc.Card(
            dbc.CardBody([
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(["Перетащите CSV сюда или ", html.A("выберите файл")]),
                    className="upload-box",
                    multiple=False,
                ),
                html.Div(id="upload-status", className="mt-2"),
            ]),
            className="mb-4",
        ),
        # Контейнеры под фильтры, KPI и графики (наполняются на следующих шагах)
        html.Div(id="filters-container"),
        html.Div(id="kpi-container", className="mb-4"),
        dbc.Row([
            graph_card("Динамика задач и коммитов", "line-chart", md=12),
        ]),
        dbc.Row([
            graph_card("Распределение задач по типам", "pie-chart"),
            graph_card("Распределение lead time", "hist-chart"),
        ]),
        dbc.Row([
            graph_card("Story points vs lead time", "scatter-chart", md=12),
        ]),
        html.Div(id="sprint-table-container", className="mb-4"),
    ],
    fluid=True,
)


if __name__ == "__main__":
    app.run(debug=True)
