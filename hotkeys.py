from __future__ import annotations

from config import Config
from win32 import (
    HOTKEY_ID,
    MOD_NOREPEAT,
    parse_hotkey,
    user32,
)


class HotkeyManager:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._hwnd = None

    def register(self, hwnd) -> bool:
        self._hwnd = hwnd
        vk = parse_hotkey(self._config.hotkey)
        if not user32.RegisterHotKey(hwnd, HOTKEY_ID, MOD_NOREPEAT, vk):
            self._hwnd = None
            return False
        return True

    def unregister(self) -> None:
        if self._hwnd:
            user32.UnregisterHotKey(self._hwnd, HOTKEY_ID)
            self._hwnd = None
