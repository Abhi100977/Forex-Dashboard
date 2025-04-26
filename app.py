import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import ta

# Set Streamlit page config
st.set_page_config(page_title="Forex Dashboard", layout="wide")

# Title
st.title("📈 Forex Dashboard - GOLD & BTC Day Trading Signals")

# Sidebar
symbol = st.sidebar.selectbox(
    "Choose a symbol",
    ["BTCUSDT"]
)

interval = st.sidebar.selectbox(
    "Choose timeframe",
    ["1m", "5m", "15m", "1h", "4h", "1d"]
)

# Function to fetch data
def get_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

# Fetch data
try:
    df = get_klines(symbol, interval)
except:
    st.error("Failed to load data. Try again later.")
    st.stop()

# 🛡️ Check if DataFrame is empty
if df.empty:
    st.error("❌ No data fetched. Please try another symbol or timeframe.")
    st.stop()

# Calculate indicators
df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
df['RSI'] = ta.momentum.rsi(df['close'], window=14)

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


# Display Signal
st.subheader(f"**Trading Signal for {symbol} ({interval}): {signal}**")

# Plot candlestick chart
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close']
)])

fig.update_layout(
    title=f"{symbol} Price Chart ({interval})",
    xaxis_title="Time",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=600,
)

st.plotly_chart(fig, use_container_width=True)

# Show Table
st.dataframe(df.tail(10))
