from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import is_role_skill, role_name


class CodexAdapter:
    name = "codex"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".codex").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        target = project_root / "AGENTS.md"
        return {sid: target for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        if is_role_skill(skill_id):
            return (
                f"## Rol: {role_name(skill_id)}\n\n"
                "(Definición de rol — ver `content/roles/*.md`. Este host no tiene subagentes nativos "
                "separados: aplicá estas reglas manualmente a cada tarea con este rol, no esperes que se "
                "despache solo.)\n\n"
                f"{content_md}"
            )
        return f"## {skill_id}\n\n{content_md}"
