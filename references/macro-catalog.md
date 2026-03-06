# Macro Catalog

Use `desktop_run_macro` with `macro_id="__catalog__"` for the machine-readable version.

## Built-in macros

- `app_launch`
  - Category: app launch macros
  - Inputs: `command`, `app`, `uri`, optional `working_directory`, `wait`

- `desktop_shortcut_launch`
  - Category: app launch macros
  - Inputs: `shortcut_path`, optional `wait`

- `search_box_submit`
  - Category: search box macros
  - Inputs: `text`, optional `focus_keys`, `press_enter`, `select_all_first`

- `chat_panel_toggle`
  - Category: chat panel macros
  - Inputs:
    - hotkey mode: `toggle_keys`
    - relative-click mode: `window_title_contains`, `x_ratio`, `y_ratio`

- `media_play_pause`
  - Category: media player macros
  - Inputs: optional `key`

- `browser_focus_address_bar`
  - Category: browser tab / address bar macros
  - Inputs: optional `keys`

- `submit_or_confirm`
  - Category: confirm / submit / open settings macros
  - Inputs: optional `keys`

- `open_windows_settings`
  - Category: confirm / submit / open settings macros
  - Inputs: optional `wait`
