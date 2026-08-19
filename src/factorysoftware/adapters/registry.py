from __future__ import annotations

import sys
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.adapters.claude_code import ClaudeCodeAdapter
from factorysoftware.adapters.codex import CodexAdapter
from factorysoftware.adapters.copilot import CopilotAdapter
from factorysoftware.adapters.opencode import OpenCodeAdapter

ALL_ADAPTERS: list[ProviderAdapter] = [
    ClaudeCodeAdapter(), CopilotAdapter(), CodexAdapter(), OpenCodeAdapter(),
]


def detect(project_root: Path, adapters: list[ProviderAdapter] | None = None) -> list[ProviderAdapter]:
    candidates = adapters if adapters is not None else ALL_ADAPTERS
    found = []
    for a in candidates:
        try:
            if a.detect(project_root):
                found.append(a)
        except OSError as e:
            print(f"Advertencia: el adapter '{a.name}' falló al detectar ({e}), se salta", file=sys.stderr)
    return found


def select(names: list[str], adapters: list[ProviderAdapter] | None = None) -> list[ProviderAdapter]:
    candidates = adapters if adapters is not None else ALL_ADAPTERS
    by_name = {a.name: a for a in candidates}
    return [by_name[n] for n in names if n in by_name]
