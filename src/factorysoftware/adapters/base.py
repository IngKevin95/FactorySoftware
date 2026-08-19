from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]: ...

    def render(self, skill_id: str, content_md: str) -> str: ...


def write_guard_script(guard_path: Path, script_text: str) -> None:
    """Write an executable shell script, creating parent directories as needed.

    Shared by adapters' install_gitflow_hook implementations — the guard
    script content and enclosing JSON config schema differ per provider,
    but writing the script file itself is identical.
    """
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    guard_path.write_text(script_text, encoding="utf-8")
    guard_path.chmod(0o755)


def read_json_config(config_path: Path) -> dict[str, Any]:
    """Read a JSON config file, returning {} if absent.

    Raises ValueError with a clear, actionable message on malformed JSON,
    rather than letting a raw json.JSONDecodeError propagate.
    """
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse {config_path}: malformed JSON. "
            f"Please fix or remove the file. Details: {e}"
        ) from e


def write_json_config(config_path: Path, config: dict[str, Any]) -> None:
    """Write a JSON config file, pretty-printed, creating parent directories as needed."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
