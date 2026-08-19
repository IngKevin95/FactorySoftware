from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter. Returns (data_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text
    second = text.index("---", 3)
    fm = yaml.safe_load(text[3:second]) or {}
    body = text[second + 3:].lstrip("\n")
    return fm, body


def _has_gwt(body: str) -> bool:
    """Return True if body contains at least one Given...When...Then block."""
    return (
        bool(re.search(r"\bGiven\b", body))
        and bool(re.search(r"\bWhen\b", body))
        and bool(re.search(r"\bThen\b", body))
    )


def _detect_circular(deps: dict[str, list[str]]) -> list[str]:
    """Return list of node ids involved in circular depende_de chains."""
    visited: set[str] = set()
    in_stack: set[str] = set()
    circular: set[str] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        in_stack.add(node)
        for neighbor in deps.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in in_stack:
                circular.add(neighbor)
                circular.add(node)
        in_stack.discard(node)

    for node in list(deps):
        if node not in visited:
            dfs(node)
    return sorted(circular)


def _parse_traceability_ids(text: str) -> list[str]:
    """Extract HU ids from the traceability table first column."""
    ids: list[str] = []
    for line in text.splitlines():
        parts = [c.strip() for c in line.split("|")]
        if len(parts) >= 2 and re.match(r"^HU-\d+\.\d+$", parts[1]):
            ids.append(parts[1])
    return ids


def validate_requirements(project_root: Path, log_path: Path) -> list[str]:
    """
    Run structural checks 1-7 on docs/requirements/ and .factory/log.jsonl.
    Returns list of error strings; empty = clean.
    """
    docs = project_root / "docs" / "requirements"
    errors: list[str] = []

    # -- Collect active HU files (exclude retiradas/) --
    stories_dir = docs / "stories"
    retiradas_dir = stories_dir / "retiradas"
    hu_files: dict[str, Path] = {}
    if stories_dir.exists():
        for f in stories_dir.glob("HU-*.md"):
            if retiradas_dir in f.parents:
                continue
            fm, _ = _parse_frontmatter(f.read_text(encoding="utf-8"))
            hu_files[fm.get("id", f.stem)] = f

    # -- Collect all HU files including retired (for check 7) --
    all_hu_ids: set[str] = set(hu_files)
    if retiradas_dir.exists():
        for f in retiradas_dir.glob("HU-*.md"):
            fm, _ = _parse_frontmatter(f.read_text(encoding="utf-8"))
            all_hu_ids.add(fm.get("id", f.stem))

    # -- Collect epic files and the HU ids they list --
    epics_dir = docs / "epics"
    epic_files: dict[str, Path] = {}
    epic_hu_lists: dict[str, list[str]] = {}
    if epics_dir.exists():
        for f in epics_dir.glob("EPIC-*.md"):
            fm, body = _parse_frontmatter(f.read_text(encoding="utf-8"))
            eid = fm.get("id", f.stem)
            epic_files[eid] = f
            epic_hu_lists[eid] = re.findall(r"HU-\d+\.\d+", body)

    # -- Collect traceability rows --
    trace_path = docs / "traceability.md"
    trace_ids: list[str] = []
    if trace_path.exists():
        trace_ids = _parse_traceability_ids(trace_path.read_text(encoding="utf-8"))

    # -- Collect flujo files --
    flujos_dir = docs / "flujos"
    flujo_data: dict[str, list[str]] = {}
    if flujos_dir.exists():
        for f in flujos_dir.glob("FLUJO-*.md"):
            fm, _ = _parse_frontmatter(f.read_text(encoding="utf-8"))
            flujo_data[fm.get("id", f.stem)] = fm.get("hu") or []

    # Check 1: every epic referenced via traceability row HU has a file in epics/
    for hu_id in trace_ids:
        f = stories_dir / f"{hu_id}.md"
        if f.exists():
            fm, _ = _parse_frontmatter(f.read_text(encoding="utf-8"))
            epic_ref = fm.get("epica", "")
            if epic_ref and epic_ref not in epic_files:
                errors.append(
                    f"Check 1: epic '{epic_ref}' referenced by '{hu_id}' has no file in epics/"
                )

    # Check 2a: every HU listed in an epic has a file in stories/
    for eid, hu_list in epic_hu_lists.items():
        for hu_id in hu_list:
            if hu_id not in hu_files:
                errors.append(
                    f"Check 2: HU '{hu_id}' listed in '{eid}' has no file in stories/"
                )

    # Check 2b: every HU file is listed in at least one epic
    all_listed: set[str] = {h for hus in epic_hu_lists.values() for h in hus}
    for hu_id in hu_files:
        if hu_id not in all_listed:
            errors.append(
                f"Check 2: HU '{hu_id}' in stories/ is not listed in any epic"
            )

    # Check 3: depende_de ids exist + circular detection
    deps: dict[str, list[str]] = {}
    for hu_id, f in hu_files.items():
        fm, _ = _parse_frontmatter(f.read_text(encoding="utf-8"))
        dep_list: list[str] = fm.get("depende_de") or []
        deps[hu_id] = dep_list
        for dep in dep_list:
            if dep not in hu_files:
                errors.append(
                    f"Check 3: HU '{hu_id}' depende_de '{dep}' which does not exist"
                )
    for cid in _detect_circular(deps):
        errors.append(f"Check 3: circular dependency detected involving '{cid}'")

    # Check 4: every HU has at least one GWT criterion
    for hu_id, f in hu_files.items():
        _, body = _parse_frontmatter(f.read_text(encoding="utf-8"))
        if not _has_gwt(body):
            errors.append(
                f"Check 4: HU '{hu_id}' has no Given/When/Then acceptance criterion"
            )

    # Check 5: traceability has exactly one row per non-retired HU, no orphans
    hu_set = set(hu_files)
    trace_set = set(trace_ids)
    for hu_id in hu_set - trace_set:
        errors.append(f"Check 5: HU '{hu_id}' has no row in traceability.md")
    for tid in trace_set - hu_set:
        errors.append(f"Check 5: traceability.md has orphan row '{tid}'")

    # Check 6: at least one advisor_note sugerencia_transversal in log
    found_transversal = False
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
                if (ev.get("type") == "advisor_note"
                        and ev.get("category") == "sugerencia_transversal"):
                    found_transversal = True
                    break
            except json.JSONDecodeError:
                continue
    if not found_transversal:
        errors.append(
            "Check 6: no advisor_note with category 'sugerencia_transversal' "
            "found in log  -  epics step must review transversal capabilities"
        )

    # Check 7: every hu id in FLUJO-N.md exists (active or retired)
    for flujo_id, hu_list in flujo_data.items():
        for hu_id in hu_list:
            if hu_id not in all_hu_ids:
                errors.append(
                    f"Check 7: FLUJO '{flujo_id}' references HU '{hu_id}' which does not exist"
                )

    return errors
