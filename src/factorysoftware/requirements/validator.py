from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml


def _parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """
    Parse YAML frontmatter. Returns (data_dict, body_text) on success,
    or (None, error_message) on parse failure.
    """
    if not text.startswith("---"):
        return {}, text
    try:
        second = text.index("---", 3)
    except ValueError:
        return None, "missing closing '---' in frontmatter"
    try:
        fm = yaml.safe_load(text[3:second]) or {}
    except yaml.YAMLError as e:
        return None, f"invalid YAML in frontmatter: {e}"
    if not isinstance(fm, dict):
        return None, "frontmatter is not a YAML mapping"
    body = text[second + 3:].lstrip("\n")
    return fm, body


def _as_list(value: object) -> list[str]:
    """Coerce a frontmatter field into a list, never iterating a scalar string."""
    return value if isinstance(value, list) else []


def _display_path(f: Path, project_root: Path) -> str:
    try:
        return str(f.relative_to(project_root))
    except ValueError:
        return str(f)


def _read_text_safely(f: Path, project_root: Path, errors: list[str]) -> str | None:
    """Read a file's text, appending a human-readable error instead of raising."""
    if not f.is_file():
        return None
    try:
        return f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        errors.append(f"Could not read {_display_path(f, project_root)}: {e}")
        return None


_GIVEN_RE = re.compile(r"\bGiven\b")
_WHEN_RE = re.compile(r"\bWhen\b")
_THEN_RE = re.compile(r"\bThen\b")


def _has_gwt(body: str) -> bool:
    """Return True if body contains at least one Given...When...Then block."""
    return (
        bool(_GIVEN_RE.search(body))
        and bool(_WHEN_RE.search(body))
        and bool(_THEN_RE.search(body))
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


def _parse_traceability_ids(text: str) -> list[tuple[str, str]]:
    """Extract (HU id, Epic id) pairs from the traceability table rows."""
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        parts = [c.strip() for c in line.split("|")]
        if len(parts) >= 3 and re.match(r"^HU-\d+\.\d+$", parts[1]):
            hu_id = parts[1]
            epic_id = parts[2]
            rows.append((hu_id, epic_id))
    return rows


def validate_requirements(project_root: Path, log_path: Path) -> list[str]:
    """
    Run structural checks 1-7 plus the epica-requerida check on
    docs/requirements/ and .factory/log.jsonl.
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
            text = _read_text_safely(f, project_root, errors)
            if text is None:
                continue
            fm, err = _parse_frontmatter(text)
            if fm is None:
                errors.append(f"Parse error in {f.relative_to(project_root)}: {err}")
                continue
            hu_files[fm.get("id", f.stem)] = f

    # -- Collect all HU files including retired (for check 7 and retired-aware checks) --
    all_hu_ids: set[str] = set(hu_files)
    if retiradas_dir.exists():
        for f in retiradas_dir.glob("HU-*.md"):
            text = _read_text_safely(f, project_root, errors)
            if text is None:
                continue
            fm, err = _parse_frontmatter(text)
            if fm is None:
                errors.append(f"Parse error in {f.relative_to(project_root)}: {err}")
                continue
            all_hu_ids.add(fm.get("id", f.stem))

    # -- Collect epic files and the HU ids they list --
    epics_dir = docs / "epics"
    epic_files: dict[str, Path] = {}
    epic_hu_lists: dict[str, list[str]] = {}
    if epics_dir.exists():
        for f in epics_dir.glob("EPIC-*.md"):
            text = _read_text_safely(f, project_root, errors)
            if text is None:
                continue
            fm, body = _parse_frontmatter(text)
            if fm is None:
                errors.append(f"Parse error in {f.relative_to(project_root)}: {body}")
                continue
            eid = fm.get("id", f.stem)
            epic_files[eid] = f
            epic_hu_lists[eid] = re.findall(r"HU-\d+\.\d+", body) if body else []

    # -- Collect traceability rows (hu_id, epic_id pairs) --
    trace_path = docs / "traceability.md"
    trace_rows: list[tuple[str, str]] = []
    if trace_path.exists() and trace_path.is_file():
        trace_text = _read_text_safely(trace_path, project_root, errors)
        if trace_text is not None:
            trace_rows = _parse_traceability_ids(trace_text)

    # -- Collect flujo files --
    flujos_dir = docs / "flujos"
    flujo_data: dict[str, list[str]] = {}
    if flujos_dir.exists():
        for f in flujos_dir.glob("FLUJO-*.md"):
            text = _read_text_safely(f, project_root, errors)
            if text is None:
                continue
            fm, err = _parse_frontmatter(text)
            if fm is None:
                errors.append(f"Parse error in {f.relative_to(project_root)}: {err}")
                continue
            flujo_data[fm.get("id", f.stem)] = _as_list(fm.get("hu"))

    # Check 1: every epic referenced in a traceability row has a file in epics/
    for hu_id, epic_ref in trace_rows:
        if epic_ref and epic_ref not in epic_files:
            errors.append(
                f"Check 1: epic '{epic_ref}' in traceability row for '{hu_id}' has no file in epics/"
            )

    # Check 2a: every HU listed in an epic has a file in stories/ (active or retired)
    for eid, hu_list in epic_hu_lists.items():
        for hu_id in hu_list:
            if hu_id not in all_hu_ids:
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

    # Check 3: depende_de ids exist (active or retired) + circular detection
    deps: dict[str, list[str]] = {}
    for hu_id, f in hu_files.items():
        text = _read_text_safely(f, project_root, errors)
        if text is None:
            continue
        fm, err = _parse_frontmatter(text)
        if fm is None:
            errors.append(f"Parse error in {f.relative_to(project_root)}: {err}")
            continue
        dep_list = _as_list(fm.get("depende_de"))
        deps[hu_id] = dep_list
        for dep in dep_list:
            if dep not in all_hu_ids:
                errors.append(
                    f"Check 3: HU '{hu_id}' depende_de '{dep}' which does not exist"
                )
    for cid in _detect_circular(deps):
        errors.append(f"Check 3: circular dependency detected involving '{cid}'")

    # Check 4: every HU has at least one GWT criterion
    for hu_id, f in hu_files.items():
        text = _read_text_safely(f, project_root, errors)
        if text is None:
            continue
        fm, body = _parse_frontmatter(text)
        if fm is None:
            # Already reported parse error above, skip GWT check for this file
            continue
        if not _has_gwt(body):
            errors.append(
                f"Check 4: HU '{hu_id}' has no Given/When/Then acceptance criterion"
            )

    # Check 5: traceability has exactly one row per non-retired HU, no orphans + detect duplicates
    hu_set = set(hu_files)
    trace_hu_ids = [hu_id for hu_id, _ in trace_rows]
    trace_set = set(trace_hu_ids)

    # Check for duplicate rows
    hu_counts = Counter(trace_hu_ids)
    for hu_id, count in hu_counts.items():
        if count > 1:
            errors.append(
                f"Check 5: traceability.md has {count} rows for HU '{hu_id}', expected exactly 1"
            )

    # Check for missing and orphan rows
    for hu_id in hu_set - trace_set:
        errors.append(f"Check 5: HU '{hu_id}' has no row in traceability.md")
    for tid in trace_set - hu_set:
        errors.append(f"Check 5: traceability.md has orphan row '{tid}'")

    # Check 6: at least one advisor_note sugerencia_transversal in log
    found_transversal = False
    if log_path.exists() and log_path.is_file():
        log_text = _read_text_safely(log_path, project_root, errors)
        for line in (log_text.splitlines() if log_text is not None else []):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict):
                continue
            if (ev.get("type") == "advisor_note"
                    and ev.get("category") == "sugerencia_transversal"):
                found_transversal = True
                break
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

    # Check (epica-requerida): every HU has a non-empty epica field.
    # Deliberately NOT numbered "Check 8" - the content pack (audit_loop step)
    # reserves checks 8-11 for its own semantic (judgment-based) checks, and
    # reusing that number here would make "Check 8" mean two different things
    # depending on whether you're reading the validator's output or the pack.
    for hu_id, f in hu_files.items():
        text = _read_text_safely(f, project_root, errors)
        if text is None:
            continue
        fm, err = _parse_frontmatter(text)
        if fm is None:
            # Already reported parse error above
            continue
        epica = fm.get("epica", "")
        if not epica or not str(epica).strip():
            errors.append(
                f"Check epica-requerida: HU '{hu_id}' has no epica assigned (epica must not be empty)"
            )

    return errors
