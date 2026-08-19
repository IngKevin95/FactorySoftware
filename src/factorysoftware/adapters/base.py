from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]: ...

    def render(self, skill_id: str, content_md: str) -> str: ...
