from __future__ import annotations

from typing import Any, Callable

from .models import ActionSpec, MacroDefinition


MacroBuilder = Callable[[dict[str, Any]], list[ActionSpec]]


def _required(inputs: dict[str, Any], name: str) -> Any:
    if name not in inputs or inputs[name] in {"", None}:
        raise RuntimeError(f"macro input is required: {name}")
    return inputs[name]


def _keys(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        if "+" in value:
            return [item.strip() for item in value.split("+") if item.strip()]
        return [value]
    raise RuntimeError("invalid key specification")


class MacroRegistry:
    def __init__(self):
        self._definitions: dict[str, MacroDefinition] = {}
        self._builders: dict[str, MacroBuilder] = {}

    def register(self, definition: MacroDefinition, builder: MacroBuilder) -> None:
        self._definitions[definition.id] = definition
        self._builders[definition.id] = builder

    def get(self, macro_id: str) -> MacroDefinition:
        if macro_id not in self._definitions:
            raise RuntimeError(f"unknown macro: {macro_id}")
        return self._definitions[macro_id]

    def build_actions(self, macro_id: str, inputs: dict[str, Any] | None = None) -> tuple[MacroDefinition, list[ActionSpec]]:
        definition = self.get(macro_id)
        builder = self._builders[macro_id]
        return definition, builder(inputs or {})

    def catalog(self) -> list[MacroDefinition]:
        return [self._definitions[key] for key in sorted(self._definitions)]


def default_macro_registry() -> MacroRegistry:
    registry = MacroRegistry()

    registry.register(
        MacroDefinition(
            id="app_launch",
            category="app launch macros",
            intent="Launch an app or URI with a single reusable wrapper.",
            inputs={"command": "Shell command", "app": "Executable path", "uri": "URI or file path"},
            postconditions=["Target application is open or launching."],
            failure_modes=["Command missing", "OS launch failure"],
        ),
        lambda inputs: [
            ActionSpec(
                action="launch_app",
                args={
                    "command": str(inputs.get("command", "")),
                    "app": str(inputs.get("app", "")),
                    "uri": str(inputs.get("uri", "")),
                    "working_directory": str(inputs.get("working_directory", "")),
                    "wait": float(inputs.get("wait", 1.5)),
                },
                wait_after=float(inputs.get("wait_after", 0.6)),
            )
        ],
    )

    registry.register(
        MacroDefinition(
            id="desktop_shortcut_launch",
            category="app launch macros",
            intent="Open a desktop shortcut or file path.",
            preconditions=["Shortcut path exists on disk."],
            inputs={"shortcut_path": "Full path to .lnk or executable"},
            postconditions=["The target app begins launching."],
            failure_modes=["Shortcut missing", "Shell launch failure"],
        ),
        lambda inputs: [
            ActionSpec(
                action="launch_app",
                args={"uri": str(_required(inputs, "shortcut_path")), "wait": float(inputs.get("wait", 1.5))},
                wait_after=float(inputs.get("wait_after", 0.8)),
            )
        ],
    )

    registry.register(
        MacroDefinition(
            id="search_box_submit",
            category="search box macros",
            intent="Focus a search box, paste text, and optionally submit.",
            inputs={
                "text": "Query text",
                "focus_keys": "Hotkey list or Ctrl+F style string",
                "press_enter": "Whether to submit after paste",
            },
            postconditions=["Search text is present in the search box."],
            failure_modes=["Focus hotkey unsupported", "Input focus lost"],
        ),
        lambda inputs: [
            ActionSpec(action="send_keys", args={"keys": _keys(inputs.get("focus_keys"), ["ctrl", "f"])}),
            ActionSpec(
                action="paste_text",
                args={
                    "text": str(_required(inputs, "text")),
                    "press_enter": bool(inputs.get("press_enter", True)),
                    "select_all_first": bool(inputs.get("select_all_first", False)),
                },
                wait_after=float(inputs.get("wait_after", 0.8)),
            ),
        ],
    )

    registry.register(
        MacroDefinition(
            id="chat_panel_toggle",
            category="chat panel macros",
            intent="Open or close a chat side panel using a hotkey or a window-relative click.",
            inputs={
                "toggle_keys": "Hotkey list or string",
                "window_title_contains": "Window title filter for relative click mode",
                "x_ratio": "Relative click x coordinate",
                "y_ratio": "Relative click y coordinate",
            },
            postconditions=["Chat panel visibility toggles."],
            failure_modes=["Hotkey unsupported", "Relative target window missing"],
        ),
        lambda inputs: (
            [
                ActionSpec(action="send_keys", args={"keys": _keys(inputs.get("toggle_keys"), ["ctrl", "l"])})
            ]
            if inputs.get("toggle_keys") or not inputs.get("window_title_contains")
            else [
                ActionSpec(
                    action="click_relative",
                    target={
                        "title_contains": str(_required(inputs, "window_title_contains")),
                        "title_regex": str(inputs.get("window_title_regex", "")),
                        "match_index": int(inputs.get("match_index", 0)),
                    },
                    args={
                        "x_ratio": float(inputs.get("x_ratio", 0.92)),
                        "y_ratio": float(inputs.get("y_ratio", 0.05)),
                        "button": str(inputs.get("button", "left")),
                    },
                    wait_after=float(inputs.get("wait_after", 0.6)),
                )
            ]
        ),
    )

    registry.register(
        MacroDefinition(
            id="media_play_pause",
            category="media player macros",
            intent="Toggle media playback using the standard play/pause shortcut.",
            inputs={"key": "Optional override key"},
            postconditions=["Playback toggles once."],
            failure_modes=["Target app not focused", "Shortcut unsupported"],
        ),
        lambda inputs: [ActionSpec(action="send_keys", args={"keys": _keys(inputs.get("key"), ["space"])})],
    )

    registry.register(
        MacroDefinition(
            id="browser_focus_address_bar",
            category="browser tab / address bar macros",
            intent="Move focus to the browser address bar.",
            postconditions=["Address bar receives keyboard focus."],
            failure_modes=["Target browser not focused"],
        ),
        lambda inputs: [ActionSpec(action="send_keys", args={"keys": _keys(inputs.get("keys"), ["ctrl", "l"])})],
    )

    registry.register(
        MacroDefinition(
            id="submit_or_confirm",
            category="confirm / submit / open settings macros",
            intent="Submit or confirm the current dialog or input field.",
            inputs={"keys": "Optional confirmation keys"},
            postconditions=["Current form or dialog is submitted."],
            failure_modes=["Focus missing", "App intercepts shortcut differently"],
        ),
        lambda inputs: [ActionSpec(action="send_keys", args={"keys": _keys(inputs.get("keys"), ["enter"])})],
    )

    registry.register(
        MacroDefinition(
            id="open_windows_settings",
            category="confirm / submit / open settings macros",
            intent="Open the Windows Settings app.",
            postconditions=["Windows Settings launches."],
            failure_modes=["Shell launch blocked"],
        ),
        lambda inputs: [ActionSpec(action="launch_app", args={"uri": "ms-settings:", "wait": float(inputs.get("wait", 1.5))})],
    )

    return registry
