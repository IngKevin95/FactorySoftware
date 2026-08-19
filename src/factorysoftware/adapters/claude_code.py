from __future__ import annotations

import json
from pathlib import Path

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
        hooks_dir.mkdir(parents=True, exist_ok=True)
        guard_path = hooks_dir / "gitflow-guard.sh"
        guard_path.write_text(_GUARD_SCRIPT, encoding="utf-8")
        guard_path.chmod(0o755)

        settings_path = project_root / ".claude" / "settings.json"
        settings = {}
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse {settings_path}: malformed JSON. "
                    f"Please fix or remove the file. Details: {e}"
                ) from e

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

        settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

        return [guard_path, settings_path]
