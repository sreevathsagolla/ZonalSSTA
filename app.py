import dash
from dash import dcc, html
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
import pandas as pd
import base64
from dash.dependencies import Input, Output, State

# File paths
data_files = {
    "SST Anomaly": "./ZONAL_CONTRIBUTIONS_SST.csv",
    "T2M Anomaly": "./ZONAL_CONTRIBUTIONS_T2M.csv"
}

# Load default data
def load_data(data_type):
    df = pd.read_csv(data_files[data_type])
    df['TIME'] = pd.to_datetime(df['TIME'])
    df.set_index('TIME', inplace=True)
    df = df[~((df.index.month == 2) & (df.index.day == 29))]  # Remove leap days
    df = df[['GLOBAL', 'TROPICS', 'POLAR (N)', 'HIGH-LATITUDES (N)', 'MID-LATITUDES (N)', 'POLAR (S)', 'HIGH-LATITUDES (S)', 'MID-LATITUDES (S)']]
    return df

df = load_data("SST Anomaly")  # Default dataset

doy = {str(x)[5:10]: i for i, x in enumerate(pd.date_range('1901-01-01', '1901-12-31', freq='1D'), 1)}

# Define x-ticks
x_ticks = [doy[str(x)[5:10]] for x in pd.date_range('1901-01-01', '1901-12-31', freq='1MS')]
x_labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

# Load image for first subplot
image_path = "./ZONAL_SUBDIVISIONS_MAP.png"
with open(image_path, "rb") as img_file:
    encoded_image = base64.b64encode(img_file.read()).decode()
image_source = f"data:image/png;base64,{encoded_image}"

def create_figure(df, show_all=True):
    fig = sp.make_subplots(rows=3, cols=3, subplot_titles=["", *df.columns],
                           specs=[[{"type": "image"}, {'type': 'xy'}, {'type': 'xy'}],
                                  [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}],
                                  [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}]],
                           horizontal_spacing=0.05, vertical_spacing=0.1)

    # Add latitude zone image
    fig.add_trace(
        go.Image(source=image_source),
        row=1, col=1
    )
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)

    # Map subplot positions
    subplot_mapping = {i: (i // 3 + 1, i % 3 + 1) for i in range(1, len(df.columns) + 1)}

    # Add traces
    added_years = set()
    for i, col in enumerate(df.columns):
        row, col_pos = subplot_mapping[i+1]
        y_min, y_max = df[col].min() + 0.40*df[col].min(), df[col].max()+0.40*df[col].max()
        for year in range(1981, 2025):
            color, alpha = ('orange', 1) if year == 2024 else ('black', 1) if year == 2023 else ('grey', 0.5)
            show_legend = year not in added_years
            fig.add_trace(
                go.Scatter(
                    x=[doy[str(x)[5:10]] for x in df[df.index.year == year].index],
                    y=df[df.index.year == year][col],
                    mode='lines',
                    name=str(year),
                    hovertemplate='<b>Year:</b> %{text}<br><b>ANOM:</b> %{y:.2f}<br><b>DOY:</b> %{x}<extra></extra>',
                    text=[str(year)] * len(df[df.index.year == year].index),
                    line=dict(color=color, width=1 if year<=2022 else 2),
                    visible='legendonly' if not show_all else True,
                    legendgroup=str(year),
                    showlegend=show_legend,# if show_all else False,
                ),
                row=row,
                col=col_pos
            )
            added_years.add(year)
        fig.update_xaxes(tickvals=x_ticks, ticktext=x_labels, showgrid=True, gridcolor='lightgrey', fixedrange=True, row=row, col=col_pos)
        fig.update_yaxes(range=[y_min, y_max], showgrid=True, gridcolor='lightgrey', row=row, col=col_pos)

    # Layout
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        title="Zonal Contributions (1981-2024)",
        height=700,
        width=1400,
        legend=dict(
            title="Years",
            font=dict(size=12),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.1,
            yanchor="top",
            itemsizing='constant'
        ),
        hovermode="closest"
    )
    return fig

# Dash App
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Graph(id='time-series-graph', figure=create_figure(df)),
    html.Div([
        html.Button("Show All", id="show-all", n_clicks=0, style={"margin-right": "10px"}),
        html.Button("Hide All", id="hide-all", n_clicks=0)
    ], style={"textAlign": "center", "marginTop": "20px"}),
    html.Div([
        dcc.RadioItems(
            id='data-selector',
            options=[{'label': k, 'value': k} for k in data_files.keys()],
            value='SST Anomaly',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        )
    ], style={"position": "absolute", "bottom": "50px", "left": "50px"})
])

@app.callback(
    Output('time-series-graph', 'figure'),
    [Input('data-selector', 'value'),
     Input('show-all', 'n_clicks'),
     Input('hide-all', 'n_clicks')],
    prevent_initial_call=True
)
def update_figure(selected_data, show_all_clicks, hide_all_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_figure(load_data(selected_data))
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    show_all = button_id != 'hide-all'
    return create_figure(load_data(selected_data), show_all)

if __name__ == '__main__':
    app.run_server(debug=True, port = 8899)
