import pandas as pd
import plotly.graph_objects as go

from bacflow.schemas import Model


def plot_simulation(results: dict[Model, pd.DataFrame], threshold: float | None = None) -> go.Figure:
    fig = go.Figure()
    for model, bac_ts in results.items():
        fig.add_trace(go.Scatter(
            x=bac_ts['time'],
            y=bac_ts['bac_perc'],
            mode='lines',
            name=str(model)
        ))

    if threshold:
        fig.add_hline(y=threshold, line_dash="dash", line_color="red")
    
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='BAC (%)'
    )

    return fig
