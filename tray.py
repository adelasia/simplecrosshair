from __future__ import annotations

import ctypes
from ctypes import byref, c_void_p
from pathlib import Path
from typing import Protocol

from config import bundle_dir, config_dir
from menu import TrayMenu
from win32 import (
    CMD_ABOUT,
    CMD_EXIT,
    CMD_OPEN_CONFIG,
    IMAGE_ICON,
    LR_LOADFROMFILE,
    NIF_ICON,
    NIF_MESSAGE,
    NIF_TIP,
    NIM_ADD,
    NIM_DELETE,
    NOTIFYICONDATAW,
    POINT,
    SW_SHOWNORMAL,
    TRAY_CLICK_MESSAGES,
    TRAY_MENU_FLAGS,
    WM_NULL,
    WM_TRAYICON,
    SM_CXSMICON,
    shell32,
    user32,
)


class TrayCallbacks(Protocol):
    @property
    def config(self): ...

    def toggle_enabled(self) -> None: ...
    def refresh_overlay(self) -> None: ...
    def exit_app(self) -> None: ...


class TrayIcon:
    TRAY_ID = 1
    TIP = "simplecrosshair"
    ABOUT_URL = "https://github.com/adelasia/simplecrosshair"

    def __init__(self, callbacks: TrayCallbacks) -> None:
        self._callbacks = callbacks
        self._hwnd: c_void_p | None = None
        self._icon: c_void_p | None = None
        self._added = False
        self._menu_builder: TrayMenu | None = None

    def create(self, hwnd: c_void_p) -> None:
        self._hwnd = hwnd
        self._icon = self._load_icon()
        self._menu_builder = TrayMenu(self._callbacks.config, self._callbacks)
        self._add_icon()

    def _icon_path(self) -> Path:
        return bundle_dir() / "resources" / "icon.ico"

    def _load_icon(self) -> c_void_p:
        path = str(self._icon_path())
        size = user32.GetSystemMetrics(SM_CXSMICON)
        icon = user32.LoadImageW(
            None,
            path,
            IMAGE_ICON,
            size,
            size,
            LR_LOADFROMFILE,
        )
        if not icon:
            raise RuntimeError(f"Failed to load tray icon: {path}")
        return icon

    def _notify_data(self) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = self.TRAY_ID
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self._icon
        nid.szTip = self.TIP
        return nid

    def _add_icon(self) -> None:
        if not shell32.Shell_NotifyIconW(NIM_ADD, byref(self._notify_data())):
            raise RuntimeError("Failed to add tray icon")
        self._added = True

    def _run_command(self, cmd: int) -> None:
        if self._menu_builder and self._menu_builder.handle_command(cmd):
            return
        if cmd == CMD_OPEN_CONFIG:
            shell32.ShellExecuteW(
                self._hwnd,
                "open",
                str(config_dir()),
                None,
                None,
                SW_SHOWNORMAL,
            )
        elif cmd == CMD_ABOUT:
            shell32.ShellExecuteW(
                self._hwnd,
                "open",
                self.ABOUT_URL,
                None,
                None,
                SW_SHOWNORMAL,
            )

    def _show_menu_at(self, x: int, y: int) -> int:
        if self._menu_builder is None:
            return 0
        menu = self._menu_builder.build()
        try:
            user32.SetForegroundWindow(self._hwnd)
            cmd = user32.TrackPopupMenu(
                menu,
                TRAY_MENU_FLAGS,
                x,
                y,
                0,
                self._hwnd,
                None,
            )
            user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
            return int(cmd)
        finally:
            user32.DestroyMenu(menu)

    def handle_message(self, lparam: int) -> None:
        if (lparam & 0xFFFF) not in TRAY_CLICK_MESSAGES:
            return
        if not self._menu_builder:
            return

        pt = POINT()
        user32.GetCursorPos(byref(pt))

        while True:
            cmd = self._show_menu_at(pt.x, pt.y)
            if cmd == 0:
                break
            if cmd == CMD_EXIT:
                self._callbacks.exit_app()
                break
            self._run_command(cmd)
            if not self._menu_builder.should_reopen_menu(cmd):
                break

    def destroy(self) -> None:
        if self._added:
            shell32.Shell_NotifyIconW(NIM_DELETE, byref(self._notify_data()))
            self._added = False
        if self._icon:
            user32.DestroyIcon(self._icon)
            self._icon = None
