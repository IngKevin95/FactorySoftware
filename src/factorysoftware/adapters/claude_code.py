from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import (
    GUARD_SCRIPT,
    read_json_config,
    write_guard_script,
    write_json_config,
)


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

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        hooks_dir = project_root / ".claude" / "hooks"
        guard_path = hooks_dir / "gitflow-guard.sh"
        write_guard_script(guard_path, GUARD_SCRIPT)

        settings_path = project_root / ".claude" / "settings.json"
        settings = read_json_config(settings_path)

        settings.setdefault("hooks", {}).setdefault("PreToolUse", [])

        # Check for idempotency: only add if not already present
        guard_command = str(guard_path)
        existing_entry = next(
            (entry for entry in settings["hooks"]["PreToolUse"]
             if entry.get("matcher") == "Bash" and
             any(h.get("command") == guard_command for h in entry.get("hooks", []))),
            None
        )

        if not existing_entry:
            settings["hooks"]["PreToolUse"].append(
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": guard_command}],
                }
            )

        write_json_config(settings_path, settings)

        return [guard_path, settings_path]
