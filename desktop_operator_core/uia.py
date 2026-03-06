from __future__ import annotations

from collections import deque
from typing import Any

import pyautogui
from pywinauto import Application

from .models import ControlInfo, WindowRect
from .windows import choose_window


def _connect_window(title_contains: str = "", title_regex: str = "", match_index: int = 0):
    target = choose_window(title_contains=title_contains, title_regex=title_regex, match_index=match_index)
    app = Application(backend="uia").connect(handle=target.hwnd)
    return target, app.window(handle=target.hwnd)


def _control_rect(wrapper: Any) -> WindowRect | None:
    try:
        rect = wrapper.rectangle()
        return WindowRect(left=rect.left, top=rect.top, right=rect.right, bottom=rect.bottom)
    except Exception:
        return None


def _control_info(wrapper: Any, depth: int) -> ControlInfo:
    element = wrapper.element_info
    return ControlInfo(
        control_type=str(getattr(element, "control_type", "") or ""),
        title=str(wrapper.window_text() or ""),
        automation_id=str(getattr(element, "automation_id", "") or ""),
        class_name=str(getattr(element, "class_name", "") or ""),
        depth=depth,
        rect=_control_rect(wrapper),
    )


def _matches_selector(
    wrapper: Any,
    control_text: str = "",
    auto_id: str = "",
    control_type: str = "",
) -> bool:
    info = _control_info(wrapper, depth=0)
    if control_text and control_text.lower() not in info.title.lower():
        return False
    if auto_id and auto_id != info.automation_id:
        return False
    if control_type and control_type.lower() != info.control_type.lower():
        return False
    return any([control_text, auto_id, control_type]) or True


def query_controls(
    *,
    window_title_contains: str = "",
    window_title_regex: str = "",
    match_index: int = 0,
    control_text: str = "",
    auto_id: str = "",
    control_type: str = "",
    max_depth: int = 2,
    limit: int = 20,
) -> list[ControlInfo]:
    _target, window = _connect_window(
        title_contains=window_title_contains,
        title_regex=window_title_regex,
        match_index=match_index,
    )
    root = window.wrapper_object()
    queue: deque[tuple[Any, int]] = deque([(root, 0)])
    matches: list[ControlInfo] = []

    while queue and len(matches) < limit:
        wrapper, depth = queue.popleft()
        if depth > 0 and _matches_selector(wrapper, control_text=control_text, auto_id=auto_id, control_type=control_type):
            matches.append(_control_info(wrapper, depth=depth))
        if depth >= max_depth:
            continue
        try:
            children = wrapper.children()
        except Exception:
            children = []
        for child in children:
            queue.append((child, depth + 1))

    return matches


def click_control(
    *,
    window_title_contains: str = "",
    window_title_regex: str = "",
    match_index: int = 0,
    control_text: str = "",
    auto_id: str = "",
    control_type: str = "",
    timeout: float = 10.0,
) -> ControlInfo:
    _target, window = _connect_window(
        title_contains=window_title_contains,
        title_regex=window_title_regex,
        match_index=match_index,
    )
    selector = {}
    if control_text:
        selector["title_re"] = f".*{control_text}.*"
    if auto_id:
        selector["auto_id"] = auto_id
    if control_type:
        selector["control_type"] = control_type
    if not selector:
        raise RuntimeError("uia selector is required")
    ctrl = window.child_window(**selector)
    ctrl.wait("visible ready", timeout=timeout)
    ctrl.click_input()
    return _control_info(ctrl.wrapper_object(), depth=1)


def type_into_control(
    *,
    window_title_contains: str = "",
    window_title_regex: str = "",
    match_index: int = 0,
    control_text: str = "",
    auto_id: str = "",
    control_type: str = "",
    text: str = "",
    clear_first: bool = False,
    interval: float = 0.0,
    timeout: float = 10.0,
) -> ControlInfo:
    _target, window = _connect_window(
        title_contains=window_title_contains,
        title_regex=window_title_regex,
        match_index=match_index,
    )
    selector = {}
    if control_text:
        selector["title_re"] = f".*{control_text}.*"
    if auto_id:
        selector["auto_id"] = auto_id
    if control_type:
        selector["control_type"] = control_type
    if not selector:
        raise RuntimeError("uia selector is required")
    ctrl = window.child_window(**selector)
    ctrl.wait("visible ready", timeout=timeout)
    ctrl.click_input()
    if clear_first:
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")
    pyautogui.write(text, interval=interval)
    return _control_info(ctrl.wrapper_object(), depth=1)
