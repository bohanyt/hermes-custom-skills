"""
API CONFIG HELPER
Simpan di hermes_skills/config_api.py

Load API keys dari .env file atau environment variable.
Semua script di hermes_skills/ import dari sini.

Usage:
    from config_api import get_api_config
    config = get_api_config("summarizer")
    print(config["api_key"])
    print(config["model"])
"""

import os
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
SKILLS_DIR = Path(__file__).parent.resolve()
ENV_FILE = SKILLS_DIR / ".env"


def load_env():
    """
    Load .env file ke os.environ.
    Kalau .env gak ada, fallback ke environment variable sistem.
    """
    if not ENV_FILE.exists():
        return

    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Jangan overwrite kalau udah ada di environment
                if key not in os.environ:
                    os.environ[key] = value


def get_api_config(profile: str = "primary") -> dict:
    """
    Get API config untuk profile tertentu.

    Profiles:
      - "primary"   → OpenRouter utama (Orchestrator, Trend Researcher, dll)
      - "summarizer" → Model terpisah untuk summarization

    Returns:
        dict dengan keys: api_key, base_url, model
    """
    load_env()

    profiles = {
        "primary": {
            "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
            "base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            "model": os.environ.get("OPENROUTER_MODEL_PRIMARY", "openrouter/owl-alpha"),
        },
        "summarizer": {
            "api_key": os.environ.get("SUMMARIZER_API_KEY", os.environ.get("OPENROUTER_API_KEY", "")),
            "base_url": os.environ.get("SUMMARIZER_BASE_URL", "https://openrouter.ai/api/v1"),
            "model": os.environ.get("SUMMARIZER_MODEL", "google/gemini-2.0-flash-001"),
        },
        "secondary": {
            "api_key": os.environ.get("SECONDARY_API_KEY", os.environ.get("OPENROUTER_API_KEY", "")),
            "base_url": os.environ.get("SECONDARY_BASE_URL", "https://openrouter.ai/api/v1"),
            "model": os.environ.get("SECONDARY_MODEL", "openrouter/owl-alpha"),
        },
    }

    if profile not in profiles:
        raise ValueError(f"Unknown profile: {profile}. Available: {list(profiles.keys())}")

    config = profiles[profile]

    if not config["api_key"]:
        raise ValueError(
            f"API key untuk profile '{profile}' tidak ditemukan. "
            f"Set di .env file atau environment variable."
        )

    return config


def call_llm(profile: str, messages: list, max_tokens: int = 2000, temperature: float = 0.3) -> str:
    """
    Call LLM API (OpenRouter) untuk profile tertentu.

    Args:
        profile: "primary" atau "summarizer"
        messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
        max_tokens: max token output
        temperature: 0.0-1.0

    Returns:
        Response text dari LLM
    """
    import urllib.request
    import json as _json

    config = get_api_config(profile)

    payload = {
        "model": config["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=_json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"LLM API error ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}")


# ── auto-load .env saat import ─────────────────────────────────────────
load_env()
