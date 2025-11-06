# pages/3_Overview.py

import streamlit as st
from config import WEATHER_API
from utils import get_weather, render_top_nav, current_user_email
from style import apply_theme
apply_theme(title="🧭 Overview — GeoShield", hide_sidebar=True)


# Theme + Layout
st.set_page_config(page_title="🧭 Overview — GeoShield", layout="wide")



render_top_nav("Overview")

# 🔒 Require login
email = current_user_email()
if not email:
    st.warning("⚠️ Please log in to access the overview.")
    st.stop()

# 🔹 Welcome Section
st.markdown(f"### 🧭 Smart Overview — Welcome, `{email}`")
st.write("GeoShield helps you monitor rainfall, reservoir risk, and floods — all in one dashboard.")

# 🌦️ Weather Snapshot
st.subheader("🌦️ Your Local Weather Risk")
city = st.text_input("🏙️ Enter City", "Chennai")
if st.button("📍 Check Weather Now"):
    with st.spinner("🔄 Fetching live weather…"):
        data = get_weather(city)

    if isinstance(data, dict) and "error" not in data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🌡️ Temp", f"{data['temp']} °C")
        col2.metric("💧 Humidity", f"{data['humidity']} %")
        col3.metric("🌧️ Rainfall", f"{data['rain']} mm")
        col4.metric("🌤️ Condition", data['condition'].title())
        st.success("✅ Weather fetched successfully!")
    else:
        st.error(data.get("error", "Unknown error."))

# 📌 Feature Directory
st.subheader("🧭 Explore Key Features")

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/4_Rain_Module.py", label="🌧️ Rain Monitoring", help="Trend + Map + Forecast")
with col2:
    st.page_link("pages/5_Dam_Module.py", label="🏞️ Reservoir Monitor", help="Reservoir + Dam stats (IMD)")
with col3:
    st.page_link("pages/6_River_module.py", label="🌊 River Levels", help="Live river levels from WRIS")

col4, col5 ,col6 = st.columns(3)
with col4:
    st.page_link("pages/7_Fuzzy_Risk.py", label="⚠️ Dam Flood Predictor", help="AI-based risk using fuzzy logic")
with col5:
    st.page_link("pages/9_History.py", label="🕓 History", help="Your past records and predictions")
with col6:
    st.page_link("pages/8_Cloudburst_Risk.py",label="⛈️ Cloudburst Risk", help="Threshold model for cloudburst" )
# 📎 Footer
st.markdown("---")
st.markdown(
    """
    <div style='color:#ffffff;font-size:14px'>
    🔔 <b>GeoShield</b> combines real-time government data and smart AI to assist you in managing climate risks.
    Navigate to modules above and stay informed.
    </div>
    """, unsafe_allow_html=True
)

# 🔙 Back Button

