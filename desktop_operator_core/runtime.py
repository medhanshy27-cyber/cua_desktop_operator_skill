from __future__ import annotations

import os
import subprocess
import time
from typing import Any

import pyautogui
import pyperclip
from pydantic import ValidationError

from . import uia
from .artifacts import ArtifactManager
from .macros import MacroRegistry, default_macro_registry
from .models import (
    ActionSpec,
    ErrorInfo,
    ExecutionResult,
    ObservationResult,
    OperationResult,
    StepResult,
    ValidationCheck,
    ValidationResult,
)
from .windows import active_window_title, choose_window, clamp_point_to_window, find_windows, focus_window, list_windows


class DesktopRuntime:
    def __init__(
        self,
        *,
        pause: float = 0.15,
        default_wait_after: float = 0.25,
        failsafe: bool = True,
        artifact_manager: ArtifactManager | None = None,
        macro_registry: MacroRegistry | None = None,
    ):
        pyautogui.FAILSAFE = failsafe
        pyautogui.PAUSE = pause
        self.default_wait_after = default_wait_after
        self.artifacts = artifact_manager or ArtifactManager()
        self.macros = macro_registry or default_macro_registry()

    def observe(
        self,
        *,
        label: str = "observe",
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        max_windows: int = 30,
        include_window_crop: bool = True,
        include_uia: bool = False,
        uia_limit: int = 20,
        uia_depth: int = 1,
    ) -> ObservationResult:
        screenshot_path = self.artifacts.capture_screenshot(label)
        visible = list_windows(limit=max_windows)
        active_title = active_window_title()

        target_window = None
        if window_title_contains or window_title_regex:
            matches = find_windows(title_contains=window_title_contains, title_regex=window_title_regex, limit=max(match_index + 1, 5))
            target_window = matches[match_index] if len(matches) > match_index else None
        elif active_title:
            matches = find_windows(title_contains=active_title, limit=3)
            target_window = matches[0] if matches else None

        window_screenshot_path = None
        if include_window_crop and target_window:
            window_screenshot_path = str(self.artifacts.capture_screenshot(f"{label}_window", rect=target_window.rect))

        controls = []
        if include_uia and (window_title_contains or window_title_regex or active_title):
            try:
                controls = uia.query_controls(
                    window_title_contains=window_title_contains or active_title,
                    window_title_regex=window_title_regex,
                    match_index=match_index,
                    max_depth=uia_depth,
                    limit=uia_limit,
                )
            except Exception as exc:
                self.artifacts.log_event("uia_query_failed", {"label": label, "error": str(exc)})

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        state = {
            "timestamp": timestamp,
            "active_window": active_title,
            "visible_windows": [item.model_dump() for item in visible],
            "screenshot_path": str(screenshot_path),
            "window_screenshot_path": window_screenshot_path,
            "uia_controls": [item.model_dump() for item in controls],
        }
        state_path = self.artifacts.write_json(f"{label}_state", state)
        artifacts = self.artifacts.update_manifest(
            last_screenshot_path=str(screenshot_path),
            last_window_screenshot_path=str(window_screenshot_path or ""),
            last_state_path=str(state_path),
            log_path=str(self.artifacts.log_path.resolve()),
        )
        self.artifacts.log_event("observe", state)
        return ObservationResult(
            ok=True,
            summary=f"Captured screenshot with active window '{active_title or '<none>'}'.",
            timestamp=timestamp,
            active_window=active_title,
            visible_windows=visible,
            screenshot_path=str(screenshot_path),
            window_screenshot_path=window_screenshot_path,
            state_path=str(state_path),
            uia_controls=controls,
            artifacts={key: str(value) for key, value in artifacts.items() if value},
        )

    def get_last_artifacts(self) -> OperationResult:
        manifest = self.artifacts.get_last_artifacts()
        return OperationResult(
            ok=True,
            action="desktop_get_last_artifacts",
            summary="Loaded latest desktop operator artifacts.",
            data=manifest,
            artifacts={key: str(value) for key, value in manifest.items() if isinstance(value, str) and value},
        )

    def cleanup_artifacts(self) -> OperationResult:
        payload = self.artifacts.cleanup_session()
        return OperationResult(
            ok=True,
            action="desktop_cleanup_artifacts",
            summary="Cleared temporary desktop operator artifacts for the completed task.",
            data=payload,
        )

    def list_windows(self, *, limit: int = 30) -> OperationResult:
        windows = list_windows(limit=limit)
        return OperationResult(
            ok=True,
            action="desktop_list_windows",
            summary=f"Found {len(windows)} visible windows.",
            data={"windows": [item.model_dump() for item in windows]},
        )

    def find_window(self, *, title_contains: str = "", title_regex: str = "", limit: int = 10) -> OperationResult:
        windows = find_windows(title_contains=title_contains, title_regex=title_regex, limit=limit)
        summary = f"Matched {len(windows)} window(s)." if windows else "No matching windows found."
        return OperationResult(
            ok=bool(windows),
            action="desktop_find_window",
            summary=summary,
            data={"matches": [item.model_dump() for item in windows]},
            error=None if windows else self._error_info("not_found", "window not found", "Call desktop_list_windows or relax the title filter."),
        )

    def focus_window(self, *, title_contains: str = "", title_regex: str = "", match_index: int = 0) -> OperationResult:
        return self._execute_simple(
            action="desktop_focus_window",
            operation=lambda: self._focus_window_impl(title_contains=title_contains, title_regex=title_regex, match_index=match_index),
        )

    def launch_app(
        self,
        *,
        command: str = "",
        app: str = "",
        uri: str = "",
        working_directory: str = "",
        wait: float = 1.5,
    ) -> OperationResult:
        return self._execute_simple(
            action="desktop_launch_app",
            operation=lambda: self._launch_app_impl(command=command, app=app, uri=uri, working_directory=working_directory, wait=wait),
        )

    def click_absolute(self, *, x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0) -> OperationResult:
        return self._execute_simple(
            action="desktop_click_absolute",
            operation=lambda: self._click_absolute_impl(x=x, y=y, button=button, clicks=clicks, interval=interval),
        )

    def click_relative(
        self,
        *,
        title_contains: str = "",
        title_regex: str = "",
        match_index: int = 0,
        x_ratio: float = 0.5,
        y_ratio: float = 0.5,
        button: str = "left",
    ) -> OperationResult:
        return self._execute_simple(
            action="desktop_click_relative",
            operation=lambda: self._click_relative_impl(
                title_contains=title_contains,
                title_regex=title_regex,
                match_index=match_index,
                x_ratio=x_ratio,
                y_ratio=y_ratio,
                button=button,
            ),
        )

    def send_keys(self, *, keys: list[str], presses: int = 1, interval: float = 0.0) -> OperationResult:
        return self._execute_simple(
            action="desktop_send_keys",
            operation=lambda: self._send_keys_impl(keys=keys, presses=presses, interval=interval),
        )

    def type_text(self, *, text: str, interval: float = 0.0, press_enter: bool = False) -> OperationResult:
        return self._execute_simple(
            action="desktop_type_text",
            operation=lambda: self._type_text_impl(text=text, interval=interval, press_enter=press_enter),
        )

    def paste_text(self, *, text: str, select_all_first: bool = False, press_enter: bool = False) -> OperationResult:
        return self._execute_simple(
            action="desktop_paste_text",
            operation=lambda: self._paste_text_impl(text=text, select_all_first=select_all_first, press_enter=press_enter),
        )

    def scroll(self, *, clicks: int, x: int | None = None, y: int | None = None) -> OperationResult:
        return self._execute_simple(
            action="desktop_scroll",
            operation=lambda: self._scroll_impl(clicks=clicks, x=x, y=y),
        )

    def wait(self, *, seconds: float) -> OperationResult:
        return self._execute_simple(
            action="desktop_wait",
            operation=lambda: self._wait_impl(seconds=seconds),
        )

    def uia_query(
        self,
        *,
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        control_text: str = "",
        auto_id: str = "",
        control_type: str = "",
        max_depth: int = 2,
        limit: int = 20,
    ) -> OperationResult:
        return self._execute_simple(
            action="desktop_uia_query",
            operation=lambda: {
                "controls": [
                    item.model_dump()
                    for item in uia.query_controls(
                        window_title_contains=window_title_contains,
                        window_title_regex=window_title_regex,
                        match_index=match_index,
                        control_text=control_text,
                        auto_id=auto_id,
                        control_type=control_type,
                        max_depth=max_depth,
                        limit=limit,
                    )
                ]
            },
        )

    def uia_click(
        self,
        *,
        window_title_contains: str = "",
        window_title_regex: str = "",
        match_index: int = 0,
        control_text: str = "",
        auto_id: str = "",
        control_type: str = "",
        timeout: float = 10.0,
    ) -> OperationResult:
        return self._execute_simple(
            action="desktop_uia_click",
            operation=lambda: {
                "control": uia.click_control(
                    window_title_contains=window_title_contains,
                    window_title_regex=window_title_regex,
                    match_index=match_index,
                    control_text=control_text,
                    auto_id=auto_id,
                    control_type=control_type,
                    timeout=timeout,
                ).model_dump()
            },
        )

    def uia_type(
        self,
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
    ) -> OperationResult:
        return self._execute_simple(
            action="desktop_uia_type",
            operation=lambda: {
                "control": uia.type_into_control(
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
            },
        )

    def validate_state(
        self,
        *,
        active_window_contains: str = "",
        active_window_regex: str = "",
        visible_window_contains: str = "",
        uia_window_title_contains: str = "",
        uia_control_text: str = "",
        uia_auto_id: str = "",
        uia_control_type: str = "",
    ) -> ValidationResult:
        checks: list[ValidationCheck] = []
        current_active = active_window_title()
        if active_window_contains:
            checks.append(
                ValidationCheck(
                    name="active_window_contains",
                    passed=(active_window_contains.lower() in current_active.lower()),
                    details=f"active window: {current_active}",
                )
            )
        if active_window_regex:
            import re

            checks.append(
                ValidationCheck(
                    name="active_window_regex",
                    passed=bool(re.search(active_window_regex, current_active)),
                    details=f"active window: {current_active}",
                )
            )
        if visible_window_contains:
            titles = [item.title for item in list_windows(limit=30)]
            checks.append(
                ValidationCheck(
                    name="visible_window_contains",
                    passed=any(visible_window_contains.lower() in title.lower() for title in titles),
                    details=f"visible windows checked: {len(titles)}",
                )
            )
        if uia_window_title_contains and any([uia_control_text, uia_auto_id, uia_control_type]):
            try:
                controls = uia.query_controls(
                    window_title_contains=uia_window_title_contains,
                    control_text=uia_control_text,
                    auto_id=uia_auto_id,
                    control_type=uia_control_type,
                    max_depth=2,
                    limit=5,
                )
                checks.append(
                    ValidationCheck(
                        name="uia_control_exists",
                        passed=bool(controls),
                        details=f"matched controls: {len(controls)}",
                    )
                )
            except Exception as exc:
                checks.append(
                    ValidationCheck(
                        name="uia_control_exists",
                        passed=False,
                        details=str(exc),
                    )
                )

        all_passed = all(check.passed for check in checks) if checks else False
        summary = "All validation checks passed." if all_passed else "One or more validation checks failed."
        self.artifacts.log_event("validate_state", {"checks": [check.model_dump() for check in checks]})
        return ValidationResult(ok=all_passed, summary=summary, checks=checks)

    def execute_actions(self, actions: list[dict[str, Any] | ActionSpec], *, dry_run: bool = False, label: str = "action_run") -> ExecutionResult:
        steps: list[StepResult] = []
        for raw in actions:
            try:
                spec = raw if isinstance(raw, ActionSpec) else ActionSpec.model_validate(raw)
            except ValidationError as exc:
                error = self._error_info("validation_failed", str(exc), "Fix the action schema before running it again.")
                steps.append(
                    StepResult(
                        ok=False,
                        action="schema_validation",
                        summary="Action schema validation failed.",
                        error=error,
                        attempts=1,
                    )
                )
                return self._finish_execution(label=label, steps=steps)
            step = self._execute_action(spec=spec, dry_run=dry_run)
            steps.append(step)
            if not step.ok and spec.on_failure == "raise":
                break
        return self._finish_execution(label=label, steps=steps)

    def run_macro(self, *, macro_id: str, inputs: dict[str, Any] | None = None, dry_run: bool = False) -> ExecutionResult:
        try:
            definition, actions = self.macros.build_actions(macro_id, inputs or {})
            result = self.execute_actions(actions, dry_run=dry_run, label=f"macro_{macro_id}")
            result.summary = f"Macro '{definition.id}' {'validated' if dry_run else 'executed'}: {result.summary}"
            return result
        except Exception as exc:
            error = self._error_info(self._classify_error(exc), str(exc), "Check the macro inputs or fall back to primitive tools.")
            failure = StepResult(
                ok=False,
                action="desktop_run_macro",
                summary=f"Macro '{macro_id}' failed.",
                error=error,
                attempts=1,
            )
            return self._finish_execution(label=f"macro_{macro_id}", steps=[failure])

    def macro_catalog(self) -> list[dict[str, Any]]:
        return [definition.model_dump() for definition in self.macros.catalog()]

    def _finish_execution(self, *, label: str, steps: list[StepResult]) -> ExecutionResult:
        ok = all(step.ok for step in steps) if steps else False
        payload = {"label": label, "ok": ok, "steps": [step.model_dump() for step in steps]}
        execution_path = self.artifacts.write_json(label, payload)
        manifest = self.artifacts.update_manifest(
            last_execution_path=str(execution_path),
            log_path=str(self.artifacts.log_path.resolve()),
        )
        self.artifacts.log_event("execution", payload)
        success_count = sum(1 for step in steps if step.ok)
        summary = f"{success_count}/{len(steps)} steps succeeded." if steps else "No steps executed."
        return ExecutionResult(ok=ok, summary=summary, steps=steps, artifacts={key: str(value) for key, value in manifest.items() if value})

    def _execute_action(self, *, spec: ActionSpec, dry_run: bool) -> StepResult:
        delay = spec.retry_policy.delay_seconds
        for attempt in range(1, spec.retry_policy.attempts + 1):
            try:
                if dry_run:
                    data = {
                        "target": spec.target,
                        "args": spec.args,
                        "expectation": spec.expectation,
                    }
                    return StepResult(
                        ok=True,
                        action=spec.action,
                        summary="Action validated in dry-run mode.",
                        data=data,
                        attempts=attempt,
                    )
                payload = self._dispatch_action(spec)
                if spec.expectation:
                    validation = self.validate_state(**spec.expectation)
                    payload["validation"] = validation.model_dump()
                    if not validation.ok:
                        raise RuntimeError(validation.summary)
                time.sleep(spec.wait_after if spec.wait_after >= 0 else self.default_wait_after)
                return StepResult(
                    ok=True,
                    action=spec.action,
                    summary=f"Action '{spec.action}' completed.",
                    data=payload,
                    attempts=attempt,
                )
            except Exception as exc:
                kind = self._classify_error(exc)
                error = self._error_info(kind, str(exc), self._suggestion(kind, spec.action))
                artifacts = self._record_failure(spec.action, error.message)
                if attempt < spec.retry_policy.attempts:
                    time.sleep(delay)
                    delay = delay * spec.retry_policy.backoff_multiplier if delay else 0.0
                    continue
                return StepResult(
                    ok=False,
                    action=spec.action,
                    summary=f"Action '{spec.action}' failed.",
                    error=error,
                    artifacts=artifacts,
                    attempts=attempt,
                )
        raise RuntimeError("unreachable")

    def _dispatch_action(self, spec: ActionSpec) -> dict[str, Any]:
        merged = dict(spec.target)
        merged.update(spec.args)
        action = spec.action
        if action == "launch_app":
            return self._unwrap(self.launch_app(**merged))
        if action == "focus_window":
            return self._unwrap(self.focus_window(**merged))
        if action == "click_absolute":
            return self._unwrap(self.click_absolute(**merged))
        if action == "click_relative":
            return self._unwrap(self.click_relative(**merged))
        if action == "send_keys":
            return self._unwrap(self.send_keys(**merged))
        if action == "type_text":
            return self._unwrap(self.type_text(**merged))
        if action == "paste_text":
            return self._unwrap(self.paste_text(**merged))
        if action == "scroll":
            return self._unwrap(self.scroll(**merged))
        if action == "wait":
            return self._unwrap(self.wait(**merged))
        if action == "uia_click":
            return self._unwrap(self.uia_click(**merged))
        if action == "uia_type":
            return self._unwrap(self.uia_type(**merged))
        raise RuntimeError(f"unsupported action: {action}")

    def _unwrap(self, result: OperationResult) -> dict[str, Any]:
        if not result.ok:
            raise RuntimeError(result.error.message if result.error else result.summary)
        return result.data

    def _execute_simple(self, *, action: str, operation: Any) -> OperationResult:
        try:
            data = operation() or {}
            self.artifacts.log_event(action, data)
            return OperationResult(ok=True, action=action, summary=f"{action} succeeded.", data=data)
        except Exception as exc:
            kind = self._classify_error(exc)
            error = self._error_info(kind, str(exc), self._suggestion(kind, action))
            artifacts = self._record_failure(action, error.message)
            self.artifacts.log_event(f"{action}_failed", {"error": error.model_dump()})
            return OperationResult(ok=False, action=action, summary=f"{action} failed.", error=error, artifacts=artifacts)

    def _focus_window_impl(self, *, title_contains: str = "", title_regex: str = "", match_index: int = 0) -> dict[str, Any]:
        target = choose_window(title_contains=title_contains, title_regex=title_regex, match_index=match_index)
        focus_window(target.hwnd)
        return {"window": target.model_dump()}

    def _launch_app_impl(self, *, command: str = "", app: str = "", uri: str = "", working_directory: str = "", wait: float = 1.5) -> dict[str, Any]:
        if command:
            subprocess.Popen(command, shell=True, cwd=working_directory or None)
        elif uri:
            os.startfile(uri)  # type: ignore[attr-defined]
        elif app:
            subprocess.Popen([app], cwd=working_directory or None)
        else:
            raise RuntimeError("launch requires command, app, or uri")
        if wait > 0:
            time.sleep(wait)
        return {"command": command, "app": app, "uri": uri, "working_directory": working_directory}

    def _click_absolute_impl(self, *, x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0) -> dict[str, Any]:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
        return {"x": x, "y": y, "button": button, "clicks": clicks}

    def _click_relative_impl(
        self,
        *,
        title_contains: str = "",
        title_regex: str = "",
        match_index: int = 0,
        x_ratio: float = 0.5,
        y_ratio: float = 0.5,
        button: str = "left",
    ) -> dict[str, Any]:
        target = choose_window(title_contains=title_contains, title_regex=title_regex, match_index=match_index)
        focus_window(target.hwnd)
        x, y = clamp_point_to_window(target.rect, x_ratio=x_ratio, y_ratio=y_ratio)
        pyautogui.click(x=x, y=y, button=button)
        return {"window": target.model_dump(), "x": x, "y": y, "button": button}

    def _send_keys_impl(self, *, keys: list[str], presses: int = 1, interval: float = 0.0) -> dict[str, Any]:
        if not keys:
            raise RuntimeError("keys cannot be empty")
        if len(keys) == 1:
            for _ in range(presses):
                pyautogui.press(keys[0])
                if interval > 0:
                    time.sleep(interval)
        else:
            for _ in range(presses):
                pyautogui.hotkey(*keys)
                if interval > 0:
                    time.sleep(interval)
        return {"keys": keys, "presses": presses}

    def _type_text_impl(self, *, text: str, interval: float = 0.0, press_enter: bool = False) -> dict[str, Any]:
        pyautogui.write(text, interval=interval)
        if press_enter:
            pyautogui.press("enter")
        return {"characters": len(text), "press_enter": press_enter}

    def _paste_text_impl(self, *, text: str, select_all_first: bool = False, press_enter: bool = False) -> dict[str, Any]:
        previous_clipboard = None
        clipboard_available = False
        try:
            previous_clipboard = pyperclip.paste()
            clipboard_available = True
        except Exception:
            previous_clipboard = None
        pyperclip.copy(text)
        try:
            if select_all_first:
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            if press_enter:
                pyautogui.press("enter")
        finally:
            if clipboard_available:
                try:
                    pyperclip.copy(previous_clipboard or "")
                except Exception:
                    pass
        return {"characters": len(text), "press_enter": press_enter, "select_all_first": select_all_first}

    def _scroll_impl(self, *, clicks: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        pyautogui.scroll(clicks, x=x, y=y)
        return {"clicks": clicks, "x": x, "y": y}

    def _wait_impl(self, *, seconds: float) -> dict[str, Any]:
        time.sleep(seconds)
        return {"seconds": seconds}

    def _record_failure(self, action: str, error_message: str) -> dict[str, str]:
        failure_path = self.artifacts.capture_screenshot(f"{action}_failure")
        manifest = self.artifacts.update_manifest(
            last_failure_screenshot_path=str(failure_path),
            log_path=str(self.artifacts.log_path.resolve()),
        )
        self.artifacts.log_event("failure_screenshot", {"action": action, "error": error_message, "path": str(failure_path)})
        return {
            "failure_screenshot_path": str(failure_path),
            "log_path": str(manifest.get("log_path", "")),
        }

    def _classify_error(self, exc: Exception) -> str:
        message = str(exc).lower()
        if "not found" in message:
            return "not_found"
        if "out of range" in message or "multiple" in message:
            return "ambiguous"
        if "timeout" in message or "timed out" in message:
            return "app_not_ready"
        if "validation" in message:
            return "validation_failed"
        if "focus" in message or "foreground" in message:
            return "action_blocked"
        return "runtime_error"

    def _suggestion(self, kind: str, action: str) -> str:
        suggestions = {
            "not_found": "Call desktop_observe or desktop_list_windows, then retry with a narrower selector.",
            "ambiguous": "Use desktop_find_window first and pass match_index explicitly.",
            "app_not_ready": "Add desktop_wait or increase the timeout before retrying.",
            "validation_failed": "Observe again and update the expectation or target window.",
            "action_blocked": "Refocus the target window before sending input.",
            "runtime_error": f"Retry {action} with simpler parameters or fall back to a macro.",
        }
        return suggestions.get(kind, suggestions["runtime_error"])

    def _error_info(self, kind: str, message: str, suggestion: str) -> ErrorInfo:
        return ErrorInfo(kind=kind, message=message, suggestion=suggestion)
