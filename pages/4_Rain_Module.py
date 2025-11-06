# pages/4_Rain_Module.py

import streamlit as st
import pandas as pd
import altair as alt
from utils import render_top_nav, current_user_email
from config import get_rainfall_trend
from style import apply_theme
apply_theme(title="🌧️ Rain Module — GeoShield", hide_sidebar=True)


st.set_page_config(page_title="🌧️ Rain Module — GeoShield", layout="wide")


render_top_nav("Rain Module")

# 🔒 Require Login
email = current_user_email()
if not email:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()

st.markdown("## 🌧️ Rainfall Trends (Past + Forecast)")

city = st.text_input("Enter City", "Chennai")

if st.button("📊 Show Rainfall Overview"):
    with st.spinner("Fetching data..."):
        trend = get_rainfall_trend(city)

    if isinstance(trend, list) and trend:
        df = pd.DataFrame(trend)

        # Rainfall chart
        chart = alt.Chart(df).mark_line(point=True).encode(
            x="date:T",
            y="rainfall_mm:Q",
            tooltip=["date", "rainfall_mm"]
        ).properties(
            width=800,
            height=400,
            title=f"🌧️ Rainfall Pattern for {city}"
        )
        st.altair_chart(chart, use_container_width="stretch")
        st.success("✅ Rainfall data loaded successfully!")

        # 📊 Rainfall Insight
        total_days = len(df)
        total_rainfall = df["rainfall_mm"].sum()
        max_rain = df["rainfall_mm"].max()
        max_day = df.loc[df["rainfall_mm"].idxmax(), "date"]
        avg_rain = df["rainfall_mm"].mean()

        insight = f"""
        💡 **Rainfall Summary for {city}:**

        - 📅 Data span: **{total_days} days**
        - 🌧️ Total rainfall: **{total_rainfall:.2f} mm**
        - 📈 Heaviest rainfall: **{max_rain:.2f} mm** on **{max_day}**
        - 📊 Average daily rainfall: **{avg_rain:.2f} mm**

        { "⚠️ Be alert! Heavy rain is expected." if max_rain > 30 else "✅ Conditions look moderate for now." }
        """
        st.markdown("### 🧠 Rainfall Insight")
        st.info(insight)

    else:
        st.error(trend.get("error", "Could not load rainfall data."))

# Navigation
if st.button("🔙 Back to Overview"):
    st.switch_page("pages/3_Overview.py")
