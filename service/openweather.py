# service/openweather.py
import os
import time
import math
import requests

# ---------------------------------------------------------
# ✅ Resolve API key (works with secrets + env variables)
# ---------------------------------------------------------
def _get_key():
    try:
        import streamlit as st
        # priority 1
        if st.secrets.get("WEATHER_API"):
            return st.secrets["WEATHER_API"]
        # priority 2
        if st.secrets.get("openweather", {}).get("api_key"):
            return st.secrets["openweather"]["api_key"]
    except Exception:
        pass
    # priority 3
    return os.getenv("WEATHER_API") or os.getenv("OPENWEATHER_API_KEY")


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------
def _sum_hourly(obj, hours):
    total = 0.0
    for h in obj.get("hourly", [])[:hours]:
        total += float(h.get("rain", {}).get("1h", 0.0) or 0.0)
    return total


def _expand_3hour_blocks(data, hours):
    """Convert 3h blocks into 1h values (spread evenly)."""
    out = []
    for item in data:
        mm3 = float(item.get("rain", {}).get("3h", 0.0) or 0.0)
        per = mm3 / 3.0
        ts = item.get("dt", time.time())
        out.extend([(ts, per), (ts + 3600, per), (ts + 7200, per)])
        if len(out) >= hours:
            return out[:hours]
    return out[:hours]


# ---------------------------------------------------------
# ✅ UNIVERSAL HOURLY FORECAST
# ---------------------------------------------------------
def forecast_hourly_mm(lat: float, lon: float, hours: int = 24):
    """Returns list of (timestamp, mm/hr) for next `hours`."""
    key = _get_key()
    if not key:
        return []

    hours = max(1, min(int(hours), 24))

    # --- ✅ Try One Call 3.0 (paid tier) ---
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/3.0/onecall",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric",
                    "exclude": "current,minutely,daily,alerts"},
            timeout=15,
        )
        if r.status_code == 200:
            js = r.json()
            out = [(h["dt"], float(h.get("rain", {}).get("1h", 0.0)))
                   for h in js.get("hourly", [])[:hours]]
            return out
    except:
        pass  # silent fallback

    # --- ✅ Fallback to One Call 2.5 (free hourly works sometimes) ---
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/onecall",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric",
                    "exclude": "current,minutely,daily,alerts"},
            timeout=15,
        )
        if r.status_code == 200:
            js = r.json()
            out = [(h["dt"], float(h.get("rain", {}).get("1h", 0.0)))
                   for h in js.get("hourly", [])[:hours]]
            return out
    except:
        pass

    # --- ✅ LAST FALLBACK: 5-day / 3h forecast ---
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric"},
            timeout=15,
        )
        if r.status_code == 200:
            js = r.json()
            return _expand_3hour_blocks(js.get("list", []), hours)
    except:
        pass

    # nothing worked
    return []


# ---------------------------------------------------------
# ✅ FUNCTION USED BY ALL MODULES (don't remove)
# ---------------------------------------------------------
def hourly_rain_series(lat: float, lon: float, hours: int = 24):
    """Return [{'time': ts, 'rain': mm}, ...] (used in River + Dam modules)"""
    return [{"time": ts, "rain": mm} for ts, mm in forecast_hourly_mm(lat, lon, hours)]


def sum_hourly_rain(lat: float, lon: float, hours: int = 24) -> float:
    """Return total rain in mm (used in Fuzzy Risk + River module)."""
    return float(sum(mm for _, mm in forecast_hourly_mm(lat, lon, hours)))


def forecast_rain_mm(lat: float, lon: float, hours: int = 24) -> float:
    """Backwards compatibility. DON'T REMOVE."""
    return sum_hourly_rain(lat, lon, hours)
