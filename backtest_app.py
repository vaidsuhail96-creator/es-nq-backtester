import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="ES/NQ Backtester", layout="wide")

st.title("📊 ES & NQ Online Backtester")

# Sidebar
st.sidebar.header("Settings")

symbol_map = {
    "ES (S&P 500)": "ES=F",
    "NQ (Nasdaq)": "NQ=F"
}

symbol = symbol_map[
    st.sidebar.selectbox("Market", symbol_map.keys())
]

timeframe = st.sidebar.selectbox(
    "Timeframe", ["1m", "2m", "5m", "15m", "30m"]
)

period_map = {
    "1m": "7d",
    "2m": "7d",
    "5m": "30d",
    "15m": "60d",
    "30m": "90d"
}

period = period_map[timeframe]

ema_fast = st.sidebar.slider("Fast EMA", 5, 50, 20)
ema_slow = st.sidebar.slider("Slow EMA", 20, 200, 50)

sl = st.sidebar.slider("Stop Loss (Points)", 1, 50, 10)
tp = st.sidebar.slider("Take Profit (Points)", 1, 100, 20)

run = st.sidebar.button("▶ Run Backtest")


@st.cache_data
def load_data(sym, tf, per):
    return yf.download(sym, period=per, interval=tf)


def backtest(df):

    df = df.copy()

    df["EMA_F"] = df["Close"].ewm(span=ema_fast).mean()
    df["EMA_S"] = df["Close"].ewm(span=ema_slow).mean()

    pos = 0
    entry = 0.0

    pnl = []
    equity = [0.0]

    for i in range(1, len(df)):

        price = float(df["Close"].iloc[i])

        if pos == 0:

            if df["EMA_F"].iloc[i] > df["EMA_S"].iloc[i]:
                pos = 1
                entry = price

            elif df["EMA_F"].iloc[i] < df["EMA_S"].iloc[i]:
                pos = -1
                entry = price

        else:

            profit = (price - entry) * pos

            if profit >= tp or profit <= -sl:
                pnl.append(float(profit))
                equity.append(equity[-1] + profit)
                pos = 0

    return pnl, equity



if run:

    st.info("Loading data...")

    df = load_data(symbol, timeframe, period)

    if df.empty:
        st.error("No data available")
        st.stop()

    pnl, equity = backtest(df)

    trades = len(pnl)
    wins = len([p for p in pnl if p > 0])
    net = sum(pnl)

    winrate = wins / trades * 100 if trades else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Net PnL", f"{net:.2f}")
    c2.metric("Trades", trades)
    c3.metric("Win Rate", f"{winrate:.1f}%")
    c4.metric("Wins", wins)

    st.subheader("📈 Equity Curve")

    fig, ax = plt.subplots()
    ax.plot(equity)
    st.pyplot(fig)

    st.subheader("📉 Price + EMAs")

    fig2, ax2 = plt.subplots(figsize=(12,5))

    ax2.plot(df["Close"], label="Price")
    ax2.plot(df["EMA_F"], label="Fast EMA")
    ax2.plot(df["EMA_S"], label="Slow EMA")

    ax2.legend()
    st.pyplot(fig2)
