"""
AI Revenue Desk — Client Config Loader
=======================================
Loads per-client configuration for multi-client deployments.

Each Railway deployment sets CLIENT_SLUG to identify which client's
config to load from clients/{slug}/config.json.

Falls back to reading env vars directly (backward-compatible with
single-client deployments that don't use CLIENT_SLUG).
"""

import os
import json
from functools import lru_cache


@lru_cache(maxsize=32)
def _load_config_file(slug: str) -> dict:
    """Load and cache a client config.json by slug."""
    config_path = os.path.join("clients", slug, "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return {}


def get_active_config() -> dict:
    """
    Returns the config for the currently active client.

    Priority:
    1. clients/{CLIENT_SLUG}/config.json  (new franchise deployments)
    2. Env vars directly                   (existing single-client deployments)
    """
    slug = os.getenv("CLIENT_SLUG")
    if slug:
        file_config = _load_config_file(slug)
        if file_config:
            return file_config

    # Backward-compatible fallback: synthesize from env vars
    return {
        "slug": slug or "default",
        "name": os.getenv("CLIENT_NAME", "AI Revenue Desk Client"),
        "industry": "general_home_services",
        "city": "",
        "fees": {
            "diagnostic": int(os.getenv("CLIENT_DIAGNOSTIC_FEE", "99")),
            "avg_job_value": int(os.getenv("CLIENT_AVG_JOB_VALUE", "150")),
            "retainer": int(os.getenv("CLIENT_RETAINER_FEE", "2000")),
        },
    }


def get_sms_prompt() -> str | None:
    """
    Returns the custom SMS prompt for the active client, or None
    if no custom prompt file exists (falls back to default in sms_ai_agent.py).
    """
    slug = os.getenv("CLIENT_SLUG")
    if not slug:
        return None
    prompt_path = os.path.join("clients", slug, "sms_prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path) as f:
            return f.read()
    return None
