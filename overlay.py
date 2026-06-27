from __future__ import annotations

import ctypes
from ctypes import byref, c_void_p, sizeof
from typing import Any

from config import Config
from win32 import (
    AC_SRC_ALPHA,
    AC_SRC_OVER,
    BI_RGB,
    BLENDFUNCTION,
    BITMAPINFO,
    BITMAPINFOHEADER,
    DIB_RGB_COLORS,
    HWND_TOPMOST,
    IDC_ARROW,
    NULL_BRUSH,
    POINT,
    PS_SOLID,
    SIZE,
    SWP_NOACTIVATE,
    SW_HIDE,
    SW_SHOWNOACTIVATE,
    ULW_ALPHA,
    WNDCLASSW,
    WNDPROC,
    WS_EX_LAYERED,
    WS_EX_NOACTIVATE,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    WS_EX_TRANSPARENT,
    WS_POPUP,
    get_module_handle,
    get_screen_size,
    gdi32,
    kernel32,
    make_int_resource,
    rgb_to_colorref,
    user32,
)


class OverlayWindow:
    CLASS_NAME = "simplecrosshairOverlay"

    def __init__(self, config: Config) -> None:
        self._config = config
        self._hwnd: c_void_p | None = None
        self._visible = False
        self._class_registered = False
        self._wndproc: Any = None
        self._register_class()

    def _register_class(self) -> None:
        if self._class_registered:
            return

        wndproc = WNDPROC(
            lambda hwnd, msg, wp, lp: user32.DefWindowProcW(hwnd, msg, wp, lp)
        )
        self._wndproc = wndproc

        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = wndproc
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = get_module_handle()
        wc.hIcon = None
        wc.hCursor = user32.LoadCursorW(None, make_int_resource(IDC_ARROW))
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = self.CLASS_NAME

        if not user32.RegisterClassW(byref(wc)):
            if kernel32.GetLastError() != 1410:
                raise RuntimeError("Failed to register overlay window class")

        self._class_registered = True

    def create(self) -> None:
        screen_w, screen_h = get_screen_size()
        win_w, win_h = self._window_size()

        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2

        ex_style = (
            WS_EX_LAYERED
            | WS_EX_TRANSPARENT
            | WS_EX_TOPMOST
            | WS_EX_TOOLWINDOW
            | WS_EX_NOACTIVATE
        )

        self._hwnd = user32.CreateWindowExW(
            ex_style,
            self.CLASS_NAME,
            "simplecrosshair",
            WS_POPUP,
            x,
            y,
            win_w,
            win_h,
            None,
            None,
            get_module_handle(),
            None,
        )
        if not self._hwnd:
            raise RuntimeError("Failed to create overlay window")

        self._render()

    def _window_size(self) -> tuple[int, int]:
        ch = self._config.crosshair
        half = 2

        if ch["dot"]["enabled"]:
            half = max(half, int(ch["dot"]["size"]) + 2)

        if ch["ring"]["enabled"]:
            half = max(
                half,
                int(ch["ring"]["diameter"]) // 2 + int(ch["ring"]["thickness"]) + 2,
            )

        cross = ch["cross"]
        if cross["enabled"]:
            cross_half = (
                int(cross["gap"]) + int(cross["length"]) + int(cross["thickness"]) + 2
            )
            half = max(half, cross_half)

        extent = half * 2
        return extent, extent

    def _render(self) -> None:
        if not self._hwnd:
            return

        width, height = self._window_size()
        cx = width // 2
        cy = height // 2

        screen_dc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(screen_dc)
        user32.ReleaseDC(None, screen_dc)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB

        bits = c_void_p()
        dib = gdi32.CreateDIBSection(
            mem_dc, byref(bmi), DIB_RGB_COLORS, byref(bits), None, 0
        )
        if not dib:
            gdi32.DeleteDC(mem_dc)
            raise RuntimeError("Failed to create DIB section")

        old_bitmap = gdi32.SelectObject(mem_dc, dib)
        pixel_count = width * height
        ctypes.memset(bits, 0, pixel_count * 4)

        ch = self._config.crosshair
        if ch["cross"]["enabled"]:
            self._draw_cross(mem_dc, cx, cy, ch["cross"])
        if ch["ring"]["enabled"]:
            self._draw_ring(mem_dc, cx, cy, ch["ring"])
        if ch["dot"]["enabled"]:
            self._draw_dot(mem_dc, cx, cy, ch["dot"])

        addr = bits.value
        if addr is None:
            gdi32.SelectObject(mem_dc, old_bitmap)
            gdi32.DeleteObject(dib)
            gdi32.DeleteDC(mem_dc)
            raise RuntimeError("DIB section returned no pixel buffer")

        buf_type = (ctypes.c_uint32 * pixel_count).from_address(addr)
        for i in range(pixel_count):
            pixel = buf_type[i] & 0xFFFFFF
            if pixel:
                buf_type[i] = pixel | 0xFF000000

        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        pt_src = POINT(0, 0)
        size_struct = SIZE(width, height)
        pt_dst = POINT(0, 0)

        user32.UpdateLayeredWindow(
            self._hwnd,
            None,
            byref(pt_dst),
            byref(size_struct),
            mem_dc,
            byref(pt_src),
            0,
            byref(blend),
            ULW_ALPHA,
        )

        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(dib)
        gdi32.DeleteDC(mem_dc)
        self._reposition_center()

    def _draw_dot(self, dc, cx: int, cy: int, dot: dict) -> None:
        size = max(1, int(dot["size"]))
        color = rgb_to_colorref(str(dot["color"]))
        radius = max(1, size // 2)
        brush = gdi32.CreateSolidBrush(color)
        pen = gdi32.CreatePen(PS_SOLID, 1, color)
        old_brush = gdi32.SelectObject(dc, brush)
        old_pen = gdi32.SelectObject(dc, pen)
        gdi32.Ellipse(
            dc,
            cx - radius,
            cy - radius,
            cx + radius + (size % 2),
            cy + radius + (size % 2),
        )
        gdi32.SelectObject(dc, old_brush)
        gdi32.SelectObject(dc, old_pen)
        gdi32.DeleteObject(brush)
        gdi32.DeleteObject(pen)

    def _draw_ring(self, dc, cx: int, cy: int, ring: dict) -> None:
        diameter = max(2, int(ring["diameter"]))
        thickness = max(1, int(ring["thickness"]))
        color = rgb_to_colorref(str(ring["color"]))
        radius = diameter // 2
        pen = gdi32.CreatePen(PS_SOLID, thickness, color)
        null_brush = gdi32.GetStockObject(NULL_BRUSH)
        old_pen = gdi32.SelectObject(dc, pen)
        old_brush = gdi32.SelectObject(dc, null_brush)
        gdi32.Ellipse(dc, cx - radius, cy - radius, cx + radius, cy + radius)
        gdi32.SelectObject(dc, old_pen)
        gdi32.SelectObject(dc, old_brush)
        gdi32.DeleteObject(pen)

    def _draw_cross(self, dc, cx: int, cy: int, cross: dict) -> None:
        length = max(1, int(cross["length"]))
        gap = max(0, int(cross["gap"]))
        thickness = max(1, int(cross["thickness"]))
        color = rgb_to_colorref(str(cross["color"]))
        pen = gdi32.CreatePen(PS_SOLID, 1, color)
        brush = gdi32.CreateSolidBrush(color)
        old_pen = gdi32.SelectObject(dc, pen)
        old_brush = gdi32.SelectObject(dc, brush)

        half_t = thickness // 2
        t_rem = thickness % 2

        self._fill_rect(
            dc, cx - gap - length, cy - half_t, cx - gap, cy + half_t + t_rem
        )
        self._fill_rect(
            dc, cx + gap, cy - half_t, cx + gap + length, cy + half_t + t_rem
        )
        self._fill_rect(
            dc, cx - half_t, cy - gap - length, cx + half_t + t_rem, cy - gap
        )
        self._fill_rect(
            dc, cx - half_t, cy + gap, cx + half_t + t_rem, cy + gap + length
        )

        gdi32.SelectObject(dc, old_pen)
        gdi32.SelectObject(dc, old_brush)
        gdi32.DeleteObject(pen)
        gdi32.DeleteObject(brush)

    @staticmethod
    def _fill_rect(dc, left: int, top: int, right: int, bottom: int) -> None:
        gdi32.Rectangle(dc, left, top, right, bottom)

    def _reposition_center(self) -> None:
        if not self._hwnd:
            return
        screen_w, screen_h = get_screen_size()
        win_w, win_h = self._window_size()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        user32.SetWindowPos(
            self._hwnd,
            HWND_TOPMOST,
            x,
            y,
            win_w,
            win_h,
            SWP_NOACTIVATE,
        )

    def show(self) -> None:
        if not self._hwnd:
            self.create()
        else:
            self._render()
        user32.ShowWindow(self._hwnd, SW_SHOWNOACTIVATE)
        self._visible = True

    def hide(self) -> None:
        if self._hwnd:
            user32.ShowWindow(self._hwnd, SW_HIDE)
        self._visible = False

    @property
    def visible(self) -> bool:
        return self._visible

    def destroy(self) -> None:
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        self._visible = False
