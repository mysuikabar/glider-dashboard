import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

dash.register_page(__name__, path="/")


content = html.Div(
    dcc.Markdown(
        """
#### [Flight log](/flight-log)
IGCファイルを読み込み、フライトの軌跡、高度推移、旋回中の平均上昇率をプロットします。

#### [Thermal spots](/thermal-spots)
過去のフライトのログデータをもとに集計した1分単位の平均上昇率を地図上にプロットします。
気温、風速、風向、過去1時間の日射時間、高度などの条件でフィルタリングすることで、コンディションに応じたサーマルスポットを可視化できます。

※ 気温などの気象条件には、[気象庁HP](https://www.data.jma.go.jp/stats/etrn/index.php)から取得した熊谷市の過去の観測データを利用しています。
"""
    ),
    style={"margin": "50px"},
)


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(content, width=10),
            ],
        ),
    ],
    fluid=True,
)
