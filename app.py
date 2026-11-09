"""Дашборд анализа процесса разработки ПО (Dash).

Запуск: python app.py  ->  http://127.0.0.1:8050
CSV с метриками загружается пользователем через веб-интерфейс (dcc.Upload).
"""
import base64
import io

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table

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


def kpi_card(title: str, value: str, color: str = "primary") -> dbc.Col:
    """Одна KPI-карточка."""
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H6(title, className="card-title text-muted mb-1"),
                html.H3(value, className=f"text-{color} mb-0"),
            ])
        ]),
        md=2,
        className="mb-4",
    )


def filter_controls() -> dbc.Card:
    """Панель фильтров."""
    return dbc.Card([
        dbc.CardHeader("Фильтры"),
        dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.Label("Команда", className="form-label fw-bold"),
                    dcc.Dropdown(
                        id="team-filter",
                        multi=True,
                        placeholder="Все команды",
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Тип задачи", className="form-label fw-bold"),
                    dcc.RadioItems(
                        id="issue-type-filter",
                        options=[
                            {"label": "Все", "value": "All"},
                            {"label": "Feature", "value": "Feature"},
                            {"label": "Bug", "value": "Bug"},
                            {"label": "Task", "value": "Task"},
                        ],
                        value="All",
                        inline=True,
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Период", className="form-label fw-bold"),
                    dcc.DatePickerRange(
                        id="date-range-filter",
                        display_format="YYYY-MM-DD",
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Story points", className="form-label fw-bold"),
                    dcc.RangeSlider(
                        id="story-points-filter",
                        min=1, max=13, step=1,
                        value=[1, 13],
                        marks={i: str(i) for i in range(1, 14)},
                    ),
                ], md=3),
            ])
        ),
    ], className="mb-4")


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
        filter_controls(),
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


# ---------------------------------------------------------------------------
# Колбэк 1: обновление опций фильтров при загрузке CSV
# ---------------------------------------------------------------------------
@callback(
    Output("team-filter", "options"),
    Output("issue-type-filter", "options"),
    Output("date-range-filter", "min_date_allowed"),
    Output("date-range-filter", "max_date_allowed"),
    Output("date-range-filter", "start_date"),
    Output("date-range-filter", "end_date"),
    Output("story-points-filter", "min"),
    Output("story-points-filter", "max"),
    Output("story-points-filter", "value"),
    Output("story-points-filter", "marks"),
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_filters(contents, filename):
    if contents is None:
        empty_opts = []
        all_types = [
            {"label": "Все", "value": "All"},
            {"label": "Feature", "value": "Feature"},
            {"label": "Bug", "value": "Bug"},
            {"label": "Task", "value": "Task"},
        ]
        return (
            empty_opts, all_types, None, None, None, None,
            1, 13, [1, 13], {i: str(i) for i in range(1, 14)},
            "",
        )

    try:
        df = parse_contents(contents)
    except Exception as exc:  # noqa: BLE001
        return (
            [], [
                {"label": "Все", "value": "All"},
                {"label": "Feature", "value": "Feature"},
                {"label": "Bug", "value": "Bug"},
                {"label": "Task", "value": "Task"},
            ], None, None, None, None,
            1, 13, [1, 13], {i: str(i) for i in range(1, 14)},
            dbc.Alert(f"Ошибка чтения CSV: {exc}", color="danger"),
        )

    teams = sorted(df["team"].dropna().unique().tolist())
    team_opts = [{"label": t, "value": t} for t in teams]

    types = sorted(df["issue_type"].dropna().unique().tolist())
    type_opts = [{"label": "Все", "value": "All"}] + \
        [{"label": t, "value": t} for t in types]

    min_date = df["date"].min().date().isoformat()
    max_date = df["date"].max().date().isoformat()

    sp_min = int(df["story_points"].min())
    sp_max = int(df["story_points"].max())
    sp_marks = {i: str(i) for i in range(sp_min, sp_max + 1)}

    msg = dbc.Alert(
        f"Файл «{filename}» загружен: {len(df)} строк, "
        f"{min_date} — {max_date}.",
        color="success",
    )

    return (
        team_opts, type_opts, min_date, max_date, min_date, max_date,
        sp_min, sp_max, [sp_min, sp_max], sp_marks, msg,
    )

# ---------------------------------------------------------------------------
# Колбэк 2: обновление дашборда (KPI, графики, таблица) по фильтрам
# ---------------------------------------------------------------------------
@callback(
    Output("kpi-container", "children"),
    Output("line-chart", "figure"),
    Output("pie-chart", "figure"),
    Output("hist-chart", "figure"),
    Output("scatter-chart", "figure"),
    Output("sprint-table-container", "children"),
    Input("team-filter", "value"),
    Input("issue-type-filter", "value"),
    Input("date-range-filter", "start_date"),
    Input("date-range-filter", "end_date"),
    Input("story-points-filter", "value"),
    Input("upload-data", "contents"),
)
def update_dashboard(teams, issue_type, start_date, end_date, sp_range, contents):
    if contents is None:
        empty_kpi = dbc.Row([
            kpi_card("Задач", "—"),
            kpi_card("Закрыто", "—"),
            kpi_card("Багов", "—"),
            kpi_card("Story points", "—"),
            kpi_card("Средний lead time", "—"),
            kpi_card("Коммитов", "—"),
        ])
        empty_table = dbc.Alert("Загрузите CSV-файл", color="warning")
        return (
            empty_kpi,
            empty_fig("Загрузите CSV-файл"),
            empty_fig("Загрузите CSV-файл"),
            empty_fig("Загрузите CSV-файл"),
            empty_fig("Загрузите CSV-файл"),
            empty_table,
        )

    try:
        df = parse_contents(contents)
    except Exception as exc:  # noqa: BLE001
        err = dbc.Alert(f"Ошибка чтения CSV: {exc}", color="danger")
        empty_fig_err = empty_fig("Ошибка данных")
        return (
            dbc.Row([kpi_card("Ошибка", "—", color="danger")]),
            empty_fig_err, empty_fig_err, empty_fig_err, empty_fig_err,
            err,
        )

    # --- Применяем фильтры ---
    dff = df.copy()
    if teams:
        dff = dff[dff["team"].isin(teams)]
    if issue_type and issue_type != "All":
        dff = dff[dff["issue_type"] == issue_type]
    if start_date:
        dff = dff[dff["date"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["date"] <= pd.to_datetime(end_date)]
    if sp_range:
        dff = dff[dff["story_points"].between(sp_range[0], sp_range[1])]

    if dff.empty:
        empty_kpi = dbc.Row([
            kpi_card("Задач", "0"),
            kpi_card("Закрыто", "0"),
            kpi_card("Багов", "0"),
            kpi_card("Story points", "0"),
            kpi_card("Средний lead time", "0.0"),
            kpi_card("Коммитов", "0"),
        ])
        msg = dbc.Alert("Нет данных после применения фильтров", color="warning")
        return (
            empty_kpi,
            empty_fig("Нет данных по выбранным фильтрам"),
            empty_fig("Нет данных по выбранным фильтрам"),
            empty_fig("Нет данных по выбранным фильтрам"),
            empty_fig("Нет данных по выбранным фильтрам"),
            msg,
        )

    # --- KPI ---
    total_tasks = len(dff)
    done_tasks = int((dff["status"] == "Done").sum())
    bug_tasks = int((dff["issue_type"] == "Bug").sum())
    total_sp = int(dff["story_points"].sum())
    avg_lead = round(dff["lead_time_days"].mean(), 1)
    total_commits = int(dff["commits"].sum())

    kpis = dbc.Row([
        kpi_card("Задач", str(total_tasks), "primary"),
        kpi_card("Закрыто", str(done_tasks), "success"),
        kpi_card("Багов", str(bug_tasks), "danger"),
        kpi_card("Story points", str(total_sp), "info"),
        kpi_card("Средний lead time", f"{avg_lead} дн.", "warning"),
        kpi_card("Коммитов", str(total_commits), "secondary"),
    ])

    # --- Линейный график: задачи + коммиты по датам (две оси Y) ---
    daily = (
        dff.groupby(dff["date"].dt.date)
        .agg(tasks=("issue_type", "size"), commits=("commits", "sum"))
        .reset_index()
        .sort_values("date")
    )
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily["date"], y=daily["tasks"],
        name="Задачи", mode="lines+markers",
        line=dict(color="#198754"),
    ))
    fig_line.add_trace(go.Scatter(
        x=daily["date"], y=daily["commits"],
        name="Коммиты", mode="lines+markers",
        yaxis="y2", line=dict(color="#0d6efd"),
    ))
    fig_line.update_layout(
        title="Динамика задач и коммитов по дням",
        xaxis_title="Дата",
        yaxis_title="Количество задач",
        yaxis2=dict(title="Коммиты", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # --- Круговая диаграмма: распределение по типам задач ---
    type_counts = dff["issue_type"].value_counts().reset_index()
    type_counts.columns = ["issue_type", "count"]
    fig_pie = go.Figure(data=[go.Pie(
        labels=type_counts["issue_type"],
        values=type_counts["count"],
        hole=0.4,
        textinfo="label+percent",
    )])
    fig_pie.update_layout(
        title="Распределение задач по типам",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # --- Гистограмма lead time ---
    fig_hist = go.Figure(data=[go.Histogram(
        x=dff["lead_time_days"],
        nbinsx=20,
        marker_color="#6f42c1",
        opacity=0.75,
    )])
    fig_hist.update_layout(
        title="Распределение lead time (дней)",
        xaxis_title="Lead time, дней",
        yaxis_title="Количество задач",
        margin=dict(l=20, r=20, t=40, b=20),
        bargap=0.1,
    )

    # --- Scatter: story points vs lead time ---
    fig_scatter = go.Figure(data=[go.Scatter(
        x=dff["story_points"],
        y=dff["lead_time_days"],
        mode="markers",
        marker=dict(
            size=8,
            color=dff["story_points"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Story points"),
        ),
        text=[
            f"Команда: {t}<br>Тип: {it}<br>Статус: {s}<br>Коммиты: {c}"
            for t, it, s, c in zip(
                dff["team"], dff["issue_type"], dff["status"], dff["commits"]
            )
        ],
        hovertemplate="%{text}<br>Story points: %{x}<br>Lead time: %{y} дн.<extra></extra>",
    )])
    fig_scatter.update_layout(
        title="Story points vs lead time",
        xaxis_title="Story points",
        yaxis_title="Lead time, дней",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # --- Таблица по спринтам ---
    sprint_stats = (
        dff.groupby("sprint")
        .agg(
            задачи=("issue_type", "size"),
            закрыто=("status", lambda s: int((s == "Done").sum())),
            story_points=("story_points", "sum"),
            avg_lead_time=("lead_time_days", "mean"),
            коммиты=("commits", "sum"),
        )
        .reset_index()
    )
    sprint_stats["avg_lead_time"] = sprint_stats["avg_lead_time"].round(1)
    sprint_stats = sprint_stats.sort_values("sprint")

    table = dash_table.DataTable(
        id="sprint-table",
        columns=[
            {"name": "Спринт", "id": "sprint"},
            {"name": "Задач", "id": "задачи", "type": "numeric"},
            {"name": "Закрыто", "id": "закрыто", "type": "numeric"},
            {"name": "Story points", "id": "story_points", "type": "numeric"},
            {"name": "Средний lead time (дн.)", "id": "avg_lead_time", "type": "numeric"},
            {"name": "Коммиты", "id": "коммиты", "type": "numeric"},
        ],
        data=sprint_stats.to_dict("records"),
        sort_action="native",
        sort_mode="multi",
        page_size=13,
        style_cell={"textAlign": "left", "padding": "6px"},
        style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f1f3f5"}
        ],
    )
    sprint_table = dbc.Card([
        dbc.CardHeader("Метрики по спринтам"),
        dbc.CardBody(table),
    ])

    return kpis, fig_line, fig_pie, fig_hist, fig_scatter, sprint_table


if __name__ == "__main__":
    app.run(debug=True)
