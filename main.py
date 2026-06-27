from __future__ import annotations

import sys
from ctypes import byref, c_void_p
from typing import Any

from config import Config
from hotkeys import HotkeyManager
from overlay import OverlayWindow
from tray import TrayIcon
from win32 import (
    HOTKEY_ID,
    HWND_MESSAGE,
    MSG,
    WM_DESTROY,
    WM_HOTKEY,
    WM_TRAYICON,
    WNDCLASSW,
    WNDPROC,
    get_module_handle,
    kernel32,
    user32,
)


class Application:
    CLASS_NAME = "simplecrosshairHost"

    def __init__(self) -> None:
        self.config = Config()
        self.overlay = OverlayWindow(self.config)
        self.hotkeys = HotkeyManager(self.config)
        self.tray = TrayIcon(self)
        self._hwnd: c_void_p | None = None
        self._wndproc: Any = None

    def run(self) -> int:
        self._create_host_window()
        hwnd = self._hwnd
        if hwnd is None:
            raise RuntimeError("Host window not created")
        self.hotkeys.register(hwnd)
        self.tray.create(hwnd)
        self._sync_overlay()

        message = MSG()
        while user32.GetMessageW(byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(byref(message))
            user32.DispatchMessageW(byref(message))

        return int(message.wParam)

    def _create_host_window(self) -> None:
        wndproc = WNDPROC(self._window_proc)
        self._wndproc = wndproc

        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = wndproc
        wc.hInstance = get_module_handle()
        wc.lpszClassName = self.CLASS_NAME

        if not user32.RegisterClassW(byref(wc)):
            if kernel32.GetLastError() != 1410:
                raise RuntimeError("Failed to register host window class")

        self._hwnd = user32.CreateWindowExW(
            0,
            self.CLASS_NAME,
            "simplecrosshair",
            0,
            0,
            0,
            0,
            0,
            HWND_MESSAGE,
            None,
            get_module_handle(),
            None,
        )
        if not self._hwnd:
            raise RuntimeError("Failed to create host window")

    def _window_proc(self, hwnd, msg, wparam, lparam) -> int:
        if msg == WM_HOTKEY and int(wparam) == HOTKEY_ID:
            self.toggle_enabled()
            return 0
        if msg == WM_TRAYICON:
            self.tray.handle_message(int(lparam))
            return 0
        if msg == WM_DESTROY:
            self.shutdown()
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def toggle_enabled(self) -> None:
        self.config.enabled = not self.config.enabled
        self._sync_overlay()

    def refresh_overlay(self) -> None:
        if self.config.enabled:
            self.overlay.show()

    def exit_app(self) -> None:
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)

    def _sync_overlay(self) -> None:
        if self.config.enabled:
            self.overlay.show()
        else:
            self.overlay.hide()

    def shutdown(self) -> None:
        self.hotkeys.unregister()
        self.tray.destroy()
        self.overlay.destroy()


def main() -> None:
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
