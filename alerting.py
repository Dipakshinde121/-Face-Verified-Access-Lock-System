import requests
import json
from datetime import datetime

def load_webhook_url():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("discord_webhook_url", "")
    except Exception:
        return ""

WEBHOOK_URL = load_webhook_url()

def trigger_high_severity_alert(roll_number):
    """
    Sends a real-time incident alert to the configured Webhook (e.g. Discord).
    Fails gracefully so the main security enforcement loop is never blocked.
    """
    if not WEBHOOK_URL:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    payload = {
        "content": f"🚨 **HIGH SEVERITY ALERT** 🚨\n**Event:** Unrecognized face detected (Possible Impersonation Attempt)\n**Session Roll Number:** `{roll_number}`\n**Time:** `{timestamp}`\n*Action Taken: Terminal Auto-Locked & Event Audited.*"
    }

    try:
        # We use a short timeout (3s). 
        # FAIL-SAFE PRINCIPLE: If the network is down or webhook fails, we MUST NOT block 
        # the local OS lock from occurring in verify.py.
        requests.post(WEBHOOK_URL, json=payload, timeout=3.0)
    except Exception as e:
        # Network failures shouldn't break local security
        print(f"[Warning] Failed to dispatch real-time alert (Network/Webhook error): {e}")
