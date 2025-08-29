# utils.py
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from collections import OrderedDict

load_dotenv()
WEATHER_API = os.getenv("WEATHER_API")

def _require_api_key():
    if not WEATHER_API or WEATHER_API.strip() == "":
        return {"error": "Missing WEATHER_API in .env"}
    return None

def get_weather(city: str = "Chennai"):
    """
    Current weather from OpenWeather (FREE plan).
    Returns: dict with city, temp (°C), humidity (%), condition (text), rain (mm in last 1h if available),
             lat, lon.
    """
    err = _require_api_key()
    if err:
        return err

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
    try:
        r = requests.get(url, timeout=15)
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
    """
    5-day / 3-hour forecast from OpenWeather (FREE).
    Aggregates rain (mm) per calendar day (UTC).
    Returns: list of {date: 'YYYY-MM-DD', rainfall_mm: float} sorted by date.
    """
    err = _require_api_key()
    if err:
        return err

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API}&units=metric"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return {"error": f"Rainfall API Error: {r.status_code} - {r.text[:120]}"}
        data = r.json()

        # Aggregate 3h rain into daily totals
        day_totals = OrderedDict()
        for item in data.get("list", []):
            dt_txt = item.get("dt_txt")  # "YYYY-MM-DD HH:MM:SS"
            if not dt_txt:
                continue
            day = dt_txt.split(" ")[0]
            rain_3h = item.get("rain", {}).get("3h", 0) or 0.0
            day_totals[day] = day_totals.get(day, 0.0) + float(rain_3h)

        # Make sorted list
        trend = [{"date": d, "rainfall_mm": round(v, 2)} for d, v in day_totals.items()]
        trend.sort(key=lambda x: x["date"])
        return trend
    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}

def flood_prediction(rainfall_mm: float, humidity_pct: float):
    """
    Basic heuristic using REAL inputs from OpenWeather.
    Tweak thresholds later when you have local calibration.
    """
    if rainfall_mm > 80 and humidity_pct > 70:
        return "High"
    elif rainfall_mm > 40:
        return "Moderate"
    else:
        return "Low"

def landslide_prediction(rainfall_mm: float, humidity_pct: float):
    """
    Basic heuristic using REAL inputs from OpenWeather.
    """
    if rainfall_mm > 100 or (rainfall_mm > 60 and humidity_pct > 80):
        return "High"
    elif rainfall_mm > 40:
        return "Moderate"
    else:
        return "Low"
from config import supabase

def save_weather_history(email, city, data, flood_risk, landslide_risk):
    """Save a weather query into Supabase"""
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
