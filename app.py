import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- THEME SETUP: Custom CSS for Dark Blue and Gold ---
def set_custom_theme():
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #0A2239;
            color: #F5F6FA;
        }
        .st-bb, .st-cq, .st-cq *, .stMarkdown, .stText {
            color: #F5F6FA !important;
        }
        .stSidebar, .css-1d391kg {
            background-color: #0A2239 !important;
            color: #F5F6FA !important;
        }
        .stHeader {
            background-color: #0A2239 !important;
        }
        .css-1y4p8pa, .css-1v3fvcr, .css-10trblm {
            color: #F5F6FA !important;
        }
        .stButton > button {
            background-color: #D4A017 !important;
            color: #0A2239 !important;
            border: none;
        }
        .stDataFrame th, .stDataFrame td {
            background-color: #11294d !important;
            color: #F5F6FA !important;
        }
        .css-1offfwp, .css-1fcdlhk, .css-1hynsf2 {
            color: #D4A017 !important;
        }
        .highlight {
            color: #D4A017 !important;
        }
        </style>
        """, unsafe_allow_html=True
    )

# --- Placeholder Data ---
def get_placeholder_portfolio_data():
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today(), periods=30)
    data = {
        'Asset_A': np.cumsum(np.random.randn(30)) + 100,
        'Asset_B': np.cumsum(np.random.randn(30)) + 120,
    }
    return pd.DataFrame(data, index=dates)

def get_placeholder_benchmark_data():
    np.random.seed(24)
    dates = pd.date_range(end=datetime.today(), periods=30)
    data = {
        'SP500': np.cumsum(np.random.randn(30)) + 150,
        'NASDAQ': np.cumsum(np.random.randn(30)) + 200,
    }
    return pd.DataFrame(data, index=dates)

# --- Modular Data Fetching (Stub for yfinance) ---
def fetch_portfolio_data(assets):
    df = get_placeholder_portfolio_data()
    return df[assets] if assets else df

def fetch_benchmark_data(benchmarks):
    df = get_placeholder_benchmark_data()
    return df[benchmarks] if benchmarks else df

# --- Chart Styling Helper ---
def themed_chart(df, title):
    import plotly.graph_objs as go
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col))
    fig.update_layout(
        title=title,
        plot_bgcolor='#0A2239',
        paper_bgcolor='#0A2239',
        font=dict(color='#F5F6FA'),
        legend=dict(font=dict(color='#F5F6FA')),
        xaxis=dict(color='#F5F6FA', gridcolor='#25375a'),
        yaxis=dict(color='#F5F6FA', gridcolor='#25375a'),
        title_font=dict(color='#D4A017')
    )
    return fig

# --- MAIN APP ---
def main():
    set_custom_theme()
    st.set_page_config(
        page_title="Phrono: Financial Intelligence Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(
        "<h1 style='color:#D4A017;font-weight:700;margin-bottom:0;'>Phrono</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h3 style='color:#F5F6FA;font-weight:400;margin-top:0;'>Intelligence-driven capital for <span class='highlight'>mispriced assets</span>.</h3>",
        unsafe_allow_html=True
    )

    st.sidebar.title("Phrono Navigation")
    section = st.sidebar.radio("Go to", ("Portfolio Monitor", "Benchmark Tracker"))

    if section == "Portfolio Monitor":
        st.subheader("Portfolio Monitor")
        st.write(
            "<span style='color:#D4A017;'>Monitor the performance of your selected assets over time.</span>",
            unsafe_allow_html=True
        )
        assets = st.multiselect(
            "Select portfolio assets",
            options=["Asset_A", "Asset_B"],
            default=["Asset_A", "Asset_B"]
        )
        df = fetch_portfolio_data(assets)
        st.plotly_chart(themed_chart(df, "Portfolio Performance"), use_container_width=True)
        st.dataframe(df.tail(5), use_container_width=True)

    elif section == "Benchmark Tracker":
        st.subheader("Benchmark Tracker")
        st.write(
            "<span style='color:#D4A017;'>Track market benchmarks and compare against your portfolio.</span>",
            unsafe_allow_html=True
        )
        benchmarks = st.multiselect(
            "Select benchmarks",
            options=["SP500", "NASDAQ"],
            default=["SP500", "NASDAQ"]
        )
        df = fetch_benchmark_data(benchmarks)
        st.plotly_chart(themed_chart(df, "Benchmark Performance"), use_container_width=True)
        st.dataframe(df.tail(5), use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<div style='text-align: right; color: #D4A017;'>Phrono &copy; 2025</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()