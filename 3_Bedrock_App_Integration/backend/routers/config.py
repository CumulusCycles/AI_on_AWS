"""
Health and configuration endpoints.

- GET /health: returns {"status": "healthy"}. Used by frontends to verify backend is up.
- GET /config: returns default_temperature, default_max_tokens, temperature_min/max,
  max_tokens_min/max (from model_limits.json for the current BEDROCK_MODEL_ID or "default"),
  and model_id. Frontends use this for sliders and defaults.
"""
import json
import os

from fastapi import APIRouter, HTTPException

from config import DEFAULT_MODEL_ID, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Liveness check; no auth. Returns {"status": "healthy"}."""
    return {"status": "healthy"}


@router.get("/config")
async def get_config() -> dict:
    """
    Return model limits and defaults for the configured BEDROCK_MODEL_ID.

    Reads model_limits.json from the backend directory (sibling of routers/).
    Falls back to the "default" entry if the current model_id is not in the file.
    default_temperature and default_max_tokens can be overridden via env.
    """
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    model_limits_path = os.path.join(backend_dir, "model_limits.json")
    try:
        with open(model_limits_path, "r") as f:
            model_limits = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Model limits configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid model limits configuration file")

    current_model_id = DEFAULT_MODEL_ID
    model_config = model_limits.get(current_model_id, model_limits.get("default", {}))

    default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
    default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

    return {
        "default_temperature": default_temperature,
        "default_max_tokens": default_max_tokens,
        "temperature_min": model_config.get("temperature_min", 0.0),
        "temperature_max": model_config.get("temperature_max", 1.0),
        "max_tokens_min": model_config.get("max_tokens_min", 100),
        "max_tokens_max": model_config.get("max_tokens_max", 8192),
        "model_id": current_model_id,
    }
