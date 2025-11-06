# service/sms.py
import os
from typing import Dict

def _get_twilio_secrets():
    """Read Twilio creds from Streamlit secrets."""
    try:
        import streamlit as st
        tw = st.secrets.get("twilio", {})
        sid = tw.get("account_sid")
        token = tw.get("auth_token")
        # IMPORTANT: this should be your Messaging Service SID (MGxxxxxxxx)
        msid = tw.get("from")
        return sid, token, msid
    except Exception:
        return None, None, None

def send_sms(to_number: str, message: str, dry_run: bool = True) -> Dict:
    """
    Send plain SMS.
    If dry_run=True → no external call (used for demos/tests).
    Uses Messaging Service SID (NOT from_ number) for Twilio.
    """
    if dry_run:
        return {"ok": True, "provider": "dry_run", "to": to_number, "message": message}

    sid, token, messaging_service_sid = _get_twilio_secrets()
    if not sid or not token or not messaging_service_sid:
        return {"ok": False, "error": "Twilio credentials missing or Messaging Service SID not set in secrets.toml [twilio].from"}

    try:
        from twilio.rest import Client  # type: ignore
        client = Client(sid, token)
        msg = client.messages.create(
            to=to_number,
            messaging_service_sid=messaging_service_sid,  # ✅ correct for Messaging Service
            body=message,
        )
        return {"ok": True, "provider": "twilio", "sid": msg.sid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
