# Core Personas & QA Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the missing `Core Personas` and `QA` phase content pack for FactorySoftware - including the validator, CLI, 13 QA skill files, and 3 core persona prompts.

**Architecture:** A new subcommand `factory validate qa` is added. The validator performs structural checks on QA planning and test coverage. Core personas live in the root of `src/factorysoftware/content/`, while QA skills live in `src/factorysoftware/content/qa/`.

**Tech Stack:** Python 3.11+, pytest, pathlib, PyYAML 6.0+, argparse.

**Spec:** `docs/superpowers/specs/2026-08-19-factory-core-design.md` and `docs/superpowers/specs/2026-08-19-qa-skill-design.md`

## Global Constraints

- Python >= 3.11; no external IO in tests - `tmp_path` fixtures only.
- PyYAML >= 6.0 already in `pyproject.toml` - do not add new dependencies.
- CLI entry point: `factory` (defined in `pyproject.toml`).
- Skill files live in `src/factorysoftware/content/qa/` and core files in `src/factorysoftware/content/`.
- All tests go in `tests/` flat.

---

### Task 1: Core Personas

**Files:**
- Create: `src/factorysoftware/content/advisor.md`
- Create: `src/factorysoftware/content/auditor.md`
- Create: `src/factorysoftware/content/auditor_integral.md`

**Interfaces:**
- Consumes: nothing
- Produces: 3 text files

- [ ] **Step 1: Write minimal implementation**
Create the 3 files with the personas prompts described in the Core Spec.
`advisor.md` provides opinions during artifact construction.
`auditor.md` runs checklists of a single phase against its own criteria.
`auditor_integral.md` runs after the phase auditor to validate consistency with previous phases.

- [ ] **Step 2: Commit**
`git add src/factorysoftware/content/*.md`
`git commit -m "feat(core): add core persona prompts"`

---

### Task 2: QA Validator Module

**Files:**
- Create: `src/factorysoftware/qa/__init__.py`
- Create: `src/factorysoftware/qa/validator.py`
- Create: `tests/test_validate_qa.py`

**Interfaces:**
- Consumes: nothing
- Produces: `validate_qa(project_root: Path) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate_qa.py
import pytest
from pathlib import Path
from factorysoftware.qa.validator import validate_qa

def test_validate_qa_clean(tmp_path: Path):
    docs = tmp_path / "docs" / "qa"
    docs.mkdir(parents=True, exist_ok=True)
    assert validate_qa(tmp_path) == []
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_validate_qa.py -v`

- [ ] **Step 3: Write minimal implementation**
Implement `validate_qa` in `src/factorysoftware/qa/validator.py` returning an empty list (minimal implementation for now).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_validate_qa.py -v`

- [ ] **Step 5: Commit**
`git add src/factorysoftware/qa/ tests/test_validate_qa.py`
`git commit -m "feat(qa): add qa structural validator stub"`

---

### Task 3: CLI Subcommand

**Files:**
- Modify: `src/factorysoftware/cli.py`
- Create: `tests/test_cli_validate_qa.py`

**Interfaces:**
- Consumes: `validate_qa`

- [ ] **Step 1: Write failing tests**
Test `factory validate qa --project-root .` in `tests/test_cli_validate_qa.py`.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Write minimal implementation**
Add parser for `validate qa` in `cli.py`.

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**
`git add src/factorysoftware/cli.py tests/test_cli_validate_qa.py`
`git commit -m "feat(qa): add CLI subcommand validate qa"`

---

### Task 4: QA Skill Files

**Files:**
- Create: `src/factorysoftware/content/qa/qa-coverage_gap_analysis.md`
- Create: `src/factorysoftware/content/qa/qa-qa_branch_setup.md`
- Create: `src/factorysoftware/content/qa/qa-integration_tests.md`
- Create: `src/factorysoftware/content/qa/qa-e2e_tests.md`
- Create: `src/factorysoftware/content/qa/qa-nfr_tests.md`
- Create: `src/factorysoftware/content/qa/qa-security_tests.md`
- Create: `src/factorysoftware/content/qa/qa-traceability_update.md`
- Create: `src/factorysoftware/content/qa/qa-qa_audit.md`
- Create: `src/factorysoftware/content/qa/qa-qa_integral_audit.md`
- Create: `src/factorysoftware/content/qa/qa-pr_gate.md`
- Create: `src/factorysoftware/content/qa/qa-flujo.md`
- Create: `src/factorysoftware/content/qa/qa-slide.md`
- Create: `src/factorysoftware/content/qa/qa-auditor.md`

- [ ] **Step 1: Create skill files**
Generate the 13 skill Markdown files in `src/factorysoftware/content/qa/` with valid `---` frontmatter for `id: qa` and `steps`. Make sure to describe the orchestrators (`qa-flujo`, `qa-slide`, `qa-auditor`) with their respective parameters.

- [ ] **Step 2: Commit**
`git add src/factorysoftware/content/qa/`
`git commit -m "feat(qa): add skill files for qa phase"`
