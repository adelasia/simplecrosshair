from __future__ import annotations

import ctypes
from collections.abc import Callable
from ctypes import byref, c_size_t, c_void_p
from typing import Protocol

from config import COLOR_PRESETS, Config
from win32 import (
    CMD_ABOUT,
    CMD_EXIT,
    CMD_OPEN_CONFIG,
    MF_CHECKED,
    MF_POPUP,
    MF_SEPARATOR,
    MF_STRING,
    MENUINFO,
    MIM_STYLE,
    MNS_MODELESS,
    user32,
)


class MenuCallbacks(Protocol):
    def toggle_enabled(self) -> None: ...
    def refresh_overlay(self) -> None: ...


class TrayMenu:
    def __init__(self, config: Config, callbacks: MenuCallbacks) -> None:
        self._config = config
        self._callbacks = callbacks
        self._next_id = 3000
        self.handlers: dict[int, Callable[[], None]] = {}
        self._check_items: list[tuple[int, int, Callable[[], bool]]] = []
        self._enabled_cmd_id: int | None = None

    def _cmd(self, handler: Callable[[], None]) -> int:
        cmd_id = self._next_id
        self._next_id += 1
        self.handlers[cmd_id] = handler
        return cmd_id

    def _track_check(self, menu, cmd_id: int, checked_fn: Callable[[], bool]) -> None:
        self._check_items.append((int(menu or 0), cmd_id, checked_fn))

    def _refresh(self) -> None:
        self._callbacks.refresh_overlay()

    def apply_modeless(self, menu) -> None:
        info = MENUINFO()
        info.cbSize = ctypes.sizeof(MENUINFO)
        info.fMask = MIM_STYLE
        info.dwStyle = MNS_MODELESS
        user32.SetMenuInfo(c_void_p(menu), byref(info))

        count = user32.GetMenuItemCount(menu)
        for index in range(count):
            submenu = user32.GetSubMenu(menu, index)
            if submenu:
                self.apply_modeless(submenu)

    def sync_checks(self) -> None:
        for menu_handle, cmd_id, checked_fn in self._check_items:
            user32.CheckMenuItem(
                c_void_p(menu_handle),
                cmd_id,
                MF_CHECKED if checked_fn() else 0,
            )

    def _append_toggle(
        self,
        menu,
        label: str,
        checked: bool,
        handler: Callable[[], None],
        checked_fn: Callable[[], bool] | None = None,
    ) -> None:
        cmd_id = self._cmd(handler)
        flags = MF_STRING | (MF_CHECKED if checked else 0)
        user32.AppendMenuW(menu, flags, cmd_id, label)
        self._track_check(menu, cmd_id, checked_fn or (lambda: checked))

    def _append_submenu(self, parent, label: str, submenu: c_void_p) -> None:
        user32.AppendMenuW(
            parent,
            MF_POPUP | MF_STRING,
            c_size_t(int(submenu or 0)).value,
            label,
        )

    def _append_value_menu(
        self,
        parent,
        label: str,
        values: list[int],
        current: int,
        on_pick: Callable[[int], None],
        getter: Callable[[], int],
    ) -> None:
        submenu = user32.CreatePopupMenu()
        for value in values:

            def make_handler(v: int) -> Callable[[], None]:
                def handler() -> None:
                    on_pick(v)
                    self._refresh()

                return handler

            cmd_id = self._cmd(make_handler(value))
            flags = MF_STRING | (MF_CHECKED if value == current else 0)
            user32.AppendMenuW(submenu, flags, cmd_id, str(value))

            def check_value(v: int = value) -> bool:
                return getter() == v

            self._track_check(submenu, cmd_id, check_value)
        self._append_submenu(parent, label, submenu)

    def _append_color_menu(
        self,
        parent,
        label: str,
        current: str,
        on_pick: Callable[[str], None],
        getter: Callable[[], str],
    ) -> None:
        submenu = user32.CreatePopupMenu()
        current_upper = current.upper()
        for name, hex_color in COLOR_PRESETS:

            def make_handler(color: str) -> Callable[[], None]:
                def handler() -> None:
                    on_pick(color)
                    self._refresh()

                return handler

            cmd_id = self._cmd(make_handler(hex_color))
            checked = hex_color.upper() == current_upper
            flags = MF_STRING | (MF_CHECKED if checked else 0)
            user32.AppendMenuW(submenu, flags, cmd_id, name)

            def check_color(c: str = hex_color) -> bool:
                return getter().upper() == c.upper()

            self._track_check(submenu, cmd_id, check_color)
        self._append_submenu(parent, label, submenu)

    def _build_crosshair_menu(self) -> c_void_p:
        menu = user32.CreatePopupMenu()
        dot = self._config.section("dot")
        ring = self._config.section("ring")
        cross = self._config.section("cross")

        self._append_toggle(
            menu,
            "Dot",
            bool(dot["enabled"]),
            lambda: self._toggle_section("dot"),
            lambda: bool(self._config.section("dot")["enabled"]),
        )
        self._append_value_menu(
            menu,
            "Dot size",
            [1, 2, 3, 4, 5, 6, 8, 10],
            int(dot["size"]),
            lambda v: self._config.set_int("dot", "size", v),
            lambda: int(self._config.section("dot")["size"]),
        )
        self._append_color_menu(
            menu,
            "Dot color",
            str(dot["color"]),
            lambda c: self._config.set_color("dot", c),
            lambda: str(self._config.section("dot")["color"]),
        )

        self._append_toggle(
            menu,
            "Ring",
            bool(ring["enabled"]),
            lambda: self._toggle_section("ring"),
            lambda: bool(self._config.section("ring")["enabled"]),
        )
        self._append_value_menu(
            menu,
            "Ring diameter",
            [8, 12, 16, 20, 24, 28, 32, 40],
            int(ring["diameter"]),
            lambda v: self._config.set_int("ring", "diameter", v),
            lambda: int(self._config.section("ring")["diameter"]),
        )
        self._append_value_menu(
            menu,
            "Ring thickness",
            [1, 2, 3, 4, 5],
            int(ring["thickness"]),
            lambda v: self._config.set_int("ring", "thickness", v),
            lambda: int(self._config.section("ring")["thickness"]),
        )
        self._append_color_menu(
            menu,
            "Ring color",
            str(ring["color"]),
            lambda c: self._config.set_color("ring", c),
            lambda: str(self._config.section("ring")["color"]),
        )

        self._append_toggle(
            menu,
            "Cross",
            bool(cross["enabled"]),
            lambda: self._toggle_section("cross"),
            lambda: bool(self._config.section("cross")["enabled"]),
        )
        self._append_value_menu(
            menu,
            "Cross gap",
            [0, 2, 4, 6, 8, 10, 12],
            int(cross["gap"]),
            lambda v: self._config.set_int("cross", "gap", v),
            lambda: int(self._config.section("cross")["gap"]),
        )
        self._append_value_menu(
            menu,
            "Cross thickness",
            [1, 2, 3, 4, 5],
            int(cross["thickness"]),
            lambda v: self._config.set_int("cross", "thickness", v),
            lambda: int(self._config.section("cross")["thickness"]),
        )
        self._append_value_menu(
            menu,
            "Cross length",
            [4, 8, 12, 16, 18, 22, 26, 30],
            int(cross["length"]),
            lambda v: self._config.set_int("cross", "length", v),
            lambda: int(self._config.section("cross")["length"]),
        )
        self._append_color_menu(
            menu,
            "Cross color",
            str(cross["color"]),
            lambda c: self._config.set_color("cross", c),
            lambda: str(self._config.section("cross")["color"]),
        )
        return menu

    def _toggle_section(self, section: str) -> None:
        self._config.toggle_section(section)
        self._refresh()

    def build(self) -> c_void_p:
        self.handlers.clear()
        self._check_items.clear()
        self._enabled_cmd_id = None
        self._next_id = 3000

        menu = user32.CreatePopupMenu()
        enabled_cmd = self._cmd(self._callbacks.toggle_enabled)
        self._enabled_cmd_id = enabled_cmd
        enabled_flags = MF_STRING | (MF_CHECKED if self._config.enabled else 0)
        user32.AppendMenuW(menu, enabled_flags, enabled_cmd, "Enabled")
        self._track_check(menu, enabled_cmd, lambda: self._config.enabled)

        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)

        crosshair_menu = self._build_crosshair_menu()
        self._append_submenu(menu, "Crosshair", crosshair_menu)

        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, CMD_OPEN_CONFIG, "Open config folder")
        user32.AppendMenuW(menu, MF_STRING, CMD_ABOUT, "About")
        user32.AppendMenuW(menu, MF_STRING, CMD_EXIT, "Exit")
        return menu

    def handle_command(self, cmd: int) -> bool:
        handler = self.handlers.get(cmd)
        if handler:
            handler()
            return True
        return False

    def should_reopen_menu(self, cmd: int) -> bool:
        return cmd in self.handlers and cmd != self._enabled_cmd_id
