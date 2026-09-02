from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import (
    GUARD_SCRIPT,
    is_role_skill,
    read_json_config,
    remove_hook_entry,
    role_description,
    write_guard_script,
    write_json_config,
    write_or_remove_json_config,
)

# confidence: verified 2026-08-19 via web search against official Antigravity
# docs (antigravity.google/docs/hooks, antigravity.google/docs/cli/plugins)
# and the "Authoring Google Antigravity Skills" codelab
# (codelabs.developers.google.com/getting-started-with-antigravity-skills),
# corroborated by an independent tester (atamel.dev). Confirmed:
#   - Skills layout: <project-root>/.agents/skills/<skill-name>/SKILL.md
#     (folder + SKILL.md, YAML frontmatter with name/description) — matches
#     the brief's best-effort grounding from the sibling installer script.
#   - hooks.json lives at .agents/hooks.json, but its real schema differs
#     from the brief's proposed "preExec" shape. The confirmed schema is
#     {"<hook-name>": {"PreToolUse": [{"matcher": "run_command",
#     "hooks": [{"type": "command", "command": ..., "timeout": ...}]}]}}.
#     "run_command" is Antigravity's shell-exec tool, the analog of Claude
#     Code's "Bash" tool matcher. Implementation below uses this confirmed
#     schema instead of the brief's proposal.

class AntigravityAdapter:
    name = "antigravity"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".agents").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {
            sid: project_root / ".agents" / "skills" / sid / "SKILL.md"
            for sid in skill_ids
        }

    def render(self, skill_id: str, content_md: str) -> str:
        if is_role_skill(skill_id):
            # Sin schema de subagente nativo verificado para Antigravity (ver
            # comentario de cabecera): se instala como skill normal, con nota
            # de que las reglas del rol se aplican manualmente por tarea.
            return (
                f"---\nname: {skill_id}\ndescription: {role_description(content_md)}\n---\n\n"
                "(Definición de rol — ver `content/roles/*.md`. Sin subagente nativo separado en este "
                "host: aplicá estas reglas manualmente a cada tarea con este rol.)\n\n"
                f"{content_md}"
            )
        description = f"Factory skill: {skill_id}"
        return f"---\nname: {skill_id}\ndescription: {description}\n---\n\n{content_md}"

    def _guard_path(self, project_root: Path) -> Path:
        return project_root / ".agents" / "gitflow-guard.sh"

    def _hooks_json_path(self, project_root: Path) -> Path:
        return project_root / ".agents" / "hooks.json"

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        guard_path = self._guard_path(project_root)
        write_guard_script(guard_path, GUARD_SCRIPT)

        hooks_json_path = self._hooks_json_path(project_root)
        hooks_config = read_json_config(hooks_json_path)

        pretooluse = hooks_config.setdefault("gitflow-guard", {}).setdefault("PreToolUse", [])

        guard_command = str(guard_path)
        existing_entry = next(
            (entry for entry in pretooluse
             if entry.get("matcher") == "run_command" and
             any(h.get("command") == guard_command for h in entry.get("hooks", []))),
            None
        )

        if not existing_entry:
            pretooluse.append(
                {
                    "matcher": "run_command",
                    "hooks": [{"type": "command", "command": guard_command}],
                }
            )

        write_json_config(hooks_json_path, hooks_config)

        return [guard_path, hooks_json_path]

    def uninstall_gitflow_hook(self, project_root: Path) -> None:
        """Deshacer install_gitflow_hook sin pisar configuración ajena.

        Mismo criterio que en Claude Code: el script de guardia es 100% de la
        fábrica y se borra entero; ``hooks.json`` puede tener hooks del usuario
        y se le saca sólo la entrada propia.
        """
        guard_path = self._guard_path(project_root)
        guard_path.unlink(missing_ok=True)

        hooks_json_path = self._hooks_json_path(project_root)
        if not hooks_json_path.exists():
            return
        hooks_config = read_json_config(hooks_json_path)
        remove_hook_entry(
            hooks_config, "gitflow-guard", "PreToolUse", "run_command", str(guard_path)
        )
        write_or_remove_json_config(hooks_json_path, hooks_config)
