# MCP Tool Catalog

## Observe

- `desktop_observe`
  - Capture a full screenshot.
  - Optionally include a cropped target window image and bounded UIA metadata.
  - Returns screenshot paths, active window, visible windows, and a JSON state artifact.

- `desktop_get_last_artifacts`
  - Load the latest screenshot, state, execution, and failure artifact paths.

- `desktop_cleanup_artifacts`
  - Remove task-scoped temporary screenshots, JSON state files, and logs after success.
  - Use this when the task is complete and the user did not ask to keep debug artifacts.

## Windows

- `desktop_list_windows`
  - Use when you need a quick inventory of visible windows.

- `desktop_find_window`
  - Use when a title filter can identify candidate windows before focusing or clicking.

- `desktop_focus_window`
  - Use before typing, pasting, or sending hotkeys to an app.

- `desktop_launch_app`
  - Launch a shell command, executable, URI, or shortcut path.

## Primitive actions

- `desktop_click_absolute`
  - Last resort for screen-coordinate clicks.

- `desktop_click_relative`
  - Preferred click method when the target stays in a stable position within a window.

- `desktop_send_keys`
  - Press a single key or a hotkey sequence.

- `desktop_type_text`
  - Type short plain text.

- `desktop_paste_text`
  - Paste clipboard-backed text. Use this for Chinese or long text.

- `desktop_scroll`
  - Scroll the focused area.

- `desktop_wait`
  - Explicit wait for UI loading.

## UIA tools

- `desktop_uia_query`
  - Bounded UIA enumeration with optional selectors.
  - Use for control discovery when the app exposes reliable accessibility metadata.

- `desktop_uia_click`
  - Click a UIA control by text, automation id, or control type.

- `desktop_uia_type`
  - Focus a UIA control and type into it.

## Workflow tools

- `desktop_run_macro`
  - Run a reusable macro or inspect the catalog with `macro_id="__catalog__"`.

- `desktop_validate_state`
  - Check whether a window or UIA control is present after an action.
