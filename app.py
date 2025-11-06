
import streamlit as st
from style import apply_theme
apply_theme(title="🏠 Home — GeoShield", hide_sidebar=True)

# ==== Page Config ====
st.set_page_config(
    page_title=" GeoShield — Smart Disaster Prediction",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==== Custom Theme Styling ====


# ==== Hero Section ====
st.markdown("""
    <div style="padding:32px 24px;border-radius:20px;
                background:linear-gradient(135deg,#0f172a,#1e3a8a);
                color:#e6eef7;border:1px solid #334155;
                margin-bottom:32px;text-align:center;">
      <h1 style="font-size:36px;margin-bottom:8px;">🌍 GeoShield</h1>
      <p style="font-size:18px;margin:0;">Smart Disaster Prediction & Alert System</p>
      <p style="font-size:14px;opacity:0.8;">Empowering communities with real-time weather intelligence</p>
    </div>
""", unsafe_allow_html=True)

# ==== Call-to-Action Buttons (Signup + Login) ====
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.page_link("pages/1_Signup.py", label="📝 Signup", use_container_width=True)
with col2:
    st.page_link("pages/2_Login.py", label="🔐 Login", use_container_width=True)

# ==== Features Overview ====
st.markdown("""
    <br><br><hr style='opacity:0.2;'><br>
    <div style="text-align:center;font-size:15px;line-height:1.6;opacity:0.95;">
        <b>About GeoShield</b><br>
        GeoShield is a next-gen disaster forecasting and alerting platform that combines real-time weather data,
        smart risk modeling, and intuitive visualizations to keep you informed and safe.
    </div>
    <br>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                gap:20px;margin-top:16px;font-size:14px;opacity:0.9;">
        <div style="padding:12px;border:1px solid #334155;border-radius:12px;background:#EBDCC7;">
            📡 <b>Live Weather Layers</b><br>Rainfall, Wind & Humidity overlays powered by OpenWeatherMap.
        </div>
        <div style="padding:12px;border:1px solid #334155;border-radius:12px;background:#EBDCC7;">
            🧠 <b>Fuzzy Risk Engine</b><br>AI-based flood & landslide prediction using fuzzy logic.
        </div>
        <div style="padding:12px;border:1px solid #334155;border-radius:12px;background:#EBDCC7;">
            🚨 <b>Instant Alerts</b><br>High-risk zones trigger real-time emergency warnings.
        </div>
        <div style="padding:12px;border:1px solid #334155;border-radius:12px;background:#EBDCC7;">
            📊 <b>Personalized Dashboards</b><br>Custom risk insights & weather history per user.
        </div>
    </div>
    <br><br>
    <div style="text-align:center;opacity:0.6;font-size:13px;">
        © 2025 GeoShield • Built with 💙 using Streamlit & Supabase
    </div>
""", unsafe_allow_html=True)
