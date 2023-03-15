import os
import json
import dash
import meshio
import numpy as np
import dash_daq as daq
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_colorscales as dcs
import dash_mantine_components as dmc

from numpy import sin, cos, pi
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "XYZ Rendering"
server = app.server

GITHUB_LINK = os.environ.get(
    "GITHUB_LINK",
    "https://github.com/ananya-k15/xyz-rendering",
)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4("XYZ Rendering"),
                                    ],
                                    className="header__title",
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "Select a 3D model from the dropdown. Use the XYZ range sliders to highlight regions."
                                        )
                                    ],
                                    className="header__info pb-20",
                                ),
                                html.Div(
                                    [
                                        html.A(
                                            "View on GitHub",
                                            href=GITHUB_LINK,
                                            target="_blank",
                                        )
                                    ],
                                    className="header__button",
                                ),
                            ],
                            className="header pb-20",
                        ),
                        dmc.LoadingOverlay(
                            dcc.Graph(id="highlight-3d-graph"),
                        ),
                    ],
                    className="container",
                )
            ],
            className="two-thirds column app__left__section",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "Select first gradient color", className="subheader"
                                ),
                                dmc.ColorPicker(
                                    id="color-picker",
                                    format="rgb",
                                    value="rgb(0, 0, 255)",
                                    fullWidth=True,
                                ),
                                dmc.Space(h=10),
                            ],
                        )
                    ],
                    className="colorscale pb-20",
                ),
                html.Div(
                    [
                        html.P("Select 3D Model", className="subheader"),
                        dcc.Dropdown(
                            options=[
                                {"value": "_".join(i.split(" ")).lower(), "label": i}
                                for i in [
                                    "Homer Simpson",
                                    "Stanford Bunny",
                                    "XYZ Dragon",
                                    "Lucy",
                                    "Human",
                                ]
                            ],
                            value="xyz_dragon",
                            placeholder="XYZ Dragon",
                            clearable=False,
                            searchable=True,
                            id="model-options",
                            optionHeight=50,
                        ),
                    ],
                    className="pb-20",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "Select second gradient color",
                                    className="subheader",
                                ),
                                dmc.ColorPicker(
                                    id="high-picker",
                                    format="rgb",
                                    value="rgb(255, 255, 255)",
                                    fullWidth=True,
                                ),
                                dmc.Space(h=10),
                            ],
                        )
                    ],
                    className="colorscale pb-20",
                ),
                #     html.Div(
                #         [
                #             html.Span("Select XYZ range", className="subheader"),
                #             dmc.Space(h=10),
                #             html.Span(
                #                 "Move the slider to change the highlight region on the graph.",
                #                 className="small-text",
                #             ),
                #             dmc.Space(h=20),
                #             html.P("Range of x coordinates: "),
                #             dcc.RangeSlider(
                #                 min=-0.7744977881566031 - 0.01,
                #                 max=0.44003154043624987 + 0.01,
                #                 id="x-range",
                #                 marks={
                #                     -0.7744977881566031: {"label": "-0.7745"},
                #                     0: {"label": "0"},
                #                     0.44003154043624984: {"label": "0.4400"},
                #                 },
                #                 value=[-0.05, 0.45],
                #                 tooltip={
                #                     "placement": "bottom",
                #                     "always_visible": False,
                #                 },
                #             ),
                #             dmc.Space(h=20),
                #             html.P("Range of y coordinates: "),
                #             dcc.RangeSlider(
                #                 min=-0.5474345419762712 - 0.01,
                #                 max=0.43922766312325695 + 0.01,
                #                 id="y-range",
                #                 marks={
                #                     -0.5474345419762712: {"label": "-0.5474"},
                #                     0: {"label": "0"},
                #                     0.43922766312325700: {"label": "0.4392"},
                #                 },
                #                 value=[0.25, 0.44],
                #                 tooltip={
                #                     "placement": "bottom",
                #                     "always_visible": False,
                #                 },
                #             ),
                #             dmc.Space(h=20),
                #             html.P("Range of z coordinates: "),
                #             dcc.RangeSlider(
                #                 min=-0.8212642714662288 - 0.01,
                #                 max=0.6537790158429256 + 0.01,
                #                 id="z-range",
                #                 marks={
                #                     -0.8212642714662288: {"label": "-0.7213"},
                #                     0: {"label": "0"},
                #                     0.6537790158429256: {"label": "0.6538"},
                #                 },
                #                 value=[-0.36, 0],
                #                 tooltip={
                #                     "placement": "bottom",
                #                     "always_visible": False,
                #                 },
                #             ),
                #         ],
                #         className="pb-20",
                #     ),
            ],
            className="one-third column app__right__section",
        ),
        dcc.Store(id="annotation_storage"),
    ]
)


def rot_x(t):
    return np.array([[1, 0, 0], [0, cos(t), -sin(t)], [0, sin(t), cos(t)]])


def rot_z(t):
    return np.array([[cos(t), -sin(t), 0], [sin(t), cos(t), 0], [0, 0, 1]])


def select(x, y, z, x_range, y_range, z_range):
    [x_min, x_max] = x_range
    [y_min, y_max] = y_range
    [z_min, z_max] = z_range
    if (
        float(x) >= x_min
        and float(x) <= x_max
        and float(y) >= y_min
        and float(y) <= y_max
        and float(z) > z_min
        and float(z) < z_max
    ):
        return True
    return False


def plot_obj(file, highlight, color):  # , x_range, y_range, z_range):
    mesh_data = meshio.read(file)
    vertices = mesh_data.points
    triangles = mesh_data.cells_dict["triangle"]

    # apply rot_z(angle2) * rot_x(angle1)
    A = rot_x(pi / 4)
    B = rot_z(4 * pi / 9 + pi / 4)

    # Apply the product of the two rotations to the object vertices:
    new_vertices = np.einsum("ik, kj -> ij", vertices, (np.dot(B, A)).T)
    # new_vertices have the shape (n_vertices, 3)

    x, y, z = new_vertices.T
    I, J, K = triangles.T
    tri_points = new_vertices[triangles]
    pl_mygrey = [0, color], [1.0, highlight]

    pl_mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        colorscale=pl_mygrey,
        intensity=z,
        flatshading=True,
        i=I,
        j=J,
        k=K,
        name="3D Mesh",
        showscale=False,
    )

    pl_mesh.update(
        cmin=-7,
        lighting=dict(
            ambient=0.18,
            diffuse=1,
            fresnel=0.1,
            specular=1,
            roughness=0.05,
            facenormalsepsilon=1e-15,
            vertexnormalsepsilon=1e-15,
        ),
        lightposition=dict(x=100, y=200, z=500),
    )

    Xe = []
    Ye = []
    Ze = []
    for T in tri_points:
        Xe.extend([T[k % 3][0] for k in range(4)] + [None])
        Ye.extend([T[k % 3][1] for k in range(4)] + [None])
        Ze.extend([T[k % 3][2] for k in range(4)] + [None])

    # define the trace for triangle sides
    lines = go.Scatter3d(
        x=Xe,
        y=Ye,
        z=Ze,
        mode="lines",
        name="",
        line=dict(color="rgb(70,70,70)", width=1),
    )

    layout = go.Layout(
        title="3D Human Mesh with Highlighting",
        font=dict(size=13, color="white"),
        scene_xaxis_visible=True,
        scene_yaxis_visible=True,
        scene_zaxis_visible=True,
        height=700,
        paper_bgcolor="#141414",
    )

    fig = go.Figure(data=[pl_mesh, lines], layout=layout)
    return fig


@app.callback(
    Output("highlight-3d-graph", "figure"),
    [
        Input("model-options", "value"),
        Input("color-picker", "value"),
        Input("high-picker", "value"),
        # Input("x-range", "value"),
        # Input("y-range", "value"),
        # Input("z-range", "value"),
    ],
)
def brain_graph_handler(val, highlight, color):  # , x_range, y_range, z_range):
    file = "data/" + str(val) + ".obj"
    figure = plot_obj(file, highlight, color)  #  x_range, y_range, z_range)
    return figure


if __name__ == "__main__":
    app.run_server(debug=True)
