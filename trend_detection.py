import numpy as np
from matplotlib import pyplot
from binance.client import Client
import config
import datetime
import pandas as pd
import plotly.graph_objects as go
import math
from itertools import chain

def detect_trend(inp_df, inp_date):
    df = inp_df #This df contains historic candlestick data from the current time
    inp_date = inp_date #Timestamp of current candlestick
    get_index = df.index[df['time'] == inp_date].tolist() #identify current timestamp in df
    get_index = get_index[-1]

    backcandles= 30 #Define how many candlesticks robot should roll back to
    brange = 10 #Should be less than backcandles, robot rolls back within range e.g. 30 - 40 candlesticks
    wind = 2 #Time interval slice
    candleid = get_index - 1
    optbackcandles= backcandles
    sldiff = 100 #SL variables are pre-defined for robot to determine most parallel slope
    sldist = 10000

    for r1 in range(backcandles-brange, backcandles+brange):
        maxim = np.array([])
        minim = np.array([])
        xxmin = np.array([])
        xxmax = np.array([])

        for i in range(candleid-r1, candleid+1, wind):
            minim = np.append(minim, df.low.iloc[i:i+wind].min())
            xxmin = np.append(xxmin, df.low.iloc[i:i+wind].idxmin())
        for i in range(candleid-r1, candleid+1, wind):
            maxim = np.append(maxim, df.high.iloc[i:i+wind].max())
            xxmax = np.append(xxmax, df.high.iloc[i:i+wind].idxmax())
        slmin, intercmin = np.polyfit(xxmin, minim,1)
        slmax, intercmax = np.polyfit(xxmax, maxim,1)

        dist = (slmax*candleid + intercmax)-(slmin*candleid + intercmin)
        if(dist<sldist): #abs(slmin-slmax)<sldiff and
            #sldiff = abs(slmin-slmax)
            sldist = dist
            optbackcandles=r1
            slminopt = slmin
            slmaxopt = slmax
            intercminopt = intercmin
            intercmaxopt = intercmax
            maximopt = maxim.copy()
            minimopt = minim.copy()
            xxminopt = xxmin.copy()
            xxmaxopt = xxmax.copy()

    smin = min(xxminopt)
    smax = min(xxmaxopt)
    lmin = max(xxminopt)
    lmax = max(xxmaxopt)

    if smin < smax: #Determine start and end candleid to represent only relevant candlesticks on graph
        s = smin
    else:
        s = smax

    if lmin > lmax:
        e = lmin
    else:
        e = lmax

    s = math.trunc(s)
    e = math.trunc(e)

    dfpl = df[s:e]

    full_view = df[s:candleid+optbackcandles+wind]
    #For testing purpose, please use full view to see what happens to price after the robot has detected a trend
    fig = go.Figure(data=[go.Candlestick(x=full_view.index,
                    open=full_view['open'],
                    high=full_view['high'],
                    low=full_view['low'],
                    close=full_view['close'])])

    adjintercmax = (df.high.iloc[xxmaxopt] - slmaxopt*xxmaxopt).max()
    adjintercmin = (df.low.iloc[xxminopt] - slminopt*xxminopt).min()
    (fig.add_trace(go.Scatter(x=xxminopt, y=slminopt*xxminopt + adjintercmin, mode='lines', name='min slope')))
    (fig.add_trace(go.Scatter(x=xxmaxopt, y=slmaxopt*xxmaxopt + adjintercmax, mode='lines', name='max slope')))

    #Caluclate slopes again for further quality checks
    minslope = slminopt * xxminopt + adjintercmin
    maxslope = slmaxopt * xxmaxopt + adjintercmax

    max_maxslope = (maxslope[-1]) #Latest max slope value
    min_maxslope = (maxslope[0])  #Start max slope value
    max_minslope = (minslope[-1]) #Latest min slope value
    min_minslope = (minslope[0])  #Start min slope value
    candle_touch = False

    #If in an uptrend script checks if the latest candlestick touches the uptrend channel
    latest_xxmaxopt = int(xxmaxopt[-1])
    time_xxmaxpot = df.time.iloc[latest_xxmaxopt]
    open = df.open.iloc[latest_xxmaxopt]
    high = df.high.iloc[latest_xxmaxopt]
    low = df.low.iloc[latest_xxmaxopt]
    close = df.close.iloc[latest_xxmaxopt]
    latest_maxslope = maxslope[-1]
    if open >= latest_maxslope or high >= latest_maxslope or low >=latest_maxslope or close >= latest_maxslope: #Equates to an uptrend
        candle_touch = True

    return candle_touch, fig
