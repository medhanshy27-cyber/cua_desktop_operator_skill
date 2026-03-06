from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from desktop_operator_core import DesktopRuntime


RUNTIME = DesktopRuntime()


def _annotations(*, title: str, read_only: bool, destructive: bool, idempotent: bool, open_world: bool = False) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=open_world,
    )


def _normalize_keys(keys: list[str] | str) -> list[str]:
    if isinstance(keys, str):
        if "+" in keys:
            return [item.strip() for item in keys.split("+") if item.strip()]
        return [keys]
    return keys


def build_server() -> FastMCP:
    mcp = FastMCP(
        name="desktop-operator",
        instructions=(
            "Local Windows desktop automation tools. Use desktop_observe first, then decide the next small step, "
            "then call one or more desktop_* tools, and verify again."
        ),
        dependencies=["mcp", "pyautogui", "pywinauto", "pyperclip", "pydantic", "pywin32"],
    )

    @mcp.tool(
        name="desktop_observe",
        annotations=_annotations(title="Capture desktop state", read_only=True, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_observe(
        label: str = "observe",
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        max_windows: int = 30,
        include_window_crop: bool = True,
        include_uia: bool = False,
        uia_limit: int = 20,
        uia_depth: int = 1,
    ) -> dict[str, Any]:
        return RUNTIME.observe(
            label=label,
            window_title_contains=window_title_contains,
            window_title_regex=window_title_regex,
            match_index=match_index,
            max_windows=max_windows,
            include_window_crop=include_window_crop,
            include_uia=include_uia,
            uia_limit=uia_limit,
            uia_depth=uia_depth,
        ).model_dump()

    @mcp.tool(
        name="desktop_get_last_artifacts",
        annotations=_annotations(title="Read latest artifacts", read_only=True, destructive=False, idempotent=True),
        structured_output=True,
    )
    def desktop_get_last_artifacts() -> dict[str, Any]:
        return RUNTIME.get_last_artifacts().model_dump()

    @mcp.tool(
        name="desktop_cleanup_artifacts",
        annotations=_annotations(title="Clean temporary desktop artifacts", read_only=False, destructive=True, idempotent=False),
        structured_output=True,
    )
    def desktop_cleanup_artifacts() -> dict[str, Any]:
        return RUNTIME.cleanup_artifacts().model_dump()

    @mcp.tool(
        name="desktop_list_windows",
        annotations=_annotations(title="List visible windows", read_only=True, destructive=False, idempotent=True),
        structured_output=True,
    )
    def desktop_list_windows(limit: int = 30) -> dict[str, Any]:
        return RUNTIME.list_windows(limit=limit).model_dump()

    @mcp.tool(
        name="desktop_find_window",
        annotations=_annotations(title="Find matching windows", read_only=True, destructive=False, idempotent=True),
        structured_output=True,
    )
    def desktop_find_window(title_contains: str = "", title_regex: str = "", limit: int = 10) -> dict[str, Any]:
        return RUNTIME.find_window(title_contains=title_contains, title_regex=title_regex, limit=limit).model_dump()

    @mcp.tool(
        name="desktop_focus_window",
        annotations=_annotations(title="Focus a window", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_focus_window(title_contains: str = "", title_regex: str = "", match_index: int = 0) -> dict[str, Any]:
        return RUNTIME.focus_window(title_contains=title_contains, title_regex=title_regex, match_index=match_index).model_dump()

    @mcp.tool(
        name="desktop_launch_app",
        annotations=_annotations(title="Launch app or URI", read_only=False, destructive=False, idempotent=False, open_world=True),
        structured_output=True,
    )
    def desktop_launch_app(command: str = "", app: str = "", uri: str = "", working_directory: str = "", wait: float = 1.5) -> dict[str, Any]:
        return RUNTIME.launch_app(command=command, app=app, uri=uri, working_directory=working_directory, wait=wait).model_dump()

    @mcp.tool(
        name="desktop_click_absolute",
        annotations=_annotations(title="Click absolute screen point", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_click_absolute(x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0) -> dict[str, Any]:
        return RUNTIME.click_absolute(x=x, y=y, button=button, clicks=clicks, interval=interval).model_dump()

    @mcp.tool(
        name="desktop_click_relative",
        annotations=_annotations(title="Click point relative to a window", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_click_relative(
        title_contains: str = "",
        title_regex: str = "",
        match_index: int = 0,
        x_ratio: float = 0.5,
        y_ratio: float = 0.5,
        button: str = "left",
    ) -> dict[str, Any]:
        return RUNTIME.click_relative(
            title_contains=title_contains,
            title_regex=title_regex,
            match_index=match_index,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            button=button,
        ).model_dump()

    @mcp.tool(
        name="desktop_send_keys",
        annotations=_annotations(title="Send keyboard keys", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_send_keys(keys: list[str] | str, presses: int = 1, interval: float = 0.0) -> dict[str, Any]:
        return RUNTIME.send_keys(keys=_normalize_keys(keys), presses=presses, interval=interval).model_dump()

    @mcp.tool(
        name="desktop_type_text",
        annotations=_annotations(title="Type short text", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_type_text(text: str, interval: float = 0.0, press_enter: bool = False) -> dict[str, Any]:
        return RUNTIME.type_text(text=text, interval=interval, press_enter=press_enter).model_dump()

    @mcp.tool(
        name="desktop_paste_text",
        annotations=_annotations(title="Paste text through clipboard", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_paste_text(text: str, select_all_first: bool = False, press_enter: bool = False) -> dict[str, Any]:
        return RUNTIME.paste_text(text=text, select_all_first=select_all_first, press_enter=press_enter).model_dump()

    @mcp.tool(
        name="desktop_scroll",
        annotations=_annotations(title="Scroll focused area", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_scroll(clicks: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        return RUNTIME.scroll(clicks=clicks, x=x, y=y).model_dump()

    @mcp.tool(
        name="desktop_wait",
        annotations=_annotations(title="Wait for UI state", read_only=True, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_wait(seconds: float) -> dict[str, Any]:
        return RUNTIME.wait(seconds=seconds).model_dump()

    @mcp.tool(
        name="desktop_uia_query",
        annotations=_annotations(title="Query bounded UIA metadata", read_only=True, destructive=False, idempotent=True),
        structured_output=True,
    )
    def desktop_uia_query(
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        control_text: str = "",
        auto_id: str = "",
        control_type: str = "",
        max_depth: int = 2,
        limit: int = 20,
    ) -> dict[str, Any]:
        return RUNTIME.uia_query(
            window_title_contains=window_title_contains,
            window_title_regex=window_title_regex,
            match_index=match_index,
            control_text=control_text,
            auto_id=auto_id,
            control_type=control_type,
            max_depth=max_depth,
            limit=limit,
        ).model_dump()

    @mcp.tool(
        name="desktop_uia_click",
        annotations=_annotations(title="Click a UIA control", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_uia_click(
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        control_text: str = "",
        auto_id: str = "",
        control_type: str = "",
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        return RUNTIME.uia_click(
            window_title_contains=window_title_contains,
            window_title_regex=window_title_regex,
            match_index=match_index,
            control_text=control_text,
            auto_id=auto_id,
            control_type=control_type,
            timeout=timeout,
        ).model_dump()

    @mcp.tool(
        name="desktop_uia_type",
        annotations=_annotations(title="Type into a UIA control", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_uia_type(
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
    ) -> dict[str, Any]:
        return RUNTIME.uia_type(
            window_title_contains=window_title_contains,
            window_title_regex=window_title_regex,
            match_index=match_index,
            control_text=control_text,
            auto_id=auto_id,
            control_type=control_type,
            text=text,
            clear_first=clear_first,
            interval=interval,
            timeout=timeout,
        ).model_dump()

    @mcp.tool(
        name="desktop_run_macro",
        annotations=_annotations(title="Run a reusable desktop macro", read_only=False, destructive=False, idempotent=False),
        structured_output=True,
    )
    def desktop_run_macro(macro_id: str, inputs: dict[str, Any] | None = None, dry_run: bool = False) -> dict[str, Any]:
        if macro_id == "__catalog__":
            return {
                "ok": True,
                "summary": "Loaded macro catalog.",
                "macro_catalog": RUNTIME.macro_catalog(),
            }
        return RUNTIME.run_macro(macro_id=macro_id, inputs=inputs or {}, dry_run=dry_run).model_dump()

    @mcp.tool(
        name="desktop_validate_state",
        annotations=_annotations(title="Validate current UI state", read_only=True, destructive=False, idempotent=True),
        structured_output=True,
    )
    def desktop_validate_state(
        active_window_contains: str = "",
        active_window_regex: str = "",
        visible_window_contains: str = "",
        uia_window_title_contains: str = "",
        uia_control_text: str = "",
        uia_auto_id: str = "",
        uia_control_type: str = "",
    ) -> dict[str, Any]:
        return RUNTIME.validate_state(
            active_window_contains=active_window_contains,
            active_window_regex=active_window_regex,
            visible_window_contains=visible_window_contains,
            uia_window_title_contains=uia_window_title_contains,
            uia_control_text=uia_control_text,
            uia_auto_id=uia_auto_id,
            uia_control_type=uia_control_type,
        ).model_dump()

    return mcp


def main() -> None:
    build_server().run(transport="stdio")
