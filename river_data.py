# river_data.py
import os
import pandas as pd
import requests
from datetime import datetime, timedelta


# ------------------------------------------------------
# ✅ OpenWeather API key (taken from env or Streamlit secrets)
# ------------------------------------------------------
try:
    import streamlit as st
    WEATHER_API = st.secrets.get("WEATHER_API", "")
except:
    WEATHER_API = os.getenv("WEATHER_API", "")


# ------------------------------------------------------
# ✅ Rainfall helpers (used by both River Name & State search)
# ------------------------------------------------------
def _rain_last_hours(lat, lon, hours=12):
    """
    Uses OpenWeather timemachine API to get last X hours rainfall.
    """
    if not WEATHER_API:
        return 0.0

    dt = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
    url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"

    try:
        r = requests.get(url, params={
            "lat": lat, "lon": lon, "dt": dt,
            "appid": WEATHER_API, "units": "metric"
        }, timeout=12)
        if r.status_code != 200:
            return 0.0
        hourly = r.json().get("hourly", [])
        return sum(float(h.get("rain", {}).get("1h", 0.0)) for h in hourly)
    except:
        return 0.0


# ------------------------------------------------------
# ✅ Mapping Major Rivers (No dependency on govt APIs)
# ------------------------------------------------------
RIVER_LOOKUP = {
    "Tungabhadra": {"lat": 15.2889, "lon": 76.4746, "reach": "Koppal"},
    "Krishna": {"lat": 16.2076, "lon": 77.3542, "reach": "Raichur"},
    "Cauvery": {"lat": 12.4244, "lon": 77.0279, "reach": "Mandya"},
    "Sharavathi": {"lat": 14.2183, "lon": 74.7876, "reach": "Sagara"},
    "Netravathi": {"lat": 12.8560, "lon": 75.2652, "reach": "Mangalore"},
    "Hemavathi": {"lat": 12.8145, "lon": 76.0463, "reach": "Hassan"},
    "Kabini": {"lat": 11.9900, "lon": 76.2850, "reach": "HD Kote"},
    "Bhadra": {"lat": 13.6963, "lon": 75.6909, "reach": "Shimoga"}
}


def list_rivers():
    """Returns sorted dropdown list"""
    return sorted(list(RIVER_LOOKUP.keys()))


# ------------------------------------------------------
# ✅ RIVER NAME → RISK (uses coordinates from lookup)
# ------------------------------------------------------
def get_river_status_by_name(name):
    data = RIVER_LOOKUP.get(name)
    if not data:
        return {"error": f"No known river '{name}' found."}

    lat, lon = data["lat"], data["lon"]
    rain_mm = round(_rain_last_hours(lat, lon, hours=12), 2)

    # simple logic
    level = "Low"
    if rain_mm >= 50:
        level = "High"
    elif rain_mm >= 20:
        level = "Moderate"

    return {
        "river": name,
        "reach": data["reach"],
        "lat": lat, "lon": lon,
        "rainfall_mm": rain_mm,
        "simulated_river_level": level,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


# ------------------------------------------------------
# ✅ STATE / DISTRICT FALLBACK (CITY BASED SEARCH)
# ------------------------------------------------------
def geocode_city(city):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={WEATHER_API}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass
    return None, None


def get_river_level_status(city="Bagalkot"):
    """Fallback mode—flood risk based only on rain."""
    lat, lon = geocode_city(city)
    if not lat or not lon:
        return {"city": city, "rainfall_mm": 0, "simulated_river_level": "Low"}

    rain = round(_rain_last_hours(lat, lon, hours=12), 2)

    level = "Low"
    if rain >= 50:
        level = "High"
    elif rain >= 20:
        level = "Moderate"

    return {
        "city": city,
        "rainfall_mm": rain,
        "simulated_river_level": level,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
