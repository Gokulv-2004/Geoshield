# 1_Home.py
import requests
import streamlit as st
from config import WEATHER_API
from utils import show_weather_map, render_top_nav
from style import apply_theme
apply_theme(title="🏠 Home — GeoShield", hide_sidebar=True)

# st.set_page_config(page_title="🏠 Home — GeoShield", layout="wide")

# ✅ Require login
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access the Home page.")
    st.stop()

render_top_nav("Home")

st.markdown("### 🏠 Home — GeoShield")
st.write("Explore live layers: **rain**, **humidity**, **wind**. Use the quick city search to jump to any city in India.")

# ---- India weather snapshot ----
if WEATHER_API:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=India&appid={WEATHER_API}&units=metric"
        res = requests.get(url, timeout=10).json()
        temp = res.get("main", {}).get("temp", "-")
        hum = res.get("main", {}).get("humidity", "-")
        wind = res.get("wind", {}).get("speed", "-")
        desc = (res.get("weather", [{}])[0].get("description", "-") or "-").title()
        st.info(
            f"**🌡️ Temp:** {temp} °C  \n"
            f"**💧 Humidity:** {hum}%  \n"
            f"**💨 Wind:** {wind} m/s  \n"
            f"**⛅ Condition:** {desc}"
        )
    except Exception:
        st.warning("⚠️ India snapshot unavailable.")
else:
    st.warning("⚠️ Set `WEATHER_API` in .env")

# ---- Weather map ----
show_weather_map()



st.markdown("""
---
⬅️ Use the sidebar to explore GeoShield features.
""")
if st.button("🔙 Back to Overview"):
    st.switch_page("pages/3_Overview.py")
