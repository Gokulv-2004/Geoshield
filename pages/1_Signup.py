# 2_Signup.py

import streamlit as st
from config import get_supabase
from utils import render_top_nav
from style import apply_theme
apply_theme(title="📝 Signup — GeoShield", hide_sidebar=True)

# st.set_page_config(page_title="📝 Signup — GeoShield", layout="centered")


# ---- Top Nav ----
render_top_nav("Signup")

# ---- Page Title ----
st.title("📝 Create Your GeoShield Account")
st.caption("Secure your environment with live flood and weather risk prediction.")

# ---- Supabase Connection ----
supabase = get_supabase()
if supabase is None:
    st.error("❌ Supabase is not configured. Please check your environment settings.")
    st.stop()

# ---- Signup Form ----
with st.form("signup_form"):
    email = st.text_input("📧 Email Address", placeholder="you@example.com")
    password = st.text_input("🔐 Password", type="password", placeholder="Enter a strong password")
    submit = st.form_submit_button("🚀 Sign Up")

    if submit:
        if not email or not password:
            st.warning("⚠️ Please fill out all fields.")
        else:
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("✅ Account created! You can now log in.")
                st.page_link("pages/2_Login.py", label="🔑 Go to Login", icon="🔁")
            except Exception as e:
                st.error(f"❌ Error during signup: {e}")

# ---- Back Button ----