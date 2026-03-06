# Interaction Patterns

## Standard GUI loop

1. `desktop_observe`
2. Decide the next minimal action
3. Execute one action or macro
4. `desktop_validate_state` or `desktop_observe`
5. Repeat

## Window-first pattern

Use for desktop apps that may not be focused:

1. `desktop_find_window`
2. `desktop_focus_window`
3. Action tool
4. Validation

## Relative-click pattern

Use when a target is visually stable inside a known window:

1. `desktop_focus_window`
2. `desktop_click_relative`
3. `desktop_observe`

## Text-entry pattern

Use this order:

1. Focus the target window or control
2. `desktop_paste_text` for multilingual or long text
3. `desktop_type_text` for short plain text
4. Submit only after validation

## UIA-assisted pattern

Use when the app has reliable accessibility metadata:

1. `desktop_uia_query`
2. `desktop_uia_click` or `desktop_uia_type`
3. `desktop_validate_state`

## Macro-first pattern

Use for repeated flows:

1. Inspect macros with `desktop_run_macro("__catalog__", dry_run=true)`
2. Run the macro with small, explicit inputs
3. Observe again
