from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import read_json_config, write_guard_script, write_json_config

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

_GUARD_SCRIPT = """\
#!/bin/sh
input=$(cat)
cmd=$(printf '%s' "$input" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)
case "$cmd" in
  *"git commit"*|*"git push"*)
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ "$branch" = "main" ] || [ "$branch" = "develop" ]; then
      echo "Bloqueado: commit/push directo a $branch prohibido por Git Flow. Usa una rama feature/*." >&2
      exit 2
    fi
    ;;
esac
exit 0
"""


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
        description = f"Factory skill: {skill_id}"
        return f"---\nname: {skill_id}\ndescription: {description}\n---\n\n{content_md}"

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        agents_dir = project_root / ".agents"
        guard_path = agents_dir / "gitflow-guard.sh"
        write_guard_script(guard_path, _GUARD_SCRIPT)

        hooks_json_path = agents_dir / "hooks.json"
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
