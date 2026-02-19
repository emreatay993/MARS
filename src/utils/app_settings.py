"""
Persistent application settings helpers for MARS.

This module stores a minimal JSON settings file in the user's home directory
and provides helpers to apply solver/runtime defaults at startup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


SETTINGS_FILE = Path.home() / ".mars_settings.json"

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}

DEFAULT_APP_SETTINGS: Dict[str, Any] = {
    "ram_percent": 0.9,
    "precision": "Double",
    "software_opengl": False,
}


def _normalize_ram_percent(value: Any) -> float:
    """Clamp RAM fraction to supported bounds."""
    try:
        ram = float(value)
    except (TypeError, ValueError):
        ram = float(DEFAULT_APP_SETTINGS["ram_percent"])
    return min(0.95, max(0.10, ram))


def _normalize_precision(value: Any) -> str:
    """Normalize precision to supported values."""
    if value in {"Single", "Double"}:
        return str(value)
    return str(DEFAULT_APP_SETTINGS["precision"])


def parse_software_opengl_env() -> Optional[bool]:
    """
    Parse MARS_SOFTWARE_OPENGL from environment.

    Returns:
        True/False when the variable is explicitly set to a supported value,
        or None when unset/invalid.
    """
    raw = os.getenv("MARS_SOFTWARE_OPENGL")
    if raw is None:
        return None

    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    return None


def load_app_settings() -> Dict[str, Any]:
    """Load persisted app settings from disk."""
    settings = dict(DEFAULT_APP_SETTINGS)

    try:
        if SETTINGS_FILE.exists():
            with SETTINGS_FILE.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if isinstance(payload, dict):
                settings["ram_percent"] = _normalize_ram_percent(payload.get("ram_percent"))
                settings["precision"] = _normalize_precision(payload.get("precision"))
                settings["software_opengl"] = bool(payload.get("software_opengl", False))
    except Exception:
        # Keep defaults when settings cannot be read.
        pass

    return settings


def save_app_settings(settings: Dict[str, Any]) -> None:
    """Persist app settings to disk."""
    payload = {
        "ram_percent": _normalize_ram_percent(settings.get("ram_percent")),
        "precision": _normalize_precision(settings.get("precision")),
        "software_opengl": bool(settings.get("software_opengl", False)),
    }

    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_FILE.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except Exception:
        # Non-fatal: keep runtime behavior even if persistence fails.
        pass


def apply_solver_runtime_settings(settings: Dict[str, Any], constants_module) -> None:
    """Apply RAM/precision values to the shared constants module."""
    constants_module.RAM_PERCENT = _normalize_ram_percent(settings.get("ram_percent"))
    constants_module.DEFAULT_PRECISION = _normalize_precision(settings.get("precision"))

    if constants_module.DEFAULT_PRECISION == "Single":
        constants_module.NP_DTYPE = np.float32
        constants_module.RESULT_DTYPE = "float32"
    else:
        constants_module.NP_DTYPE = np.float64
        constants_module.RESULT_DTYPE = "float64"

