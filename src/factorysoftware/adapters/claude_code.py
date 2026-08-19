from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import (
    GUARD_SCRIPT,
    read_json_config,
    remove_hook_entry,
    write_guard_script,
    write_json_config,
    write_or_remove_json_config,
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

    def _guard_path(self, project_root: Path) -> Path:
        return project_root / ".claude" / "hooks" / "gitflow-guard.sh"

    def _settings_path(self, project_root: Path) -> Path:
        return project_root / ".claude" / "settings.json"

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        guard_path = self._guard_path(project_root)
        write_guard_script(guard_path, GUARD_SCRIPT)

        settings_path = self._settings_path(project_root)
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

    def uninstall_gitflow_hook(self, project_root: Path) -> None:
        """Deshacer install_gitflow_hook sin pisar configuración ajena.

        El script de guardia lo genera siempre la fábrica desde cero, así que
        se borra entero. ``settings.json``, en cambio, puede ser del usuario y
        la instalación se fusionó adentro: se le saca únicamente la entrada de
        la fábrica y se lo vuelve a escribir; sólo si no queda nada más se
        borra el archivo.
        """
        guard_path = self._guard_path(project_root)
        guard_path.unlink(missing_ok=True)

        settings_path = self._settings_path(project_root)
        if not settings_path.exists():
            return
        settings = read_json_config(settings_path)
        remove_hook_entry(settings, "hooks", "PreToolUse", "Bash", str(guard_path))
        write_or_remove_json_config(settings_path, settings)
