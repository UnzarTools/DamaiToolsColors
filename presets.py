"""
ColorMod Presets
================
Built-in presets + user preset persistence (JSON files stored in AppData).
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# ── Built-in presets ──────────────────────────────────────────────────────────
BUILTIN: Dict[str, dict] = {
    "DEFAULT": {
        "brightness": 0,   "contrast": 0,  "exposure": 0.0,  "gamma": 1.0,
        "saturation": 0,   "vibrance": 0,  "hue_shift": 0,   "color_temp": 0,
    },
    "SUMMER": {
        # Warm, vivid, golden-hour feel
        "brightness": 10,  "contrast": 5,   "exposure": 0.1,  "gamma": 1.0,
        "saturation": 65,  "vibrance": 35,  "hue_shift": 5,   "color_temp": 35,
    },
    "WINTER": {
        # Cool, crisp, high clarity
        "brightness": 0,   "contrast": 22,  "exposure": 0.0,  "gamma": 1.1,
        "saturation": 22,  "vibrance": 12,  "hue_shift": -8,  "color_temp": -45,
    },
    "DESERT": {
        # Hot, sandy, high-visibility warm tones
        "brightness": 15,  "contrast": 12,  "exposure": 0.2,  "gamma": 0.92,
        "saturation": 45,  "vibrance": 25,  "hue_shift": 10,  "color_temp": 55,
    },
    "NIGHT": {
        # Eye-strain reduction, dark & cool
        "brightness": -22, "contrast": 8,   "exposure": -0.3, "gamma": 1.25,
        "saturation": -18, "vibrance": 0,   "hue_shift": 0,   "color_temp": -22,
    },
    "VIVID": {
        # Maximum colour punch — gaming / esports
        "brightness": 5,   "contrast": 18,  "exposure": 0.1,  "gamma": 0.92,
        "saturation": 130, "vibrance": 85,  "hue_shift": 0,   "color_temp": 12,
    },
    "COMPETITIVE": {
        # High contrast, clarity — FPS / Battle Royale
        "brightness": 12,  "contrast": 35,  "exposure": 0.2,  "gamma": 0.88,
        "saturation": 55,  "vibrance": 45,  "hue_shift": 0,   "color_temp": 0,
    },
    "CINEMA": {
        # Film-grade look, rich shadows, warm tone
        "brightness": -5,  "contrast": 22,  "exposure": -0.1, "gamma": 1.45,
        "saturation": 42,  "vibrance": 22,  "hue_shift": 0,   "color_temp": -12,
    },
}

# User preset directory
_PRESET_DIR = (
    Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")))
    / "ColorMod"
    / "presets"
)


class PresetManager:
    """
    Provides a unified view of built-in + user presets with
    load / save / delete / import / export.
    """

    def __init__(self):
        _PRESET_DIR.mkdir(parents=True, exist_ok=True)
        self._user: Dict[str, dict] = {}
        self._load_user()

    # ── Query ──────────────────────────────────────────────────────────────────

    def all_names(self) -> list:
        """Built-in names first, then user names (alphabetical)."""
        return list(BUILTIN.keys()) + sorted(self._user.keys())

    def get(self, name: str) -> Optional[dict]:
        return BUILTIN.get(name) or self._user.get(name)

    def is_builtin(self, name: str) -> bool:
        return name in BUILTIN

    def exists(self, name: str) -> bool:
        return name in BUILTIN or name in self._user

    # ── Write ──────────────────────────────────────────────────────────────────

    def save(self, name: str, params: dict) -> bool:
        """Save / overwrite a user preset. Returns False on bad name."""
        clean = name.strip().upper()
        if not clean:
            return False
        self._user[clean] = dict(params)
        self._write(clean, params)
        return True

    def delete(self, name: str) -> bool:
        """Delete a user preset. Cannot delete built-ins."""
        if self.is_builtin(name) or name not in self._user:
            return False
        del self._user[name]
        path = _PRESET_DIR / f"{name}.json"
        if path.exists():
            path.unlink()
        return True

    # ── Import / Export ────────────────────────────────────────────────────────

    def export_to_file(self, params: dict, path: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(params, f, indent=2)
            return True
        except Exception:
            return False

    def import_from_file(self, path: str) -> Tuple[str, dict]:
        """
        Parse a preset JSON file.
        Returns (preset_name, params_dict) or raises ValueError.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Not a valid preset file.")
        name   = data.get("name", Path(path).stem).strip().upper()
        params = {k: v for k, v in data.items() if k != "name"}
        return name, params

    # ── Internal ───────────────────────────────────────────────────────────────

    def _write(self, name: str, params: dict):
        path = _PRESET_DIR / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, **params}, f, indent=2)

    def _load_user(self):
        for path in _PRESET_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name", path.stem).strip().upper()
                if name and name not in BUILTIN:
                    self._user[name] = {k: v for k, v in data.items() if k != "name"}
            except Exception:
                pass
