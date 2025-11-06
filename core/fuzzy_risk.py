# core/fuzzy_risk.py
import math

def tri(x, a, b, c):
    """Triangular membership."""
    try:
        x = float(x)
    except Exception:
        return 0.0
    if x <= a or x >= c:
        return 0.0
    if math.isclose(x, b):
        return 1.0
    return (x - a) / (b - a) if x < b else (c - x) / (c - b)

def mem_cap_pct(x):
    """Dam capacity used (%)"""
    return {
        "low":    tri(x, 0, 25, 50),
        "medium": tri(x, 40, 65, 85),
        "high":   tri(x, 75, 90, 100),
    }

def mem_rain(x):
    """Rain mm (next 24–48h)"""
    return {
        "low":    tri(x, 0, 5, 15),
        "medium": tri(x, 10, 25, 50),
        "high":   tri(x, 40, 80, 200),
    }

def mem_flow(x):
    """Inflow as ratio of design spill (qin / Qsafe)"""
    return {
        "low":    tri(x, 0, 0.2, 0.4),
        "medium": tri(x, 0.3, 0.6, 0.9),
        "high":   tri(x, 0.8, 1.4, 2.0),
    }

# Alias used by pages
def mem_flow_ratio(x):
    return mem_flow(x)

def aggregate_rules(cap, rain, inflow_ratio):
    """
    Combine memberships and return (score 0–100, label, agg dict).
    Keys expected in cap/rain/inflow_ratio: 'low','medium','high'
    """
    r = inflow_ratio  # brevity

    # Rule set (no outflow input anymore)
    # Critical: high cap & (high rain OR high inflow)
    critical = min(cap["high"], max(rain["high"], r["high"]))

    # High: high cap & (medium rain OR medium inflow)  OR  medium cap & (high inflow or high rain)
    high = max(
        min(cap["high"], max(rain["medium"], r["medium"])),
        min(cap["medium"], max(r["high"], rain["high"]))
    )

    # Medium: medium cap & medium inflow  OR  high cap & low rain & low inflow
    medium = max(
        min(cap["medium"], r["medium"]),
        min(cap["high"], rain["low"], r["low"])
    )

    # Low: whatever is left
    low = max(0.0, 1.0 - max(critical, high, medium))

    agg = {"low": low, "medium": medium, "high": high, "critical": critical}

    # Defuzzify to score
    num = agg["low"]*15 + agg["medium"]*45 + agg["high"]*75 + agg["critical"]*95
    den = max(agg["low"] + agg["medium"] + agg["high"] + agg["critical"], 1e-6)
    score = num / den

    label = ("critical" if score >= 85
             else "high" if score >= 65
             else "medium" if score >= 35
             else "low")
    return score, label, agg
