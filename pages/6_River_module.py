import streamlit as st
from style import apply_theme
from utils import render_top_nav, current_user_email
from river_data import list_rivers, get_river_status_by_name, get_river_level_status
from service.openweather import hourly_rain_series, sum_hourly_rain
from service.alerts import notify_on_risk   # ✅ NEW: auto-SMS helper
import pandas as pd
import altair as alt

# ------------------------------
# PAGE CONFIG
# ------------------------------
apply_theme(title="🌊 River Module — GeoShield", hide_sidebar=True)
st.set_page_config(page_title="🌊 River Module — GeoShield", layout="wide")
render_top_nav("River Module")

# ------------------------------
# AUTH CHECK
# ------------------------------
if not current_user_email():
    st.warning("⚠️ Please log in to access this module.")
    st.stop()

st.markdown("## 🌊 River Flood Risk Monitor (Real-Time)")
st.caption("Powered by OpenWeather hourly forecast + GeoShield logic.")

mode = st.radio("Search Method:", ["River Name", "State / District"], horizontal=True)

# ✅ UTILITY
def get_rainfall_by_coords(lat: float, lon: float, hours: int = 12) -> float:
    return round(sum_hourly_rain(lat, lon, hours=hours), 2)

# ======================================================
# ✅ MODE 1 — RIVER NAME
# ======================================================
if mode == "River Name":

    river = st.selectbox("Select River", list_rivers())
    col1, col2 = st.columns([1, 1])
    with col1:
        show_map = st.checkbox("Show Map", value=True)
    with col2:
        hours = st.slider("Rainfall Window (hours)", 6, 24, 12)

    if st.button("🚰 Analyze Flood Risk", type="primary"):
        status = get_river_status_by_name(river)
        if "error" in status:
            st.error(status["error"])
            st.stop()

        lat, lon = status["lat"], status["lon"]
        rainfall_mm = sum_hourly_rain(lat, lon, hours=hours)

        # GeoShield risk logic
        level = ("High" if rainfall_mm >= 35 else "Moderate" if rainfall_mm >= 15 else "Low")

        # ✅ NEW: Auto-SMS notify (uses ALERT_PHONE/MIN_ALERT_LEVEL in secrets)
        notify_on_risk(
            feature="River",
            risk=level,
            ctx={"river": river, "reach": status.get("reach"), "hours": hours, "rain": float(rainfall_mm)},
        )

        st.session_state["river_result"] = {
            **status,
            "rainfall_mm": round(rainfall_mm, 2),
            "simulated_river_level": level
        }

    # ✅ Persist result (no flash disappear)
    if st.session_state.get("river_result"):
        s = st.session_state["river_result"]
        lat, lon = s["lat"], s["lon"]
        rainfall_mm = s["rainfall_mm"]
        level = s["simulated_river_level"]

        st.markdown(f"""
        ### 🏞️ {s['river']} — {s['reach']}
        - 🌐 Coordinates: `{lat:.3f}, {lon:.3f}`
        - 🌧️ Rainfall next {hours}h: **{rainfall_mm} mm**
        - 🚨 Flood Risk: **{level}**
        - 🕒 Updated: `{s['timestamp']}`
        """)

        if level == "High":
            st.error("🚨 HIGH FLOOD RISK — Avoid low-lying river banks.")
        elif level == "Moderate":
            st.warning("⚠️ Moderate rise likely — monitor alerts.")
        else:
            st.success("✅ Safe for now.")

        # ✅ Hourly Rain Chart
        series = hourly_rain_series(lat, lon, hours=hours)
        if series:
            df = pd.DataFrame(series)
            df["time"] = pd.to_datetime(df["time"], unit="s")

            st.markdown("#### 📊 Hourly Rainfall Trend")
            chart = (
                alt.Chart(df)
                .mark_bar(color="#4CA3FF")
                .encode(
                    x=alt.X("time:T", title="Time"),
                    y=alt.Y("rain:Q", title="Rain (mm/hr)"),
                    tooltip=["time:T", "rain:Q"]
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width="stretch")

        # ✅ River Map
        if st.checkbox("Show Map", value=show_map, key="map_toggle"):
            try:
                import folium
                from streamlit_folium import st_folium

                color = {"Low": "green", "Moderate": "orange", "High": "red"}[level]
                m = folium.Map(location=[lat, lon], zoom_start=9, tiles="CartoDB dark_matter")

                folium.Circle(
                    location=[lat, lon],
                    radius=20000,
                    popup=f"{s['river']} | {level}",
                    color=color,
                    fill=True,
                    fill_opacity=0.6
                ).add_to(m)

                st_folium(m, width=750, height=420)

            except Exception as e:
                st.warning(f"Map failed: {e}")

# ======================================================
# ✅ MODE 2 — STATE / DISTRICT
# ======================================================
else:
    city = st.text_input("State/District (e.g., Bagalkot, Raichur, Mandya)")
    if st.button("🌧️ Get Rainfall & Risk", type="primary"):
        if not city.strip():
            st.error("Enter a valid location.")
            st.stop()

        st.session_state["state_result"] = get_river_level_status(city)

        # ✅ NEW: Auto-SMS for region fallback too
        _s = st.session_state["state_result"]
        notify_on_risk(
            feature="Region",
            risk=_s.get("simulated_river_level", "Low"),
            ctx={"city": _s.get("city"), "rain": float(_s.get("rainfall_mm", 0.0))},
        )

    if st.session_state.get("state_result"):
        s = st.session_state["state_result"]
        st.markdown(f"""
        ### 📍 {s['city']}
        - 🌧️ Last 12h Rainfall: **{s['rainfall_mm']} mm**
        - 🚨 River Rise Risk: **{s['simulated_river_level']}**
        - 🕒 Updated: `{s['timestamp']}`
        """)

        bar = (
            alt.Chart(pd.DataFrame({"Rain (mm)": [s["rainfall_mm"]], "Time": ["Last 12h"]}))
            .mark_bar(color="#1E90FF")
            .encode(
                x="Time:N",
                y="Rain (mm):Q",
                tooltip=["Rain (mm):Q"]
            )
            .properties(height=280)
        )
        st.altair_chart(bar, use_container_width="stretch")

# ------------------------------
# BACK BUTTON
# ------------------------------
if st.button("🔙 Back to Home"):
    st.switch_page("pages/3_Overview.py")
