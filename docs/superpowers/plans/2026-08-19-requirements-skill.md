# Requirements Engineering Skill  -  Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `requirements` content pack for FactorySoftware  -  a CLI validator and 7 SKILL.md files that guide an agent through producing PRD, Epics, User Stories, Flows, and a Traceability matrix for any project.

**Architecture:** A new subcommand `factory validate requirements` is added to the existing argparse CLI in `cli.py`. It calls `validate_requirements()` in a new module `src/factorysoftware/requirements/validator.py` which performs 7 deterministic structural checks on `docs/requirements/` and `.factory/log.jsonl`. Six skill files live in `src/factorysoftware/content/requirements/` and are installed by the existing installer. Skills are plain SKILL.md markdown files; the validator is the only Python code deliverable.

**Tech Stack:** Python 3.11+, pytest, pathlib, PyYAML 6.0+ (already a dependency), argparse (existing CLI framework)

**Spec:** `docs/superpowers/specs/2026-08-19-requirements-skill-design.md`

## Global Constraints

- Python >= 3.11; no external IO in tests  -  `tmp_path` fixtures only (matching existing test patterns in `tests/`).
- PyYAML >= 6.0 already in `pyproject.toml`  -  do not add new dependencies.
- CLI entry point: `factory` (defined in `pyproject.toml` as `factorysoftware.cli:main`).
- New subcommand: `factory validate requirements` extending the existing `argparse` parser in `src/factorysoftware/cli.py`.
- Log file path: `.factory/log.jsonl`  -  append-only JSONL, one JSON object per line (matches existing `append_log` / `read_log` in `state.py`).
- ID schemes (verbatim from spec): `EPIC-N`, `HU-N.M`, `FLUJO-N`  -  sequentially assigned, never reused, retired to `retiradas/` subfolder.
- Frontmatter format: YAML between `---` delimiters.
- Gate: phase never advances to Architecture without explicit user approval.
- Audit loop max iterations: 3.
- `hu_por_epica` fan-out: one subagent per epic when parallel dispatch available; sequential one-at-a-time otherwise  -  never collapsed into one pass.
- Skill files live in `src/factorysoftware/content/requirements/` to be picked up by the existing installer.
- All tests go in `tests/` flat (matching existing structure  -  no subdirectories).

---

### Task 1: Validator Module  -  Structural Checks 1-7

**Files:**
- Create: `src/factorysoftware/requirements/__init__.py`
- Create: `src/factorysoftware/requirements/validator.py`
- Create: `tests/test_validate_requirements.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces:
  - `validate_requirements(docs_root: Path, log_path: Path) -> list[str]`
    Returns list of human-readable error strings. Empty list = all checks pass.
  - Internal helpers (not used outside this module):
    - `_parse_frontmatter(text: str) -> tuple[dict, str]`
    - `_has_gwt(body: str) -> bool`
    - `_detect_circular(deps: dict[str, list[str]]) -> list[str]`
    - `_parse_traceability_ids(text: str) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate_requirements.py
from __future__ import annotations
import json
from pathlib import Path
import pytest
import yaml
from factorysoftware.requirements.validator import validate_requirements


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


def _log(log_path: Path, event: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    return tmp_path / "docs" / "requirements"


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    return tmp_path / ".factory" / "log.jsonl"


# --- Check 1: every epic referenced by traceability row has a file in epics/ ---

def test_check1_missing_epic_file(docs, log_path):
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("EPIC-1" in e and "epics/" in e for e in errors)


# --- Check 2: HU listed in epic has file; HU file is listed in epic ---

def test_check2_hu_listed_in_epic_but_no_file(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n- HU-1.2\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e for e in errors)


def test_check2_hu_file_not_listed_in_any_epic(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    _write(docs / "stories" / "HU-1.2.md",
           _fm({"id": "HU-1.2", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "media", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e for e in errors)


# --- Check 3: depende_de ids exist + no circular deps ---

def test_check3_missing_dependency(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e and "depende_de" in e for e in errors)


def test_check3_circular_dependency(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n- HU-1.2\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]}))
    _write(docs / "stories" / "HU-1.2.md",
           _fm({"id": "HU-1.2", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.1"]}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("circular" in e.lower() for e in errors)


# --- Check 4: every HU has at least one Given/When/Then ---

def test_check4_no_gwt(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "Como usuario quiero algo para algo.\n"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and ("Given" in e or "criterio" in e.lower()) for e in errors)


# --- Check 5: traceability has exactly one row per non-retired HU ---

def test_check5_missing_row(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n|----|-------|--------|----|----|\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and "traceability" in e.lower() for e in errors)


def test_check5_orphan_row(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n"
           "| HU-9.9 | EPIC-9 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-9.9" in e for e in errors)


# --- Check 6: advisor_note sugerencia_transversal in log ---

def test_check6_missing_advisor_note(docs, log_path):
    _log(log_path, {"type": "step_complete", "step": "epics"})
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("sugerencia_transversal" in e or "advisor_note" in e for e in errors)


def test_check6_passes_when_note_present(docs, log_path):
    _log(log_path, {"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"})
    # minimal valid structure so other checks pass too
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("sugerencia_transversal" in e for e in errors)


# --- Check 7: every hu id in FLUJO-N.md exists as a file ---

def test_check7_flujo_references_missing_hu(docs, log_path):
    _write(docs / "flujos" / "FLUJO-1.md",
           _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1", "HU-9.9"]}))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-9.9" in e and "FLUJO-1" in e for e in errors)


def test_check7_retired_hu_is_acceptable(docs, log_path):
    _write(docs / "flujos" / "FLUJO-1.md",
           _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1"]}))
    _write(docs / "stories" / "retiradas" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "retirada",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("HU-1.1" in e and "FLUJO-1" in e for e in errors)


# --- Happy path: fully valid minimal set ---

def test_happy_path(docs, log_path):
    _log(log_path, {"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"})
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_validate_requirements.py -v
```
Expected: `ImportError`  -  `factorysoftware.requirements.validator` does not exist.

- [ ] **Step 3: Create `__init__.py` and implement `validator.py`**

```python
# src/factorysoftware/requirements/__init__.py
# (empty  -  marks package)
```

```python
# src/factorysoftware/requirements/validator.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_validate_requirements.py -v
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/requirements/__init__.py src/factorysoftware/requirements/validator.py tests/test_validate_requirements.py
git commit -m "feat(requirements): add structural validator checks 1-7"
```

---

### Task 2: CLI Subcommand  -  `factory validate requirements`

**Files:**
- Modify: `src/factorysoftware/cli.py` (add `validate` subparser group + `requirements` sub-subcommand)
- Create: `tests/test_cli_validate_requirements.py`

**Interfaces:**
- Consumes: `validate_requirements(project_root: Path, log_path: Path) -> list[str]` from Task 1
- Produces:
  - CLI: `factory validate requirements [--project-root PATH] [--log PATH]`
  - Exit code 0 if no errors, 1 if errors found.
  - Each error printed to stdout, one per line.

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli_validate_requirements.py
from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest
from factorysoftware.cli import main


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


def test_validate_requirements_clean(tmp_path, capsys):
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text(
        json.dumps({"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"}) + "\n"
    )
    docs = tmp_path / "docs" / "requirements"
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")

    code = main(["validate", "requirements",
                 "--project-root", str(tmp_path),
                 "--log", str(log)])
    assert code == 0
    assert capsys.readouterr().out.strip() == ""


def test_validate_requirements_reports_errors(tmp_path, capsys):
    # empty log -> check 6 fails
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text("")

    code = main(["validate", "requirements",
                 "--project-root", str(tmp_path),
                 "--log", str(log)])
    assert code == 1
    out = capsys.readouterr().out
    assert "sugerencia_transversal" in out
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli_validate_requirements.py -v
```
Expected: FAIL  -  `validate` is not a known subcommand yet.

- [ ] **Step 3: Add `validate requirements` to `cli.py`**

Add the following function and parser registration to `src/factorysoftware/cli.py`:

```python
# add at top of cli.py with other imports
from factorysoftware.requirements.validator import validate_requirements as _validate_reqs
```

```python
# new command function  -  add before build_parser()
def cmd_validate_requirements(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    log_path = Path(args.log)
    errors = _validate_reqs(project_root, log_path)
    for e in errors:
        print(e)
    return 1 if errors else 0
```

In `build_parser()`, add after the `log` subparser block:

```python
    # validate <subcommand>
    validate_p = sub.add_parser("validate")
    validate_sub = validate_p.add_subparsers(dest="validate_command", required=True)

    p = validate_sub.add_parser("requirements")
    p.add_argument("--project-root", default=".")
    p.add_argument("--log", default=".factory/log.jsonl")
    p.set_defaults(func=cmd_validate_requirements)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cli_validate_requirements.py -v
```
Expected: PASS.

- [ ] **Step 5: Run full test suite to check no regressions**

```bash
pytest tests/ -v
```
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/factorysoftware/cli.py tests/test_cli_validate_requirements.py
git commit -m "feat(requirements): add factory validate requirements CLI subcommand"
```

---

### Task 3: Skill files  -  `requirements-prd` and `requirements-epics`

**Files:**
- Create: `src/factorysoftware/content/requirements/requirements-prd.md`
- Create: `src/factorysoftware/content/requirements/requirements-epics.md`
- Create: `tests/test_skill_requirements_prd_epics.py`

**Interfaces:**
- Consumes: nothing from prior tasks (these are content files, not Python)
- Produces:
  - Two SKILL.md-style files parseable by the existing content installer
  - Contract test validates the output format of each skill's expected deliverables using `tmp_path` fixtures

- [ ] **Step 1: Write contract tests**

```python
# tests/test_skill_requirements_prd_epics.py
"""
Contract tests: verify the expected output format of requirements-prd and
requirements-epics deliverables. Uses fixtures that simulate post-skill execution.
"""
from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


# --- PRD contract ---

@pytest.fixture
def prd_output(tmp_path: Path) -> Path:
    prd = tmp_path / "docs" / "requirements" / "PRD.md"
    prd.parent.mkdir(parents=True)
    prd.write_text(
        "# PRD\n\n"
        "## Problema\nAlgo.\n\n"
        "## Objetivo de negocio\nUna frase.\n\n"
        "## Alcance\n### Que entra\n- X\n### Que no entra\n- Y\n\n"
        "## Metricas de exito\n- M1\n\n"
        "## Stakeholders\n- S1\n\n"
        "## Restricciones\n- R1\n\n"
        "## Supuestos\n- A1\n",
        encoding="utf-8",
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "prd",
                    "output_files": ["docs/requirements/PRD.md"]}) + "\n"
    )
    return tmp_path


def test_prd_file_exists(prd_output):
    assert (prd_output / "docs" / "requirements" / "PRD.md").exists()


def test_prd_log_step_complete(prd_output):
    events = [json.loads(l) for l in
              (prd_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events if e.get("step") == "prd" and e.get("type") == "step_complete"]
    assert len(done) == 1
    assert "docs/requirements/PRD.md" in done[0]["output_files"]


def test_prd_required_sections(prd_output):
    text = (prd_output / "docs" / "requirements" / "PRD.md").read_text()
    for s in ["Problema", "Alcance", "Metricas", "Stakeholders"]:
        assert s in text, f"PRD missing section containing: {s}"


# --- Epics contract ---

@pytest.fixture
def epics_output(tmp_path: Path) -> Path:
    epic = tmp_path / "docs" / "requirements" / "epics" / "EPIC-1.md"
    epic.parent.mkdir(parents=True)
    epic.write_text(
        _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "Obj1"},
            "## Meta de negocio\nAlgo.\n\n## HUs\n- HU-1.1\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "advisor_note", "category": "sugerencia_transversal",
                    "step": "epics", "suggestions": ["autenticacion"], "accepted": []}) + "\n" +
        json.dumps({"type": "step_complete", "step": "epics",
                    "output_files": ["docs/requirements/epics/EPIC-1.md"]}) + "\n"
    )
    return tmp_path


def test_epic_file_exists(epics_output):
    assert (epics_output / "docs" / "requirements" / "epics" / "EPIC-1.md").exists()


def test_epic_frontmatter_fields(epics_output):
    text = (epics_output / "docs" / "requirements" / "epics" / "EPIC-1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "EPIC-1"
    assert fm["estado"] in ("draft", "validada")
    assert "objetivo_prd" in fm


def test_epics_advisor_note_logged(epics_output):
    events = [json.loads(l) for l in
              (epics_output / ".factory" / "log.jsonl").read_text().splitlines()]
    notes = [e for e in events
             if e.get("type") == "advisor_note"
             and e.get("category") == "sugerencia_transversal"]
    assert len(notes) >= 1


def test_epics_step_complete_logged(epics_output):
    events = [json.loads(l) for l in
              (epics_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events if e.get("step") == "epics" and e.get("type") == "step_complete"]
    assert len(done) == 1
```

- [ ] **Step 2: Run tests (pass via fixture  -  they validate output contracts, not skill text)**

```bash
pytest tests/test_skill_requirements_prd_epics.py -v
```
Expected: all PASS.

- [ ] **Step 3: Write `requirements-prd.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-prd.md -->
---
id: requirements
steps:
  - id: prd
    depende_de: []
---

# Skill: requirements-prd

Produce `docs/requirements/PRD.md`. First step of the requirements pipeline; no prerequisites.

## Verificacion de prerequisitos

- Si `docs/requirements/PRD.md` ya existe: preguntar al usuario si desea sobrescribirlo antes de continuar.

## Output esperado

Archivo `docs/requirements/PRD.md` con estas secciones en orden (sin detalle tecnico  -  sin nombres de tablas, verbos HTTP ni componentes de UI):

1. **Problema**  -  Que dolor o necesidad resuelve el sistema.
2. **Objetivo de negocio**  -  Una frase que describe el resultado deseado.
3. **Alcance**
   - **Que entra**  -  Lista explicita de capacidades incluidas.
   - **Que no entra**  -  Lista explicita de exclusiones.
4. **Metricas de exito**  -  Como se mide que el proyecto fue exitoso.
5. **Stakeholders**  -  Quienes tienen interes en el resultado.
6. **Restricciones conocidas**  -  Tiempo, presupuesto, tecnologia, regulaciones.
7. **Supuestos**  -  Que se asume como verdadero para que el alcance tenga sentido.

## Pasos

- [ ] Preguntar al usuario por el contexto del proyecto si no fue provisto.
- [ ] Redactar `docs/requirements/PRD.md` con las 7 secciones.
- [ ] Logear en `.factory/log.jsonl`:
  `{"type": "step_complete", "step": "prd", "output_files": ["docs/requirements/PRD.md"]}`
- [ ] Confirmar al usuario que el PRD fue guardado y mostrar su ruta.
```

- [ ] **Step 4: Write `requirements-epics.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-epics.md -->
---
id: requirements
steps:
  - id: epics
    depende_de: [prd]
---

# Skill: requirements-epics

Produce `docs/requirements/epics/EPIC-N.md`  -  un archivo por cada epica.
Requiere que `docs/requirements/PRD.md` exista.

## Verificacion de prerequisitos

- Si `docs/requirements/PRD.md` no existe: mostrar error y sugerir correr `requirements-prd` primero. No continuar.

## Reglas de redaccion

- Una sola pasada para todas las epicas  -  el agente necesita ver el conjunto completo para distribuir el alcance del PRD sin solapes entre epicas.
- Un archivo por epica: `docs/requirements/epics/EPIC-N.md` (N secuencial desde 1, nunca reutilizado).
- Frontmatter obligatorio: `id` (EPIC-N), `estado: draft`, `objetivo_prd` (a que objetivo del PRD responde esta epica).
- Cuerpo: meta de negocio de la epica + lista de HU por id (se completara en el paso `hu_por_epica`  -  por ahora la lista puede quedar vacia o con ids estimados).

## Sugerencia de capacidades transversales (OBLIGATORIO antes de cerrar)

Antes de logear step_complete, revisar si las siguientes capacidades estan cubiertas por alguna epica.
Sugerir al usuario (via pregunta explicita) las que falten  -  NUNCA agregarlas en silencio:

- Autenticacion / Login
- Gestion de perfil de usuario
- Cambio de contrasena
- Foto de perfil
- Recuperacion de cuenta
- Cualquier otra que la naturaleza del proyecto sugiera

Logear SIEMPRE este evento (aunque el usuario rechace todas las sugerencias):
`{"type": "advisor_note", "category": "sugerencia_transversal", "step": "epics", "suggestions": [...lista sugerida...], "accepted": [...lista aceptada...]}`

Crear epicas adicionales solo para las sugerencias que el usuario acepte explicitamente.

## Pasos

- [ ] Verificar que `docs/requirements/PRD.md` existe.
- [ ] Leer el PRD completo.
- [ ] Redactar todas las epicas en una sola pasada; crear un archivo por epica en `docs/requirements/epics/`.
- [ ] Revisar capacidades transversales y preguntar al usuario por las que falten.
- [ ] Logear el evento `advisor_note` de sugerencia_transversal.
- [ ] Crear epicas adicionales solo para las sugerencias aceptadas.
- [ ] Logear `{"type": "step_complete", "step": "epics", "output_files": [...lista de archivos creados...]}`.
```

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/requirements/requirements-prd.md src/factorysoftware/content/requirements/requirements-epics.md tests/test_skill_requirements_prd_epics.py
git commit -m "feat(requirements): add requirements-prd and requirements-epics skills with contract tests"
```

---

### Task 4: Skill files  -  `requirements-hu_por_epica`, `requirements-traceability`, `requirements-flujos`

**Files:**
- Create: `src/factorysoftware/content/requirements/requirements-hu_por_epica.md`
- Create: `src/factorysoftware/content/requirements/requirements-traceability.md`
- Create: `src/factorysoftware/content/requirements/requirements-flujos.md`
- Create: `tests/test_skill_requirements_hu_trace_flujos.py`

**Interfaces:**
- Consumes: nothing from Python tasks (content files)
- Produces:
  - Three SKILL.md-style files
  - Contract tests for HU, traceability, and flujos output formats

- [ ] **Step 1: Write contract tests**

```python
# tests/test_skill_requirements_hu_trace_flujos.py
from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


# --- HU contract ---

@pytest.fixture
def hu_output(tmp_path: Path) -> Path:
    hu = tmp_path / "docs" / "requirements" / "stories" / "HU-1.1.md"
    hu.parent.mkdir(parents=True)
    hu.write_text(
        _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
             "prioridad": "alta", "depende_de": []},
            "Como usuario quiero algo para algo.\n\n"
            "**Given** usuario existe **When** hace login **Then** ve dashboard\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "hu_por_epica",
                    "epic": "EPIC-1",
                    "output_files": ["docs/requirements/stories/HU-1.1.md"]}) + "\n"
    )
    return tmp_path


def test_hu_file_exists(hu_output):
    assert (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").exists()


def test_hu_frontmatter_complete(hu_output):
    text = (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "HU-1.1"
    assert fm["epica"] == "EPIC-1"
    assert "prioridad" in fm
    assert isinstance(fm.get("depende_de", []), list)


def test_hu_has_gwt(hu_output):
    text = (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").read_text()
    assert "Given" in text and "When" in text and "Then" in text


def test_hu_step_complete_logged(hu_output):
    events = [json.loads(l) for l in
              (hu_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("type") == "step_complete" and e.get("step") == "hu_por_epica"]
    assert len(done) >= 1


# --- Traceability contract ---

@pytest.fixture
def trace_output(tmp_path: Path) -> Path:
    t = tmp_path / "docs" / "requirements" / "traceability.md"
    t.parent.mkdir(parents=True)
    t.write_text(
        "| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |\n"
        "|----|-------|--------|------------------|------------------------------|\n"
        "| HU-1.1 | EPIC-1 | draft | _pendiente (fase QA)_ | _pendiente (fase Arquitectura)_ |\n"
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "traceability",
                    "output_files": ["docs/requirements/traceability.md"]}) + "\n"
    )
    return tmp_path


def test_traceability_file_exists(trace_output):
    assert (trace_output / "docs" / "requirements" / "traceability.md").exists()


def test_traceability_has_hu_row(trace_output):
    assert "HU-1.1" in (trace_output / "docs" / "requirements" / "traceability.md").read_text()


def test_traceability_step_complete_logged(trace_output):
    events = [json.loads(l) for l in
              (trace_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("step") == "traceability" and e.get("type") == "step_complete"]
    assert len(done) == 1


# --- Flujos contract ---

@pytest.fixture
def flujos_output(tmp_path: Path) -> Path:
    flujo = tmp_path / "docs" / "requirements" / "flujos" / "FLUJO-1.md"
    flujo.parent.mkdir(parents=True)
    flujo.write_text(
        _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1", "HU-2.1"]},
            "## Alta de cuenta y primer login\n\n"
            "Paso 1 (HU-1.1): el usuario completa el formulario.\n"
            "Paso 2 (HU-2.1): el sistema le muestra el dashboard.\n\n"
            "## Criterio de exito del flujo\n"
            "El usuario ve el dashboard despues de completar el alta.\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "flujos",
                    "output_files": ["docs/requirements/flujos/FLUJO-1.md"]}) + "\n"
    )
    return tmp_path


def test_flujo_file_exists(flujos_output):
    assert (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").exists()


def test_flujo_frontmatter_valid(flujos_output):
    text = (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "FLUJO-1"
    assert isinstance(fm["hu"], list) and len(fm["hu"]) >= 1


def test_flujo_has_success_criterion(flujos_output):
    text = (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").read_text()
    assert "criterio" in text.lower() or "Criterio" in text


def test_flujos_step_complete_logged(flujos_output):
    events = [json.loads(l) for l in
              (flujos_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("step") == "flujos" and e.get("type") == "step_complete"]
    assert len(done) == 1
```

- [ ] **Step 2: Run contract tests (pass via fixture)**

```bash
pytest tests/test_skill_requirements_hu_trace_flujos.py -v
```
Expected: all PASS.

- [ ] **Step 3: Write `requirements-hu_por_epica.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-hu_por_epica.md -->
---
id: requirements
steps:
  - id: hu_por_epica
    depende_de: [epics]
---

# Skill: requirements-hu_por_epica

Produce `docs/requirements/stories/HU-N.M.md` para todas las HU de UNA epica.
Se invoca una vez por epica. Si el proveedor soporta subagentes paralelos, cada instancia corre en paralelo para su epica; si no, se corre una a la vez de forma secuencial  -  NUNCA en una sola pasada para todas las epicas juntas.

## Prerequisitos

- `docs/requirements/PRD.md` debe existir.
- `docs/requirements/epics/EPIC-N.md` (la epica asignada a esta instancia) debe existir.
- Si alguno falta: mostrar error, listar que falta, sugerir el paso previo. No continuar.

## Contexto de esta instancia

Esta instancia recibe SOLO:
- El PRD completo.
- Su `EPIC-N.md` completa.
- El listado de ids de las demas epicas (NUNCA su contenido completo  -  para mantener el contexto acotado).

## Reglas de redaccion

- Un archivo por HU: `docs/requirements/stories/HU-N.M.md`.
- ID: `HU-N.M` donde N = numero de la epica duena, M = secuencial dentro de esa epica desde 1.
- IDs asignados una vez, nunca reutilizados. Si una HU se retira: cambiar frontmatter `estado: retirada` y mover a `stories/retiradas/`.
- Frontmatter obligatorio: `id`, `epica`, `estado: draft`, `prioridad` (alta/media/baja), `depende_de` (lista de ids, puede ser vacia).
- `depende_de` puede referenciar HU de esta epica o de otras  -  usar solo el id, NUNCA el contenido de la otra epica.
- Cuerpo: formato *Como [rol] quiero [accion] para [beneficio]* + al menos un criterio Given/When/Then.
- Tantos criterios Given/When/Then como casos relevantes (felices y de borde a nivel de negocio).
- **Anexo funcional** (solo si la HU toca una pantalla o un endpoint): que campos, que validaciones de negocio, que estados visibles, que datos entran/salen  -  en terminos de negocio, sin tecnicismos (sin nombres de tablas, verbos HTTP, componentes de UI concretos).

## Pasos

- [ ] Leer el PRD completo y `EPIC-N.md`.
- [ ] Redactar todas las HU de esta epica en una sola pasada (todos los archivos a la vez).
- [ ] Actualizar `EPIC-N.md` con la lista definitiva de ids de HU generadas.
- [ ] Logear `{"type": "step_complete", "step": "hu_por_epica", "epic": "EPIC-N", "output_files": [...lista de archivos creados...]}`.
```

- [ ] **Step 4: Write `requirements-traceability.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-traceability.md -->
---
id: requirements
steps:
  - id: traceability
    depende_de: [hu_por_epica]
---

# Skill: requirements-traceability

Produce `docs/requirements/traceability.md`  -  tabla con una fila por cada HU no retirada.
Requiere que todos los pasos `hu_por_epica` esten completos en el log.
Corre en paralelo con `requirements-flujos` (ambos dependen solo de `hu_por_epica`).

## Prerequisitos

- Todos los archivos `docs/requirements/stories/HU-N.M.md` generados (todos los eventos `step_complete` de `hu_por_epica` presentes en el log).
- Si alguna epica no tiene su paso completo en el log: listar cuales faltan y no continuar.

## Output

Archivo `docs/requirements/traceability.md` con tabla markdown:

```
| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |
|----|-------|--------|------------------|------------------------------|
| HU-1.1 | EPIC-1 | draft | _pendiente (fase QA)_ | _pendiente (fase Arquitectura)_ |
```

- Una fila por cada HU no retirada (excluir las de `stories/retiradas/`).
- Columnas "Casos de prueba" y "Componentes de arquitectura" quedan como `_pendiente (fase X)_`  -  se completan en fases futuras.

## Pasos

- [ ] Leer todos los archivos `docs/requirements/stories/HU-N.M.md` (excluyendo `retiradas/`).
- [ ] Generar `docs/requirements/traceability.md` con una fila por HU, en orden de id.
- [ ] Logear `{"type": "step_complete", "step": "traceability", "output_files": ["docs/requirements/traceability.md"]}`.
```

- [ ] **Step 5: Write `requirements-flujos.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-flujos.md -->
---
id: requirements
steps:
  - id: flujos
    depende_de: [hu_por_epica]
---

# Skill: requirements-flujos

Produce `docs/requirements/flujos/FLUJO-N.md`  -  un archivo por cada flujo de negocio identificado.
Corre en paralelo con `requirements-traceability` (ambos dependen solo de `hu_por_epica`).

## Prerequisitos

- Todos los archivos `docs/requirements/stories/HU-N.M.md` disponibles.
- NO requiere `traceability.md` (son pasos independientes).

## Que es un flujo de negocio

- Flujos de NEGOCIO, no de navegacion de UI (Arquitectura no existe todavia).
- Se derivan de las relaciones `depende_de` entre HU y de la narrativa de las Epicas.
- Solo crear flujos que representen un camino real que un usuario recorreria para lograr un objetivo de negocio (alta de cuenta, compra, publicacion de contenido, etc.).
- No todo par de HU relacionadas forma un flujo relevante.
- Arquitectura, cuando defina la navegacion real en `SCREEN-N.md`, tiene que honrar estos flujos ya declarados.

## Formato de cada archivo

- ID: `FLUJO-N`, secuencial desde 1, nunca reutilizado.
- Frontmatter: `id`, `estado: draft`, `hu` (lista ORDENADA de ids `HU-x.y` que el flujo recorre  -  puede cruzar varias Epicas).
- Cuerpo:
  - Nombre del flujo (ej. "Alta de cuenta y primer login").
  - Descripcion paso a paso de que hace el usuario en cada HU de la secuencia.
  - **Criterio de exito del flujo completo**  -  distinto de los criterios de aceptacion de cada HU aislada. Un flujo puede fallar aunque cada HU pase sus propios tests (ej. el dato que HU-1.3 guarda no es el que HU-2.1 espera leer).

## Pasos

- [ ] Leer todas las HU de todas las epicas en una sola pasada.
- [ ] Identificar secuencias de negocio coherentes que crucen multiples HU y representen objetivos reales.
- [ ] Crear un archivo `FLUJO-N.md` por cada flujo en `docs/requirements/flujos/`.
- [ ] Logear `{"type": "step_complete", "step": "flujos", "output_files": [...lista de archivos creados...]}`.
```

- [ ] **Step 6: Commit**

```bash
git add src/factorysoftware/content/requirements/requirements-hu_por_epica.md src/factorysoftware/content/requirements/requirements-traceability.md src/factorysoftware/content/requirements/requirements-flujos.md tests/test_skill_requirements_hu_trace_flujos.py
git commit -m "feat(requirements): add hu_por_epica, traceability, and flujos skills with contract tests"
```

---

### Task 5: Skill files  -  `requirements-audit_loop` and `requirements-flujo` orchestrator

**Files:**
- Create: `src/factorysoftware/content/requirements/requirements-audit_loop.md`
- Create: `src/factorysoftware/content/requirements/requirements-flujo.md`
- Create: `tests/test_skill_requirements_audit_orchestrator.py`

**Interfaces:**
- Consumes: nothing from Python tasks (content files)
- Produces:
  - Two SKILL.md-style files
  - Contract tests for audit_loop and orchestrator output formats

- [ ] **Step 1: Write contract tests**

```python
# tests/test_skill_requirements_audit_orchestrator.py
from __future__ import annotations
import json
from pathlib import Path
import pytest


EXPECTED_STEPS = ["prd", "epics", "hu_por_epica", "traceability", "flujos", "audit_loop"]


@pytest.fixture
def full_run_log(tmp_path: Path) -> Path:
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    events = [
        {"type": "advisor_note", "category": "sugerencia_transversal",
         "step": "epics", "suggestions": [], "accepted": []},
        {"type": "step_complete", "step": "prd",
         "output_files": ["docs/requirements/PRD.md"]},
        {"type": "step_complete", "step": "epics",
         "output_files": ["docs/requirements/epics/EPIC-1.md"]},
        {"type": "step_complete", "step": "hu_por_epica", "epic": "EPIC-1",
         "output_files": ["docs/requirements/stories/HU-1.1.md"]},
        {"type": "step_complete", "step": "traceability",
         "output_files": ["docs/requirements/traceability.md"]},
        {"type": "step_complete", "step": "flujos",
         "output_files": ["docs/requirements/flujos/FLUJO-1.md"]},
        {"type": "step_complete", "step": "audit_loop",
         "iterations": 1, "approved_by": "user"},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return tmp_path


def test_all_pipeline_steps_logged(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    completed = {e["step"] for e in events if e.get("type") == "step_complete"}
    for step in EXPECTED_STEPS:
        assert step in completed, f"Missing step_complete for: {step}"


def test_audit_loop_approved_by_user(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    audit = [e for e in events
             if e.get("step") == "audit_loop" and e.get("type") == "step_complete"]
    assert len(audit) == 1
    assert audit[0]["approved_by"] == "user"
    assert 1 <= audit[0]["iterations"] <= 3


def test_advisor_note_before_epics_close(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    notes = [e for e in events
             if e.get("type") == "advisor_note"
             and e.get("category") == "sugerencia_transversal"]
    assert len(notes) >= 1
```

- [ ] **Step 2: Run contract tests (pass via fixture)**

```bash
pytest tests/test_skill_requirements_audit_orchestrator.py -v
```
Expected: all PASS.

- [ ] **Step 3: Write `requirements-audit_loop.md`**

```markdown
<!-- src/factorysoftware/content/requirements/requirements-audit_loop.md -->
---
id: requirements
steps:
  - id: audit_loop
    depende_de: [traceability, flujos]
---

# Skill: requirements-audit_loop

Loop auditor-constructor (maximo 3 iteraciones) + gate de aprobacion humana explicita.
No avanza a Arquitectura sin aprobacion del usuario.

## Prerequisitos

- `docs/requirements/traceability.md` debe existir (evento `step_complete` de `traceability` en el log).
- Al menos un `docs/requirements/flujos/FLUJO-N.md` (evento `step_complete` de `flujos` en el log).
- Si alguno falta: listar que falta y no continuar.

## Loop (maximo 3 iteraciones)

Por cada iteracion:

- [ ] **Checks deterministicos (1-7):** Correr `factory validate requirements --project-root . --log .factory/log.jsonl` y capturar la lista de errores.
- [ ] Si hay errores: corregirlos editando los archivos afectados, luego volver a correr el validator para confirmar que quedo limpio.
- [ ] **Checks semanticos (8-11):** Revisar con lectura propia del agente:
  - Check 8: Cada Epica tiene meta de negocio trazable a un objetivo explicito del PRD (sin epicas flotantes fuera del alcance declarado).
  - Check 9: No hay contradicciones entre criterios de aceptacion de HU distintas dentro de la misma epica.
  - Check 10: El alcance del PRD no tiene huecos evidentes en las epicas (cobertura), ni las epicas se salen del alcance (scope creep).
  - Check 11: Todo objetivo multi-paso del PRD tiene al menos un FLUJO-N que lo cubre de inicio a fin. Un flujo importante sin documentar es hallazgo BLOQUEANTE.
- [ ] Si hay hallazgos semanticos: corregirlos.
- [ ] Si ambas validaciones pasan: salir del loop antes de las 3 iteraciones.

## Gate de aprobacion humana (BLOQUEO DURO)

Despues del loop (con o sin iteraciones pendientes):

- [ ] Presentar resumen al usuario: numero de iteraciones realizadas, hallazgos encontrados y corregidos, hallazgos que quedaron pendientes (si los hay).
- [ ] Preguntar explicitamente al usuario (via el mecanismo de pregunta del proveedor detectado):
  **"Apruebas el conjunto completo de Requerimientos (PRD + Epicas + HU + Flujos + Trazabilidad) y autorizas avanzar a la fase de Arquitectura?"**
- [ ] Si el usuario dice NO: listar los puntos que senala, corregirlos, y volver a preguntar (no cuenta como iteracion del loop auditor).
- [ ] Si el usuario dice SI:
  - Logear `{"type": "step_complete", "step": "audit_loop", "iterations": N, "approved_by": "user"}`.
  - Marcar la fase de Requerimientos como completa.
- [ ] NUNCA avanzar a Arquitectura sin que `approved_by: "user"` este en el log  -  ni si el usuario lo pide de forma ambigua, ni "por cortesia".
```

- [ ] **Step 4: Write `requirements-flujo.md`** (orchestrator)

```markdown
<!-- src/factorysoftware/content/requirements/requirements-flujo.md -->
---
id: requirements
steps:
  - id: flujo_completo
    depende_de: []
---

# Skill: requirements-flujo (Orquestador completo)

Encadena todo el pipeline de Requerimientos de inicio a fin sin pausas entre pasos intermedios.
Usar cuando el usuario quiere ejecutar la fase completa desde cero.
Para correr un solo paso, usar el skill individual (`requirements-prd`, `requirements-epics`, etc.).

## Prerequisitos

- `docs/requirements/` debe estar vacio, o el usuario debe confirmar explicitamente que desea continuar sobre un conjunto existente.

## Pipeline (ejecutar en este orden)

### Paso 1  -  requirements-prd
Sin prerequisitos. Pedir contexto al usuario si no fue provisto. Generar `docs/requirements/PRD.md`.

### Paso 2  -  requirements-epics
Prerequisito: PRD.md existe. Generar epicas + sugerir capacidades transversales.
**Unica pausa obligatoria del pipeline**: esperar confirmacion del usuario sobre las sugerencias transversales antes de continuar.

### Paso 3  -  requirements-hu_por_epica (fan-out)
Una instancia por epica. Ejecutar asi:
- **Si el proveedor soporta subagentes paralelos** (Antigravity: `invoke_subagent`): despachar todas las instancias en paralelo, una por epica, y esperar que todas terminen.
- **Si no soporta paralelo**: ejecutar una epica a la vez, de forma secuencial, cada una con su propio evento `step_complete` en el log. NUNCA colapsar en una sola pasada para todas las epicas.

### Paso 4  -  requirements-traceability + requirements-flujos (paralelo)
Ambos dependen solo de `hu_por_epica`. Ejecutar en paralelo si el proveedor lo soporta; si no, secuencial en cualquier orden.

### Paso 5  -  requirements-audit_loop
Loop auditor + gate de aprobacion humana. Ver skill `requirements-audit_loop`.

## Manejo de errores

- Si cualquier paso falla con hallazgos no corregibles en <= 3 iteraciones: pausar, presentar al usuario los hallazgos pendientes, y esperar instrucciones antes de continuar.
- Si el usuario pide avanzar a Arquitectura sin que el log contenga `{"step": "audit_loop", "approved_by": "user"}`: negarse, explicar que falta la aprobacion del gate, listar que hallazgos quedaron pendientes.
```

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all tests PASS (no regressions from prior tasks).

- [ ] **Step 6: Commit**

```bash
git add src/factorysoftware/content/requirements/requirements-audit_loop.md src/factorysoftware/content/requirements/requirements-flujo.md tests/test_skill_requirements_audit_orchestrator.py
git commit -m "feat(requirements): add audit_loop and requirements-flujo orchestrator skills"
```

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Task |
|---|---|
| Conjunto de documentos: PRD, epics/EPIC-N.md, stories/HU-N.M.md, flujos/FLUJO-N.md, traceability.md | Tasks 3, 4, 5 (skill content) |
| Esquema de IDs EPIC-N / HU-N.M / FLUJO-N, nunca reutilizados, retiradas/ | Tasks 1 (validator), 3, 4, 5 (skills) |
| flujos/FLUJO-N.md: frontmatter id+estado+hu, criterio de exito del flujo | Task 4 (skill + contract test) |
| Pipeline: prd -> epics -> hu_por_epica -> traceability + flujos -> audit_loop | Task 5 (orchestrator skill) |
| fan-out paralelizable en hu_por_epica; secuencial si no hay paralelo | Task 4 (skill instruccion) + Task 5 (orquestador) |
| requirements-flujo (modo completo, sin pausas intermedias) | Task 5 |
| requirements-\<step_id\> (modo manual, con chequeo de prerequisitos) | Tasks 3, 4 |
| Gate de aprobacion humana bloqueo duro | Task 5 (audit_loop skill) |
| Checks 1-7 deterministicos | Task 1 (validator.py) |
| Checks 8-11 semanticos | Task 5 (audit_loop skill instruccion) |
| CLI `factory validate requirements` | Task 2 |
| HU sin epica: error estructural | Task 1 (check 2) |
| Referencia circular en depende_de: bloqueante | Task 1 (check 3 + test) |
| Usuario fuerza avance sin gate: skill se niega | Task 5 (orchestrator skill) |
| pytest, cero IO externo, tmp_path | All tasks |
| advisor_note sugerencia_transversal obligatorio | Task 3 (epics skill) + Task 1 (check 6) |

### 2. Placeholder Scan

All Python steps contain real, runnable code. All skill files contain concrete numbered steps with exact field names, log event formats, and CLI commands. No "TBD" or "add validation" without specifics.

### 3. Type Consistency

- `validate_requirements(docs_root: Path, log_path: Path) -> list[str]`  -  consistent between Task 1 (definition) and Task 2 (call).
- `project_root` param in CLI (`args.project_root`) passed correctly to `validate_requirements` as `Path(args.project_root)`.
- Log event field `"type": "step_complete"` + `"step"`  -  consistent across all skill files and contract tests.
- `"depende_de"` as `list[str]`  -  consistent in validator (`fm.get("depende_de") or []`) and all HU skill instructions.
- `"hu"` as `list[str]` in FLUJO frontmatter  -  consistent in validator check 7 (`fm.get("hu") or []`) and flujos skill.
