"""
config.py - Centralized Configuration Module
Companion to TRD v1.0 §6.
Externalizes tunable settings (interval, tolerance, grace period, webhook URL).
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_JSON_PATH = os.path.join(BASE_DIR, "config.json")

# Default Parameters per TRD §6
DEFAULT_CONFIG = {
    "verification_interval": 30,             # Re-verification interval (seconds)
    "grace_period_missed_checks": 2,         # Consecutive missed checks before auto-lock (≈60s)
    "face_match_tolerance": 0.6,             # Euclidean distance tolerance in 128-d space
    "totp_valid_window": 1,                  # TOTP drift tolerance (±30s interval)
    "max_pause_duration_seconds": 300,       # Admin monitoring pause cap (5 min)
    "jwt_expiry_hours": 24,                  # Per-device token lifetime
    "discord_webhook_url": ""                # Webhook URL for HIGH severity alerting
}

def load_config() -> dict:
    """Loads configuration merging defaults with config.json overrides."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_JSON_PATH):
        try:
            with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                overrides = json.load(f)
                for k, v in overrides.items():
                    if not k.startswith("_comment_"):
                        config[k] = v
        except Exception as e:
            print(f"[Config Warning] Could not parse config.json, using defaults: {e}")
    return config

# Module-level convenient access
_current_cfg = load_config()
VERIFICATION_INTERVAL = _current_cfg.get("verification_interval", 30)
GRACE_PERIOD_MISSED_CHECKS = _current_cfg.get("grace_period_missed_checks", 2)
FACE_MATCH_TOLERANCE = _current_cfg.get("face_match_tolerance", 0.6)
TOTP_VALID_WINDOW = _current_cfg.get("totp_valid_window", 1)
MAX_PAUSE_DURATION_SECONDS = _current_cfg.get("max_pause_duration_seconds", 300)
JWT_EXPIRY_HOURS = _current_cfg.get("jwt_expiry_hours", 24)
DISCORD_WEBHOOK_URL = _current_cfg.get("discord_webhook_url", "")
