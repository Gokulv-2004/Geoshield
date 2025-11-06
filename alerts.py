
from datetime import datetime
from config import get_supabase

def check_risk_alerts(rain_mm: float, humidity_pct: float, dam_pct: float):
    """Trigger alerts based on risk levels."""
    alerts = []

    # Flood Risk
    if rain_mm > 80 and humidity_pct > 70:
        alerts.append({
            "type": "Flood Risk",
            "severity": "High",
            "message": "🚨 Heavy rain + high humidity detected. Flooding likely in low-lying areas.",
            "recommendation": "Avoid travel. Stay indoors. Monitor news for evacuation updates."
        })

    # Landslide Risk
    if rain_mm > 100 or (rain_mm > 60 and humidity_pct > 80):
        alerts.append({
            "type": "Landslide Risk",
            "severity": "High",
            "message": "⚠️ Continuous rainfall and moist soil increases landslide danger in hilly areas.",
            "recommendation": "Avoid hill roads. Stay alert if in risk zones."
        })

    # Dam Risk
    if dam_pct > 90:
        alerts.append({
            "type": "Dam Overflow Risk",
            "severity": "High",
            "message": "🌊 Dam levels nearing full capacity. Potential overflow risk.",
            "recommendation": "Authorities may release water. Stay away from riverbanks."
        })

    return alerts


def save_alerts_to_supabase(email: str, city: str, alerts: list):
    """Store triggered alerts to Supabase."""
    supabase = get_supabase()
    if not supabase or not alerts:
        return

    now = datetime.utcnow().isoformat()
    try:
        data = [{
            "user_email": email,
            "city": city,
            "alert_type": a["type"],
            "severity": a["severity"],
            "message": a["message"],
            "recommendation": a["recommendation"],
            "timestamp": now,
        } for a in alerts]
        supabase.table("alerts").insert(data).execute()
    except Exception as e:
        print(f"[Alert Save Error]: {e}")