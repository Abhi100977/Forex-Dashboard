import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import ta
import requests
from datetime import datetime
import time

# Functions
def fetch_btc_data():
    try:
        url = 'https://api.binance.com/api/v3/klines'
        params = {'symbol': 'BTCUSDT', 'interval': '1h', 'limit': 100}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        return df[['time', 'open', 'high', 'low', 'close']]
    except Exception as e:
        st.error(f"Error fetching BTC data: {e}")
        return pd.DataFrame()

def fetch_xau_data(api_key):
    try:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'FX_INTRADAY',
            'from_symbol': 'XAU',
            'to_symbol': 'USD',
            'interval': '60min',
            'apikey': api_key,
            'outputsize': 'compact'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        time_series = data.get('Time Series FX (60min)', {})
        records = []
        for time_str, values in time_series.items():
            time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            open_price = float(values['1. open'])
            high = float(values['2. high'])
            low = float(values['3. low'])
            close = float(values['4. close'])
            records.append({'time': time, 'open': open_price, 'high': high, 'low': low, 'close': close})
        df = pd.DataFrame(records)
        df.sort_values('time', inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching XAU data: {e}")
        return pd.DataFrame()

def add_indicators(df):
    df['EMA9'] = ta.trend.ema_indicator(df['close'], window=9)
    df['EMA21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD_hist'] = ta.trend.macd_diff(df['close'])
    return df

def generate_signal(df):
    if (
        df['EMA9'].iloc[-2] < df['EMA21'].iloc[-2] and
        df['EMA9'].iloc[-1] > df['EMA21'].iloc[-1] and
        df['RSI'].iloc[-1] < 70 and
        df['MACD_hist'].iloc[-1] > 0
    ):
        return '📈 BUY'
    elif (
        df['EMA9'].iloc[-2] > df['EMA21'].iloc[-2] and
        df['EMA9'].iloc[-1] < df['EMA21'].iloc[-1] and
        df['RSI'].iloc[-1] > 30 and
        df['MACD_hist'].iloc[-1] < 0
    ):
        return '📉 SELL'
    else:
        return '⏸ HOLD'

# Streamlit Dashboard
st.set_page_config(page_title="Forex Dashboard", page_icon="📈", layout="wide")

st.title("🚀 Real-Time Forex Dashboard")

refresh_rate = st.sidebar.selectbox(
    "Refresh Rate (minutes):", options=[1, 2, 5], index=1
)

api_key = st.secrets["api_key"] if "api_key" in st.secrets else st.text_input("🔑 Enter Alpha Vantage API Key:")

tabs = st.tabs(["💰 BTC/USD", "🪙 XAU/USD (Gold)"])

if api_key:

    with tabs[0]:
        st.header("💰 Bitcoin (BTC/USD)")
        btc_df = fetch_btc_data()
        if not btc_df.empty:
            btc_df = add_indicators(btc_df)
            btc_signal = generate_signal(btc_df)
            st.subheader(f"Signal: {btc_signal}")
            fig_btc = go.Figure()
            fig_btc.add_trace(go.Candlestick(x=btc_df['time'], open=btc_df['open'], high=btc_df['high'],
                                             low=btc_df['low'], close=btc_df['close'], name='Price'))
            fig_btc.add_trace(go.Scatter(x=btc_df['time'], y=btc_df['EMA9'], line=dict(color='blue'), name='EMA9'))
            fig_btc.add_trace(go.Scatter(x=btc_df['time'], y=btc_df['EMA21'], line=dict(color='red'), name='EMA21'))
            fig_btc.update_layout(xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_btc, use_container_width=True)

    with tabs[1]:
        st.header("🪙 Gold (XAU/USD)")
        xau_df = fetch_xau_data(api_key)
        if not xau_df.empty:
            xau_df = add_indicators(xau_df)
            xau_signal = generate_signal(xau_df)
            st.subheader(f"Signal: {xau_signal}")
            fig_xau = go.Figure()
            fig_xau.add_trace(go.Candlestick(x=xau_df['time'], open=xau_df['open'], high=xau_df['high'],
                                             low=xau_df['low'], close=xau_df['close'], name='Price'))
            fig_xau.add_trace(go.Scatter(x=xau_df['time'], y=xau_df['EMA9'], line=dict(color='blue'), name='EMA9'))
            fig_xau.add_trace(go.Scatter(x=xau_df['time'], y=xau_df['EMA21'], line=dict(color='red'), name='EMA21'))
            fig_xau.update_layout(xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_xau, use_container_width=True)

    st.success("Signals are based on EMA Crossover, RSI, and MACD Histogram indicators.")

    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()
Added app.py
