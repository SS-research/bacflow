import pandas as pd
import plotly.graph_objects as go

from bacflow.schemas import Model


def plot_simulation(results: dict[Model, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()
    for model, bac_ts in results.items():
        fig.add_trace(go.Scatter(
            x=bac_ts['time'],
            y=bac_ts['bac_perc'],
            mode='lines',
            name=str(model)
        ))
    
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='BAC (%)'
    )

    return fig
