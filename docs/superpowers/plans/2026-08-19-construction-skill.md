# Construction Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `construction` content pack for FactorySoftware - a CLI validator, triage heuristics, epic dependency calculator, and 12 SKILL.md files for epic-based code generation.

**Architecture:** A new subcommand `factory validate construction` and `factory audit-triage` are added to the CLI. The validator performs structural checks on construction plans and functionality audits. Heuristics for audit dimensions and epic dependencies are implemented in Python to support the skills. Skill files live in `src/factorysoftware/content/construction/`.

**Tech Stack:** Python 3.11+, pytest, pathlib, PyYAML 6.0+, argparse.

**Spec:** `docs/superpowers/specs/2026-08-19-construction-skill-design.md`

## Global Constraints

- Python >= 3.11; no external IO in tests - `tmp_path` fixtures only.
- PyYAML >= 6.0 already in `pyproject.toml` - do not add new dependencies.
- CLI entry point: `factory` (defined in `pyproject.toml`).
- Skill files live in `src/factorysoftware/content/construction/`.
- All tests go in `tests/` flat.

---

### Task 1: Validator Module - Structural Checks

**Files:**
- Create: `src/factorysoftware/construction/__init__.py`
- Create: `src/factorysoftware/construction/validator.py`
- Create: `tests/test_validate_construction.py`

**Interfaces:**
- Consumes: nothing
- Produces: `validate_construction(project_root: Path) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate_construction.py
import pytest
from pathlib import Path
import yaml
from factorysoftware.construction.validator import validate_construction

def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

@pytest.fixture
def docs(tmp_path: Path) -> Path:
    req = tmp_path / "docs" / "requirements"
    arch = tmp_path / "docs" / "architecture"
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(req / "traceability.md", "| HU | Implementado |\n|---|---|\n| HU-1.1 | _p_ |")
    _write(arch / "apis" / "API-1.md", _fm({"id": "API-1"}))
    _write(arch / "adrs" / "ADR-1.md", _fm({"id": "ADR-1"}))
    _write(cons / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-1\n- depende_de: []"))
    return tmp_path

def test_validate_construction_clean(docs):
    assert validate_construction(docs) == []

def test_missing_api_reference(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-99\n- depende_de: []"))
    errors = validate_construction(docs)
    assert any("API-99" in e for e in errors)

def test_circular_dependency(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- depende_de: [TASK-1.2]\n\n### TASK-1.2\n- depende_de: [TASK-1.1]"))
    errors = validate_construction(docs)
    assert any("circular" in e.lower() for e in errors)

def test_invalid_role(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: alien\n- implementa: API-1\n- depende_de: []"))
    errors = validate_construction(docs)
    assert any("alien" in e for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_validate_construction.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
Implement `validate_construction` in `src/factorysoftware/construction/validator.py` checking tasks in `docs/construction/plan/*.md` for missing implementations in architecture, circular dependencies, and valid roles.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_validate_construction.py -v`

- [ ] **Step 5: Commit**
`git add src/factorysoftware/construction/ tests/test_validate_construction.py`
`git commit -m "feat(construction): add structural checks"`

---

### Task 2: Triage and Dependencies Logic

**Files:**
- Create: `src/factorysoftware/construction/triage.py`
- Create: `src/factorysoftware/construction/dependencies.py`
- Create: `tests/test_audit_triage.py`
- Create: `tests/test_epic_dependencies.py`

**Interfaces:**
- Produces: `decide_dimensions(diff_text: str, plan_text: str) -> list[str]`
- Produces: `compute_dependencies(epics_data: dict, hu_data: dict) -> dict[str, list[str]]`

- [ ] **Step 1: Write failing tests for triage and dependencies**
In `test_audit_triage.py`, test that `decide_dimensions` returns `["functionality", "practices"]` always. Returns `security` if diff contains `auth/` paths or plan has `rol: seguridad`. Returns `efficiency` if diff has `for.*for` or `SELECT`.
In `test_epic_dependencies.py`, test `compute_dependencies` finding dependencies between epics based on shared HUs or `depende_de` links across epics.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Write minimal implementation**
Implement `decide_dimensions` checking diff lines and plan text.
Implement `compute_dependencies` parsing the `depende_de` fields and returning epic id links.

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**
`git add src/factorysoftware/construction/ tests/test_audit_triage.py tests/test_epic_dependencies.py`
`git commit -m "feat(construction): add triage heuristics and epic dependencies logic"`

---

### Task 3: CLI Subcommands

**Files:**
- Modify: `src/factorysoftware/cli.py`
- Create: `tests/test_cli_validate_construction.py`

**Interfaces:**
- Consumes: `validate_construction`, `decide_dimensions`

- [ ] **Step 1: Write failing tests**
Test `factory validate construction` and `factory audit-triage --epic EPIC-1`.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Write minimal implementation**
Add parsers for `validate construction` and `audit-triage` in `cli.py`.

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**
`git add src/factorysoftware/cli.py tests/test_cli_validate_construction.py`
`git commit -m "feat(construction): add CLI subcommands"`

---

### Task 4: Skill Files (Planning and Orchestration)

**Files:**
- Create: `src/factorysoftware/content/construction/construction-task_planning.md`
- Create: `src/factorysoftware/content/construction/construction-plan_audit.md`
- Create: `src/factorysoftware/content/construction/construction-plan_integral_audit.md`
- Create: `src/factorysoftware/content/construction/construction-slide.md`
- Create: `src/factorysoftware/content/construction/construction-e2e.md`
- Create: `src/factorysoftware/content/construction/construction-auditor.md`

- [ ] **Step 1: Create planning skills**
Generate the 3 planning Markdown files specifying frontmatter and structural rules described in the spec.

- [ ] **Step 2: Create orchestrator skills**
Generate the 3 orchestrator files (`slide`, `e2e`, `auditor`).

- [ ] **Step 3: Commit**
`git add src/factorysoftware/content/construction/`
`git commit -m "feat(construction): add planning and orchestration skills"`

---

### Task 5: Skill Files (Execution and Audit)

**Files:**
- Create: `src/factorysoftware/content/construction/construction-branch_setup.md`
- Create: `src/factorysoftware/content/construction/construction-task_execution.md`
- Create: `src/factorysoftware/content/construction/construction-worktree_integration.md`
- Create: `src/factorysoftware/content/construction/construction-audit_triage.md`
- Create: `src/factorysoftware/content/construction/construction-construction_audit.md`
- Create: `src/factorysoftware/content/construction/construction-construction_integral_audit.md`
- Create: `src/factorysoftware/content/construction/construction-pr_gate.md`

- [ ] **Step 1: Create execution and integration skills**
Generate branch setup, task execution (TDD), worktree integration skills.

- [ ] **Step 2: Create audit skills**
Generate triage, construction audit (4 dimensions), integral audit, and PR gate skills.

- [ ] **Step 3: Commit**
`git add src/factorysoftware/content/construction/`
`git commit -m "feat(construction): add execution and audit skills"`
