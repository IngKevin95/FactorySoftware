from __future__ import annotations

from pathlib import Path


class CopilotAdapter:
    name = "copilot"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".github").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        target = project_root / ".github" / "copilot-instructions.md"
        return {sid: target for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return f"## {skill_id}\n\n{content_md}"
