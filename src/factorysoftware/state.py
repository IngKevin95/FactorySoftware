from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ManifestFile(BaseModel):
    path: str
    hash: str
    skill_id: str


class Manifest(BaseModel):
    version: str
    installed_at: str
    providers: list[str]
    files: list[ManifestFile]


def _factory_dir(project_root: Path) -> Path:
    return project_root / ".factory"


def _manifest_path(project_root: Path) -> Path:
    return _factory_dir(project_root) / "manifest.json"


def read_manifest(project_root: Path) -> Manifest | None:
    path = _manifest_path(project_root)
    if not path.exists():
        return None
    return Manifest.model_validate_json(path.read_text(encoding="utf-8"))


def write_manifest(project_root: Path, manifest: Manifest) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    _manifest_path(project_root).write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )


def _log_path(project_root: Path) -> Path:
    return _factory_dir(project_root) / "log.jsonl"


def append_log(project_root: Path, event_type: str, data: dict) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
    }
    with _log_path(project_root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(project_root: Path) -> list[dict]:
    path = _log_path(project_root)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
