from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote_plus


def resolve_project_root() -> Path:
    current = Path(__file__).resolve()
    candidates = [current.parent, *current.parents, Path.cwd()]
    for candidate in candidates:
        if (candidate / "desktop_operator_core").exists() and (candidate / "desktop_operator_mcp").exists():
            return candidate
    raise RuntimeError("Could not locate desktop operator project root.")


PROJECT_ROOT = resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from desktop_operator_core import ActionSpec, DesktopRuntime  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run desktop operator validation tasks.")
    parser.add_argument("--task", default="observe", choices=["observe", "notepad", "browser", "settings", "media", "chat", "all"])
    parser.add_argument("--text", default="Desktop operator validation: hello, world.")
    parser.add_argument("--query", default="desktop operator mcp")
    parser.add_argument("--shortcut-path", default="")
    parser.add_argument("--window-title", default="")
    parser.add_argument("--chat-message", default="Hello from desktop operator validation.")
    parser.add_argument("--chat-toggle-keys", default="")
    parser.add_argument("--chat-open-x-ratio", type=float, default=0.92)
    parser.add_argument("--chat-open-y-ratio", type=float, default=0.05)
    parser.add_argument("--play-x-ratio", type=float, default=-1.0)
    parser.add_argument("--play-y-ratio", type=float, default=-1.0)
    parser.add_argument("--keep-artifacts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def default_notepad_path() -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return Path(tempfile.gettempdir()).resolve() / "desktop-operator" / "verify" / f"verify_notepad_{stamp}.txt"


def run_observe(runtime: DesktopRuntime) -> dict:
    return {"observe": runtime.observe(label="verify_observe").model_dump()}


def run_notepad(runtime: DesktopRuntime, text: str, dry_run: bool) -> dict:
    save_path = default_notepad_path()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text("", encoding="utf-8")
    actions = [
        ActionSpec(
            action="launch_app",
            args={"command": f'cmd /c start "" notepad.exe "{save_path}"', "wait": 1.2},
            wait_after=1.0,
        ),
        ActionSpec(action="paste_text", args={"text": text, "select_all_first": True}, wait_after=0.4),
        ActionSpec(action="send_keys", args={"keys": ["ctrl", "s"]}, wait_after=1.0),
    ]
    result = runtime.execute_actions(actions, dry_run=dry_run, label="verify_notepad")
    observe = runtime.observe(label="verify_notepad_after", window_title_contains="Notepad")
    saved_text = save_path.read_text(encoding="utf-8", errors="ignore") if save_path.exists() else ""
    return {
        "execution": result.model_dump(),
        "observation": observe.model_dump(),
        "save_path": str(save_path),
        "saved_text": saved_text,
    }


def run_browser(runtime: DesktopRuntime, query: str, dry_run: bool) -> dict:
    uri = f"https://www.bing.com/search?q={quote_plus(query)}"
    actions = [ActionSpec(action="launch_app", args={"uri": uri, "wait": 2.0}, wait_after=1.0)]
    result = runtime.execute_actions(actions, dry_run=dry_run, label="verify_browser")
    observe = runtime.observe(label="verify_browser_after")
    return {"execution": result.model_dump(), "observation": observe.model_dump(), "uri": uri}


def run_settings(runtime: DesktopRuntime, dry_run: bool) -> dict:
    result = runtime.run_macro(macro_id="open_windows_settings", dry_run=dry_run).model_dump()
    observe = runtime.observe(label="verify_settings_after")
    return {"execution": result, "observation": observe.model_dump()}


def run_media(runtime: DesktopRuntime, shortcut_path: str, query: str, window_title: str, play_x_ratio: float, play_y_ratio: float, dry_run: bool) -> dict:
    if not shortcut_path or not window_title:
        raise RuntimeError("media task requires --shortcut-path and --window-title")
    actions: list[ActionSpec] = [
        ActionSpec(action="launch_app", args={"uri": shortcut_path, "wait": 2.0}, wait_after=1.0),
        ActionSpec(action="focus_window", target={"title_contains": window_title}, wait_after=0.4),
    ]
    _definition, macro_actions = runtime.macros.build_actions("search_box_submit", {"text": query})
    actions.extend(macro_actions)
    if play_x_ratio >= 0.0 and play_y_ratio >= 0.0:
        actions.append(
            ActionSpec(
                action="click_relative",
                target={"title_contains": window_title},
                args={"x_ratio": play_x_ratio, "y_ratio": play_y_ratio},
                wait_after=0.8,
            )
        )
    result = runtime.execute_actions(actions, dry_run=dry_run, label="verify_media")
    observe = runtime.observe(label="verify_media_after", window_title_contains=window_title)
    return {"execution": result.model_dump(), "observation": observe.model_dump()}


def run_chat(
    runtime: DesktopRuntime,
    window_title: str,
    chat_message: str,
    chat_toggle_keys: str,
    chat_open_x_ratio: float,
    chat_open_y_ratio: float,
    dry_run: bool,
) -> dict:
    if not window_title:
        raise RuntimeError("chat task requires --window-title")
    actions: list[ActionSpec] = [ActionSpec(action="focus_window", target={"title_contains": window_title}, wait_after=0.4)]
    if chat_toggle_keys:
        _definition, macro_actions = runtime.macros.build_actions("chat_panel_toggle", {"toggle_keys": chat_toggle_keys})
    else:
        _definition, macro_actions = runtime.macros.build_actions(
            "chat_panel_toggle",
            {"window_title_contains": window_title, "x_ratio": chat_open_x_ratio, "y_ratio": chat_open_y_ratio},
        )
    actions.extend(macro_actions)
    actions.append(ActionSpec(action="paste_text", args={"text": chat_message, "press_enter": True}, wait_after=0.8))
    result = runtime.execute_actions(actions, dry_run=dry_run, label="verify_chat")
    observe = runtime.observe(label="verify_chat_after", window_title_contains=window_title)
    return {"execution": result.model_dump(), "observation": observe.model_dump()}


def main() -> int:
    args = parse_args()
    runtime = DesktopRuntime()
    summary: dict[str, dict] = {}

    if args.task in {"observe", "all"}:
        summary["observe"] = run_observe(runtime)
    if args.task in {"notepad", "all"}:
        summary["notepad"] = run_notepad(runtime, text=args.text, dry_run=args.dry_run)
    if args.task in {"browser", "all"}:
        summary["browser"] = run_browser(runtime, query=args.query, dry_run=args.dry_run)
    if args.task in {"settings", "all"}:
        summary["settings"] = run_settings(runtime, dry_run=args.dry_run)
    if args.task in {"media", "all"} and args.shortcut_path:
        summary["media"] = run_media(
            runtime,
            shortcut_path=args.shortcut_path,
            query=args.query,
            window_title=args.window_title,
            play_x_ratio=args.play_x_ratio,
            play_y_ratio=args.play_y_ratio,
            dry_run=args.dry_run,
        )
    if args.task in {"chat", "all"} and args.window_title:
        summary["chat"] = run_chat(
            runtime,
            window_title=args.window_title,
            chat_message=args.chat_message,
            chat_toggle_keys=args.chat_toggle_keys,
            chat_open_x_ratio=args.chat_open_x_ratio,
            chat_open_y_ratio=args.chat_open_y_ratio,
            dry_run=args.dry_run,
        )

    if not args.keep_artifacts:
        summary["cleanup"] = runtime.cleanup_artifacts().model_dump()

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
