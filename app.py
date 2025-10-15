# app.py
# Phrono Lab - UI v3 (clean, professional, navbar visual)
# Replace existing app.py with this file.
# Note: edit the TICKERS_TO_MONITOR and BENCHMARKS_TO_MONITOR in the CONFIG block below.

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# -----------------------------
# CONFIG / THEME
# -----------------------------
BLUE = "#0A2239"     # azul petróleo
GOLD = "#D4A017"     # dorado
LIGHT_BG = "#FFFFFF"
SIDEBAR_BG = "#F7F9FC"
GRID = "#ECEFF3"

st.set_page_config(page_title="Phrono Lab", page_icon="🧭", layout="wide")

# -----------------------------
# CSS / STYLING (visual navbar fixed up top)
# -----------------------------
def inject_styles():
    st.markdown(
        f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
    :root {{ --blue: {BLUE}; --gold: {GOLD}; --light-bg: {LIGHT_BG}; --sidebar-bg: {SIDEBAR_BG}; --grid: {GRID}; }}

    /* App */
    .stApp {{ background-color: var(--light-bg); color: var(--blue); font-family: 'Inter', sans-serif; }}

    /* NAVBAR (visual only) */
    .ph-navbar {{
        position: sticky;
        top: 0;
        z-index: 9999;
        display:flex;
        align-items:center;
        justify-content:space-between;
        padding:12px 22px;
        background: var(--light-bg);
        border-bottom: 1px solid #E6E9EE;
        box-shadow: 0 6px 18px rgba(10,34,57,0.03);
    }}
    .ph-brand {{
        display:flex; align-items:center; gap:12px;
    }}
    .ph-logo {{
        width:44px; height:44px; border-radius:8px;
        background: linear-gradient(135deg, var(--blue), #073043);
        display:flex; align-items:center; justify-content:center; color:var(--gold);
        font-weight:800; font-size:18px;
    }}
    .ph-title {{ font-size:18px; font-weight:700; color:var(--blue); line-height:1; }}
    .ph-sub {{ font-size:12px; color:#6B7280; margin-top:2px; }}

    .ph-links a {{
        margin-left:16px; color:var(--blue); text-decoration:none; font-weight:600; padding:6px 8px; border-radius:6px;
    }}
    .ph-links a:hover {{ color:var(--gold); background: rgba(212,160,23,0.06); }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: var(--sidebar-bg) !important; padding:18px 14px 30px 14px; border-right:1px solid #E6E9EE; }}
    [data-testid="stSidebar"] .stButton > button {{ background-color: var(--gold) !important; color:white !important; }}

    /* Metric cards */
    .metric-card {{
        background: #FFFFFF;
        border-radius:12px;
        padding:12px 14px;
        border:1px solid #E9EEF4;
        box-shadow: 0 10px 30px rgba(10,34,57,0.06);
        margin-bottom:12px;
    }}
    .metric-title {{ font-size:13px; color:var(--blue); margin-bottom:6px; font-weight:700; }}
    .metric-value {{ font-size:20px; color:var(--gold); font-weight:800; }}

    /* Section title */
    .section-title {{ font-size:18px; color:var(--blue); font-weight:700; margin-bottom:10px; }}

    /* Footer */
    .ph-footer {{ text-align:right; color:#6B7280; font-size:13px; margin-top:18px; }}

    /* Responsive tweaks */
    @media (max-width: 800px) {{
        .ph-links {{ display:none; }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


# -----------------------------
# CONFIG: where to add tickers
# -----------------------------
# --- IMPORTANT ---
# To add or change tickers, edit the lists below only.
# This block is safe to modify and will NOT break the app structure.
#
# Examples:
# - Use yfinance tickers like "AAPL", "MSFT", or ETFs like "SPY", "QQQ".
# - Commodities examples: "CL=F" (Crude Oil), "GC=F" (Gold), "ZC=F" (Corn)
#
# Edit here:

TICKERS_TO_MONITOR = [
    # Add/remove tickers here, e.g. "AAPL", "CL=F", "GC=F"
    "CL=F", "NG=F", "GC=F", "SI=F", "HG=F", "ZC=F", "ZS=F", "KC=F", "EWW", "ILF"
]
BENCHMARKS_TO_MONITOR = [
    # Add/remove benchmark tickers here
    "^GSPC", "^IXIC", "^MXX", "GC=F", "CL=F"
]
# End of editable block
# -----------------------------


# -----------------------------
# DATA HELPERS (cached)
# -----------------------------
@st.cache_data(ttl=3600)
def fetch_prices(tickers, period="3y", interval="1d"):
    """
    Fetch adjusted close prices via yfinance.
    Returns DataFrame with date index and ticker columns.
    """
    if not tickers:
        return pd.DataFrame()
    if isinstance(tickers, str):
        tickers = [tickers]
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False, threads=True)
    except Exception as e:
        # Bubble up as runtime error for streamlit to capture
        raise RuntimeError(f"yfinance download error: {e}")

    if data.empty:
        return pd.DataFrame()

    # yfinance can return MultiIndex columns for multiple tickers
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.get_level_values(0):
            df = data["Adj Close"].copy()
        elif "Close" in data.columns.get_level_values(0):
            df = data["Close"].copy()
        else:
            df = data.copy()
    else:
        # Single ticker returns normal DataFrame/Series
        if "Adj Close" in data.columns:
            df = data["Adj Close"].to_frame() if isinstance(data["Adj Close"], pd.Series) else data["Adj Close"]
        elif "Close" in data.columns:
            df = data["Close"].to_frame() if isinstance(data["Close"], pd.Series) else data["Close"]
        else:
            df = data.copy()

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


# -----------------------------
# PLOTS (plotly)
# -----------------------------
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


# -----------------------------
# UI: render navbar (visual only)
# -----------------------------
def render_navbar():
    navbar_html = f"""
    <div class="ph-navbar" role="navigation" aria-label="Phrono navigation">
      <div class="ph-brand">
        <div class="ph-logo">P</div>
        <div>
          <div class="ph-title">Phrono Lab</div>
          <div class="ph-sub">Intelligence-driven capital</div>
        </div>
      </div>
      <div class="ph-links">
        <a href="#portfolio">Portfolio Monitor</a>
        <a href="#benchmarks">Benchmark Tracker</a>
        <a href="#signals">Insights</a>
      </div>
      <div style="display:flex;gap:12px;align-items:center;">
        <a href="#settings" style="color:#6B7280;text-decoration:none;font-weight:600;">Settings</a>
        <a href="#about" style="color:#6B7280;text-decoration:none;font-weight:600;">About</a>
        <a href="#login" style="color:#6B7280;text-decoration:none;font-weight:600;">Login</a>
      </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)


# -----------------------------
# MAIN
# -----------------------------
def main():
    inject_styles()
    render_navbar()

    # Sidebar controls (compact)
    st.sidebar.title("Phrono Controls")
    st.sidebar.markdown("Select universe and data preferences.")
    assets = st.sidebar.multiselect("Assets to monitor (edit CONFIG block in file to change default list)", options=TICKERS_TO_MONITOR, default=TICKERS_TO_MONITOR[:6])
    period = st.sidebar.selectbox("History length", options=["1y", "2y", "3y", "5y"], index=2)
    refresh_btn = st.sidebar.button("Refresh Data")

    # Top KPI cards
    col1, col2, col3, col4 = st.columns([1.2, 1.0, 1.0, 1.2])
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Monitored assets</div><div class='metric-value'>{len(assets)}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Daily Change</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Fund Sharpe (est.)</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Top Performer</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Fetch prices (cached)
    try:
        if refresh_btn or ("prices" not in st.session_state):
            prices = fetch_prices(assets, period=period)
            st.session_state["prices"] = prices
        else:
            prices = st.session_state.get("prices", fetch_prices(assets, period=period))
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return

    # If no prices found
    if prices.empty:
        st.warning("No data available for selected assets. Add tickers in the CONFIG block at the top of the file.")
        return

    # Portfolio Monitor
    st.markdown('<div class="section-title" id="portfolio">📊 Portfolio Monitor</div>', unsafe_allow_html=True)
    left, right = st.columns([3, 1])
    with left:
        df_base = base100(prices.fillna(method="ffill")).dropna()
        fig_base = plot_base100(df_base, title="Portfolio (Base 100)")
        st.plotly_chart(fig_base, use_container_width=True)
        st.markdown("### Performance (cumulative log-returns)")
        fig_lr = plot_log_returns(prices)
        st.plotly_chart(fig_lr, use_container_width=True)
    with right:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>KPIs</div>", unsafe_allow_html=True)
        kpis = compute_kpis(prices)
        if not kpis.empty:
            st.dataframe(kpis.style.format("{:.6f}"))
        else:
            st.write("KPIs not available for current selection.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Benchmarks section
    st.markdown('<div class="section-title" id="benchmarks">📈 Benchmark Tracker</div>', unsafe_allow_html=True)
    bench_sel = st.multiselect("Select benchmarks (edit default in CONFIG block)", options=BENCHMARKS_TO_MONITOR, default=BENCHMARKS_TO_MONITOR[:4])
    if bench_sel:
        bench_prices = fetch_prices(bench_sel, period=period)
        if not bench_prices.empty:
            bench_base = base100(bench_prices.fillna(method="ffill")).dropna()
            fig_bench = plot_base100(bench_base, title="Benchmarks (Base 100)")
            st.plotly_chart(fig_bench, use_container_width=True)
        else:
            st.info("No benchmark data available for selected tickers.")
    else:
        st.info("Select one or more benchmarks to visualize.")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Research & Signals (placeholder)
    st.markdown('<div class="section-title" id="signals">🔍 Research & Signals</div>', unsafe_allow_html=True)
    st.write("Integrations coming: SARIMA, GARCH, Parrondo alternation, options overlays. This space will host signal visualizations and backtest summaries.")

    # Footer
    st.markdown(f"<div class='ph-footer'>Phrono © {datetime.now().year} — Built for iterative research.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
