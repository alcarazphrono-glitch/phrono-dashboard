# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# -------------------------
# Constants / Theme colors
# -------------------------
BLUE = "#0A2239"
GOLD = "#D4A017"
LIGHT_BG = "#FFFFFF"
SIDEBAR_BG = "#F7F9FC"
GRID = "#ECEFF3"

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Phrono Lab", layout="wide", page_icon="🧭")

# -------------------------
# CSS / Theme
# -------------------------
def load_styles():
    st.markdown(
        f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
    :root {{ --blue: {BLUE}; --gold: {GOLD}; --light-bg: {LIGHT_BG}; --sidebar-bg: {SIDEBAR_BG}; --grid: {GRID}; }}

    /* App background & font */
    .stApp {{
        background-color: var(--light-bg);
        color: var(--blue);
        font-family: 'Inter', sans-serif;
    }}

    /* Top navbar */
    .topbar {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        padding:14px 22px;
        border-bottom:1px solid #E6E9EE;
        margin-bottom:18px;
        background: linear-gradient(180deg, #ffffff 0%, #ffffff 100%);
    }}
    .brand {{
        display:flex;
        align-items:center;
        gap:12px;
    }}
    .logo {{
        width:44px;height:44px;border-radius:8px;
        background: linear-gradient(135deg, var(--blue), #073043);
        display:flex;align-items:center;justify-content:center;color:var(--gold);
        font-weight:800;font-size:18px;
        box-shadow: 0 6px 18px rgba(10,34,57,0.08);
    }}
    .brand-title {{
        font-size:18px;font-weight:700;color:var(--blue);
        line-height:1;
    }}
    .brand-sub {{
        font-size:12px;color:#6B7280;margin-top:2px;
    }}
    .nav-links a {{
        margin-left:18px;
        color: var(--blue);
        font-weight:600;
        text-decoration:none;
        font-size:14px;
        padding:6px 8px;border-radius:6px;
    }}
    .nav-links a:hover {{ color: var(--gold); background: rgba(212,160,23,0.06); }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        padding: 18px 14px 30px 14px;
        border-right: 1px solid #E6E9EE;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background-color: var(--gold) !important;
        color: white !important;
    }}

    /* Metric cards */
    .metric-card {{
        background: #FFFFFF;
        border-radius:12px;
        padding:14px 18px;
        border:1px solid #E9EEF4;
        box-shadow: 0 8px 20px rgba(10,34,57,0.06);
    }}
    .metric-title {{ font-size:13px; color:var(--blue); margin-bottom:6px; font-weight:600; }}
    .metric-value {{ font-size:20px; color:var(--gold); font-weight:800; }}

    /* Section headings */
    .section-title {{
        font-size:18px;color:var(--blue);font-weight:700;margin-bottom:10px;
    }}

    /* Footer */
    .footer {{ text-align:right;color:#6B7280;font-size:13px;margin-top:20px; }}

    /* Responsive tweaks */
    @media (max-width: 800px) {{
        .nav-links {{ display:none; }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


# -------------------------
# Data helpers (cached)
# -------------------------
@st.cache_data(ttl=3600)
def fetch_prices(tickers, period="3y", interval="1d"):
    """Fetch adjusted close prices for tickers via yfinance."""
    if isinstance(tickers, str):
        tickers = [tickers]
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False, threads=True)
    except Exception as e:
        raise RuntimeError(f"yfinance download error: {e}")
    # Handle single vs multiple tickers
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.get_level_values(0):
            df = data["Adj Close"].copy()
        else:
            # sometimes yfinance returns different structure
            if "Close" in data.columns.get_level_values(0):
                df = data["Close"].copy()
            else:
                df = data.copy()
    else:
        # DataFrame with single column or several but flattened
        if "Adj Close" in data.columns:
            df = data["Adj Close"].to_frame() if isinstance(data["Adj Close"], pd.Series) else data["Adj Close"]
        elif "Close" in data.columns:
            df = data["Close"].to_frame() if isinstance(data["Close"], pd.Series) else data["Close"]
        else:
            df = data.copy()
    # normalise column names and index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    df.columns = [str(c) for c in df.columns]
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
    """
    Return dataframe with KPIs for each asset: Annualized Vol, Sharpe, Cumulative Return, Max Drawdown
    """
    if prices_df.empty:
        return pd.DataFrame()
    lret = log_returns(prices_df.fillna(method="ffill")).dropna()
    out = {}
    for col in lret.columns:
        lr = lret[col].dropna()
        out[col] = {
            "Annualized Vol": float(round(annualized_vol(lr), 6)),
            "Sharpe": float(round(sharpe_ratio(lr), 6)),
            "Cumulative Return": float(round(np.exp(lr.sum()) - 1, 6)),
            "Max Drawdown": float(round(max_drawdown(prices_df[col].dropna()), 6)),
        }
    return pd.DataFrame(out).T


# -------------------------
# Plotly & charts
# -------------------------
def plot_base100(df, title="Base 100"):
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=col, line=dict(width=2)))
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(color=GOLD, size=18)),
        plot_bgcolor=LIGHT_BG,
        paper_bgcolor=LIGHT_BG,
        font=dict(color=BLUE),
        legend=dict(font=dict(color=BLUE)),
        xaxis=dict(color=BLUE, gridcolor=GRID),
        yaxis=dict(color=BLUE, gridcolor=GRID),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified",
    )
    return fig


def plot_log_returns(df, title="Log Returns (cumulative)"):
    lret = log_returns(df.fillna(method="ffill")).dropna()
    if lret.empty:
        return go.Figure()
    cum = lret.cumsum().apply(np.exp).subtract(1)
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col], mode="lines", name=col, line=dict(width=2)))
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(color=GOLD, size=14)),
        plot_bgcolor=LIGHT_BG,
        paper_bgcolor=LIGHT_BG,
        font=dict(color=BLUE),
        xaxis=dict(color=BLUE, gridcolor=GRID),
        yaxis=dict(color=BLUE, gridcolor=GRID),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified",
    )
    return fig


# -------------------------
# UI Components
# -------------------------
def render_navbar():
    nav_html = f"""
    <div class="topbar">
      <div class="brand">
        <div class="logo">P</div>
        <div>
          <div class="brand-title">Phrono Lab</div>
          <div class="brand-sub">Intelligence-driven capital</div>
        </div>
      </div>
      <div class="nav-links">
        <a href="#overview">Overview</a>
        <a href="#portfolio">Portfolio</a>
        <a href="#benchmarks">Benchmarks</a>
        <a href="#signals">Signals</a>
        <a href="#about">About</a>
      </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)


# -------------------------
# Main app
# -------------------------
def main():
    load_styles()
    render_navbar()

    # Sidebar controls
    st.sidebar.header("Phrono Controls")
    default_assets = ["CL=F", "NG=F", "GC=F", "SI=F", "HG=F", "ZC=F", "ZS=F", "KC=F", "EWW", "ILF"]
    assets = st.sidebar.multiselect("Assets to monitor", options=default_assets, default=default_assets[:6])
    period = st.sidebar.selectbox("History length", options=["1y", "2y", "3y", "5y"], index=2)
    refresh = st.sidebar.button("Refresh Data")

    # KPI top row
    col1, col2, col3, col4 = st.columns([1.2, 1.0, 1.0, 1.2])
    with col1:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>Total Assets</div><div class='metric-value'>"
            + str(len(assets))
            + "</div></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>Daily Change</div><div class='metric-value'>+0.0%</div></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>Fund Sharpe (est.)</div><div class='metric-value'>0.00</div></div>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            "<div class='metric-card'><div class='metric-title'>Top Performer</div><div class='metric-value'>—</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Fetch prices (cached)
    try:
        if refresh or ("prices" not in st.session_state):
            prices = fetch_prices(assets, period=period)
            st.session_state["prices"] = prices
        else:
            prices = st.session_state.get("prices", fetch_prices(assets, period=period))
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return

    if prices.empty:
        st.warning("No data available for selected assets. Try different selection.")
        return

    # Portfolio Monitor section
    st.markdown('<div class="section-title" id="portfolio">📊 Portfolio Monitor</div>', unsafe_allow_html=True)
    left, right = st.columns([3, 1])
    with left:
        df_base = base100(prices.fillna(method="ffill")).dropna()
        fig = plot_base100(df_base, title="Portfolio (Base 100)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Performance (cumulative log-returns)")
        fig_lr = plot_log_returns(prices)
        st.plotly_chart(fig_lr, use_container_width=True)
    with right:
        st.markdown("<div class='metric-card'><div class='metric-title'>KPIs</div>", unsafe_allow_html=True)
        kpis = compute_kpis(prices)
        if not kpis.empty:
            st.dataframe(kpis.style.format("{:.6f}"))
        else:
            st.write("No KPIs available.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Benchmarks
    st.markdown('<div class="section-title" id="benchmarks">📈 Benchmarks & Context</div>', unsafe_allow_html=True)
    bench_defaults = ["^GSPC", "^IXIC", "^MXX", "GC=F", "CL=F"]
    bench_sel = st.multiselect("Select benchmarks", options=bench_defaults, default=bench_defaults[:4])
    if bench_sel:
        bench_prices = fetch_prices(bench_sel, period=period)
        if not bench_prices.empty:
            fig2 = plot_base100(base100(bench_prices.fillna(method="ffill")).dropna(), title="Benchmarks (Base 100)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Benchmark data not available.")
    else:
        st.info("Select at least one benchmark.")

    st.markdown("---")

    # Research / Signals
    st.markdown('<div class="section-title" id="signals">🔍 Research & Signals</div>', unsafe_allow_html=True)
    st.write(
        "This area will host SARIMA, GARCH and Parrondo alternation modules. For now it contains research notes and placeholders."
    )
    st.markdown(
        "<div style='color:#6B7280;font-size:13px;'>Phrono Lab — iterative build. Models coming: SARIMA/GARCH, Parrondo alternation, options overlay.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='footer'>Phrono © " + str(datetime.now().year) + "</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
