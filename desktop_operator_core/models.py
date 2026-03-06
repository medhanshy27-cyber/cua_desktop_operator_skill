from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempts: int = Field(default=1, ge=1, le=10, description="Max retry attempts.")
    delay_seconds: float = Field(default=0.0, ge=0.0, le=30.0, description="Delay before retry.")
    backoff_multiplier: float = Field(default=1.0, ge=1.0, le=5.0, description="Per-retry delay multiplier.")


class ActionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(description="Primitive runtime action name.")
    target: dict[str, Any] = Field(default_factory=dict, description="Target selectors such as window title filters.")
    args: dict[str, Any] = Field(default_factory=dict, description="Action-specific arguments.")
    wait_after: float = Field(default=0.2, ge=0.0, le=120.0, description="Seconds to wait after success.")
    timeout: float = Field(default=10.0, gt=0.0, le=300.0, description="Per-step timeout budget.")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    on_failure: Literal["raise", "continue"] = Field(default="raise")
    expectation: dict[str, Any] = Field(default_factory=dict, description="Optional validation checks after the action.")


class ErrorInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    message: str
    suggestion: str


class WindowRect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


class WindowInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hwnd: int
    title: str
    rect: WindowRect
    is_foreground: bool = False


class ControlInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_type: str
    title: str
    automation_id: str
    class_name: str
    depth: int
    rect: WindowRect | None = None


class OperationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    action: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: ErrorInfo | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)


class StepResult(OperationResult):
    model_config = ConfigDict(extra="forbid")

    attempts: int = 1


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    summary: str
    steps: list[StepResult] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class ObservationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    summary: str
    timestamp: str
    active_window: str
    visible_windows: list[WindowInfo] = Field(default_factory=list)
    screenshot_path: str
    window_screenshot_path: str | None = None
    state_path: str
    uia_controls: list[ControlInfo] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class ValidationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    details: str


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    summary: str
    checks: list[ValidationCheck] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class MacroDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    intent: str
    preconditions: list[str] = Field(default_factory=list)
    inputs: dict[str, str] = Field(default_factory=dict)
    postconditions: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
