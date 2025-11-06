# pages/5_Dam_Module.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from style import apply_theme
from utils import render_top_nav, current_user_email, save_history
from core.reservoir_master import (
    list_reservoirs, get_latlon, get_catchment_km2,
    get_design_spill_cumecs, get_capacity_tmc, get_curve_number
)
from service.openweather import forecast_hourly_mm, forecast_rain_mm

apply_theme(title="🏞️ Reservoir Insights — GeoShield", hide_sidebar=True)
st.set_page_config(page_title="🏞️ Reservoir Insights — GeoShield", layout="wide")
render_top_nav("Dam Module")

email = current_user_email()
if not email:
    st.warning("⚠️ Please log in to access dam module.")
    st.stop()

st.markdown("## 🏞️ Reservoir Overflow Predictor (OpenWeather + SCS + Fuzzy)")

# --- pick reservoir
station = st.selectbox("📍 Choose a Dam (Karnataka)", list_reservoirs())

# --- fetch parameters with safe fallbacks
latlon  = get_latlon(station) or (None, None)
A_km2   = get_catchment_km2(station) or 3000.0
Qsafe   = get_design_spill_cumecs(station) or 4000.0
Cap_tmc = get_capacity_tmc(station) or 25.0
CN      = get_curve_number(station) or 78

cap_pct_now = st.slider("Current Capacity Used (%)", 0, 100, 60, 1)

# quick facts row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Dam", station)
c2.metric("Capacity (TMC)", f"{Cap_tmc:g}")
c3.metric("Design Spill (cumecs)", f"{Qsafe:g}")
c4.metric("Catchment (km²)", f"{A_km2:g}")

# --- rainfall forecast (hourly)
lat, lon = latlon if latlon != (None, None) else (12.97, 77.59)  # fallback: BLR
series = forecast_hourly_mm(lat, lon, hours=24)
rain24 = float(sum(mm for _, mm in series)) if series else 0.0
st.metric("Forecast Rain (24h)", f"{rain24:.1f} mm")

# --- runoff & inflow per hour (SCS)
def scs_runoff_mm(P_mm: float, CN: float) -> float:
    if P_mm <= 0 or CN <= 0: return 0.0
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S
    if P_mm <= Ia: return 0.0
    Q = ((P_mm - Ia) ** 2) / (P_mm - Ia + S)
    return max(0.0, Q)

def runoff_volume_m3(runoff_mm: float, area_km2: float) -> float:
    if runoff_mm <= 0 or area_km2 <= 0: return 0.0
    return area_km2 * 1_000_000.0 * (runoff_mm / 1000.0)

def inflow_from_mm(mm_1h):
    r_mm = scs_runoff_mm(mm_1h, CN)
    vol = runoff_volume_m3(r_mm, A_km2)
    return vol / 3600.0  # m3/s (cumecs) in that hour

hours = np.arange(24)
inflow = np.array([inflow_from_mm(mm) for _, mm in series]) if series else np.zeros(24)

# assume operator can release up to spill capacity:
outflow = np.minimum(inflow, Qsafe)

# compute simple storage trajectory
TMC_M3 = 2.8316846592e10
storage_now_tmc = (cap_pct_now/100.0) * Cap_tmc
storage = [storage_now_tmc]
for i in range(24):
    dV_m3 = (inflow[i] - outflow[i]) * 3600.0  # per hour
    dV_tmc = dV_m3 / TMC_M3
    s_next = max(0.0, min(storage[-1] + dV_tmc, Cap_tmc))
    storage.append(s_next)

cap_pct_series = [100.0 * s / Cap_tmc for s in storage]  # length 25

# --- Risk (very simple: peak inflow vs spill + final capacity)
ratio = float((inflow.max() / Qsafe) if Qsafe > 0 else 0.0)
final_cap = cap_pct_series[-1]
score = 20*min(1, ratio) + 0.8*final_cap  # heuristic scoring
bucket = "LOW"
if score >= 85: bucket = "CRITICAL"
elif score >= 65: bucket = "HIGH"
elif score >= 35: bucket = "MEDIUM"

st.subheader("⚠️ Overflow Risk")
st.metric("Risk", f"{bucket} ({score:.0f}/100)")
st.caption(f"Inputs → Cap: {cap_pct_now:.0f}%, Rain24: {rain24:.1f} mm, Peak inflow/spill: {ratio:.2f}")

# --- Charts
st.markdown("### 📈 Inflow vs Spill Capacity (next 24h)")
df_in = pd.DataFrame({
    "hour": hours,
    "inflow_cumecs": inflow,
})
line = alt.Chart(df_in).mark_line(point=True).encode(
    x=alt.X("hour:Q", title="Hour →"),
    y=alt.Y("inflow_cumecs:Q", title="Inflow (m³/s)"),
    tooltip=["hour","inflow_cumecs"]
).properties(height=300)
rule = alt.Chart(pd.DataFrame({"y":[Qsafe]})).mark_rule(strokeDash=[6,3]).encode(y="y:Q")
st.altair_chart(line + rule, use_container_width="stretch")
# ↓ EXPLANATION for Inflow vs Spill chart
peak_inflow = float(inflow.max()) if len(inflow) else 0.0
peak_hr = int(np.argmax(inflow)) if len(inflow) else 0
exceeds = peak_inflow > Qsafe if Qsafe else False

st.info(
    f"**How to read this chart**  \n"
    f"• Blue line = estimated inflow each hour (m³/s) from rainfall→runoff.  \n"
    f"• Black dashed line = design spill capacity (m³/s). If the blue line goes above it, spillway may be insufficient.  \n\n"
    f"**This forecast**  \n"
    f"• Peak inflow: **{peak_inflow:,.0f} m³/s** at hour **{peak_hr}**.  \n"
    f"• Spill capacity: **{Qsafe:,.0f} m³/s**.  \n"
    f"• Status: **{'🔴 Peak exceeds spill → watch closely' if exceeds else '🟢 Peak below spill'}**."
)


st.markdown("### 🏦 Storage % Trajectory (0–24h)")
df_cap = pd.DataFrame({"hour": np.arange(25), "cap_pct": cap_pct_series})
chart2 = alt.Chart(df_cap).mark_line(point=True).encode(
    x=alt.X("hour:Q", title="Hour →"),
    y=alt.Y("cap_pct:Q", title="Capacity used (%)"),
    tooltip=["hour","cap_pct"]
).properties(height=300)
st.altair_chart(chart2, use_container_width="stretch")
# ↓ EXPLANATION for Storage % chart
start_pct = float(cap_pct_series[0]) if cap_pct_series else 0.0
end_pct = float(cap_pct_series[-1]) if cap_pct_series else 0.0
max_pct = float(np.max(cap_pct_series)) if len(cap_pct_series) else 0.0
overflow_flag = max_pct >= 95.0

st.warning(
    f"**How to read this chart**  \n"
    f"• Line shows projected reservoir fill (%) over the next 24h using inflow–outflow balance.  \n"
    f"• If it approaches **95%**, operators should consider precautionary releases.  \n\n"
    f"**This forecast**  \n"
    f"• Start: **{start_pct:.1f}%** → End (24h): **{end_pct:.1f}%**.  \n"
    f"• Max in 24h: **{max_pct:.1f}%** → **{'⚠️ Near/above 95% threshold' if overflow_flag else 'OK: below 95%'}**."
)


# --- Save
if st.button("Save this prediction"):
    save_history({
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "user": email,
        "type": "Dam Risk",
        "station": station,
        "cap_pct": float(cap_pct_now),
        "rain24_mm": float(rain24),
        "inflow_ratio": float(ratio),
        "risk_score": float(score),
        "risk_bucket": bucket,
    })
    st.success("Saved to History.")
if st.button("🔙 Back to Home"):
    st.switch_page("pages/3_Overview.py")
