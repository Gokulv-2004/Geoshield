# pages/7_Fuzzy_Risk.py
import os
import time
import requests
import pandas as pd
import altair as alt
import streamlit as st

from style import apply_theme
from utils import render_top_nav, current_user_email, save_history
from core.fuzzy_risk import mem_cap_pct, mem_rain, mem_flow_ratio, aggregate_rules
from service.openweather import forecast_rain_mm  # robust fallback chain

# -------------------- Page chrome --------------------
st.set_page_config(page_title="⚠️ Fuzzy Risk — GeoShield", layout="wide")
apply_theme(title="⚠️ Fuzzy Risk Predictor", hide_sidebar=True)
render_top_nav("Fuzzy Risk")

# -------------------- Auth guard --------------------
if not current_user_email():
    st.warning("⚠️ Please log in.")
    st.stop()

# ====================================================
# 0) Apply any deferred state BEFORE creating widgets
#    (fixes 'cannot be modified after instantiated')
# ====================================================
for src, dst in [
    ("cap_pct_pending", "cap_pct"),
    ("rain24_pending", "rain24"),
    ("inflow_ratio_pending", "inflow_ratio"),
]:
    if src in st.session_state:
        st.session_state[dst] = st.session_state.pop(src)

if "__notice" in st.session_state:
    st.success(st.session_state.pop("__notice"))

# ====================================================
# 1) Defaults
# ====================================================
st.session_state.setdefault("cap_pct", 60)
st.session_state.setdefault("rain24", 50)
st.session_state.setdefault("inflow_ratio", 0.8)

# ====================================================
# 2) Helpers
# ====================================================
def _resolve_weather_key():
    # Align with service.openweather logic
    try:
        v = st.secrets.get("WEATHER_API")
        if v: return v
        ow = st.secrets.get("openweather", {})
        if isinstance(ow, dict) and ow.get("api_key"):
            return ow["api_key"]
    except Exception:
        pass
    return os.getenv("WEATHER_API") or os.getenv("OPENWEATHER_API_KEY")

def geocode_city(city: str):
    key = _resolve_weather_key()
    if not key or not city.strip():
        return None, None
    try:
        r = requests.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city.strip(), "limit": 1, "appid": key},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

def _compute(cap_pct: float, rain_mm: float, inflow_ratio: float):
    # memberships
    m_cap = mem_cap_pct(cap_pct)
    m_rain = mem_rain(rain_mm)
    m_flow = mem_flow_ratio(inflow_ratio)
    # risk
    score, label, agg = aggregate_rules(m_cap, m_rain, m_flow)
    return score, label, agg, m_cap, m_rain, m_flow

# ====================================================
# 3) SIMPLE MODE (for normal users): fetch rain by city
# ====================================================
st.markdown("## 🧠 Auto Mode — Use Real Rainfall")
c1, c2 = st.columns([2, 1])
with c1:
    city = st.text_input("City / District (e.g., ‘Bengaluru’, ‘Bagalkot’, ‘Mandya’)", "")
with c2:
    hours_city = st.slider("Rainfall window (hours)", 6, 24, 12, key="hours_city")

if st.button("🌧️ Fetch rain & update model", type="primary"):
    if not city.strip():
        st.error("Enter a valid city/district.")
    else:
        lat, lon = geocode_city(city)
        if not (lat and lon):
            st.error(f"Could not geocode ‘{city}’. Try a different spelling.")
        else:
            try:
                r = forecast_rain_mm(lat, lon, hours=hours_city)
                r_int = max(0, min(300, int(round(r))))
                st.session_state["rain24_pending"] = r_int
                st.session_state["__notice"] = (
                    f"Fetched {r:.1f} mm for next {hours_city}h at {city}. "
                    f"Rain slider updated to {r_int}."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Failed to fetch rainfall: {e}")

st.markdown("---")

# ====================================================
# 4) CURRENT MODEL RESULT (cards + charts)
# ====================================================
st.markdown("## 📈 Current Prediction (based on inputs below)")
cap = float(st.session_state["cap_pct"])
rain = float(st.session_state["rain24"])
flow = float(st.session_state["inflow_ratio"])

score, label, agg, m_cap, m_rain, m_flow = _compute(cap, rain, flow)

# Summary cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Capacity Used", f"{cap:.0f}%")
c2.metric("Rain (next 24h)", f"{rain:.0f} mm")
c3.metric("Inflow / Spill", f"{flow:.2f}×")
c4.metric("Risk", f"{label.upper()} ({score:.0f}/100)")

# --- Chart A: Memberships for current inputs (Low/Med/High)
st.markdown("#### 🔎 Membership Strengths (for your inputs)")
mem_rows = []
for what, m in [("Capacity %", m_cap), ("Rain (mm)", m_rain), ("Inflow ratio", m_flow)]:
    for lvl in ("low", "medium", "high"):
        mem_rows.append({"Factor": what, "Level": lvl.title(), "Strength": float(m.get(lvl, 0.0))})

mem_df = pd.DataFrame(mem_rows)
mem_chart = (
    alt.Chart(mem_df)
    .mark_bar()
    .encode(
        x=alt.X("Strength:Q", title="Membership (0–1)"),
        y=alt.Y("Factor:N", title=None),
        color=alt.Color("Level:N"),
        tooltip=["Factor", "Level", alt.Tooltip("Strength:Q", format=".2f")],
    )
    .properties(height=220)
)
st.altair_chart(mem_chart, width="stretch")
st.caption("**What this shows:** For each input, how strongly it belongs to Low/Medium/High fuzzy sets. Example: rain=50mm usually has medium–high membership.")

# --- Chart B: Rule aggregation strengths (Low/Medium/High/Critical)
st.markdown("#### 🧮 Rule Outcome Strengths")
agg_df = pd.DataFrame(
    {"Bucket": ["Low", "Medium", "High", "Critical"],
     "Strength": [float(agg.get("low", 0)), float(agg.get("medium", 0)),
                  float(agg.get("high", 0)), float(agg.get("critical", 0))]}
)
agg_chart = (
    alt.Chart(agg_df)
    .mark_bar()
    .encode(
        x=alt.X("Bucket:N", title=None),
        y=alt.Y("Strength:Q", title="Activated strength"),
        tooltip=["Bucket", alt.Tooltip("Strength:Q", format=".2f")],
    )
    .properties(height=230)
)
st.altair_chart(agg_chart, width="stretch")
st.info(
    "**Interpretation:** The rules fire with different strengths; we combine them and defuzzify to a score (0–100). "
    "If ‘Critical’ has non-zero strength, the system leans towards emergency."
)

st.markdown("---")

# ====================================================
# 5) MANUAL MODE (keep at bottom as you asked)
# ====================================================
st.markdown("## 🛠️ Manual / Quick Fuzzy Tuning (for demos)")
c1, c2, c3 = st.columns(3)
with c1:
    cap_new = st.slider("Capacity Used (%)", 0, 100, int(st.session_state["cap_pct"]), key="cap_pct")
with c2:
    rain_new = st.slider("Rain (next 24h, mm)", 0, 300, int(st.session_state["rain24"]), key="rain24")
with c3:
    flow_new = st.slider("Inflow / Design Spill (×)", 0.0, 3.0, float(st.session_state["inflow_ratio"]), 0.05, key="inflow_ratio")

# Recompute after manual change
cap = float(cap_new)
rain = float(rain_new)
flow = float(flow_new)
score, label, agg, m_cap, m_rain, m_flow = _compute(cap, rain, flow)

st.success(f"**Updated Risk:** {label.upper()} ({score:.0f}/100)")

if st.button("💾 Save this scenario to History"):
    try:
        save_history({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "user": current_user_email(),
            "type": "Fuzzy Risk",
            "cap_pct": cap,
            "rain24_mm": rain,
            "inflow_ratio": flow,
            "risk_score": float(score),
            "risk_bucket": label,
        })
        st.success("Saved.")
    except Exception as e:
        st.error(f"Save failed: {e}")
if st.button("🔙 Back to Home"):
    st.switch_page("pages/3_Overview.py")
