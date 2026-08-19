from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map
from factorysoftware.state import Manifest, ManifestFile, compute_hash, write_manifest

_VERSION = "0.1.0"


def write_skills(
    project_root: Path, adapter: ProviderAdapter, skill_map: dict[str, str]
) -> list[ManifestFile]:
    skill_ids = list(skill_map.keys())
    paths = adapter.target_paths(project_root, skill_ids)

    by_path: dict[Path, list[str]] = {}
    for sid in skill_ids:
        by_path.setdefault(paths[sid], []).append(sid)

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
