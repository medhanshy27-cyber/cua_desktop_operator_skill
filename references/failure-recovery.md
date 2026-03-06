# Failure Recovery

## First miss after a click

1. Stop issuing blind retries.
2. Call `desktop_observe`.
3. Check focus, window position, and whether the UI changed.

## Multiple similar windows

1. Call `desktop_find_window`.
2. Inspect candidate titles.
3. Re-run the action with `match_index`.

## Typing goes to the wrong place

1. `desktop_focus_window`
2. Validate the active window
3. Re-run text input

## UIA lookup returns nothing

1. Re-check the target window title.
2. Reduce `max_depth` and add a tighter selector.
3. Switch back to screenshot-driven relative clicks if needed.

## App still loading

1. Add `desktop_wait`
2. Re-observe
3. Continue only after the expected page or control appears
