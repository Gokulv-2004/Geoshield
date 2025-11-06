# pages/9_History.py  — robust / column-safe
import streamlit as st
import pandas as pd
from config import get_supabase
from utils import render_top_nav, current_user_email, load_history
from style import apply_theme

apply_theme(title="📜 History — GeoShield", hide_sidebar=True)
st.set_page_config(page_title="📜 History — GeoShield", layout="wide")
render_top_nav("History")

st.markdown("## 📜 Local Predictions (CSV)")
local_df = load_history()
if local_df.empty:
    st.info("No local history yet (CSV).")
else:
    st.dataframe(local_df.sort_values("timestamp", ascending=False), width="stretch")
    st.caption("Local CSV columns: timestamp, user, type, station, cap_pct, rain24_mm, inflow_ratio, risk_score, risk_bucket")

st.markdown("---")
st.markdown("## ☁️ Cloud/Account History (Supabase)")

# ---- Require Login ----
email = current_user_email()
if not email:
    st.warning("⚠️ Please login to view your account history.")
    st.stop()

# ---- Supabase ----
supabase = get_supabase()
if not supabase:
    st.error("❌ Supabase not connected. Check SUPABASE_URL / SUPABASE_KEY.")
    st.stop()

# ---- Query and render safely ----
try:
    resp = supabase.table("weather_history") \
        .select("*") \
        .eq("user_email", email) \
        .order("created_at", desc=True) \
        .limit(200) \
        .execute()

    data = resp.data or []
    if not data:
        st.info("No cloud history yet. Use Overview / Rain / River / Cloudburst to generate records.")
    else:
        raw = pd.DataFrame(data)

        # Rename map (only those keys that actually exist will be applied)
        rename_map = {
            "created_at": "⏰ Timestamp",
            "city": "🌆 City",
            "temperature": "🌡️ Temp (°C)",
            "humidity": "💧 Humidity (%)",
            "rainfall": "🌧️ Rainfall (mm)",
            "condition": "⛅ Condition",
            "flood_risk": "🌊 Flood Risk",
            "landslide_risk": "🏔️ Landslide Risk",
            "cloudburst_risk": "⛈️ Cloudburst Risk",
            "user_email": "👤 User",
        }
        # keep only keys present, then rename
        present = {k: v for k, v in rename_map.items() if k in raw.columns}
        df = raw.rename(columns=present)

        # Desired display order (will keep only those that truly exist)
        desired = [
            "⏰ Timestamp", "👤 User", "🌆 City",
            "🌡️ Temp (°C)", "💧 Humidity (%)", "🌧️ Rainfall (mm)",
            "⛅ Condition", "🌊 Flood Risk", "🏔️ Landslide Risk", "⛈️ Cloudburst Risk"
        ]
        display_cols = [c for c in desired if c in df.columns]

        # If some desired columns are missing in DB, create empty ones so table looks consistent
        for c in desired:
            if c not in df.columns:
                df[c] = None

        st.dataframe(df[display_cols] if display_cols else df, width="stretch")
        st.success(f"✅ Showing {len(df)} records from Supabase.")

except Exception as e:
    st.error(f"❌ Failed to load history: {e}")
if st.button("🔙 Back to Home"):
    st.switch_page("pages/3_Overview.py")
