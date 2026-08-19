from __future__ import annotations

from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.state import ManifestFile, compute_hash


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
