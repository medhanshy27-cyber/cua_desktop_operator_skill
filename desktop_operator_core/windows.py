from __future__ import annotations

import re

import win32con
import win32gui

from .models import WindowInfo, WindowRect


def _window_text(hwnd: int) -> str:
    return (win32gui.GetWindowText(hwnd) or "").strip()


def _window_rect(hwnd: int) -> WindowRect:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return WindowRect(left=left, top=top, right=right, bottom=bottom)


def foreground_window_handle() -> int | None:
    try:
        hwnd = win32gui.GetForegroundWindow()
        return hwnd if hwnd else None
    except Exception:
        return None


def active_window_title() -> str:
    hwnd = foreground_window_handle()
    return _window_text(hwnd) if hwnd else ""


def list_windows(limit: int = 50, visible_only: bool = True) -> list[WindowInfo]:
    foreground = foreground_window_handle()
    windows: list[WindowInfo] = []

    def _callback(hwnd: int, _extra: object) -> None:
        if len(windows) >= limit:
            return
        if visible_only and not win32gui.IsWindowVisible(hwnd):
            return
        title = _window_text(hwnd)
        if not title:
            return
        windows.append(
            WindowInfo(
                hwnd=hwnd,
                title=title,
                rect=_window_rect(hwnd),
                is_foreground=(foreground == hwnd),
            )
        )

    win32gui.EnumWindows(_callback, None)
    return windows


def _matches(title: str, title_contains: str = "", title_regex: str = "") -> bool:
    if title_contains and title_contains.lower() not in title.lower():
        return False
    if title_regex and not re.search(title_regex, title):
        return False
    return bool(title)


def find_windows(
    title_contains: str = "",
    title_regex: str = "",
    limit: int = 20,
    visible_only: bool = True,
) -> list[WindowInfo]:
    matched: list[WindowInfo] = []
    for win in list_windows(limit=max(limit * 3, limit), visible_only=visible_only):
        if _matches(win.title, title_contains=title_contains, title_regex=title_regex):
            matched.append(win)
        if len(matched) >= limit:
            break
    return matched


def choose_window(
    title_contains: str = "",
    title_regex: str = "",
    match_index: int = 0,
    visible_only: bool = True,
) -> WindowInfo:
    matches = find_windows(
        title_contains=title_contains,
        title_regex=title_regex,
        limit=max(match_index + 1, 10),
        visible_only=visible_only,
    )
    if not matches:
        raise RuntimeError("window not found")
    if match_index >= len(matches):
        raise RuntimeError(f"window match_index out of range: {match_index} >= {len(matches)}")
    return matches[match_index]


def focus_window(hwnd: int) -> None:
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    win32gui.SetForegroundWindow(hwnd)


def clamp_point_to_window(rect: WindowRect, x_ratio: float, y_ratio: float) -> tuple[int, int]:
    x_ratio = min(max(x_ratio, 0.0), 1.0)
    y_ratio = min(max(y_ratio, 0.0), 1.0)
    x = int(rect.left + rect.width * x_ratio)
    y = int(rect.top + rect.height * y_ratio)
    return x, y
