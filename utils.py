import os
import requests
from dotenv import load_dotenv
from collections import OrderedDict
import numpy as np
import streamlit as st

from config import WEATHER_API, get_supabase

load_dotenv()

# ========= THEME / UI HELPERS =========

def inject_base_css():
    """Optional: small polish; safe to keep."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] { display: none !important; } /* hide default sidebar nav */
        .block-container { padding-top: 1.25rem; padding-bottom: 1.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_top_nav(active: str = ""):
    inject_base_css()
    supabase = get_supabase()
    user = st.session_state.get("user")
    email = None
    if user:
        if isinstance(user, str):
            email = user
        elif hasattr(user, "user"):
            email = user.user.email

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "gokulkumarvvmg7@gmail.com")
    is_admin = (email == ADMIN_EMAIL)

    st.markdown(
        """
        <div style="padding:12px 14px;border-radius:12px;
        background:linear-gradient(90deg,#0f172a,#0b2b4e);
        border:1px solid #1f2937; color:#cde7ff; margin-bottom:10px;">
        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <div style="font-weight:800;">🌍 GeoShield</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns(6)

    def page_link(col, path, label, icon):
        with col:
            st.page_link(path, label=label, icon=icon)

    if not email:
        page_link(cols[0], "pages/1_Signup.py", "Signup", "📝")
        page_link(cols[1], "pages/2_Login.py", "Login", "🔐")
    else:
        page_link(cols[0], "pages/1_Home.py", "Home", "🏠")
        page_link(cols[1], "pages/3_Overview.py", "Overview", "📊")
        if is_admin:
            page_link(cols[2], "pages/10_Admin_dashboard.py", "Admin Dashboard", "🛠️")
        with cols[5]:
            if st.button("🚪 Logout"):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                st.session_state.pop("user", None)
                st.success("Logged out.")
                st.switch_page("pages/2_Login.py")

# ========= WEATHER API HELPERS =========

def _require_api_key():
    if not WEATHER_API or WEATHER_API.strip() == "":
        return {"error": "Missing WEATHER_API in .env"}
    return None

def get_weather(city: str = "Chennai"):
    err = _require_api_key()
    if err: return err
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": WEATHER_API, "units": "metric"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return {"error": f"API Error: {r.status_code} - {r.text[:120]}"}
        data = r.json()
        return {
            "city": data.get("name", city),
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
            "rain": data.get("rain", {}).get("1h", 0) or 0.0,
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
        }
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}

def get_rainfall_trend(city: str = "Chennai"):
    err = _require_api_key()
    if err: return err
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": WEATHER_API, "units": "metric"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return {"error": f"Rainfall API Error: {r.status_code} - {r.text[:120]}"}
        data = r.json()
        day_totals = OrderedDict()
        for item in data.get("list", []):
            dt_txt = item.get("dt_txt")
            if not dt_txt: continue
            day = dt_txt.split(" ")[0]
            rain_3h = item.get("rain", {}).get("3h", 0) or 0.0
            day_totals[day] = day_totals.get(day, 0.0) + float(rain_3h)
        trend = [{"date": d, "rainfall_mm": round(v, 2)} for d, v in day_totals.items()]
        trend.sort(key=lambda x: x["date"])
        return trend
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}

def flood_prediction(rainfall_mm: float, humidity_pct: float):
    if rainfall_mm > 80 and humidity_pct > 70: return "High"
    elif rainfall_mm > 40: return "Moderate"
    else: return "Low"

def landslide_prediction(rainfall_mm: float, humidity_pct: float):
    if rainfall_mm > 100 or (rainfall_mm > 60 and humidity_pct > 80): return "High"
    elif rainfall_mm > 40: return "Moderate"
    else: return "Low"

def save_weather_history(email, city, data, flood_risk, landslide_risk):
    supabase = get_supabase()
    if supabase is None: return
    try:
        supabase.table("weather_history").insert({
            "user_email": email,
            "city": city,
            "temperature": data["temp"],
            "humidity": data["humidity"],
            "rainfall": data["rain"],
            "condition": data["condition"],
            "flood_risk": flood_risk,
            "landslide_risk": landslide_risk,
        }).execute()
    except Exception as e:
        print("Error saving history:", e)

# ========= FUZZY RISK (robust) =========

def fuzzy_risk_evaluator(rainfall, humidity, dam_percent):
    import skfuzzy as fuzz
    import numpy as np

    def norm(x): return max(0, min(100, float(x) if x else 0))

    r = norm(rainfall)
    h = norm(humidity)
    d = norm(dam_percent)

    x = np.arange(0, 101, 1)
    rain_lo = fuzz.trimf(x, [0, 0, 40])
    rain_md = fuzz.trimf(x, [30, 60, 80])
    rain_hi = fuzz.trimf(x, [60, 100, 100])

    hum_lo = fuzz.trimf(x, [0, 0, 40])
    hum_md = fuzz.trimf(x, [30, 60, 80])
    hum_hi = fuzz.trimf(x, [60, 100, 100])

    dam_lo = fuzz.trimf(x, [0, 0, 40])
    dam_md = fuzz.trimf(x, [30, 60, 80])
    dam_hi = fuzz.trimf(x, [60, 100, 100])

    risk_lo = fuzz.trimf(x, [0, 0, 40])
    risk_md = fuzz.trimf(x, [30, 60, 80])
    risk_hi = fuzz.trimf(x, [60, 100, 100])

    r_lo = fuzz.interp_membership(x, rain_lo, r)
    r_md = fuzz.interp_membership(x, rain_md, r)
    r_hi = fuzz.interp_membership(x, rain_hi, r)

    h_lo = fuzz.interp_membership(x, hum_lo, h)
    h_md = fuzz.interp_membership(x, hum_md, h)
    h_hi = fuzz.interp_membership(x, hum_hi, h)

    d_lo = fuzz.interp_membership(x, dam_lo, d)
    d_md = fuzz.interp_membership(x, dam_md, d)
    d_hi = fuzz.interp_membership(x, dam_hi, d)

    rule_lo = np.fmin(np.fmin(r_lo, h_lo), d_lo)
    rule_md = np.fmax(np.fmin(r_md, h_md), np.fmin(d_md, h_md))
    rule_hi = np.fmax(np.fmin(r_hi, h_hi), np.fmax(d_hi, r_hi))

    out_lo = np.fmin(rule_lo, risk_lo)
    out_md = np.fmin(rule_md, risk_md)
    out_hi = np.fmin(rule_hi, risk_hi)

    aggregate = np.fmax(out_lo, np.fmax(out_md, out_hi))

    try:
        crisp = fuzz.defuzz(x, aggregate, 'centroid')
        return "High" if crisp > 70 else "Moderate" if crisp > 40 else "Low"
    except:
        return "Low"

# ========= MAP HELPERS =========

def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=6).json()
        lat, lon = map(float, res["loc"].split(","))
        city = res.get("city", "Unknown")
        return lat, lon, city
    except Exception:
        return 13.0827, 80.2707, "Chennai"

def _geocode_city(q: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={"q": q, "format": "json", "limit": 1}, headers={"User-Agent": "GeoShield/1.0"}, timeout=8)
        j = r.json()
        if j:
            return float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name", q)
    except Exception:
        pass
    return None

def show_weather_map():
    import folium
    from streamlit_folium import st_folium

    st.subheader("🛰️ Live Interactive Weather Map")

    lat, lon, city = get_user_location()

    with st.expander("Quick Search: City", expanded=False):
        q = st.text_input("City name", placeholder="e.g., Bengaluru / Chennai / Mumbai")
        if st.button("Locate"):
            hit = _geocode_city(q.strip())
            if hit: lat, lon, city = hit[0], hit[1], q.strip()
            else: st.warning("No match found. Showing your detected location.")

    st.info(f"Map center: **{city}**")

    THEMES = {
        "CartoDB Dark Matter": {"builtin": "CartoDB dark_matter"},
        "OpenStreetMap": {"builtin": "OpenStreetMap"},
        "Esri WorldImagery (Satellite)": {
            "custom": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attr": "Tiles © Esri — sources: Esri, USGS, NOAA, and others."
        },
    }
    theme_name = st.selectbox("Choose Map Theme", list(THEMES.keys()), index=0)

    m = folium.Map(location=[lat, lon], zoom_start=7, tiles=None, control_scale=True)
    conf = THEMES[theme_name]
    if "builtin" in conf:
        folium.TileLayer(
    tiles=conf["builtin"],
    attr='Map tiles by OpenStreetMap, under ODbL.',
    name=theme_name,
    control=False
).add_to(m)

    else:
        folium.TileLayer(tiles=conf["custom"], attr=conf["attr"], name=theme_name, control=False).add_to(m)

    if WEATHER_API:
        base = "https://tile.openweathermap.org/map"
        folium.TileLayer(f"{base}/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={WEATHER_API}",
                         attr="OpenWeatherMap", name="🌧️ Rain", overlay=True, control=True).add_to(m)
        folium.TileLayer(f"{base}/wind_new/{{z}}/{{x}}/{{y}}.png?appid={WEATHER_API}",
                         attr="OpenWeatherMap", name="💨 Wind", overlay=True, control=True).add_to(m)
        folium.TileLayer(f"{base}/humidity/{{z}}/{{x}}/{{y}}.png?appid={WEATHER_API}",
                         attr="OpenWeatherMap", name="💧 Humidity", overlay=True, control=True).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=740, height=500)
    
# ========= USER SESSION HELPERS =========

def current_user_email():
    """Safely extract logged-in user's email from session."""
    try:
        u = st.session_state.get("user")
        if isinstance(u, str):
            return u
        if u and getattr(u, "user", None) and getattr(u.user, "email", None):
            return u.user.email
    except Exception:
        pass
    return None

import os, pandas as pd

_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "data", "history.csv")

def _history_schema():
    # simple, flat schema
    return ["timestamp","user","type","station","cap_pct","rain24_mm","inflow_ratio","risk_score","risk_bucket"]

def save_history(record: dict):
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    cols = _history_schema()
    # normalize
    row = {k: record.get(k, None) for k in cols}
    df = pd.DataFrame([row], columns=cols)
    if os.path.exists(_HISTORY_PATH):
        old = pd.read_csv(_HISTORY_PATH)
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(_HISTORY_PATH, index=False)

def load_history() -> pd.DataFrame:
    cols = _history_schema()
    if not os.path.exists(_HISTORY_PATH):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(_HISTORY_PATH)
    # add any missing columns
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]

