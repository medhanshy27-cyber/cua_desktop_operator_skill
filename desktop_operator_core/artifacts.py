from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pyautogui

from .models import WindowRect


def default_artifact_root() -> Path:
    override = os.environ.get("DESKTOP_OPERATOR_ARTIFACTS", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
    if local_appdata:
        return Path(local_appdata).expanduser().resolve() / "desktop-operator" / "artifacts"
    return Path(tempfile.gettempdir()).resolve() / "desktop-operator" / "artifacts"


class ArtifactManager:
    def __init__(self, root: Path | None = None):
        self.root = (root or default_artifact_root()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.session_id = ""
        self.session_root = self.root
        self.manifest_path = self.root / "last_artifacts.json"
        self.log_path = self.root / "execution.jsonl"
        self._start_session()

    def _stamp(self) -> str:
        return time.strftime("%Y%m%d_%H%M%S")

    def _safe_label(self, label: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in (label or "artifact"))
        return cleaned.strip("_") or "artifact"

    def _new_session_id(self) -> str:
        return f"{self._stamp()}_{uuid4().hex[:8]}"

    def _start_session(self, session_id: str | None = None) -> None:
        self.session_id = session_id or self._new_session_id()
        self.session_root = (self.root / self.session_id).resolve()
        self.session_root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.session_root / "last_artifacts.json"
        self.log_path = self.session_root / "execution.jsonl"

    def capture_screenshot(self, label: str, rect: WindowRect | None = None) -> Path:
        path = self.session_root / f"{self._safe_label(label)}_{self._stamp()}.png"
        image = pyautogui.screenshot()
        if rect and rect.width > 0 and rect.height > 0:
            crop_box = (
                max(0, rect.left),
                max(0, rect.top),
                max(0, rect.right),
                max(0, rect.bottom),
            )
            image = image.crop(crop_box)
        image.save(path)
        return path.resolve()

    def write_json(self, label: str, payload: dict[str, Any]) -> Path:
        path = self.session_root / f"{self._safe_label(label)}_{self._stamp()}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path.resolve()

    def log_event(self, event: str, payload: dict[str, Any]) -> Path:
        record = {"timestamp": self._stamp(), "event": event, "payload": payload}
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return self.log_path.resolve()

    def update_manifest(self, **paths: str) -> dict[str, Any]:
        manifest = self.get_last_artifacts()
        manifest.update(paths)
        manifest["updated_at"] = self._stamp()
        manifest["session_id"] = self.session_id
        manifest["session_root"] = str(self.session_root)
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    def get_last_artifacts(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {
                "updated_at": "",
                "session_id": self.session_id,
                "session_root": str(self.session_root),
                "log_path": str(self.log_path.resolve()),
            }
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def cleanup_session(self) -> dict[str, Any]:
        old_session_id = self.session_id
        old_session_root = self.session_root
        deleted_files = 0
        deleted_dirs = 0
        if old_session_root.exists():
            deleted_files = sum(1 for path in old_session_root.rglob("*") if path.is_file())
            deleted_dirs = sum(1 for path in old_session_root.rglob("*") if path.is_dir())
            shutil.rmtree(old_session_root, ignore_errors=False)
        self._start_session()
        return {
            "deleted_session_id": old_session_id,
            "deleted_session_root": str(old_session_root),
            "deleted_files": deleted_files,
            "deleted_directories": deleted_dirs,
            "new_session_id": self.session_id,
            "new_session_root": str(self.session_root),
        }
