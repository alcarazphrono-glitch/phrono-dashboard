# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# -------------------------
# CONFIG
# -------------------------
BLUE = "#0A2239"
GOLD = "#D4A017"
LIGHT = "#F7F9FB"
TEXT = "#0A2239"

st.set_page_config(page_title="Phrono Lab", layout="wide", page_icon="🧭")

# -------------------------
# THEME / CSS
# -------------------------
def set_custom_theme():
    st.markdown(
        f"""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
        :root {{ --blue: {BLUE}; --gold: {GOLD}; --light: {LIGHT}; --text: {TEXT}; }}

        /* Page background */
        .stApp {{
            background-color: #FFFFFF;
            color: var(--text);
            font-family: 'Inter', sans-serif;
        }}

        /* Top navbar */
        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 18px;
            border-bottom: 1px solid #e6e9ee;
            margin-bottom: 18px;
        }}
        .brand {{
            display:flex;
            align-items:center;
            gap:12px;
        }}
        .logo {{
            width:44px;height:44px;border-radius:6px;
            background: linear-gradient(135deg, var(--blue), #073043);
            display:flex;align-items:center;justify-content:center;color:var(--gold);
            font-weight:700;font-size:18px;
        }}
        .nav-links a {{
            margin-left:18px;
            color:var(--blue);
            font-weight:600;
            text-decoration:none;
        }}
        .nav-links a:hover {{ color: var(--gold); }}

        /* Sidebar */
        .sidebar .css-1d391kg {{
            background-color: {LIGHT} !important;
        }}

        /* Cards */
        .card {{
            background: #ffffff;
            border: 1px solid #e8edf2;
            border-radius:10px;
            padding:12px 16px;
            box-shadow: 0 6px 18px rgba(14,30,37,0.06);
        }}
        .card-title {{
            color: var(--blue);
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .card-value {{
            color: var(--gold);
            font-weight: 700;
            font-size: 20px;
        }}

        /* Buttons */
        .stButton > button {{
            background-color: var(--gold) !important;
            color: white !important;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 700;
        }}

        /* Tables */
        .stDataFrame table {{
            border-radius: 6px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# -------------------------
# DATA HELPERS
# -------------------------
@st.cache_data(ttl=3600)
def fetch_prices(tickers, period="3y", interval="1d"):
    """Fetch Adj Close prices via yfinance and return DataFrame with date index."""
    if isinstance(tickers, str):
        tickers = [tickers]
    data = yf.download(tickers, period=period, interval=interval, progress=False)
    # yfinance returns single column when one ticker
    if 'Adj Close' in data.columns:
        df = data['Adj Close'].to_frame()
    elif isinstance(data, pd.DataFrame) and ('Adj Close' in data.columns.levels[1] if hasattr(data.columns, 'levels') else False):
        df = data['Adj Close']
    else:
        # fallback: assume DataFrame of Close
        if 'Close' in data.columns:
            df = data['Close'].to_frame() if isinstance(data['Close'], pd.Series) else data['Close']
        else:
            df = pd.DataFrame()
    # ensure columns are ticker names for multi
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    df.index = pd.to_datetime(df.index).date
    return df.sort_index()

def base100(df):
    return df.divide(df.iloc[0]).multiply(100)

def log_returns(df):
    return np.log(df / df.shift(1)).dropna()

def annualized_vol(logret, trading_days=252):
    return logret.std() * np.sqrt(trading_days)

def sharpe_ratio(logret, rf=0.0, trading_days=252):
    mu = logret.mean() * trading_days
    sigma = logret.std() * np.sqrt(trading_days)
    return (mu - rf) / sigma if sigma != 0 else np.nan

def max_drawdown(price_series):
    roll_max = price_series.cummax()
    drawdown = (price_series - roll_max) / roll_max
    return drawdown.min()

def compute_kpis(prices_df):
    lret = log_returns(prices_df.fillna(method='ffill')).dropna()
    out = {}
    for col in lret.columns:
        lr = lret[col].dropna()
        out[col] = {
            "Annualized Vol": round(annualized_vol(lr), 6),
            "Sharpe": round(sharpe_ratio(lr), 6),
            "Cumulative Return": round(np.exp(lr.sum()) - 1, 6),
            "Max Drawdown": round(max_drawdown(prices_df[col].dropna()), 6)
        }
    return pd.DataFrame(out).T

# -------------------------
# PLOTLY THEME (white bg)
# -------------------------
def themed_chart(df, title):
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col, line=dict(width=2)))
    fig.update_layout(
        title=dict(text=title, font=dict(color=GOLD, size=18)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=BLUE),
        legend=dict(font=dict(color=BLUE)),
        xaxis=dict(color=BLUE, gridcolor='#ECEFF3'),
        yaxis=dict(color=BLUE, gridcolor='#ECEFF3'),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig

# -------------------------
# UI: NAVBAR
# -------------------------
def render_navbar(active="Home"):
    nav_html = f"""
    <div class="topbar">
      <div class="brand">
        <div class="logo">P</div>
        <div style="display:flex;flex-direction:column;">
          <div style="font-weight:700;color:{BLUE};font-size:18px;">Phrono</div>
          <div style="font-size:12px;color:#677489;">Intelligence-driven capital</div>
        </div>
      </div>
      <div class="nav-links">
        <a href="#home" style="{'color:'+GOLD if active=='Home' else ''}">Home</a>
        <a href="#portfolio" style="{'color:'+GOLD if active=='Portfolio' else ''}">Portfolio</a>
        <a href="#bench" style="{'color:'+GOLD if active=='Bench' else ''}">Benchmarks</a>
        <a href="#research" style="{'color:'+GOLD if active=='Research' else ''}">Research</a>
        <a href="#about" style="{'color:'+GOLD if active=='About' else ''}">About</a>
      </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)

# -------------------------
# MAIN APP
# -------------------------
def main():
    set_custom_theme()
    render_navbar(active="Home")

    # Sidebar controls
    st.sidebar.header("Phrono Controls")
    st.sidebar.markdown("**Universe (select assets)**")
    default_assets = ["CL=F","NG=F","GC=F","SI=F","HG=F","ZC=F","ZS=F","KC=F","EWW","ILF"]
    assets = st.sidebar.multiselect("Assets to monitor", options=default_assets, default=default_assets[:6])
    period = st.sidebar.selectbox("History length", options=["1y","2y","3y","5y"], index=2)
    refresh = st.sidebar.button("Refresh Data")

    # Top metrics area (cards)
    col1, col2, col3, col4 = st.columns([1.2,1.0,1.0,1.2])
    with col1:
        st.markdown("<div class='card'><div class='card-title'>Total Assets</div><div class='card-value'>10</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'><div class='card-title'>Daily Change</div><div class='card-value'>+0.8%</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card'><div class='card-title'>Fund Sharpe (est.)</div><div class='card-value'>0.92</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='card'><div class='card-title'>Top Performer</div><div class='card-value'>GC=F</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Fetch data
    if refresh or ("prices" not in st.session_state):
        try:
            prices = fetch_prices(assets, period=period)
            st.session_state['prices'] = prices
        except Exception as e:
            st.error("Error fetching prices: " + str(e))
            return
    else:
        prices = st.session_state.get('prices', fetch_prices(assets, period=period))

    if prices is None or prices.empty:
        st.warning("No data found for selected assets. Try different selection or extend history.")
        return

    # Layout sections
    st.markdown("## Portfolio Monitor")
    left, right = st.columns([3,1])
    with left:
        df_base = base100(prices.fillna(method='ffill')).dropna()
        fig = themed_chart(df_base, "Portfolio (Base 100)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Returns (log)")
        st.line_chart(log_returns(prices.fillna(method='ffill')).cumsum().apply(np.exp).subtract(1).fillna(0))

    with right:
        st.markdown("### KPIs")
        kpis = compute_kpis(prices)
        st.dataframe(kpis.style.format("{:.4f}"))

    st.markdown("---")
    st.markdown("## Benchmarks & Context")
    bench_defaults = ["^GSPC","^IXIC","^MXX","GC=F","CL=F"]
    bench_sel = st.multiselect("Benchmarks", options=bench_defaults, default=bench_defaults[:4])
    bench_prices = fetch_prices(bench_sel, period=period)
    if not bench_prices.empty:
        fig2 = themed_chart(base100(bench_prices.fillna(method='ffill')).dropna(), "Benchmarks (Base 100)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No benchmark data available.")

    st.markdown("---")
    st.markdown("## Research & Signals (Preview)")
    st.write("SARIMA and GARCH modules will be integrated here. For now this section holds research notes and exploratory charts.")
    st.markdown("<div style='color:#677489;font-size:13px;'>Phrono Lab — iterative build. Models: SARIMA/GARCH, Parrondo alternation, options overlay.</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<div style='text-align:right;color:{GOLD};'>Phrono © {datetime.now().year}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
