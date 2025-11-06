# service/alerts.py
# GeoShield — Alerts config + SMS notifier
# -------------------------------------------------
import time
from typing import Dict, Optional

import streamlit as st
from service.sms import send_sms

# Session key for storing alert config
_ALERTS_KEY = "_alerts_cfg"

# Risk ordering for threshold checks
_RISK_ORDER = {"Low": 0, "Medium": 1, "Moderate": 1, "High": 2, "Critical": 3}


# ---------- Defaults & Config State ----------

def _defaults() -> Dict:
    """
    Defaults can be influenced by Streamlit secrets:
      - sms_dry_run: bool
      - alert_phone: str (E.164 like +91XXXXXXXXXX)
    """
    secs = getattr(st, "secrets", {})
    sms_dry_run = bool(secs.get("sms_dry_run", True))
    phone = secs.get("alert_phone", "")
    return {
        "enabled": False,
        "min_level": "High",        # "Moderate" | "High" | "Critical"
        "cooldown_sec": 1800,       # 30 minutes
        "phone": phone,             # recipient
        "dry_run": sms_dry_run,     # simulated send by default unless toggled off in Admin
        "_last_sent_at": 0.0,
    }


def get_alerts_cfg() -> Dict:
    """Get the current alerts configuration from session state (with defaults merged)."""
    if _ALERTS_KEY not in st.session_state:
        st.session_state[_ALERTS_KEY] = _defaults()
    base = _defaults()
    base.update(st.session_state[_ALERTS_KEY])  # non-destructive merge
    st.session_state[_ALERTS_KEY] = base
    return st.session_state[_ALERTS_KEY]


def set_alerts_cfg(
    *,
    enabled: Optional[bool] = None,
    min_level: Optional[str] = None,
    cooldown_sec: Optional[int] = None,
    phone: Optional[str] = None,
    dry_run: Optional[bool] = None,
):
    """Update alerts configuration safely."""
    cfg = get_alerts_cfg()
    if enabled is not None:
        cfg["enabled"] = bool(enabled)
    if min_level is not None:
        if min_level not in ("Moderate", "High", "Critical"):
            raise ValueError("min_level must be one of: Moderate, High, Critical")
        cfg["min_level"] = min_level
    if cooldown_sec is not None:
        cfg["cooldown_sec"] = int(cooldown_sec)
    if phone is not None:
        cfg["phone"] = phone.strip()
    if dry_run is not None:
        cfg["dry_run"] = bool(dry_run)
    st.session_state[_ALERTS_KEY] = cfg


# ---------- Helpers ----------

def _recently_sent(cooldown_sec: int) -> bool:
    last = get_alerts_cfg().get("_last_sent_at", 0.0)
    return (time.time() - float(last)) < cooldown_sec


def _meets_threshold(risk: str, min_level: str) -> bool:
    return _RISK_ORDER.get(risk, 0) >= _RISK_ORDER.get(min_level, 2)


def _sanitize(v: Optional[object]) -> str:
    s = "" if v is None else str(v)
    # keep it simple, SMS-safe
    return " ".join(s.split())[:120]


def _build_sms_message(*, risk: str, feature: str, ctx: Optional[Dict]) -> str:
    """
    Build a short, actionable SMS based on risk level.
    Context keys we’ll use if present:
      location, district, river, dam, rainfall_mm, eta_hours, note
    """
    c = ctx or {}
    location = _sanitize(c.get("location") or c.get("district") or c.get("river") or "Unknown")
    rainfall = _sanitize(c.get("rainfall_mm"))
    eta = _sanitize(c.get("eta_hours"))
    note = _sanitize(c.get("note"))

    # Common header
    header = "[GeoShield Alert]"

    risk_upper = (risk or "High").upper()

    if risk_upper == "MODERATE":
        # Advisory tone; no evacuation directive.
        lines = [
            header,
            f"Moderate flood risk in {location}.",
            "Stay alert. Avoid low-lying areas and monitor updates.",
        ]
        if rainfall:
            lines.append(f"Rain (mm): {rainfall}")
        if eta:
            lines.append(f"ETA (hrs): {eta}")
        if note:
            lines.append(note)

    elif risk_upper == "HIGH":
        # Action required.
        lines = [
            header,
            f"⚠️ HIGH flood risk in {location}.",
            "Move away from rivers/drains. Prepare to relocate to higher ground.",
        ]
        if rainfall:
            lines.append(f"Rain (mm): {rainfall}")
        if eta:
            lines.append(f"ETA (hrs): {eta}")
        if note:
            lines.append(note)

    else:
        # Treat anything else >= threshold as CRITICAL
        lines = [
            header,
            f"🚨 CRITICAL flood risk in {location}.",
            "EVACUATE to higher ground NOW. Avoid water bodies & underpasses.",
        ]
        if rainfall:
            lines.append(f"Rain (mm): {rainfall}")
        if eta:
            lines.append(f"ETA (hrs): {eta}")
        if note:
            lines.append(note)

    # Fail-safe footer kept short
    lines.append("Automated warning • Stay safe")
    msg = "\n".join(lines)

    # SMS hard cap safeguard
    return msg[:480]


# ---------- Public API ----------

def notify_on_risk(
    *,
    feature: str,
    risk: str,
    ctx: Optional[Dict] = None,
    force: bool = False,
) -> Dict:
    """
    Main entry-point used by feature pages.

    Normal mode:
      - requires: enabled=True, risk >= min_level, not in cooldown, phone present
    Force mode:
      - bypasses enabled/threshold/cooldown
      - still requires phone
    """
    cfg = get_alerts_cfg()

    # Phone is always required (even in force)
    if not cfg.get("phone"):
        return {"ok": False, "skipped": "no_phone"}

    if not force:
        if not cfg.get("enabled", False):
            return {"ok": False, "skipped": "disabled"}
        if not _meets_threshold(risk, cfg.get("min_level", "High")):
            return {"ok": False, "skipped": "below_threshold"}
        if _recently_sent(cfg.get("cooldown_sec", 1800)):
            return {"ok": False, "skipped": "cooldown"}

    # Build final SMS text
    message = _build_sms_message(risk=risk, feature=feature, ctx=ctx)

    # Dispatch
    res = send_sms(cfg["phone"], message, dry_run=bool(cfg.get("dry_run", True)))
    if res.get("ok"):
        cfg["_last_sent_at"] = time.time()
        st.session_state[_ALERTS_KEY] = cfg
    return res
