import dash
import dash_bootstrap_components as dbc
from dash import Dash, html


def create_app():
    app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=True)

    navbar = dbc.NavbarSimple(
        children=[
            *[
                dbc.NavItem(dbc.NavLink(f"{page['name']}", href=page["relative_path"]))
                for page in dash.page_registry.values()
            ],
        ],
        brand="Glider Dashboard",
        color="primary",
        dark=True,
    )

    app.layout = html.Div(
        [
            navbar,
            dash.page_container,
        ]
    )

    return app
