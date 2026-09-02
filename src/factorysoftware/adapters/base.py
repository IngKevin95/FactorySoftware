from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]: ...

    def render(self, skill_id: str, content_md: str) -> str: ...


# Prefijo que marca un skill_id como "pack de rol" (content/roles/*.md, ver
# docs/CREDITS.md — adaptado de YarnovaSoft/.opencode/agents y de los agentes
# especializados por gate de DemoWhatsappAgent/.claude/agents/build). Los
# adapters que soportan subagentes nativos (Claude Code, OpenCode) instalan
# estos IDs en el directorio de agents del host en vez del de skills, así el
# host puede invocar/enrutar a ese rol como un agente propio y no como una
# skill más. Los adapters de archivo único (Codex, Copilot) no tienen ese
# concepto, así que no necesitan branch: el rol termina como una sección más
# del único archivo que ya escriben.
ROLE_PREFIX = "role-"


def is_role_skill(skill_id: str) -> bool:
    return skill_id.startswith(ROLE_PREFIX)


def role_name(skill_id: str) -> str:
    return skill_id[len(ROLE_PREFIX):]


def role_description(content_md: str) -> str:
    """Primera línea no vacía del body: por convención, la descripción corta del rol."""
    for line in content_md.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return content_md.strip()


# Guardia de Git Flow compartida por los adapters primarios (Claude Code y
# Antigravity). Es un badén de conveniencia, NO una frontera de seguridad:
# hace pattern-matching sobre el string "command" del payload JSON del hook, así
# que variantes como `git  commit` (dos espacios) o `cd sub && git push` lo
# esquivan. Sirve para evitar el commit distraído a main/develop, no para
# impedir a alguien que quiera saltárselo. También bloquea `git commit` en una
# rama que no siga la convención feat|fix|chore|docs|style|refactor|perf|test|
# build|ci|revert/<slug> (ver `content/construction.md`, paso `branch_setup`).
# Adaptado del patrón de gitflow-guard.sh de DemoWhatsappAgent/.claude (mismo
# usuario) — ver docs/CREDITS.md.
GUARD_SCRIPT = """\
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
    case "$cmd" in
      *"git commit"*)
        case "$branch" in
          feat/*|fix/*|chore/*|docs/*|style/*|refactor/*|perf/*|test/*|build/*|ci/*|revert/*) ;;
          *)
            echo "Bloqueado: rama '$branch' no sigue la convencion de nombres." >&2
            echo "Usa feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert/<slug>." >&2
            exit 2
            ;;
        esac
        ;;
    esac
    ;;
esac
exit 0
"""


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


def remove_hook_entry(
    config: dict[str, Any], outer: str, inner: str, matcher: str, command: str
) -> None:
    """Quitar in-place la entrada de hook que instaló la fábrica.

    ``outer``/``inner`` son las dos claves que anidan la lista de entradas
    (``hooks``/``PreToolUse`` en Claude Code, ``gitflow-guard``/``PreToolUse``
    en Antigravity). Se borra sólo la entrada cuyo matcher y comando coinciden
    exactamente con lo que escribió ``install_gitflow_hook``: todo lo demás del
    archivo queda intacto. Los dos contenedores se podan si quedan vacíos, así
    un archivo que sólo tenía el hook de la fábrica termina como ``{}`` y el
    llamador puede borrarlo entero.
    """
    container = config.get(outer)
    if not isinstance(container, dict):
        return
    entries = container.get(inner)
    if not isinstance(entries, list):
        return

    remaining = [e for e in entries if not _is_factory_entry(e, matcher, command)]
    if remaining:
        container[inner] = remaining
        return
    del container[inner]
    if not container:
        del config[outer]


def _is_factory_entry(entry: Any, matcher: str, command: str) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get("matcher") == matcher
        and any(
            isinstance(h, dict) and h.get("command") == command
            for h in entry.get("hooks", [])
        )
    )


def write_or_remove_json_config(config_path: Path, config: dict[str, Any]) -> None:
    """Escribir el config, o borrar el archivo si no quedó nada adentro."""
    if config:
        write_json_config(config_path, config)
    else:
        config_path.unlink(missing_ok=True)
