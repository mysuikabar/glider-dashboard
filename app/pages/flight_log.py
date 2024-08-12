import os
from pathlib import Path
from typing import List

import dash
import dash_bootstrap_components as dbc
import dash_uploader as du
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from igc_processor.circling import compute_heading_transition, detect_circling
from igc_processor.parser import igc2df
from plotly.express import colors
from utils import stats

dash.register_page(__name__)
du.configure_upload(dash.get_app(), "/tmp/uploads")


sidebar = html.Div(
    [
        du.Upload(text="Upload IGC File", filetypes=["igc"], id="igc-files-uploader"),
        dcc.Dropdown([], optionHeight=50, multi=True, id="igc-files-dropdown"),
        dcc.Checklist([" highlight circling"], [], id="highlight-circling"),
        dcc.Store(id="current-tmp-dir"),
    ],
    className="parent-div",
)

content = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(
                            id="trajectory", className="fig", style={"height": "50vh"}
                        ),
                    ]
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(
                            id="altitude-transition",
                            className="fig",
                            style={"height": "40vh"},
                        ),
                    ],
                    width=8,
                ),
                dbc.Col(
                    [
                        dcc.Graph(
                            id="climb-rate", className="fig", style={"height": "40vh"}
                        ),
                    ],
                    width=4,
                ),
            ],
        ),
    ],
)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2, className="bg-light"),
                dbc.Col(content, width=10),
            ],
        ),
    ],
    fluid=True,
)


@du.callback(
    output=Output(component_id="current-tmp-dir", component_property="data"),
    id="igc-files-uploader",
)
def preprocess_igc(files: List[str]):
    """
    アップロードされたIGCファイルを前処理し、格納先のディレクトリのパスをStoreに保存する
    """
    for file in files:
        text = Path(file).read_text()
        df = igc2df(text)
        df["heading"] = compute_heading_transition(df["latitude"], df["longitude"])
        df["circling"] = detect_circling(df["heading"])
        df.to_csv(Path(file).with_suffix(".csv"), index=False)

    current_tmp_dir = Path(file).parent
    return str(current_tmp_dir)


@callback(
    Output(component_id="igc-files-dropdown", component_property="options"),
    Input(component_id="current-tmp-dir", component_property="data"),
)
def update_dropdown(current_tmp_dir: str):
    """
    アップロードしたIGCファイルのリストをドロップダウンに表示する
    """
    if current_tmp_dir is None:
        return []

    return [file.stem for file in Path(current_tmp_dir).glob("*.csv")]


@callback(
    Output(component_id="trajectory", component_property="figure"),
    Input(component_id="igc-files-dropdown", component_property="value"),
    Input(component_id="highlight-circling", component_property="value"),
    State(component_id="current-tmp-dir", component_property="data"),
)
def update_trajectory(files: List[str], checklists: List[str], current_tmp_dir: str):
    """
    選択されたIGCファイルに対して飛行軌跡を描画する
    """
    fig = go.Figure()
    fig.update_layout(
        margin={"l": 0, "t": 0, "b": 0, "r": 0},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_ACCESS_TOKEN"),
            "center": {"lon": 139.444722, "lat": 36.232222},
            "style": "satellite",
            "zoom": 12,
        },
        uirevision=True,
    )

    if files is None:
        fig.add_trace(go.Scattermapbox())
        return fig

    for file, color in zip(files, colors.qualitative.Plotly):
        df = pd.read_csv(Path(current_tmp_dir) / f"{file}.csv")
        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lat=df["latitude"],
                lon=df["longitude"],
                hovertext=df["altitude"],
                hovertemplate="%{hovertext} m",
                marker=dict(color=color),
                name=file,
            )
        )

        if checklists:
            # highlight circling when the checkbox is checked
            df_circling = df[df["circling"] == 1]
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lat=df_circling["latitude"],
                    lon=df_circling["longitude"],
                    hovertext=df["altitude"],
                    hovertemplate="%{hovertext} m",
                    marker=dict(color="yellow", size=3),
                    name=file,
                    showlegend=False,
                )
            )

    return fig


@callback(
    Output(component_id="altitude-transition", component_property="figure"),
    Input(component_id="igc-files-dropdown", component_property="value"),
    State(component_id="current-tmp-dir", component_property="data"),
)
def update_altitude(files: List[str], current_tmp_dir: str):
    """
    選択されたIGCファイルに対して高度推移を描画する
    """
    fig = go.Figure()
    fig.update_layout(
        margin=dict(t=10, b=10),
        xaxis_title="time",
        yaxis_title="altitulde (m)",
        showlegend=False,
        hovermode="x unified",
    )

    if files is None:
        return fig

    for file in files:
        df = pd.read_csv(Path(current_tmp_dir) / f"{file}.csv")
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["altitude"], name=file))

    return fig


@callback(
    Output(component_id="climb-rate", component_property="figure"),
    Input(component_id="igc-files-dropdown", component_property="value"),
    State(component_id="current-tmp-dir", component_property="data"),
)
def update_climb_rate(files: List[str], current_tmp_dir: str):
    """
    選択したIGCファイルに対して平均上昇率を描画する
    """
    fig = go.Figure()
    fig.update_layout(
        margin=dict(t=10, b=10),
        xaxis_title="filename",
        yaxis_title="climb rate (m/s)",
        showlegend=False,
    )

    if files is None:
        return fig

    for file in files:
        df = pd.read_csv(Path(current_tmp_dir) / f"{file}.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        climb_rate = stats.average_climb_rate(df)
        fig.add_trace(
            go.Bar(
                x=[file],
                y=[climb_rate],
                text=[round(climb_rate, 2)],
                hovertext=[round(climb_rate, 2)],
                hovertemplate="%{hovertext} m/s",
                name=file,
            )
        )

    return fig
