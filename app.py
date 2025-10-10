import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# -------------------------
# CONFIG
# -------------------------
# Se mantiene la paleta de colores para una identidad visual consistente.
BLUE = "#0A2239" # Color principal (Texto, Ejes)
GOLD = "#D4A017" # Color de acento (Botones, Títulos, Valores clave)
LIGHT_GREY = "#F0F2F6" # Nuevo: Un gris claro para el fondo de la sidebar.
TEXT = "#0A2239"
LINE_COLORS = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099', '#0099C6', '#DD4477', '#66AA00', '#B82E2E', '#316395'] # Paleta de colores más profesional para líneas.

st.set_page_config(page_title="Phrono Lab", layout="wide", page_icon="🧭")

# Inicialización de Session State al inicio para mejor práctica
if 'prices' not in st.session_state:
    st.session_state['prices'] = pd.DataFrame()

# -------------------------
# THEME / CSS (Optimizado y más robusto)
# -------------------------
def set_custom_theme():
    st.markdown(
        f"""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
        <style>
        :root {{ --blue: {BLUE}; --gold: {GOLD}; --light: {LIGHT_GREY}; --text: {TEXT}; }}

        /* General & Tipografía */
        .stApp {{
            background-color: #FFFFFF;
            color: var(--text);
            font-family: 'Inter', sans-serif;
        }}
        
        /* Encabezados */
        h1, h2, h3 {{ color: var(--blue); }}
        h2 {{ border-bottom: 2px solid #E8EBF0; padding-bottom: 5px; margin-top: 30px; }}
        
        /* Top navbar (Mejor alineación y separación) */
        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 18px;
            border-bottom: 1px solid #e6e9ee;
            margin-bottom: 24px;
        }}
        .brand {{
            display:flex; align-items:center; gap:12px;
        }}
        .logo {{
            width:40px;height:40px;border-radius:6px;
            background: linear-gradient(135deg, var(--blue), #073043);
            display:flex;align-items:center;justify-content:center;color:var(--gold);
            font-weight:800;font-size:18px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Añadido: Ligera sombra para un efecto 3D sutil */
        }}
        .nav-links a {{
            margin-left:20px; color:var(--blue); font-weight:600; text-decoration:none;
            padding: 5px 0;
            transition: color 0.2s ease;
        }}
        .nav-links a:hover, .nav-links a[style*="color:"]:not([href="#home"]) {{ 
            color: var(--gold) !important; 
        }}
        
        /* Sidebar (Estilo más sutil) */
        [data-testid="stSidebarContent"] {{
            background-color: {LIGHT_GREY} !important;
            padding-top: 2rem;
        }}
        .sidebar .stSelectbox label, .sidebar .stMultiselect label {{
             font-weight: 600;
        }}

        /* Cards (Sombra más pronunciada para profundidad) */
        .card {{
            background: #ffffff;
            border: 1px solid #e8edf2;
            border-radius:10px;
            padding:18px; /* Padding aumentado para un look más "airy" */
            box-shadow: 0 10px 30px rgba(14,30,37,0.08); /* Sombra más profesional */
            transition: transform 0.2s ease; /* Efecto hover sutil */
        }}
        .card:hover {{ transform: translateY(-3px); }}
        .card-title {{
            color: var(--blue);
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 14px;
            opacity: 0.8;
        }}
        .card-value {{
            color: var(--text);
            font-weight: 700;
            font-size: 24px;
            display: flex; align-items: center;
        }}
        .positive {{ color: #109618; }} /* Verde para positivo */
        .negative {{ color: #DC3912; }} /* Rojo para negativo */

        /* Botones (Mismo color, estilo más limpio) */
        .stButton > button {{
            background-color: var(--gold) !important;
            color: white !important;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 700;
            border: none;
            transition: background-color 0.2s ease;
        }}
        .stButton > button:hover {{
            background-color: #C09015 !important; /* Tono más oscuro al hacer hover */
        }}

        /* DataFrame (tablas) */
        .stDataFrame {{
            font-size: 13px;
        }}
        .stDataFrame table {{
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); /* Sombra en la tabla */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# -------------------------
# DATA HELPERS (Mantenidos)
# -------------------------
@st.cache_data(ttl=3600)
def fetch_prices(tickers, period="3y", interval="1d"):
    """Fetch Adj Close prices via yfinance and return DataFrame with date index."""
    if isinstance(tickers, str):
        tickers = [tickers]
    
    # Manejo de tickers vacíos
    if not tickers:
        return pd.DataFrame()

    data = yf.download(tickers, period=period, interval=interval, progress=False)
    
    # Manejo de múltiples columnas de yfinance (incluyendo multi-index)
    if data.empty:
        return pd.DataFrame()

    if 'Adj Close' in data.columns:
        df = data['Adj Close'].to_frame() if isinstance(data['Adj Close'], pd.Series) else data['Adj Close']
    elif isinstance(data.columns, pd.MultiIndex) and 'Adj Close' in data.columns.get_level_values(1):
        df = data['Adj Close']
    elif 'Close' in data.columns:
        df = data['Close'].to_frame() if isinstance(data['Close'], pd.Series) else data['Close']
    else:
        df = pd.DataFrame()
        
    # Asegurar que el nombre de las columnas sean solo los tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    
    # Si solo hay un ticker, asegurar que la columna tenga el nombre del ticker
    if len(tickers) == 1 and df.shape[1] == 1 and df.columns[0] != tickers[0]:
        df.columns = [tickers[0]]
        
    df.index = pd.to_datetime(df.index).date
    return df.sort_index().dropna(how='all')

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
    # Rellenar y luego calcular retornos para evitar problemas
    lret = log_returns(prices_df.ffill().dropna()).dropna() 
    out = {}
    for col in lret.columns:
        lr = lret[col].dropna()
        if lr.empty: continue
        
        # Último retorno diario (simplificación para el card de ejemplo)
        daily_ret = prices_df[col].iloc[-1] / prices_df[col].iloc[-2] - 1 if prices_df[col].shape[0] >= 2 else 0
        
        out[col] = {
            "Daily Return": daily_ret,
            "Annualized Vol": annualized_vol(lr),
            "Sharpe": sharpe_ratio(lr),
            "Cumulative Return": np.exp(lr.sum()) - 1,
            "Max Drawdown": max_drawdown(prices_df[col].dropna())
        }
    df = pd.DataFrame(out).T
    # Quitar decimales innecesarios de los índices antes de mostrar
    df.index.name = "Asset" 
    return df.round(6) 

# -------------------------
# PLOTLY THEME (Optimizado con mejor uso de colores)
# -------------------------
def themed_chart(df, title, colors=LINE_COLORS):
    fig = go.Figure()
    # Asignación de colores rotativos
    for i, col in enumerate(df.columns):
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df[col], 
            mode='lines', 
            name=col, 
            line=dict(width=2, color=colors[i % len(colors)])))
        
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>', # Título en negrita
            font=dict(color=BLUE, size=18, family='Inter')),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=BLUE, family='Inter'),
        # Leyenda en la parte superior central para ahorrar espacio vertical
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(color=BLUE)
        ),
        xaxis=dict(color=BLUE, gridcolor='#ECEFF3', showgrid=True),
        yaxis=dict(color=BLUE, gridcolor='#ECEFF3', zeroline=True, zerolinecolor='#ECEFF3'),
        margin=dict(l=40, r=20, t=60, b=80), # Margen inferior aumentado para la leyenda
        hovermode="x unified" # Mejor experiencia de usuario al pasar el ratón
    )
    return fig

# -------------------------
# UI: NAVBAR (Mantenido)
# -------------------------
def render_navbar(active="Home"):
    nav_html = f"""
    <div class="topbar">
      <div class="brand">
        <div class="logo">P</div>
        <div style="display:flex;flex-direction:column;">
          <div style="font-weight:800;color:{BLUE};font-size:18px;">Phrono</div>
          <div style="font-size:12px;color:#677489;font-weight:400;">Intelligence-driven capital</div>
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
# UI: CARDS (Optimizado con color de cambio diario)
# -------------------------
def render_kpi_cards(kpis_df):
    # Calculamos métricas de resumen para las cards
    if kpis_df.empty:
        total_assets = 0
        daily_change = 0.0
        fund_sharpe = 0.0
        top_performer = "N/A"
    else:
        total_assets = len(kpis_df)
        # Se puede asumir un simple promedio de cambio diario para el dashboard
        daily_change = kpis_df['Daily Return'].mean()
        # Se puede calcular un Sharpe promedio (simplificado)
        fund_sharpe = kpis_df['Sharpe'].mean()
        # Se busca el ticker con el mayor retorno acumulado
        top_performer = kpis_df['Cumulative Return'].idxmax()
        
    change_class = 'positive' if daily_change >= 0 else 'negative'
    
    # Formato de los valores para las cards
    daily_change_str = f"{daily_change * 100:.2f}%"
    fund_sharpe_str = f"{fund_sharpe:.2f}"
    
    col1, col2, col3, col4 = st.columns([1.2, 1.0, 1.0, 1.2])
    
    with col1:
        st.markdown(f"<div class='card'><div class='card-title'>Total Assets</div><div class='card-value'>{total_assets}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><div class='card-title'>Daily Change (Avg)</div><div class='card-value'><span class='{change_class}'>{daily_change_str}</span></div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><div class='card-title'>Fund Sharpe (Avg)</div><div class='card-value'>{fund_sharpe_str}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card'><div class='card-title'>Top Performer (Total Return)</div><div class='card-value'>{top_performer}</div></div>", unsafe_allow_html=True)

# -------------------------
# MAIN APP
# -------------------------
def main():
    set_custom_theme()
    render_navbar(active="Home")

    # --- Sidebar controls ---
    st.sidebar.header("Phrono Controls")
    st.sidebar.markdown("#### **Universe Selection**")
    default_assets = ["CL=F", "NG=F", "GC=F", "SI=F", "HG=F", "ZC=F", "ZS=F", "KC=F", "EWW", "ILF"]
    # Se aumenta el número de valores por defecto para evitar un gráfico vacío si se usan menos.
    assets = st.sidebar.multiselect("Assets to monitor", options=default_assets, default=default_assets[:6])
    period = st.sidebar.selectbox("History length", options=["1y", "2y", "3y", "5y", "10y", "max"], index=2)
    # Se añade un input para el benchmark que puede ser relevante para el usuario
    st.sidebar.markdown("#### **Benchmark Context**")
    default_benchmark = ["^GSPC"]
    bench_sel_sidebar = st.sidebar.multiselect("Primary Benchmarks", options=["^GSPC", "^IXIC", "^DJI", "^MXX", "GC=F"], default=default_benchmark)
    
    # El botón de refresco ahora es un elemento `st.form` para un mejor manejo del estado de la sidebar
    with st.sidebar.form("control_form"):
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Refresh Data")

    # --- Data Fetching Logic ---
    # La lógica de refresco se ejecuta si se envía el formulario o si no hay datos.
    if submitted or st.session_state['prices'].empty:
        if assets:
            try:
                # Combinar assets y benchmarks para la carga inicial
                all_tickers = list(set(assets + bench_sel_sidebar))
                prices = fetch_prices(all_tickers, period=period)
                st.session_state['prices'] = prices
            except Exception as e:
                st.error(f"Error fetching prices: {e}. Check ticker symbols or connection.")
                return
        else:
            st.warning("Please select at least one asset to monitor.")
            st.session_state['prices'] = pd.DataFrame()
            return

    prices = st.session_state['prices']
    
    # Filtrar solo los precios del portfolio y benchmarks para su uso posterior
    portfolio_prices = prices[[c for c in assets if c in prices.columns]]
    benchmark_prices = prices[[c for c in bench_sel_sidebar if c in prices.columns]]

    if portfolio_prices.empty:
        st.warning("No data found for selected assets. Try different selection or extend history.")
        return
    
    # --- KPI Calculations ---
    kpis_df = compute_kpis(portfolio_prices)
    
    # --- Top Metrics Area (Cards) ---
    render_kpi_cards(kpis_df)
    st.markdown("---")

    # --- Portfolio Monitor ---
    st.markdown("<a name='portfolio'></a>")
    st.markdown("## Portfolio Monitor")
    
    # Dividir el monitor en gráfico + KPIs en una sola fila
    left, right = st.columns([3, 1.5])
    
    with left:
        # Portfolio (Base 100)
        df_base = base100(portfolio_prices.ffill()).dropna()
        fig_port = themed_chart(df_base, f"Portfolio Performance (Base 100) - {period}")
        st.plotly_chart(fig_port, use_container_width=True, config={'displayModeBar': False})
        
    with right:
        # KPIs
        st.markdown("### Key Performance Indicators (KPIs)")
        # Solo mostrar las columnas más relevantes, con formato más limpio
        kpis_display = kpis_df[['Cumulative Return', 'Annualized Vol', 'Sharpe', 'Max Drawdown']]
        # Mapeo de nombres de columnas para una mejor presentación en el dataframe
        kpis_display.columns = ["Total Return", "Ann. Vol.", "Sharpe Ratio", "Max DD"]
        st.dataframe(kpis_display.style.format({
            "Total Return": "{:.2%}",
            "Ann. Vol.": "{:.2%}",
            "Sharpe Ratio": "{:.2f}",
            "Max DD": "{:.2%}"
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', LIGHT_GREY)]},
            {'selector': 'td', 'props': [('font-size', '12px')]}
        ]), use_container_width=True)

    # Gráfico de retornos logarítmicos
    st.markdown("### Daily Log Returns (Cumulative)")
    # Se usa Plotly para una consistencia de diseño
    df_lret_cum = log_returns(portfolio_prices.ffill()).cumsum().apply(np.exp).subtract(1).fillna(0)
    fig_lret = themed_chart(df_lret_cum, "") # Título vacío ya que está en el markdown
    st.plotly_chart(fig_lret, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")
    
    # --- Benchmarks & Context ---
    st.markdown("<a name='bench'></a>")
    st.markdown("## Benchmarks & Context")
    
    if not benchmark_prices.empty:
        fig_bench = themed_chart(base100(benchmark_prices.ffill()).dropna(), "Benchmark Performance (Base 100)")
        st.plotly_chart(fig_bench, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No benchmark data available. Use the sidebar to select primary benchmarks.")

    st.markdown("---")
    
    # --- Research & Signals ---
    st.markdown("<a name='research'></a>")
    st.markdown("## Research & Signals (Preview)")
    st.write("SARIMA and GARCH modules will be integrated here, providing volatility forecasts and time-series analysis charts.")
    st.markdown("<div style='color:#677489;font-size:13px; margin-top:15px;'>Phrono Lab — iterative build. Next up: Model backtesting, Factor exposure, and Predictive signals display.</div>", unsafe_allow_html=True)

    st.markdown("---")
    # --- Footer ---
    st.markdown(f"<div style='text-align:right;color:{GOLD};font-weight:600;'>Phrono Lab © {datetime.now().year}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
