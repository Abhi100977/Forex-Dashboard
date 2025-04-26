# app.py

import streamlit as st
import pandas as pd
import ta
import plotly.graph_objects as go

from binance.client import Client

# Binance API keys (optional: or use environment variables for safety)
api_key = "your_api_key"
api_secret = "your_api_secret"
client = Client(api_key, api_secret)

# Get historical kline/candle data
def get_klines(symbol, interval, lookback="1 day ago UTC"):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback))
    if not frame.empty:
        frame = frame.iloc[:, :6]
        frame.columns = ['Time', 'open', 'high', 'low', 'close', 'volume']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
    return frame

# Streamlit UI
st.title("📈 Forex Dashboard - Gold & BTC Signals")

# Sidebar - choose symbol and interval
symbol = st.sidebar.selectbox("Select Symbol", ["BTCUSDT", "XAUUSDT"])
interval = st.sidebar.selectbox("Select Interval", ["1m", "5m", "15m", "1h", "4h"])

# Fetch data
try:
    df = get_klines(symbol, interval)
except Exception as e:
    st.error(f"Failed to load data. Error: {e}")
    st.stop()

# Check if DataFrame is empty
if df.empty:
    st.error("❌ No data fetched. Please try another symbol or timeframe.")
    st.stop()

# Check if 'close' column exists
if 'close' not in df.columns:
    st.error("❌ 'close' column not found in data.")
    st.stop()

# Calculate indicators
df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
df['RSI'] = ta.momentum.rsi(df['close'], window=14)

# Check if indicator columns are ready
if df[['EMA20', 'EMA50', 'RSI']].isnull().values.any():
    st.error("❌ Indicators could not be calculated correctly.")
    st.stop()

# Signal Logic
latest_close = df['close'].iloc[-1]
latest_ema20 = df['EMA20'].iloc[-1]
latest_ema50 = df['EMA50'].iloc[-1]
latest_rsi = df['RSI'].iloc[-1]

if latest_close > latest_ema20 and latest_ema20 > latest_ema50 and latest_rsi < 70:
    signal = "📈 Buy Signal"
elif latest_close < latest_ema20 and latest_ema20 < latest_ema50 and latest_rsi > 30:
    signal = "📉 Sell Signal"
else:
    signal = "⏳ No Clear Signal"

st.subheader(f"Trading Signal for {symbol}: {signal}")

# Plot chart
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Candlestick'
))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='blue', width=1), name="EMA20"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='orange', width=1), name="EMA50"))

fig.update_layout(title=f"{symbol} Price Chart", xaxis_title="Time", yaxis_title="Price (USD)")
st.plotly_chart(fig, use_container_width=True)
