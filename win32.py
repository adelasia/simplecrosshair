from __future__ import annotations

import ctypes
from ctypes import (
    WINFUNCTYPE,
    c_bool,
    c_int,
    c_long,
    c_size_t,
    c_uint,
    c_ulong,
    c_void_p,
    c_wchar_p,
    Structure,
)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32

WS_POPUP = 0x80000000

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

SW_HIDE = 0
SW_SHOWNOACTIVATE = 4

WM_DESTROY = 0x0002
WM_NULL = 0x0000
WM_HOTKEY = 0x0312
WM_COMMAND = 0x0111
WM_USER = 0x0400

WM_TRAYICON = WM_USER + 1

MOD_NOREPEAT = 0x4000

HOTKEY_ID = 1

ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

BI_RGB = 0
DIB_RGB_COLORS = 0

PS_SOLID = 0
NULL_BRUSH = 5

NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

TPM_RIGHTBUTTON = 0x0002
TPM_RIGHTALIGN = 0x0008
TPM_BOTTOMALIGN = 0x0020
TPM_VERTICAL = 0x0040
TPM_NONOTIFY = 0x0080
TPM_RETURNCMD = 0x0100

TRAY_MENU_FLAGS = (
    TPM_RIGHTBUTTON
    | TPM_RIGHTALIGN
    | TPM_BOTTOMALIGN
    | TPM_VERTICAL
    | TPM_NONOTIFY
    | TPM_RETURNCMD
)

MF_STRING = 0x00000000
MF_CHECKED = 0x00000008
MF_SEPARATOR = 0x00000800
MF_POPUP = 0x00000010

MIM_STYLE = 0x00000002
MNS_MODELESS = 0x40000000

IDC_ARROW = 32512

HWND_MESSAGE = -3

VK_NAMES: dict[str, int] = {
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
}

WNDPROC = WINFUNCTYPE(c_long, c_void_p, c_uint, c_size_t, c_size_t)


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class MSG(Structure):
    _fields_ = [
        ("hwnd", c_void_p),
        ("message", c_uint),
        ("wParam", c_size_t),
        ("lParam", c_size_t),
        ("time", c_ulong),
        ("pt", POINT),
    ]


class WNDCLASSW(Structure):
    _fields_ = [
        ("style", c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", c_int),
        ("cbWndExtra", c_int),
        ("hInstance", c_void_p),
        ("hIcon", c_void_p),
        ("hCursor", c_void_p),
        ("hbrBackground", c_void_p),
        ("lpszMenuName", c_wchar_p),
        ("lpszClassName", c_wchar_p),
    ]


class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", c_ulong),
        ("biWidth", c_long),
        ("biHeight", c_long),
        ("biPlanes", ctypes.c_ushort),
        ("biBitCount", ctypes.c_ushort),
        ("biCompression", c_ulong),
        ("biSizeImage", c_ulong),
        ("biXPelsPerMeter", c_long),
        ("biYPelsPerMeter", c_long),
        ("biClrUsed", c_ulong),
        ("biClrImportant", c_ulong),
    ]


class RGBQUAD(Structure):
    _fields_ = [
        ("rgbBlue", ctypes.c_ubyte),
        ("rgbGreen", ctypes.c_ubyte),
        ("rgbRed", ctypes.c_ubyte),
        ("rgbReserved", ctypes.c_ubyte),
    ]


class BITMAPINFO(Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", RGBQUAD * 1)]


class BLENDFUNCTION(Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class SIZE(Structure):
    _fields_ = [("cx", c_long), ("cy", c_long)]


class NOTIFYICONDATAW(Structure):
    _fields_ = [
        ("cbSize", c_ulong),
        ("hWnd", c_void_p),
        ("uID", c_uint),
        ("uFlags", c_uint),
        ("uCallbackMessage", c_uint),
        ("hIcon", c_void_p),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", c_ulong),
        ("dwStateMask", c_ulong),
        ("szInfo", ctypes.c_wchar * 256),
        ("uVersion", c_uint),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", c_ulong),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", c_void_p),
    ]


class MENUINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("fMask", c_uint),
        ("dwStyle", c_uint),
        ("cyMax", c_uint),
        ("hbrBack", c_void_p),
        ("dwContextHelpID", c_ulong),
        ("dwMenuData", c_size_t),
    ]


user32.DefWindowProcW.restype = c_long
user32.DefWindowProcW.argtypes = [c_void_p, c_uint, c_size_t, c_size_t]

user32.RegisterClassW.restype = ctypes.c_ushort
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]

user32.CreateWindowExW.restype = c_void_p
user32.CreateWindowExW.argtypes = [
    c_ulong,
    c_wchar_p,
    c_wchar_p,
    c_ulong,
    c_int,
    c_int,
    c_int,
    c_int,
    c_void_p,
    c_void_p,
    c_void_p,
    c_void_p,
]

user32.DestroyWindow.restype = c_bool
user32.DestroyWindow.argtypes = [c_void_p]

user32.ShowWindow.restype = c_bool
user32.ShowWindow.argtypes = [c_void_p, c_int]

user32.GetMessageW.restype = c_int
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), c_void_p, c_uint, c_uint]

user32.TranslateMessage.restype = c_bool
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]

user32.DispatchMessageW.restype = c_long
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]

user32.PostQuitMessage.restype = None
user32.PostQuitMessage.argtypes = [c_int]

user32.PostMessageW.restype = c_bool
user32.PostMessageW.argtypes = [c_void_p, c_uint, c_size_t, c_size_t]

user32.RegisterHotKey.restype = c_bool
user32.RegisterHotKey.argtypes = [c_void_p, c_int, c_uint, c_uint]

user32.UnregisterHotKey.restype = c_bool
user32.UnregisterHotKey.argtypes = [c_void_p, c_int]

user32.GetSystemMetrics.restype = c_int
user32.GetSystemMetrics.argtypes = [c_int]

user32.LoadCursorW.restype = c_void_p
user32.LoadCursorW.argtypes = [c_void_p, c_wchar_p]

user32.TrackPopupMenu.restype = c_uint
user32.TrackPopupMenu.argtypes = [
    c_void_p,
    c_uint,
    c_int,
    c_int,
    c_int,
    c_void_p,
    c_void_p,
]

user32.GetCursorPos.restype = c_bool
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]

user32.CreatePopupMenu.restype = c_void_p

user32.DestroyMenu.restype = c_bool
user32.DestroyMenu.argtypes = [c_void_p]

user32.AppendMenuW.restype = c_bool
user32.AppendMenuW.argtypes = [c_void_p, c_uint, c_size_t, c_wchar_p]

user32.CheckMenuItem.restype = c_ulong
user32.CheckMenuItem.argtypes = [c_void_p, c_uint, c_uint]

user32.GetMenuItemCount.restype = c_int
user32.GetMenuItemCount.argtypes = [c_void_p]

user32.GetSubMenu.restype = c_void_p
user32.GetSubMenu.argtypes = [c_void_p, c_int]

user32.SetMenuInfo.restype = c_bool
user32.SetMenuInfo.argtypes = [c_void_p, ctypes.POINTER(MENUINFO)]

user32.LoadImageW.restype = c_void_p
user32.LoadImageW.argtypes = [c_void_p, c_wchar_p, c_uint, c_int, c_int, c_uint]

user32.UpdateLayeredWindow.restype = c_bool
user32.UpdateLayeredWindow.argtypes = [
    c_void_p,
    c_void_p,
    ctypes.POINTER(POINT),
    ctypes.POINTER(SIZE),
    c_void_p,
    ctypes.POINTER(POINT),
    c_ulong,
    ctypes.POINTER(BLENDFUNCTION),
    c_ulong,
]

user32.GetDC.restype = c_void_p
user32.GetDC.argtypes = [c_void_p]

user32.ReleaseDC.restype = c_int
user32.ReleaseDC.argtypes = [c_void_p, c_void_p]

user32.SetForegroundWindow.restype = c_bool
user32.SetForegroundWindow.argtypes = [c_void_p]

user32.DestroyIcon.restype = c_bool
user32.DestroyIcon.argtypes = [c_void_p]

user32.SetWindowPos.restype = c_bool
user32.SetWindowPos.argtypes = [
    c_void_p,
    c_void_p,
    c_int,
    c_int,
    c_int,
    c_int,
    c_uint,
]

kernel32.GetModuleHandleW.restype = c_void_p
kernel32.GetModuleHandleW.argtypes = [c_wchar_p]

kernel32.GetLastError.restype = c_ulong

gdi32.CreateCompatibleDC.restype = c_void_p
gdi32.CreateCompatibleDC.argtypes = [c_void_p]

gdi32.DeleteDC.restype = c_bool
gdi32.DeleteDC.argtypes = [c_void_p]

gdi32.CreateDIBSection.restype = c_void_p
gdi32.CreateDIBSection.argtypes = [
    c_void_p,
    ctypes.POINTER(BITMAPINFO),
    c_uint,
    ctypes.POINTER(c_void_p),
    c_void_p,
    c_ulong,
]

gdi32.SelectObject.restype = c_void_p
gdi32.SelectObject.argtypes = [c_void_p, c_void_p]

gdi32.DeleteObject.restype = c_bool
gdi32.DeleteObject.argtypes = [c_void_p]

gdi32.CreatePen.restype = c_void_p
gdi32.CreatePen.argtypes = [c_int, c_int, c_ulong]

gdi32.CreateSolidBrush.restype = c_void_p
gdi32.CreateSolidBrush.argtypes = [c_ulong]

gdi32.Rectangle.restype = c_bool
gdi32.Rectangle.argtypes = [c_void_p, c_int, c_int, c_int, c_int]

gdi32.Ellipse.restype = c_bool
gdi32.Ellipse.argtypes = [c_void_p, c_int, c_int, c_int, c_int]

gdi32.GetStockObject.restype = c_void_p
gdi32.GetStockObject.argtypes = [c_int]

shell32.Shell_NotifyIconW.restype = c_bool
shell32.Shell_NotifyIconW.argtypes = [c_ulong, ctypes.POINTER(NOTIFYICONDATAW)]

shell32.ShellExecuteW.restype = c_void_p
shell32.ShellExecuteW.argtypes = [
    c_void_p,
    c_wchar_p,
    c_wchar_p,
    c_wchar_p,
    c_wchar_p,
    c_int,
]

user32.MessageBoxW.restype = c_int
user32.MessageBoxW.argtypes = [c_void_p, c_wchar_p, c_wchar_p, c_uint]

MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
SW_SHOWNORMAL = 1

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE = 0x0040

SWP_NOACTIVATE = 0x0010
HWND_TOPMOST = c_void_p(-1).value

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_CXSMICON = 49
SM_CYSMICON = 50

CMD_TOGGLE_ENABLED = 1001
CMD_OPEN_CONFIG = 1002
CMD_ABOUT = 1003
CMD_EXIT = 1004

TRAY_CLICK_MESSAGES = {0x0201, 0x0202, 0x0204, 0x0205, 0x0206, 0x007B}


def make_int_resource(value: int):
    return ctypes.cast(value, c_wchar_p)


def get_module_handle() -> c_void_p:
    return kernel32.GetModuleHandleW(None)


def parse_hotkey(name: str) -> int:
    key = name.strip().upper()
    if key not in VK_NAMES:
        raise ValueError(f"Unsupported hotkey: {name}")
    return VK_NAMES[key]


def rgb_to_colorref(hex_color: str) -> int:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r | (g << 8) | (b << 16)


def get_screen_size() -> tuple[int, int]:
    return (
        user32.GetSystemMetrics(SM_CXSCREEN),
        user32.GetSystemMetrics(SM_CYSCREEN),
    )
