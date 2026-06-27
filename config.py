from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "simplecrosshair"

DEFAULT_CONFIG: dict[str, Any] = {
    "hotkey": "F2",
    "crosshair": {
        "dot": {
            "enabled": True,
            "size": 2,
            "color": "#00FF00",
        },
        "ring": {
            "enabled": False,
            "diameter": 20,
            "thickness": 2,
            "color": "#00FF00",
        },
        "cross": {
            "enabled": True,
            "gap": 6,
            "thickness": 2,
            "length": 18,
            "color": "#00FF00",
        },
    },
}

COLOR_PRESETS: list[tuple[str, str]] = [
    ("Green", "#00FF00"),
    ("Red", "#FF0000"),
    ("Cyan", "#00FFFF"),
    ("Yellow", "#FFFF00"),
    ("White", "#FFFFFF"),
    ("Magenta", "#FF00FF"),
    ("Orange", "#FF8800"),
]


def config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable is not set")
    return Path(appdata) / APP_NAME


def bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def config_path() -> Path:
    return config_dir() / "config.json"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _migrate_legacy_crosshair(data: dict[str, Any]) -> dict[str, Any]:
    crosshair = data.get("crosshair", {})
    if "dot" in crosshair:
        return data

    legacy = crosshair
    data["crosshair"] = deepcopy(DEFAULT_CONFIG["crosshair"])
    if "size" in legacy:
        data["crosshair"]["cross"]["length"] = legacy.get("size", 18)
    if "gap" in legacy:
        data["crosshair"]["cross"]["gap"] = legacy.get("gap", 6)
    if "thickness" in legacy:
        data["crosshair"]["cross"]["thickness"] = legacy.get("thickness", 2)
    if "color" in legacy:
        color = legacy["color"]
        data["crosshair"]["cross"]["color"] = color
        data["crosshair"]["dot"]["color"] = color
        data["crosshair"]["ring"]["color"] = color
    return data


class Config:
    def __init__(self) -> None:
        self._data = deepcopy(DEFAULT_CONFIG)
        self._path = config_path()
        self._enabled = False
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def hotkey(self) -> str:
        return str(self._data["hotkey"])

    @property
    def crosshair(self) -> dict[str, Any]:
        return self._data["crosshair"]

    def section(self, name: str) -> dict[str, Any]:
        return self._data["crosshair"][name]

    def load(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                loaded = json.load(f)
            self._data = _deep_merge(DEFAULT_CONFIG, loaded)
            self._data = _migrate_legacy_crosshair(self._data)
        else:
            self._data = deepcopy(DEFAULT_CONFIG)
            self.save()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
            f.write("\n")

    def set_bool(self, section: str, key: str, value: bool) -> None:
        self._data["crosshair"][section][key] = value
        self.save()

    def set_int(self, section: str, key: str, value: int) -> None:
        self._data["crosshair"][section][key] = int(value)
        self.save()

    def set_color(self, section: str, value: str) -> None:
        self._data["crosshair"][section]["color"] = value
        self.save()

    def toggle_section(self, section: str) -> None:
        current = bool(self._data["crosshair"][section]["enabled"])
        self.set_bool(section, "enabled", not current)
