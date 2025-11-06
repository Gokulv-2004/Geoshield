# config.py

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=False)

# Public configs
OAUTH_REDIRECT = os.getenv("OAUTH_REDIRECT", "http://localhost:8501").strip()
WEATHER_API = os.getenv("WEATHER_API", "").strip()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = get_supabase()

# 🌍 Geocode the city using OpenWeather
def geocode_city(city):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={WEATHER_API}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None

# 🌧️ Main function for 5-day rain trend + today + previous 5 days
def get_rainfall_trend(city):
    if not WEATHER_API:
        return {"error": "API key missing. Set WEATHER_API in .env"}

    coords = geocode_city(city)
    if not coords:
        return {"error": f"City '{city}' not found"}

    lat, lon = coords
    historical, today, forecast = [], [], []

    # 📅 Historical (Past 5 Days)
    for i in range(1, 6):
        dt = datetime.utcnow() - timedelta(days=i)
        timestamp = int(dt.replace(hour=12, minute=0, second=0).timestamp())
        url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={timestamp}&appid={WEATHER_API}&units=metric"
        res = requests.get(url)
        if res.status_code != 200:
            continue
        data = res.json()
        rain_total = sum(hour.get("rain", {}).get("1h", 0.0) for hour in data.get("hourly", []))
        date_str = dt.strftime("%Y-%m-%d")
        historical.append({"date": date_str, "rainfall": round(rain_total, 2)})

    # 📍 Today’s data
    url_today = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API}&units=metric"
    res_today = requests.get(url_today)
    if res_today.status_code == 200:
        data_today = res_today.json()
        date_today = datetime.utcfromtimestamp(data_today.get("dt")).strftime("%Y-%m-%d")
        rain_today = data_today.get("rain", {}).get("1h", 0.0)
        today.append({"date": date_today, "rainfall": round(rain_today, 2)})

    # 🔮 Forecast (Next 5 Days in 3h blocks)
    url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API}&units=metric"
    res_forecast = requests.get(url_forecast)
    if res_forecast.status_code == 200:
        forecast_data = res_forecast.json().get("list", [])
        daily = {}
        for item in forecast_data:
            date = item["dt_txt"].split(" ")[0]
            rain_amt = item.get("rain", {}).get("3h", 0.0)
            daily[date] = daily.get(date, 0.0) + rain_amt
        for date, rain in daily.items():
            forecast.append({"date": date, "rainfall": round(rain, 2)})

    # Combine all for charting
    trend_data = historical[::-1] + today + forecast
    return [{"date": d["date"], "rainfall_mm": d["rainfall"]} for d in trend_data]
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=10)
def load_dam_data():
    # Merge multiple days if needed, for now load just the latest
    df = pd.read_csv("ksndmc-daily-reservoir-report-2023-11-23.csv")  # Update path as needed
    df.columns = df.columns.str.strip()  # Clean column names
    df.rename(columns={
        "Name of the Reservoir": "Reservoir",
        "Gross Capacity": "Capacity_TMC",
        "Gross Storage as on 23/11/2023 TMC": "Current_Storage_TMC",
        "Inflows in cusecs on 23/11/2023": "Inflows_cusecs"
    }, inplace=True)
    return df
