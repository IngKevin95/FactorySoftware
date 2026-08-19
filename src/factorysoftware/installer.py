from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map
from factorysoftware.state import Manifest, ManifestFile, compute_hash, read_manifest, write_manifest

_VERSION = "0.1.0"


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
    all_files = []
    for content_path in sorted(content_dir.glob("*.md")):
        content = parse_content(content_path)
        skill_map = build_skill_map(content)
        for adapter in adapters:
            try:
                all_files.extend(write_skills(project_root, adapter, skill_map))
            except OSError as e:
                print(f"Advertencia: el adapter '{adapter.name}' falló al escribir ({e}), se salta", file=sys.stderr)

    manifest = Manifest(
        version=_VERSION,
        installed_at=datetime.now(timezone.utc).isoformat(),
        providers=[a.name for a in adapters],
        files=all_files,
    )
    write_manifest(project_root, manifest)
    return manifest


def update_all(
    project_root: Path, content_dir: Path, adapters: list[ProviderAdapter]
) -> tuple[Manifest, list[str]]:
    existing = read_manifest(project_root)
    existing_by_path = {f.path: f for f in existing.files} if existing else {}

    all_files: list[ManifestFile] = []
    warnings: list[str] = []

    for content_path in sorted(content_dir.glob("*.md")):
        content = parse_content(content_path)
        skill_map = build_skill_map(content)
        for adapter in adapters:
            skill_ids = list(skill_map.keys())
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

    manifest = Manifest(
        version=_VERSION,
        installed_at=datetime.now(timezone.utc).isoformat(),
        providers=[a.name for a in adapters],
        files=all_files,
    )
    write_manifest(project_root, manifest)
    return manifest, warnings
