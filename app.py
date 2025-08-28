import streamlit as st
from config import supabase

st.set_page_config(page_title="GeoShield", layout="wide")

st.title("🌍 GeoShield - Smart Disaster Prediction & Alert System")

menu = ["Home", "Signup", "Login", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    st.subheader("Welcome to GeoShield 🚨")
    st.write("A smart system for predicting floods & landslides, sending early alerts to save lives.")

elif choice == "Signup":
    st.subheader("Create an Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.success("✅ Account created! Please login.")
        except Exception as e:
            st.error(f"Error: {e}")

elif choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if user and user.user:
                st.success("✅ Logged in successfully!")
                st.session_state["user"] = user
            else:
                st.error("❌ Invalid credentials")
        except Exception as e:
            st.error(f"Error: {e}")

elif choice == "Dashboard":
    if "user" in st.session_state:
        st.subheader(f"📊 Dashboard - Welcome {st.session_state['user'].user.email}")

        # --- Dummy Rainfall Data ---
        st.markdown("### 🌧️ Rainfall Trend (Last 7 Days)")
        import pandas as pd
        import altair as alt

        rainfall_data = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Rainfall (mm)": [10, 20, 15, 30, 25, 40, 35]
        })

        chart = alt.Chart(rainfall_data).mark_line(point=True).encode(
            x="Day",
            y="Rainfall (mm)"
        ).properties(width=600, height=300)

        st.altair_chart(chart)

        # --- Dummy Dam Level ---
        st.markdown("### 💧 Dam Water Level")
        dam_level = 70  # percentage
        st.progress(dam_level / 100)
        st.write(f"Current Dam Level: {dam_level}%")

        # --- Dummy Landslide Risk ---
        st.markdown("### 🏔️ Landslide Risk")
        risk_level = "Medium"
        st.warning(f"⚠️ Risk Level: {risk_level}")

    else:
        st.warning("⚠️ Please login to access the dashboard.")
