# pages/8_Cloudburst_Risk.py

import streamlit as st
from utils import render_top_nav, current_user_email, get_weather
from style import apply_theme
apply_theme(title="⛈️ Cloudburst Risk — GeoShield", hide_sidebar=True)


# ✅ Must be first Streamlit command
st.set_page_config(page_title="⛈️ Cloudburst Risk — GeoShield", layout="wide")

# 🧭 Top Navigation
render_top_nav("Cloudburst Risk")



# 🔒 Auth Check
email = current_user_email()
if not email:
    st.warning("⚠️ Please log in to access this feature.")
    st.stop()

# 🧪 UI Header
st.title("⛈️ Cloudburst Risk Assessment")
st.markdown("Evaluate cloudburst potential manually or by fetching live weather data.")

# 👉 Manual Input Section
st.subheader("🖐️ Manual Assessment")
intensity = st.number_input("Rainfall intensity (mm/h)", min_value=0, max_value=200, value=0)
threshold_high = 75
threshold_moderate = 50

if st.button("🔍 Assess Manual Risk"):
    if intensity >= threshold_high:
        st.error("🚨 High Risk of Cloudburst based on rainfall rate.")
    elif intensity >= threshold_moderate:
        st.warning("⚠️ Moderate Risk based on rainfall rate.")
    else:
        st.success("✅ Low Risk based on rainfall rate.")

# 🌦️ Live Weather-Based Risk Section
st.subheader("📡 Predict via Weather API")
city = st.text_input("📍 Enter City for Weather Check", "Mysuru")

if st.button("📡 Predict Cloudburst Risk"):
    with st.spinner("Fetching weather data..."):
        weather = get_weather(city)

    if not isinstance(weather, dict) or "error" in weather:
        st.error("❌ Failed to fetch weather data.")
    else:
        rain = weather.get("rain", 0)
        humidity = weather.get("humidity", 0)
        condition = weather.get("condition", "").lower()

        # 📊 Rule-based risk score
        is_high_rainfall = rain >= 50
        is_humid = humidity >= 85
        is_thunderstorm = "thunder" in condition or "storm" in condition

        risk_score = sum([
            40 if is_high_rainfall else 0,
            30 if is_humid else 0,
            30 if is_thunderstorm else 0
        ])

        # 🎯 Display metrics
        st.metric("🌧️ Rainfall (mm/h)", f"{rain}")
        st.metric("💧 Humidity (%)", f"{humidity}")
        st.metric("🌩️ Condition", condition.title())
        st.metric("⚠️ Cloudburst Risk Score", f"{risk_score} / 100")

        if risk_score >= 70:
            st.error("🚨 High cloudburst risk. Avoid outdoor activity.")
        elif risk_score >= 40:
            st.warning("⚠️ Moderate risk. Monitor updates.")
        else:
            st.success("✅ Low cloudburst risk.")

st.caption("Risk scores are based on rainfall intensity, humidity, and thunderstorm presence.")
if st.button("🔙 Back to Home"):
    st.switch_page("pages/3_Overview.py")
