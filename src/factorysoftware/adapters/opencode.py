from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import is_role_skill, role_description, role_name


class OpenCodeAdapter:
    name = "opencode"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".opencode").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        paths = {}
        for sid in skill_ids:
            if is_role_skill(sid):
                paths[sid] = project_root / ".opencode" / "agents" / f"{role_name(sid)}.md"
            else:
                paths[sid] = project_root / "AGENTS.md"
        return paths

    def render(self, skill_id: str, content_md: str) -> str:
        if is_role_skill(skill_id):
            # Subagente nativo de OpenCode (ver YarnovaSoft/.opencode/agents,
            # docs/CREDITS.md): frontmatter description + mode: subagent.
            return (
                f"---\ndescription: {role_description(content_md)}\nmode: subagent\n---\n\n"
                f"{content_md}"
            )
        return f"## {skill_id}\n\n{content_md}"
