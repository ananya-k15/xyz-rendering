from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import dash
import dash_design_kit as ddk
import dash_mantine_components as dmc
import numpy as np
import meshio
import plotly.graph_objects as go

from numpy import sin, cos, pi

app = dash.Dash()
server = app.server


DEFAULT_COLOR = "rgb(207,181,59)"
HIGHLIGHT = "rgb(1, 0, 79)"


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


def plot_obj(file, x_range, y_range, z_range):
    mesh_data = meshio.read(file)
    vertices = mesh_data.points
    triangles = mesh_data.cells_dict["triangle"]

    # apply rot_z(angle2) * rot_x(angle1)
    A = rot_x(pi / 4)
    B = rot_z(4 * pi / 9 + pi / 4)

    # Apply the product of the two rotations to the object vertices:
    new_vertices = np.einsum(
        "ik, kj -> ij", vertices, (np.dot(B, A)).T
    )  # new_vertices has the shape (n_vertices, 3)

    x, y, z = new_vertices.T
    I, J, K = triangles.T
    tri_points = new_vertices[triangles]
    pl_mygrey = [0, "rgb(0, 255, 0)"], [1.0, "rgb(255,255,255)"]

    facecolor = [DEFAULT_COLOR for i in range(2 * len(x))]
    for i in range(len(I)):
        index1 = I[i]
        index2 = J[i]
        index3 = K[i]
        if (
            select(x[index1], y[index1], z[index1], x_range, y_range, z_range)
            and select(x[index2], y[index2], z[index2], x_range, y_range, z_range)
            and select(x[index3], y[index3], z[index3], x_range, y_range, z_range)
        ):
            facecolor[i] = HIGHLIGHT
        else:
            facecolor[i] = DEFAULT_COLOR

    pl_mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        # colorscale=pl_mygrey,
        # intensity=z,
        # flatshading=True,
        i=I,
        j=J,
        k=K,
        name="3D Mesh",
        showscale=False,
        facecolor=facecolor,
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
        #  font=dict(size=16, color='white'),
        scene_xaxis_visible=True,
        scene_yaxis_visible=True,
        scene_zaxis_visible=True,
        height=700,
        #  paper_bgcolor='rgb(50,50,50)',
    )

    fig = go.Figure(data=[pl_mesh, lines], layout=layout)
    fig.update_layout(title_text="Pain Points")

    return fig


# Create app layout
app.layout = html.Div(
    [
        ddk.Card(
            [
                ddk.CardHeader(
                    title="Select portion to highlight", style={"margin-bottom": "10px"}
                ),
                dcc.RadioItems(
                    options=["Forearm", "Foot", "Head", "Custom"],
                    value="Forearm",
                    id="body-part",
                ),
            ],
        ),
        ddk.Card(
            [
                dmc.LoadingOverlay(
                    dcc.Graph(id="highlight-graph"),
                ),
            ]
        ),
        ddk.Card(
            [
                ddk.CardHeader(title="Modify highlighted range"),
                html.P("Range of x coordinates: "),
                dcc.RangeSlider(
                    -0.7744977881566031 - 0.01,
                    0.44003154043624987 + 0.01,
                    id="x-range",
                    marks={
                        -0.7744977881566031: {"label": "-0.7745"},
                        0: {"label": "0"},
                        0.44003154043624984: {"label": "0.4400"},
                    },
                    value=[-0.05, 0.45],
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.P("Range of y coordinates: "),
                dcc.RangeSlider(
                    -0.5474345419762712 - 0.01,
                    0.43922766312325695 + 0.01,
                    id="y-range",
                    marks={
                        -0.5474345419762712: {"label": "-0.5474"},
                        0: {"label": "0"},
                        0.43922766312325700: {"label": "0.4392"},
                    },
                    value=[0.25, 0.44],
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.P("Range of z coordinates: "),
                dcc.RangeSlider(
                    -0.8212642714662288 - 0.01,
                    0.6537790158429256 + 0.01,
                    id="z-range",
                    marks={
                        -0.8212642714662288: {"label": "-0.7213"},
                        0: {"label": "0"},
                        0.6537790158429256: {"label": "0.6538"},
                    },
                    value=[-0.36, 0],
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ],
        ),
    ]
)


@app.callback(
    Output("x-range", "value"),
    Output("y-range", "value"),
    Output("z-range", "value"),
    Input("body-part", "value"),
)
def add_preset(option):
    if option == "Forearm":
        return [-0.05, 0.45], [0.25, 0.44], [-0.36, 0]
    elif option == "Foot":
        return [-0.78, 0], [-0.4, 0.44], [-0.83, -0.63]
    elif option == "Head":
        return [0.22, 0.45], [0.22, 0.44], [0.4, 0.68]
    else:
        return (
            [-0.78, 0.45],
            [-0.56, 0.44],
            [-0.83, 0.68],
        )


# Callback controlling 3D object dropdown
@app.callback(
    Output("highlight-graph", "figure"),
    Input("x-range", "value"),
    Input("y-range", "value"),
    Input("z-range", "value"),
)
def display_highlight_mesh(x_range, y_range, z_range):
    fig = plot_obj("assets/data/SPRING0008.obj", x_range, y_range, z_range)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
