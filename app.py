import streamlit as st
import os
from typing import Optional
import pandas as pd
import altair as alt
from config import supabase

# Extra imports for map
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="GeoShield", layout="wide")

# ---------- Helpers ----------
def set_page(page: str):
    st.session_state["page"] = page
    st.rerun()

def current_user_email() -> Optional[str]:
    try:
        user = st.session_state.get("user")
        if user and getattr(user, "user", None) and getattr(user.user, "email", None):
            return user.user.email
    except Exception:
        pass
    return None

# ---------- Custom Alert Card ----------
def show_risk_alert(label, risk):
    color = {
        "high": "#ff4d4d",      # red
        "medium": "#ffa500",    # orange
        "low": "#4CAF50"        # green
    }
    risk_level = str(risk).lower()
    bg_color = color.get(risk_level, "#4CAF50")

    st.markdown(
        f"""
        <div style="
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            color: white;
            background-color: {bg_color};
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
        ">
            ⚠️ {label} Risk: {risk.upper()}
        </div>
        """,
        unsafe_allow_html=True
    )

def show_global_alert(flood_risk, landslide_risk):
    if str(flood_risk).lower() == "high" or str(landslide_risk).lower() == "high":
        st.markdown(
            """
            <div style="
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                color: white;
                background-color: #d00000;
                font-weight: bold;
                font-size: 18px;
                text-align: center;
                box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
            ">
                🚨 EMERGENCY ALERT: High Risk Detected! Stay Safe & Follow Precautions 🚨
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------- Weather Map ----------
def show_weather_map():
    india_center = [22.9734, 78.6569]
    m = folium.Map(location=india_center, zoom_start=5)

    API_KEY = "YOUR_OPENWEATHER_API_KEY"

    # 🌧 Rainfall
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
        attr="OpenWeatherMap", name="Rainfall", overlay=True, control=True
    ).add_to(m)

    # 🌡 Temperature
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/temp_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
        attr="OpenWeatherMap", name="Temperature", overlay=True, control=True
    ).add_to(m)

    # 💧 Humidity
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/humidity_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
        attr="OpenWeatherMap", name="Humidity", overlay=True, control=True
    ).add_to(m)

    # 🌬 Wind
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
        attr="OpenWeatherMap", name="Wind", overlay=True, control=True
    ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=800, height=500)

# ---------- Session defaults ----------
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "city" not in st.session_state:
    st.session_state["city"] = "Chennai"

menu = ["Home", "Signup", "Login", "Dashboard"]

# ---------- Sidebar (compact) ----------
with st.sidebar.expander("📌 Menu", expanded=False):
    choice = st.radio(
        "Navigate",
        menu,
        index=menu.index(st.session_state["page"]),
        key="nav_choice",
    )

if choice != st.session_state["page"]:
    st.session_state["page"] = choice

st.title("🌍 GeoShield - Smart Disaster Prediction & Alert System")

page = st.session_state["page"]


# ---------- HOME ----------
if page == "Home":
    st.subheader("🌍 Welcome to GeoShield 🚨")
    st.markdown("""
    GeoShield is a **smart disaster prediction system** for floods 🌊 & landslides ⛰️.  
    Powered by **real-time weather data** from OpenWeather API.  

    🔎 Explore the live India Weather Dashboard:
    - 🌡️ Thermal-style weather visualization
    - 🌧️ Rainfall overlay showing precipitation intensity
    - 💧 Humidity + 💨 Wind layers for deeper insights
    """)

    # --- Live Weather Snapshot (India Center) ---
    import requests
    API_KEY = os.getenv("WEATHER_API")

    if API_KEY:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=India&appid={API_KEY}&units=metric"
        try:
            res = requests.get(url).json()
            temp = res["main"]["temp"]
            humidity = res["main"]["humidity"]
            wind = res["wind"]["speed"]
            weather_desc = res["weather"][0]["description"].title()

            st.info(f"""
            **🌡️ Temperature:** {temp} °C  
            **💧 Humidity:** {humidity}%  
            **💨 Wind Speed:** {wind} m/s  
            **🌧️ Condition:** {weather_desc}  
            """)
        except Exception as e:
            st.warning("⚠️ Could not fetch live weather data.")
    else:
        st.warning("⚠️ No API key found. Please set `OPENWEATHER_API_KEY` in your environment.")

    # --- Live Interactive Thermal Weather Map ---
    m = folium.Map(location=[22.5, 78.9], zoom_start=5, control_scale=True, tiles="CartoDB dark_matter" ,world_copy_jump=True)

    if API_KEY:
        # Thermal-like Rainfall (primary focus)
        rainfall_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
        temp_url     = f"https://tile.openweathermap.org/map/temp_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
        humidity_url = f"https://tile.openweathermap.org/map/humidity_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
        wind_url     = f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"

        # Add overlays
        folium.TileLayer(rainfall_url, attr="OpenWeatherMap", name="🌧️ Rainfall Intensity", overlay=True , control=True, no_wrap=True).add_to(m)
        folium.TileLayer(temp_url, attr="OpenWeatherMap", name="🌡️ Temperature Heatmap", overlay=True).add_to(m)
        folium.TileLayer(humidity_url, attr="OpenWeatherMap", name="💧 Humidity", overlay=True).add_to(m)
        folium.TileLayer(wind_url, attr="OpenWeatherMap", name="💨 Wind Speed", overlay=True).add_to(m)

        # Layer control (collapsed like legend)
        folium.LayerControl(collapsed=False).add_to(m)

        st.subheader("🛰️ Live Thermal Weather Map (India)")
        st.write("""
        - **Rainfall layer** → darker = heavier rain  
        - **Temperature layer** → warm colors = hotter regions  
        - **Humidity & Wind layers** available for deeper exploration  
        👉 Move/zoom on the map to focus on specific states.
        """)
        st_folium(m, width=750, height=520)
    else:
        st.error("🌐 Cannot render weather map without API key.")

# ---------- SIGNUP ----------
elif page == "Signup":
    st.subheader("Create an Account")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Signup"):
            try:
                _ = supabase.auth.sign_up({"email": email, "password": password})
                st.success("✅ Account created! Please login.")
                set_page("Login")
            except Exception as e:
                st.error(f"Error: {e}")

    with col_b:
        if st.button("Already have an account? Login"):
            set_page("Login")

# ---------- LOGIN ----------
elif page == "Login":
    if "user" in st.session_state and current_user_email():
        set_page("Dashboard")

    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                if user and getattr(user, "user", None):
                    st.success("✅ Logged in successfully!")
                    st.session_state["user"] = user
                    set_page("Dashboard")
                else:
                    st.error("❌ Invalid credentials")
            except Exception as e:
                st.error(f"Error: {e}")

    with c2:
        if st.button("Create new account"):
            set_page("Signup")

# ---------- DASHBOARD ----------
elif page == "Dashboard":
    if "user" in st.session_state and current_user_email():
        email = current_user_email()
        top_left, top_right = st.columns([3, 1])
        with top_left:
            st.subheader(f"📊 Dashboard — Welcome {email}")
        with top_right:
            if st.button("Logout"):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                for k in ["user", "page"]:
                    if k in st.session_state:
                        del st.session_state[k]
                set_page("Home")

        st.divider()

        # --- Weather + Real Risk ---
        from utils import (
            get_weather, flood_prediction, landslide_prediction,
            get_rainfall_trend, save_weather_history
        )

        city = st.text_input("Enter city for weather check", "Chennai")
        if st.button("Get Weather"):
            with st.spinner("Fetching live weather…"):
                data = get_weather(city)

            if isinstance(data, dict) and "error" not in data:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("🌡️ Temperature", f"{data['temp']} °C")
                with m2:
                    st.metric("💧 Humidity", f"{data['humidity']} %")
                with m3:
                    st.metric("🌧️ Rainfall (1h)", f"{data['rain']} mm")
                with m4:
                    st.metric("⛅ Condition", data['condition'])

                flood_risk = flood_prediction(data["rain"], data["humidity"])
                landslide_risk = landslide_prediction(data["rain"], data["humidity"])

                show_global_alert(flood_risk, landslide_risk)
                show_risk_alert("Flood", flood_risk)
                show_risk_alert("Landslide", landslide_risk)

                save_weather_history(email, city, data, flood_risk, landslide_risk)
                st.success("✅ Weather query saved to history")

                # --- Show Rainfall Trend directly (no button repeat) ---
                trend = get_rainfall_trend(city)
                if "error" not in trend:
                    df = pd.DataFrame(trend)
                    chart = alt.Chart(df).mark_line(point=True).encode(
                        x="date",
                        y="rainfall_mm"
                    ).properties(width=600, height=300, title="🌧️ Rainfall Trend (Last 7 Days)")
                    st.altair_chart(chart)
                else:
                    st.error(trend["error"])

            else:
                st.error(data.get("error", "Unknown error fetching weather."))

        # --- 📜 Weather History ---
        st.subheader("📜 Your Weather History")
        try:
            history = supabase.table("weather_history") \
                .select("*") \
                .eq("user_email", email) \
                .order("created_at", desc=True) \
                .limit(10) \
                .execute()
            if history.data:
                df = pd.DataFrame(history.data)
                st.dataframe(df[[
                    "city", "temperature", "humidity",
                    "rainfall", "flood_risk", "landslide_risk", "created_at"
                ]])
            else:
                st.info("No history found yet.")
        except Exception as e:
            st.error(f"Error fetching history: {e}")

    else:
        st.warning("⚠️ Please login to access the dashboard.")
        if st.button("Go to Login"):
            set_page("Login")
