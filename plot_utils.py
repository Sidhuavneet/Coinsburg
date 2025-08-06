import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

def plot_and_save(df: pd.DataFrame, pattern_info: dict, output_dir: str, html_dir: str):
    """
    Plots a detected Cup and Handle pattern and saves it as a PNG and an interactive HTML file.
    """
    indices = pattern_info['indices']
    coeffs = pattern_info['poly_coeffs']
    
    buffer = int(pattern_info['cup_duration'] * 0.2)
    start_idx = max(0, indices['left_rim'] - buffer)
    # Use .iloc for integer-based slicing
    end_idx = min(len(df) - 1, indices['breakout'] + buffer)
    
    plot_df = df.iloc[start_idx:end_idx].copy()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(x=plot_df['timestamp'],
                                 open=plot_df['open'], high=plot_df['high'],
                                 low=plot_df['low'], close=plot_df['close'],
                                 name='Price'), row=1, col=1)

    fig.add_trace(go.Bar(x=plot_df['timestamp'], y=plot_df['volume'], name='Volume', marker_color='rgba(100,149,237,0.5)'), row=2, col=1)
    
    # --- THIS ENTIRE SECTION IS CORRECTED TO USE .iloc for integer indexing ---
    cup_plot_data = df.iloc[indices['left_rim']:indices['right_rim'] + 1]
    cup_x_abs = cup_plot_data['timestamp']
    x_cup_fit = np.arange(len(cup_plot_data))
    p = np.poly1d(coeffs)
    y_cup_fit = p(x_cup_fit)
    
    fig.add_trace(go.Scatter(x=cup_x_abs, y=y_cup_fit, mode='lines', 
                             name='Cup Fit (R^2={:.2f})'.format(pattern_info['r_squared_fit']),
                             line=dict(color='orange', width=2, dash='dash')), row=1, col=1)

    rim_price = min(df.iloc[indices['left_rim']]['high'], df.iloc[indices['right_rim']]['high'])
    
    fig.add_shape(type="line",
        x0=df.iloc[indices['left_rim']]['timestamp'], y0=rim_price,
        x1=df.iloc[indices['breakout']]['timestamp'], y1=rim_price,
        line=dict(color="red", width=2, dash="dot"), name="Resistance", row=1, col=1)

    fig.add_shape(type="line",
        x0=df.iloc[indices['right_rim']]['timestamp'], y0=df.iloc[indices['right_rim']]['high'],
        x1=df.iloc[indices['handle_low']]['timestamp'], y1=df.iloc[indices['handle_low']]['low'],
        line=dict(color="purple", width=1), row=1, col=1)
    fig.add_shape(type="line",
        x0=df.iloc[indices['handle_low']]['timestamp'], y0=df.iloc[indices['handle_low']]['low'],
        x1=df.iloc[indices['handle_high']]['timestamp'], y1=df.iloc[indices['handle_high']]['high'],
        line=dict(color="purple", width=1), row=1, col=1)

    breakout_candle = df.iloc[indices['breakout']]
    # --- END OF CORRECTED SECTION ---

    fig.add_annotation(
        x=breakout_candle['timestamp'], y=breakout_candle['high'],
        text="Breakout!", showarrow=True, arrowhead=2, arrowcolor="green", arrowsize=1.5,
        font=dict(size=12, color="white"), bgcolor="green", ax=0, ay=-40, row=1, col=1)

    fig.update_layout(
        title=f"Cup & Handle Pattern #{pattern_info['pattern_id']} (Valid)",
        xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50))
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    img_filename = os.path.join(output_dir, f"cup_handle_{pattern_info['pattern_id']}.png")
    html_filename = os.path.join(html_dir, f"cup_handle_{pattern_info['pattern_id']}.html")
    
    try:
        fig.write_image(img_filename, width=1200, height=700, engine='kaleido')
        fig.write_html(html_filename)
        print(f"Successfully saved plot for pattern #{pattern_info['pattern_id']}")
    except Exception as e:
        print(f"Error saving plot for pattern #{pattern_info['pattern_id']}: {e}")