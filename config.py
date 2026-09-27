"""
config.py - Centralized Configuration Module.
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "verification_interval": 30,
    "grace_period_missed_checks": 2,
    "face_match_tolerance": 0.6,
    "totp_valid_window": 1,
    "max_pause_duration_seconds": 300,
    "jwt_expiry_hours": 24,
    "discord_webhook_url": ""
}

def load_config() -> dict:
    """Loads configuration merging defaults with config.json overrides."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config.update({k: v for k, v in json.load(f).items() if not k.startswith("_")})
        except Exception as e:
            print(f"[Config Warning] Could not parse config.json, using defaults: {e}")
    return config
