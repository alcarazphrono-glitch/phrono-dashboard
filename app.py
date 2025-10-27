# ===============================================================
# Phrono Lab — Streamlit Dashboard (v4)
# Elegante, funcional y preparado para ampliarse.
# ===============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ===============================================================
# CONFIGURACIÓN PRINCIPAL
# ===============================================================

st.set_page_config(page_title="Phrono Lab", layout="wide", page_icon="🧭")

# Paleta de colores corporativa
BLUE = "#0A2239"     # Azul petróleo
GOLD = "#D4A017"     # Dorado elegante
LIGHT_BG = "#FFFFFF"
GRID = "#ECEFF3"
SIDEBAR_BG = "#F7F9FC"

# ===============================================================
# CSS — Tema visual completo
# ===============================================================

def inject_styles():
    css = f"""
    <style>
    :root {{
        --blue: {BLUE};
        --gold: {GOLD};
        --light-bg: {LIGHT_BG};
        --sidebar-bg: {SIDEBAR_BG};
        --grid: {GRID};
    }}

    .stApp {{
        background-color: var(--light-bg);
        color: var(--blue);
        font-family: 'Inter', sans-serif;
    }}

    /* NAVBAR */
    .ph-navbar {{
        position: sticky;
        top: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 28px;
        background: var(--light-bg);
        border-bottom: 1px solid #E6E9EE;
        box-shadow: 0 4px 18px rgba(10,34,57,0.05);
    }}
    .ph-brand {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .ph-logo {{
        width: 42px; height: 42px;
        background: linear-gradient(135deg, var(--blue), #073043);
        color: var(--gold);
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 18px; border-radius: 8px;
    }}
    .ph-title {{
        font-size: 18px; font-weight: 700; color: var(--blue);
    }}
    .ph-sub {{
        font-size: 12px; color: #6B7280;
    }}
    .ph-links a {{
        margin-left: 20px;
        color: var(--blue);
        text-decoration: none;
        font-weight: 600;
        padding: 6px 8px;
        border-radius: 6px;
    }}
    .ph-links a:hover {{
        color: var(--gold);
        background: rgba(212,160,23,0.08);
    }}

    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid #E6E9EE !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background-color: var(--gold) !important;
        color: white !important;
        border: none;
    }}

    /* METRIC CARDS */
    .metric-card {{
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px 18px;
        border: 1px solid #E9EEF4;
        box-shadow: 0 6px 18px rgba(10,34,57,0.06);
        margin-bottom: 12px;
    }}
    .metric-title {{
        font-size: 13px;
        color: var(--blue);
        margin-bottom: 6px;
        font-weight: 700;
    }}
    .metric-value {{
        font-size: 22px;
        color: var(--gold);
        font-weight: 800;
    }}

    /* SECCIONES */
    .section-title {{
        font-size: 19px;
        color: var(--blue);
        font-weight: 800;
        margin: 20px 0 10px 0;
    }}

    .ph-footer {{
        text-align: right;
        color: #6B7280;
        font-size: 13px;
        margin-top: 20px;
    }}
    </style>
    """
    components.html(css, height=0, scrolling=False)

# ===============================================================
# BLOQUE CONFIGURABLE (solo modificar aquí)
# ===============================================================

TICKERS_TO_MONITOR = [
    "CL=F", "NG=F", "GC=F", "SI=F", "HG=F", "ZC=F", "ZS=F", "KC=F", "EWW", "ILF"
]
BENCHMARKS_TO_MONITOR = [
    "^GSPC", "^IXIC", "^MXX", "GC=F", "CL=F"
]

# ===============================================================
# FUNCIONES DE DATOS
# ===============================================================

@st.cache_data(ttl=3600)
def fetch_prices(tickers, period="3y", interval="1d"):
    if not tickers:
        return pd.DataFrame()
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False, threads=True)
        if data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            df = data["Adj Close"] if "Adj Close" in data.columns.levels[0] else data["Close"]
        else:
            df = data[["Adj Close"]] if "Adj Close" in data.columns else data[["Close"]]
        df.columns = [str(c) for c in df.columns]
        df.index = pd.to_datetime(df.index).date
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

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
            "Volatility": float(round(annualized_vol(lr), 6)),
            "Sharpe": float(round(sharpe_ratio(lr), 6)),
            "Cumulative Return": float(round(np.exp(lr.sum()) - 1, 6)),
            "Max Drawdown": float(round(max_drawdown(prices_df[col].dropna()), 6)),
        }
    return pd.DataFrame(out).T

# ===============================================================
# VISUALIZACIONES
# ===============================================================

def plot_base100(df, title="Performance (Base 100)"):
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=col, line=dict(width=2)))
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(color=GOLD, size=18)),
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

def plot_log_returns(df, title="Cumulative Log Returns"):
    lret = log_returns(df.fillna(method="ffill")).dropna()
    if lret.empty:
        return go.Figure()
    cum = lret.cumsum().apply(np.exp).subtract(1)
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col], mode="lines", name=col, line=dict(width=2)))
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(color=GOLD, size=16)),
        plot_bgcolor=LIGHT_BG,
        paper_bgcolor=LIGHT_BG,
        font=dict(color=BLUE),
        xaxis=dict(color=BLUE, gridcolor=GRID),
        yaxis=dict(color=BLUE, gridcolor=GRID),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified",
    )
    return fig

# ===============================================================
# NAVBAR
# ===============================================================

def render_navbar():
    navbar_html = f"""
    <div class="ph-navbar">
        <div class="ph-brand">
            <div class="ph-logo">P</div>
            <div>
                <div class="ph-title">Phrono Lab</div>
                <div class="ph-sub">Intelligence-driven capital</div>
            </div>
        </div>
        <div class="ph-links">
            <a href="#portfolio">Portfolio</a>
            <a href="#benchmarks">Benchmarks</a>
            <a href="#signals">Signals</a>
        </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)

# ===============================================================
# MAIN APP
# ===============================================================

def main():
    inject_styles()
    render_navbar()

    st.sidebar.title("Controls")
    st.sidebar.markdown("Refine your portfolio selection.")
    assets = st.sidebar.multiselect("Select assets", options=TICKERS_TO_MONITOR, default=TICKERS_TO_MONITOR[:6])
    period = st.sidebar.selectbox("History length", ["1y", "2y", "3y", "5y"], index=2)
    refresh_btn = st.sidebar.button("🔄 Refresh Data")

    if refresh_btn or "prices" not in st.session_state:
        st.session_state["prices"] = fetch_prices(assets, period=period)
    prices = st.session_state["prices"]

    st.markdown("<div class='section-title' id='portfolio'>📊 Portfolio Overview</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<div class='metric-card'><div class='metric-title'>Assets</div><div class='metric-value'>{len(assets)}</div></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><div class='metric-title'>Sharpe (est.)</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><div class='metric-title'>Volatility</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='metric-card'><div class='metric-title'>Top Asset</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)

    if prices.empty:
        st.warning("No data available. Edit tickers in the CONFIG section.")
        return

    df_base = base100(prices)
    st.plotly_chart(plot_base100(df_base, "Portfolio (Base 100)"), use_container_width=True)
    st.plotly_chart(plot_log_returns(prices), use_container_width=True)

    st.markdown("<div class='section-title' id='benchmarks'>📈 Benchmark Tracker</div>", unsafe_allow_html=True)
    benchmarks = st.multiselect("Select benchmarks", options=BENCHMARKS_TO_MONITOR, default=BENCHMARKS_TO_MONITOR[:4])
    if benchmarks:
        bench_prices = fetch_prices(benchmarks, period=period)
        if not bench_prices.empty:
            st.plotly_chart(plot_base100(base100(bench_prices)), use_container_width=True)

    st.markdown("<div class='section-title' id='signals'>🧠 Research & Signals</div>", unsafe_allow_html=True)
    st.write("This section will include SARIMA / GARCH cycle detectors and Parrondo alternation analytics.")

    st.markdown(f"<div class='ph-footer'>Phrono © {datetime.now().year} — built for intelligent capital.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
