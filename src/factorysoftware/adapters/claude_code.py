from __future__ import annotations

from pathlib import Path


class ClaudeCodeAdapter:
    name = "claude_code"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".claude").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {
            sid: project_root / ".claude" / "skills" / sid / "SKILL.md"
            for sid in skill_ids
        }

    def render(self, skill_id: str, content_md: str) -> str:
        description = f"Factory skill: {skill_id}"
        return f"---\nname: {skill_id}\ndescription: {description}\n---\n\n{content_md}"
