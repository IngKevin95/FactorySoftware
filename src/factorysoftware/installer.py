from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.adapters.registry import ALL_ADAPTERS
from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map
from factorysoftware.state import Manifest, ManifestFile, compute_hash, read_manifest, write_manifest

_VERSION = "0.1.0"

# skill_id sintético con el que se registran en el manifest los archivos del
# hook de Git Flow. Lleva pegado el nombre del adapter que lo instaló
# (``_gitflow_hook:claude_code``) porque uninstall necesita saber a quién
# pedirle que lo desinstale: esos archivos no se pueden borrar a ciegas, el
# config JSON está fusionado con configuración del usuario.
_GITFLOW_SKILL_ID = "_gitflow_hook"


def _gitflow_skill_id(adapter: ProviderAdapter) -> str:
    return f"{_GITFLOW_SKILL_ID}:{adapter.name}"


def _gitflow_owner(skill_id: str) -> ProviderAdapter | None:
    """Adapter dueño de una entrada de hook del manifest, si la entrada lo es."""
    prefix = f"{_GITFLOW_SKILL_ID}:"
    if not skill_id.startswith(prefix):
        return None
    name = skill_id[len(prefix):]
    return next((a for a in ALL_ADAPTERS if a.name == name), None)


def _load_skill_map(content_dir: Path) -> dict[str, str]:
    """Parse every content file into a single combined skill map.

    Los IDs de skill ya vienen prefijados por fase (``requirements-prd``,
    ``architecture-adrs``, ...), así que las fases no colisionan entre sí.
    Combinarlas antes de escribir es lo que permite que un adapter de archivo
    único (Copilot, Codex, OpenCode) reciba todas las fases juntas en una sola
    escritura agrupada, en vez de una escritura por fase que pisa a la anterior.

    Un archivo de contenido malformado no aborta la corrida entera: se avisa por
    stderr y se sigue con los demás.
    """
    skill_map: dict[str, str] = {}
    for content_path in sorted(content_dir.glob("**/*.md")):
        try:
            content = parse_content(content_path)
        except (OSError, ValueError, KeyError) as e:
            print(
                f"Advertencia: no se pudo leer el contenido '{content_path.name}' ({e}), se salta",
                file=sys.stderr,
            )
            continue
        skill_map.update(build_skill_map(content))
    return skill_map


def _dedupe_by_path(files: list[ManifestFile]) -> list[ManifestFile]:
    """Collapse manifest entries that share a path, last one wins.

    Dos adapters pueden apuntar al mismo archivo (Codex y OpenCode escriben
    ambos ``AGENTS.md``); el manifest debe tener una sola fila por ruta.
    """
    by_path: dict[str, ManifestFile] = {}
    for f in files:
        by_path[f.path] = f
    return list(by_path.values())


def _install_gitflow_hook(project_root: Path, adapter: ProviderAdapter) -> list[ManifestFile]:
    """Install the Git Flow guard for adapters that expose one.

    Sólo Claude Code y Antigravity (proveedores primarios) tienen mecanismo de
    hook; el resto no implementa el método y se saltea. La operación es
    idempotente y fusiona con la config existente, así que volver a correrla en
    un ``update`` no destruye configuración del usuario.
    """
    install = getattr(adapter, "install_gitflow_hook", None)
    if install is None:
        return []
    return [
        ManifestFile(
            path=str(p.relative_to(project_root)),
            hash=compute_hash(p.read_text(encoding="utf-8")),
            skill_id=_gitflow_skill_id(adapter),
        )
        for p in install(project_root)
    ]


def _group_by_path(
    adapter: ProviderAdapter, project_root: Path, skill_ids: list[str]
) -> dict[Path, list[str]]:
    """Group skill IDs by their resolved target paths."""
    paths = adapter.target_paths(project_root, skill_ids)
    by_path: dict[Path, list[str]] = {}
    for sid in skill_ids:
        by_path.setdefault(paths[sid], []).append(sid)
    return by_path


def write_skills(
    project_root: Path, adapter: ProviderAdapter, skill_map: dict[str, str]
) -> list[ManifestFile]:
    skill_ids = list(skill_map.keys())
    by_path = _group_by_path(adapter, project_root, skill_ids)

    files: list[ManifestFile] = []
    for path, sids in by_path.items():
        sids_sorted = sorted(sids)
        rendered = "\n\n".join(adapter.render(sid, skill_map[sid]) for sid in sids_sorted)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        files.append(
            ManifestFile(
                path=str(path.relative_to(project_root)),
                hash=compute_hash(rendered),
                skill_id=",".join(sids_sorted),
            )
        )
    return files


def install_all(
    project_root: Path, content_dir: Path, adapters: list[ProviderAdapter]
) -> Manifest:
    skill_map = _load_skill_map(content_dir)

    all_files: list[ManifestFile] = []
    for adapter in adapters:
        try:
            all_files.extend(write_skills(project_root, adapter, skill_map))
            all_files.extend(_install_gitflow_hook(project_root, adapter))
        except (OSError, ValueError) as e:
            # ValueError: read_json_config avisa así de un config JSON malformado
            # preexistente (por ejemplo un .claude/settings.json roto a mano).
            print(f"Advertencia: el adapter '{adapter.name}' falló al escribir ({e}), se salta", file=sys.stderr)

    manifest = Manifest(
        version=_VERSION,
        installed_at=datetime.now(timezone.utc).isoformat(),
        providers=[a.name for a in adapters],
        files=_dedupe_by_path(all_files),
    )
    write_manifest(project_root, manifest)
    return manifest


def update_all(
    project_root: Path, content_dir: Path, adapters: list[ProviderAdapter]
) -> tuple[Manifest, list[str]]:
    existing = read_manifest(project_root)
    existing_by_path = {f.path: f for f in existing.files} if existing else {}

    skill_map = _load_skill_map(content_dir)
    skill_ids = list(skill_map.keys())

    all_files: list[ManifestFile] = []
    warnings: list[str] = []

    for adapter in adapters:
        try:
            by_path = _group_by_path(adapter, project_root, skill_ids)

            for path, sids in by_path.items():
                rel = str(path.relative_to(project_root))
                sids_sorted = sorted(sids)
                rendered = "\n\n".join(adapter.render(sid, skill_map[sid]) for sid in sids_sorted)

                prior = existing_by_path.get(rel)
                if prior is not None and path.exists():
                    on_disk_hash = compute_hash(path.read_text(encoding="utf-8"))
                    if on_disk_hash != prior.hash:
                        warnings.append(f"{rel} (skill(s): {','.join(sids_sorted)}) fue editado a mano, no se sobreescribe")
                        all_files.append(prior)
                        continue

                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered, encoding="utf-8")
                all_files.append(
                    ManifestFile(path=rel, hash=compute_hash(rendered), skill_id=",".join(sids_sorted))
                )

            all_files.extend(_install_gitflow_hook(project_root, adapter))
        except (OSError, ValueError) as e:
            # ValueError: read_json_config avisa así de un config JSON malformado
            # preexistente (por ejemplo un .claude/settings.json roto a mano).
            print(f"Advertencia: el adapter '{adapter.name}' falló al escribir ({e}), se salta", file=sys.stderr)

    # Gap conocido (pendiente para una tarea futura): las entradas del manifest
    # anterior cuyo contenido de origen ya no está en content_dir no entran en
    # este manifest nuevo, así que el archivo escrito sobrevive en disco sin
    # seguimiento y uninstall_all no puede encontrarlo. No se barren acá a
    # propósito: un archivo realmente huérfano es indistinguible de uno que
    # pertenece a un adapter que no entró en esta corrida (por ejemplo con
    # `--providers` acotado), y borrarlo en ese caso sería destructivo. Hace
    # falta distinguir ambos casos antes de barrer.
    manifest = Manifest(
        version=_VERSION,
        installed_at=datetime.now(timezone.utc).isoformat(),
        providers=[a.name for a in adapters],
        files=_dedupe_by_path(all_files),
    )
    write_manifest(project_root, manifest)
    return manifest, warnings


def _prune_empty_parents(project_root: Path, rel_path: Path) -> None:
    """Remove directories left empty after deleting an installed file.

    Nunca borra el directorio marcador del proveedor (``.claude``, ``.github``,
    ``.agents``, ...): ese lo creó el usuario y su existencia es justamente lo
    que hace que ``detect()`` encuentre al proveedor. Sólo se podan los
    directorios estrictamente por debajo de él, que sí creó la fábrica.
    """
    if len(rel_path.parts) < 2:
        return
    marker_dir = project_root / rel_path.parts[0]

    parent = (project_root / rel_path).parent
    while parent != project_root and parent != marker_dir and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def uninstall_all(project_root: Path) -> list[str]:
    manifest = read_manifest(project_root)
    if manifest is None:
        return []

    warnings: list[str] = []
    gitflow: dict[str, list[ManifestFile]] = {}
    for f in manifest.files:
        # Los archivos del hook de Git Flow no se borran a ciegas: el config
        # JSON está fusionado con configuración del usuario (que puede ser
        # anterior a la fábrica) y borrarlo entero se la lleva puesta. Los
        # desinstala el adapter que los instaló, sacando sólo su propia entrada.
        if f.skill_id.startswith(_GITFLOW_SKILL_ID):
            gitflow.setdefault(f.skill_id, []).append(f)
            continue
        path = project_root / f.path
        if not path.exists():
            continue
        on_disk_hash = compute_hash(path.read_text(encoding="utf-8"))
        if on_disk_hash != f.hash:
            warnings.append(f"{f.path} (skill(s): {f.skill_id}) fue editado a mano, no se borra")
            continue
        path.unlink()
        _prune_empty_parents(project_root, Path(f.path))

    for skill_id, files in gitflow.items():
        adapter = _gitflow_owner(skill_id)
        if adapter is None:
            warnings.append(f"{skill_id}: no se encontró el adapter que lo instaló, no se borra")
            continue
        adapter.uninstall_gitflow_hook(project_root)
        for f in files:
            _prune_empty_parents(project_root, Path(f.path))

    if not warnings:
        (project_root / ".factory" / "manifest.json").unlink(missing_ok=True)

    return warnings
