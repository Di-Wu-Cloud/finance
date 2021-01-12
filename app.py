import pandas as pd
import re
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import yfinance as yf
from get_all_tickers import get_tickers as gt
from plotly.tools import mpl_to_plotly
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objs as go
import plotly.tools as tls

#from pandas_datareader import data as pdr

spy_ticker = yf.Ticker('SPY')
df = yf.download('SPY')
df = df[-600:]

##### Dashboard layout #####
# Dash Set up
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
#algo calcs
def get_points_above(sma_low, sma_high):
    points_above = {}
    for pair in zip(sma_low, sma_high):
        if pair[0] >= pair[1]:
            date = sma_low[sma_low == pair[0]].index[0]
            points_above[date] = pair[0]
            
    points_above = pd.Series(points_above, name='Price_Points')
    points_above.index.name = 'Date'    
    return points_above
#SMA means simple moving average
SMA10 = df['Close'].rolling(window = 10).mean()
SMA20 = df['Close'].rolling(window = 20).mean()
SMA50 = df['Close'].rolling(window = 50).mean()
SMA100 = df['Close'].rolling(window = 100).mean()

points_above_SMA50 = get_points_above(SMA20, SMA50)

SMA20 = SMA20.reset_index()
SMA50 = SMA50.reset_index()

crossovers = pd.DataFrame()
crossovers['Dates'] = SMA20['Date']
crossovers['Price'] = [i for i in df['Close']]
crossovers['SMA20'] = SMA20['Close']
crossovers['SMA50'] = SMA50['Close']
crossovers['position'] = crossovers['SMA20'] >= crossovers['SMA50']
crossovers['pre-position'] = crossovers['position'].shift(1)
crossovers['Crossover'] = np.where(crossovers['position'] == crossovers['pre-position'], False, True)
crossovers.loc['Crossover', '0'] = False
#print(crossovers)

crossovers = crossovers.loc[crossovers['Crossover'] == True]
crossovers = crossovers.reset_index()
crossovers = crossovers.drop(['position', 'pre-position', 'Crossover', 'index'], axis=1)
crossovers['Signal'] = np.nan
crossovers['Binary_Signal'] = 0.0
for i in range(len(crossovers['SMA20'])):
    if crossovers['SMA20'][i] > crossovers['SMA50'][i]:
        crossovers['Binary_Signal'][i] = 1.0
        crossovers['Signal'][i] = 'Buy'
    else:
        crossovers['Signal'][i] = 'Sell'
#print(crossovers)

# taking last 600 trading days

SMA20 = df['Close'].rolling(window=20).mean()
SMA50 = df['Close'].rolling(window=50).mean()
df.reset_index(level=0, inplace=True)
fig = go.Figure()
# Create and style traces
fig.add_trace(go.Scatter(x=df['Date'],y=df['Close'], name='SPY',
                         line=dict(color='firebrick', width=4)))
fig.add_trace(go.Scatter(x=df['Date'], y=SMA20, name = 'SMA20',
                         line=dict(color='royalblue', width=2, dash = 'dot')))
fig.add_trace(go.Scatter(x=df['Date'], y=SMA50, name = 'SMA50',
                         line=dict(color='mediumseagreen', width=2, dash = 'dash')))

# Edit the layout
fig.update_layout(title='SMA against actual',
                   xaxis_title='Dates',
                   yaxis_title='Price')

# Base Layout
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Stock Trend Analytics", className="header-title"
                ),
                html.P(
                    children="Analyze the SMA of stocks",
                    className="header-description"
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="SMA-chart", config={"displayModeBar": False}, figure=fig
                    ),
                    className="card",
                ),
            ],
            className="header",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)