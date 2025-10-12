import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------
# ✅ 1. PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="Phrono Dashboard v2",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# ✅ 2. CUSTOM STYLES (Limpio & Profesional)
# ---------------------------
def load_css():
    st.markdown("""
    <style>

    /* Global */
    body, .stApp {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        font-family: 'Inter', sans-serif;
    }

    /* Navbar */
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 24px;
        background-color: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
    }
    .brand {
        font-size: 26px;
        font-weight: 700;
        color: #0A2239;
    }
    .brand span {
        color: #D4A017;
    }
    .nav-links a {
        margin-left: 20px;
        font-size: 15px;
        color: #0A2239;
        text-decoration: none;
        font-weight: 500;
    }
    .nav-links a:hover {
        color: #D4A017;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F7F9FC !important;
        padding: 20px;
        border-right: 1px solid #E5E7EB;
    }
    [data-testid="stSidebar"] h2, h3, h4 {
        color: #0A2239 !important;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #0A2239;
        font-weight: 700;
    }

    /* Cards */
    .metric-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 18px 22px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-card h4 {
        font-size: 16px;
        margin-bottom: 8px;
        color: #0A2239;
    }
    .metric-card span {
        font-size: 22px;
        font-weight: 600;
        color: #D4A017;
    }

    /* Footer */
    .footer {
        text-align: right;
        margin-top: 50px;
        font-size: 13px;
        color: #555;
    }

    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# ✅ 3. NAVBAR
# ---------------------------
def navbar():
    st.markdown("""
    <div class="topbar">
        <div class="brand">Phrono <span>Lab</span></div>
        <div class="nav-links">
            <a href="#overview">Overview</a>
            <a href="#portfolio">Portfolio</a>
            <a href="#benchmarks">Benchmarks</a>
            <a href="#signals">Signals</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# ✅ 4. PLACEHOLDER DATA
# ---------------------------
def get_mock_data():
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today(), periods=30)
    df = pd.DataFrame({
        'Asset_A': np.cumsum(np.random.randn(30)) + 100,
        'Asset_B': np.cumsum(np.random.randn(30)) + 120,
    }, index=dates)
    return df

# ---------------------------
# ✅ 5. MAIN APP
# ---------------------------
def main():
    load_css()
    navbar()

    st.sidebar.title("Phrono Controls")
    assets = st.sidebar.multiselect(
        "Universe (select assets):",
        ["Asset_A", "Asset_B"],
        default=["Asset_A", "Asset_B"]
    )
    st.sidebar.write(f"Selected: {assets}")
    st.sidebar.write("More filters soon...")

    st.markdown("## 🟦 Overview", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Total Assets</h4>
            <span>10</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Daily Change</h4>
            <span>+0.8%</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Sharpe (est.)</h4>
            <span>0.92</span>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>Top Performer</h4>
            <span>GC=F</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("## 📊 Portfolio Monitor", unsafe_allow_html=True)
    df = get_mock_data()
    st.dataframe(df.tail(), use_container_width=True)

    st.markdown("## 📈 Benchmarks & Context", unsafe_allow_html=True)
    st.write("Soon: index data + charts here.")

    st.markdown("## 🔍 Research & Signals", unsafe_allow_html=True)
    st.write("Placeholder for SARIMA/GARCH/Parrondo modules.")

    st.markdown(
        "<div class='footer'>Phrono © 2025</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
