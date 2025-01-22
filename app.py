import dash
from dash import dcc, html
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
import pandas as pd
import base64

# Load data
df = pd.read_csv('./ZONAL_CONTRIBUTIONS.csv')
df['TIME'] = pd.to_datetime(df['TIME'])
df.set_index('TIME', inplace=True)
df = df[~((df.index.month == 2) & (df.index.day == 29))]  # Remove leap days

df = df[['GLOBAL', 'POLAR (N)', 'HIGH-LATITUDES (N)', 'MID-LATITUDES (N)', 'TROPICS' ,'MID-LATITUDES (S)', 'HIGH-LATITUDES (S)', 'POLAR (S)']]

doy = {str(x)[5:10]: i for i, x in enumerate(pd.date_range('1901-01-01', '1901-12-31', freq='1D'), 1)}

# Define x-ticks
x_ticks = [doy[str(x)[5:10]] for x in pd.date_range('1901-01-01', '1901-12-31', freq='1MS')]
x_labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

# Load image for first subplot
image_path = "./ZONAL_SUBDIVISIONS_MAP.png"
with open(image_path, "rb") as img_file:
    encoded_image = base64.b64encode(img_file.read()).decode()
image_source = f"data:image/png;base64,{encoded_image}"

# Create subplots
fig = sp.make_subplots(rows=3, cols=3, subplot_titles=["", *df.columns],
                       specs=[[{"type": "image"}, {'type': 'xy'}, {'type': 'xy'}],
                              [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}],
                             [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}]], horizontal_spacing = 0.05, vertical_spacing = 0.1)


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
    y_min, y_max = df[col].min() + 0.40*df[col].min(), df[col].max()+0.40*df[col].max()  # Unique y-axis limits per subplot
    for year in range(1981, 2025):
        color, alpha = ('orange', 1) if year == 2024 else ('black', 1) if year == 2023 else ('grey', 0.5)
        show_legend = year not in added_years
        fig.add_trace(
            go.Scatter(
                x=[doy[str(x)[5:10]] for x in df[df.index.year == year].index],
                y=df[df.index.year == year][col],
                mode='lines',
                name=str(year),
                hovertemplate='<b>Year:</b> %{text}<br><b>SSTA:</b> %{y:.2f}<br><b>DOY:</b> %{x}<extra></extra>',
                text=[str(year)] * len(df[df.index.year == year].index),
                line=dict(color=color, width=1 if year <= 2022 else 2),
                opacity=alpha,
                legendgroup=str(year),
                showlegend=show_legend
            ),
            row=row,
            col=col_pos
        )
        added_years.add(year)
    fig.update_xaxes(tickvals=x_ticks, ticktext=x_labels, showgrid=True, gridcolor='lightgrey', fixedrange=True, row=row, col=col_pos)
    fig.update_yaxes(range=[y_min, y_max], showgrid=True, gridcolor='lightgrey', row=row, col=col_pos)  # Independent y-limits

# Layout
fig.update_layout(
    autosize=True,  # Ensures tight layout
    margin=dict(l=50, r=50, t=50, b=50),  # Reducing extra white space
    plot_bgcolor='white',  # Set background to white
    paper_bgcolor='white',  # Set paper background to white
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
        traceorder="normal",
        itemsizing="constant",
        itemclick="toggle",
        itemdoubleclick="toggleothers",
        tracegroupgap=5,
        bgcolor="rgba(255,255,255,0.5)",
        bordercolor="black",
        borderwidth=1
    ),
    hovermode="closest"
)

# Dash App
app = dash.Dash(__name__)
server = app.server
app.layout = html.Div([
    dcc.Graph(id='time-series-graph', figure=fig),
    html.Div([
        html.Button("Show All", id="show-all", n_clicks=0, style={"margin-right": "10px"}),
        html.Button("Hide All", id="hide-all", n_clicks=0)
    ], style={"textAlign": "center", "marginTop": "20px"})
])

@app.callback(
    dash.dependencies.Output('time-series-graph', 'figure'),
    [dash.dependencies.Input('show-all', 'n_clicks'),
     dash.dependencies.Input('hide-all', 'n_clicks')]
)
def toggle_traces(show_clicks, hide_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return fig
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    new_fig = fig.to_dict()
    for trace in new_fig['data']:
        if 'source' in trace:  # Skip image trace in first subplot
            continue
        if button_id == "show-all":
            trace['visible'] = True
        elif button_id == "hide-all":
            trace['visible'] = "legendonly"
    
    return go.Figure(new_fig)

if __name__ == '__main__':
    app.run_server(debug=True)
