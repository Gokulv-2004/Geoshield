# ------------------------------
# 🛠️ GeoShield — Admin Dashboard  (CLEAN / FIXED)
# ------------------------------
import re
import streamlit as st
import pandas as pd

from config import get_supabase
from utils import render_top_nav, current_user_email
from style import apply_theme
from service.alerts import get_alerts_cfg, set_alerts_cfg, notify_on_risk, _ALERTS_KEY

# ---------- MUST BE FIRST ----------
st.set_page_config(page_title="🛠️ Admin Dashboard — GeoShield", layout="wide")

# ---------- THEME + NAV ----------
apply_theme(title="🛠️ Admin Dashboard — GeoShield", hide_sidebar=True)
render_top_nav("Admin_Dashboard")

# ---------- AUTH ----------
st.markdown("## 🛠️ GeoShield Admin Panel")
st.info("Only authorized admins can access this page to manage datasets and system controls.")

supabase = get_supabase()
if not supabase:
    st.error("❌ Supabase not configured.")
    st.stop()

email = current_user_email()
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "admin@geoshield.com")
if email != ADMIN_EMAIL:
    st.warning("⚠️ Access denied. Only GeoShield Admins are allowed here.")
    st.stop()

# ---------- QUICK NAV ----------
with st.container():
    st.subheader("📋 Quick Feature Access")
    row1 = st.columns(4)
    row1[0].page_link("pages/3_Overview.py",    label="🏠 Dashboard")
    row1[1].page_link("pages/4_Rain_Module.py", label="🌧️ Rain Monitor")
    row1[2].page_link("pages/5_Dam_Module.py",  label="💧 Reservoir Data")
    row1[3].page_link("pages/6_River_module.py",label="🌊 River Status")

    row2 = st.columns(3)
    row2[0].page_link("pages/7_Fuzzy_Risk.py",      label="🚨 Fuzzy Flood Risk")
    row2[1].page_link("pages/8_Cloudburst_Risk.py", label="⛈️ Cloudburst Model")
    row2[2].page_link("pages/9_History.py",         label="📜 User History")

st.markdown(
    "<div style='display:flex;justify-content:flex-end;margin-top:-42px;'></div>",
    unsafe_allow_html=True
)
if st.button("🔙 Back to Home", key="btn_back_home"):
    st.switch_page("pages/3_Overview.py")

st.markdown("---")

# ---------- METRICS ----------
st.subheader("📊 Platform Usage Overview")
try:
    usage = supabase.table("weather_history").select("*").execute().data
    user_df = pd.DataFrame(usage) if usage else pd.DataFrame(columns=["user_email"])
    c = st.columns(2)
    c[0].metric("📦 Total Records", len(user_df))
    c[1].metric("👥 Unique Users", user_df["user_email"].nunique() if "user_email" in user_df else 0)
except Exception:
    st.warning("⚠️ No usage data available yet.")

st.markdown("---")

# ---------- RESERVOIR CSV ----------
with st.expander("📤 Upload Reservoir Master CSV", expanded=False):
    upload = st.file_uploader("Upload CSV", type="csv", key="reservoir_csv")
    if upload:
        try:
            df = pd.read_csv(upload)
            st.success("✅ File loaded successfully.")
            st.dataframe(df, use_container_width="stretch")
            st.info("🛠️ Preview only. DB write disabled to avoid accidental overwrite.")
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")

st.markdown("---")

# ===================================================================
# 📨 SMS Alerts (Admin-only) — SINGLE, DEDUPED PANEL WITH UNIQUE KEYS
# ===================================================================
st.subheader("📨 SMS Alerts")

def _twilio_config_ok():
    try:
        sid      = st.secrets["twilio"]["account_sid"]
        tok      = st.secrets["twilio"]["auth_token"]
        from_num = st.secrets["twilio"]["from"]
        return all([sid, tok, from_num])
    except Exception:
        return False

if not _twilio_config_ok():
    st.warning("⚠️ Twilio credentials are not set correctly in `secrets.toml` "
               "(need `[twilio] account_sid`, `auth_token`, `from`).")

cfg = get_alerts_cfg()

def _is_e164(s: str) -> bool:
    # Basic E.164 check: + followed by 8..15 digits
    return bool(re.fullmatch(r"\+\d{8,15}", s or ""))

with st.form("sms_alerts_form", clear_on_submit=False):
    st.caption("Notes: Alerts are triggered by the feature pages after they compute a risk. "
               "This panel only configures when and where to send.")

    # two columns for neat layout
    col1, col2 = st.columns(2)

    with col1:
        enabled = st.checkbox(
            "Enable SMS alerts",
            value=cfg.get("enabled", False),
            key="sms_enabled"
        )
        min_level = st.selectbox(
            "Minimum risk level to alert",
            ["Moderate", "High", "Critical"],
            index=["Moderate", "High", "Critical"].index(cfg.get("min_level", "High")),
            key="sms_min_level"
        )
        cooldown = st.number_input(
            "Cooldown (seconds)",
            min_value=60, max_value=24 * 3600,
            value=int(cfg.get("cooldown_sec", 1800)),
            step=60,
            key="sms_cooldown"
        )

    with col2:
        phone = st.text_input(
            "Recipient phone (E.164, e.g., +91XXXXXXXXXX)",
            value=cfg.get("phone", ""),
            key="sms_phone"
        )
        dry_run = st.checkbox(
            "Dry-run (don’t actually send)",
            value=cfg.get("dry_run", True),
            help="If ON, messages won’t hit Twilio; good for demos.",
            key="sms_dry_run"
        )

    save_clicked = st.form_submit_button("💾 Save Alert Settings", use_container_width="stretch")

if save_clicked:
    if enabled and not _is_e164(phone):
        st.error("❌ Invalid phone format. Use E.164 like +91XXXXXXXXXX.")
    else:
        set_alerts_cfg(
            enabled=bool(enabled),
            min_level=min_level,
            cooldown_sec=int(cooldown),
            phone=phone.strip(),
            dry_run=bool(dry_run),
        )
        st.success("✅ SMS alert settings saved.")

# ---- Test buttons (separate row to avoid re-creating same widgets) ----
test_cols = st.columns(3)
with test_cols[0]:
    if st.button("🧪 Test send (respect rules)", key="sms_test_respect"):
        res = notify_on_risk(feature="AdminTest", risk="High", ctx={"note": "test"})
        st.json(res)  # show provider / error / sid
        if res.get("ok"):
            st.success(f"Test OK via {res.get('provider')}.")
        else:
            st.warning(f"Test skipped/failed: {res}")

with test_cols[1]:
    if st.button("🧪 Force test (ignore cooldown)", key="sms_test_force"):
        res = notify_on_risk(feature="AdminTest", risk="High", ctx={"note": "force"}, force=True)
        st.json(res)  # show provider / error / sid
        if res.get("ok"):
            st.success(f"Force test OK via {res.get('provider')}.")
            if res.get("sid"):
                st.write(f"Twilio Message SID: {res['sid']}")
                st.caption("Check delivery status in Twilio → SMS logs using that SID.")
        else:
            st.error(f"Force test failed/skipped: {res}")

with test_cols[2]:
    if st.button("🧹 Reset cooldown (allow next send)", key="sms_reset_cd"):
        if _ALERTS_KEY in st.session_state and "_last_sent_at" in st.session_state[_ALERTS_KEY]:
            st.session_state[_ALERTS_KEY].pop("_last_sent_at", None)
        st.success("Cooldown cleared.")
