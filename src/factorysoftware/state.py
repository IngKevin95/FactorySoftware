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


_PHASE_ORDER = ["requirements", "architecture", "construction", "qa"]
_PHASE_LABELS = {
    "requirements": "Requerimientos",
    "architecture": "Arquitectura",
    "construction": "Construcción",
    "qa": "QA",
}


def _phase_status_icon(events: list[dict], phase: str) -> str:
    gates = [
        e for e in events
        if e["event_type"] == "phase_gate" and e["data"].get("phase") == phase
    ]
    if not gates:
        return "⚪ no iniciado"
    last = gates[-1]
    if last["data"].get("result") == "approved":
        return "✅ completo"
    return "🟡 en progreso"


def _epic_rows(events: list[dict], phase: str) -> list[tuple[str, str]]:
    steps = [
        e for e in events
        if e["event_type"] == "pipeline_step"
        and e["data"].get("phase") == phase
        and e["data"].get("scope")
        and e["data"]["scope"] != "all"
    ]
    latest_by_epic: dict[str, dict] = {}
    for e in steps:
        latest_by_epic[e["data"]["scope"]] = e["data"]
    rows = []
    for epic, data in sorted(latest_by_epic.items()):
        estado = "🟢 en progreso" if data.get("estado") == "iniciado" else "✅ completo"
        rows.append((epic, f"{data.get('step_id', '')} — {estado}"))
    return rows


def generate_board(project_root: Path) -> str:
    events = read_log(project_root)
    lines = ["# Tablero de la Fábrica (auto-generado, no editar a mano)", ""]
    for phase in _PHASE_ORDER:
        lines.append(f"### {_PHASE_LABELS[phase]}: {_phase_status_icon(events, phase)}")
    rows = []
    for phase in _PHASE_ORDER:
        rows.extend(_epic_rows(events, phase))
    if rows:
        lines.append("")
        lines.append("## Detalle por unidad")
        lines.append("")
        lines.append("| Unidad | Paso |")
        lines.append("|---|---|")
        for epic, detail in rows:
            lines.append(f"| {epic} | {detail} |")
    return "\n".join(lines) + "\n"


def write_board(project_root: Path) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    (_factory_dir(project_root) / "board.md").write_text(
        generate_board(project_root), encoding="utf-8"
    )


def query_step_status(
    project_root: Path, phase: str, step_id: str, fan_out_index: int | None = None
) -> str:
    events = [
        e for e in read_log(project_root)
        if e["event_type"] == "pipeline_step"
        and e["data"].get("phase") == phase
        and e["data"].get("step_id") == step_id
    ]
    if fan_out_index is not None:
        matching = [e for e in events if e["data"].get("fan_out_index") == fan_out_index]
        if not matching:
            return "pendiente"
        return "completado" if matching[-1]["data"].get("estado") == "completado" else "pendiente"

    if not events:
        return "pendiente"
    latest_by_index: dict = {}
    for e in events:
        latest_by_index[e["data"].get("fan_out_index")] = e
    all_done = all(e["data"].get("estado") == "completado" for e in latest_by_index.values())
    return "completado" if all_done else "pendiente"


def compute_metrics(project_root: Path) -> dict:
    events = read_log(project_root)
    invocations: dict[str, int] = {}
    for e in events:
        if e["event_type"] != "pipeline_step":
            continue
        phase = e["data"].get("phase")
        step_id = e["data"].get("step_id")
        if not phase or not step_id:
            continue
        key = f"{phase}.{step_id}"
        invocations[key] = invocations.get(key, 0) + 1
    return {"skill_invocations": invocations}


def write_metrics(project_root: Path) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    (_factory_dir(project_root) / "metrics.json").write_text(
        json.dumps(compute_metrics(project_root), indent=2), encoding="utf-8"
    )
