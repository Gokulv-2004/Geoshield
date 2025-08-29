# app.py
import streamlit as st
from typing import Optional
import pandas as pd
import altair as alt
from config import supabase

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

# Keep URL/page state in sync
if choice != st.session_state["page"]:
    st.session_state["page"] = choice

st.title("🌍 GeoShield - Smart Disaster Prediction & Alert System")

page = st.session_state["page"]

# ---------- HOME ----------
if page == "Home":
    st.subheader("Welcome to GeoShield 🚨")
    st.write(
        "A smart system for predicting floods & landslides, using real weather data (OpenWeather Free API)."
    )

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

        # --- Weather + Real Risk (from utils) ---
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

                # ✅ Use real prediction functions
                flood_risk = flood_prediction(data["rain"], data["humidity"])
                landslide_risk = landslide_prediction(data["rain"], data["humidity"])

                st.info(f"🌊 Flood Risk: **{flood_risk}**")
                st.warning(f"🏔️ Landslide Risk: **{landslide_risk}**")

                # ✅ Save into Supabase history
                save_weather_history(email, city, data, flood_risk, landslide_risk)
                st.success("✅ Weather query saved to history")

            else:
                st.error(data.get("error", "Unknown error fetching weather."))

        # --- Rainfall Trend ---
        import pandas as pd
        import altair as alt
        if st.button("Show Rainfall Trend (7 days)"):
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
