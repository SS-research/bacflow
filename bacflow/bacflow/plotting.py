import plotly.graph_objects as go
import pandas as pd


def plot_simulation(aggregated: pd.DataFrame, driving_limit: float) -> go.Figure:
    """
    Plot the aggregated simulation result.
    Expects an aggregated DataFrame with columns: 'time', 'mean_bac', 'var_bac'.
    BAC is shown in percentage (g/dL * 100). A confidence band is drawn based on the standard deviation.
    Also plots a horizontal line for the driving limit.
    """
    fig = go.Figure()
    # Mean BAC line (convert from fraction to percentage)
    fig.add_trace(go.Scatter(
        x=aggregated['time'],
        y=aggregated['mean_bac'] * 100,
        mode='lines',
        name='Mean BAC (%)'
    ))
    # Confidence band: mean ± standard deviation
    std = aggregated['var_bac']**0.5
    upper = (aggregated['mean_bac'] + std) * 100
    lower = (aggregated['mean_bac'] - std) * 100
    fig.add_trace(go.Scatter(
        x=aggregated['time'],
        y=upper,
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=aggregated['time'],
        y=lower,
        mode='lines',
        fill='tonexty',
        line=dict(width=0),
        fillcolor='rgba(0,100,80,0.2)',
        name='Confidence Band'
    ))
    # Driving limit line
    fig.add_trace(go.Scatter(
        x=aggregated['time'],
        y=[driving_limit * 100] * len(aggregated),
        mode='lines',
        line=dict(dash='dash', color='red'),
        name='Driving Limit'
    ))
    fig.update_layout(
        title="BAC Simulation",
        xaxis_title="Time",
        yaxis_title="BAC (%)",
        template="plotly_white"
    )
    return fig
