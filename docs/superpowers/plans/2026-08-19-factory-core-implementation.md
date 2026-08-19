# Factory Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `factorysoftware` Python package — the vendor-agnostic
installer/render/state core that scaffolds the multi-phase SDLC skill
system into any project, per
`docs/superpowers/specs/2026-08-19-factory-core-design.md`.

**Architecture:** Three layers exactly as specced: `content` (parsed
markdown+YAML phase definitions, source of truth), `adapters` (one module
per AI provider, each implementing `detect`/`target_paths`/`render`), and
`cli` + `state` (lifecycle commands, append-only local log, manifest,
board). No layer calls an LLM API — the package only writes instruction
files an already-running assistant reads.

**Tech Stack:** Python 3.11+, pydantic v2 (data models), PyYAML (content
frontmatter), stdlib `argparse` (CLI — no new dependency needed), pytest +
pytest-mock (testing, zero real IO/network).

## Global Constraints

- Zero external IO in tests: no real network, no real git/test-runner
  calls, no real package registries. Filesystem via `tmp_path`.
- Every finding/decision that matters is logged to `.factory/log.jsonl` —
  this plan builds that mechanism first because everything else depends on
  it.
- Git Flow: this work happens on the existing `feature/factory-core-and-phase-specs`
  branch. Commits are plain (no AI co-authorship trailer, per prior
  decision in this project). Never commit directly to `main`/`develop`.
- Beck rules apply: no abstraction without a second real use, no
  speculative config, fewest elements that pass the tests.
- Real phase content (`content/requirements.md`, `content/architecture.md`,
  etc. — the actual prose for each phase spec) is **out of scope for this
  plan**. This plan builds the mechanism that parses and renders such
  content; the content itself is a follow-up subsystem. Tests use small
  fixture content strings, not the real phase specs.
- Antigravity's exact skill-loading convention is not officially confirmed
  from training knowledge. This plan grounds it in a real-world
  implementation observed during this project's research (a sibling repo,
  `FabricaAgenticaClaude`, whose `powers/INSTALL-ANTIGRAVITY.ps1` installs
  to `.agents/skills/<id>/SKILL.md` and `.agents/hooks.json`) rather than
  fabricating it — Task 20 flags the one piece (hook JSON schema) that
  still needs verification against current docs before this ships for
  real users.

---

## File Structure

```
factorysoftware/
  pyproject.toml
  src/factorysoftware/
    __init__.py
    state.py              # Manifest, ManifestFile, log, board
    content.py             # StepDecl, PhaseContent, parse_content()
    render.py               # build_skill_map()
    installer.py             # write_skills(), install_all/update_all/uninstall_all
    cli.py                   # argparse CLI: init/update/uninstall/status/log
    adapters/
      __init__.py
      base.py                # ProviderAdapter Protocol
      claude_code.py
      copilot.py
      codex.py
      opencode.py
      antigravity.py
      registry.py             # detect(), select()
  tests/
    conftest.py
    test_state.py
    test_board.py
    test_content.py
    test_render.py
    test_adapters.py
    test_installer.py
    test_cli.py
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/factorysoftware/__init__.py`
- Create: `src/factorysoftware/adapters/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_state.py` (placeholder import test)

**Interfaces:**
- Produces: importable package `factorysoftware`, pytest runnable via `pytest`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "factorysoftware"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.scripts]
factory = "factorysoftware.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package files**

`src/factorysoftware/__init__.py`:
```python
```

`src/factorysoftware/adapters/__init__.py`:
```python
```

- [ ] **Step 3: Write a trivial smoke test**

`tests/test_state.py`:
```python
def test_package_imports():
    import factorysoftware
```

- [ ] **Step 4: Install in editable mode and run**

Run: `pip install -e ".[dev]"` (or `uv pip install -e .` then
`pip install pytest pytest-mock` — no `[dev]` extra defined, install
pytest/pytest-mock directly: `pip install pytest pytest-mock`)
Then: `pytest tests/test_state.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/factorysoftware/__init__.py src/factorysoftware/adapters/__init__.py tests/conftest.py tests/test_state.py
git commit -m "chore: scaffold factorysoftware package"
```

---

### Task 2: Manifest model + read/write + hash

**Files:**
- Create: `src/factorysoftware/state.py`
- Modify: `tests/test_state.py`

**Interfaces:**
- Produces:
  - `compute_hash(content: str) -> str`
  - `class ManifestFile(BaseModel)`: `path: str`, `hash: str`, `skill_id: str`
  - `class Manifest(BaseModel)`: `version: str`, `installed_at: str`, `providers: list[str]`, `files: list[ManifestFile]`
  - `read_manifest(project_root: Path) -> Manifest | None`
  - `write_manifest(project_root: Path, manifest: Manifest) -> None`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_state.py` content with:
```python
from pathlib import Path
from factorysoftware.state import (
    compute_hash,
    Manifest,
    ManifestFile,
    read_manifest,
    write_manifest,
)


def test_package_imports():
    import factorysoftware


def test_compute_hash_is_deterministic():
    assert compute_hash("abc") == compute_hash("abc")
    assert compute_hash("abc") != compute_hash("abd")


def test_read_manifest_returns_none_when_missing(tmp_path: Path):
    assert read_manifest(tmp_path) is None


def test_write_then_read_manifest_roundtrip(tmp_path: Path):
    manifest = Manifest(
        version="0.1.0",
        installed_at="2026-08-19T00:00:00Z",
        providers=["claude_code"],
        files=[ManifestFile(path=".claude/skills/x/SKILL.md", hash="abc", skill_id="requirements-prd")],
    )
    write_manifest(tmp_path, manifest)
    loaded = read_manifest(tmp_path)
    assert loaded == manifest


def test_write_manifest_creates_factory_dir(tmp_path: Path):
    manifest = Manifest(version="0.1.0", installed_at="t", providers=[], files=[])
    write_manifest(tmp_path, manifest)
    assert (tmp_path / ".factory" / "manifest.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py -v`
Expected: FAIL (no module `factorysoftware.state`)

- [ ] **Step 3: Implement `state.py` (manifest portion)**

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ManifestFile(BaseModel):
    path: str
    hash: str
    skill_id: str


class Manifest(BaseModel):
    version: str
    installed_at: str
    providers: list[str]
    files: list[ManifestFile]


def _factory_dir(project_root: Path) -> Path:
    return project_root / ".factory"


def _manifest_path(project_root: Path) -> Path:
    return _factory_dir(project_root) / "manifest.json"


def read_manifest(project_root: Path) -> Manifest | None:
    path = _manifest_path(project_root)
    if not path.exists():
        return None
    return Manifest.model_validate_json(path.read_text(encoding="utf-8"))


def write_manifest(project_root: Path, manifest: Manifest) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    _manifest_path(project_root).write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/state.py tests/test_state.py
git commit -m "feat: add Manifest model with hash/read/write"
```

---

### Task 3: Append-only log (`log.jsonl`)

**Files:**
- Modify: `src/factorysoftware/state.py`
- Modify: `tests/test_state.py`

**Interfaces:**
- Consumes: `_factory_dir(project_root)` (private helper from Task 2).
- Produces:
  - `append_log(project_root: Path, event_type: str, data: dict) -> None`
  - `read_log(project_root: Path) -> list[dict]`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_state.py`:
```python
from factorysoftware.state import append_log, read_log


def test_read_log_empty_when_missing(tmp_path: Path):
    assert read_log(tmp_path) == []


def test_append_log_then_read_roundtrip(tmp_path: Path):
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "prd"})
    append_log(tmp_path, "phase_gate", {"phase": "requirements", "result": "approved"})
    events = read_log(tmp_path)
    assert len(events) == 2
    assert events[0]["event_type"] == "pipeline_step"
    assert events[0]["data"]["step_id"] == "prd"
    assert "ts" in events[0]
    assert events[1]["event_type"] == "phase_gate"


def test_append_log_is_append_only(tmp_path: Path):
    append_log(tmp_path, "a", {})
    append_log(tmp_path, "b", {})
    lines = (tmp_path / ".factory" / "log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    json.loads(lines[0])
    json.loads(lines[1])
```

Add `import json` near the top of `tests/test_state.py` if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py -v -k log`
Expected: FAIL (no `append_log`/`read_log`)

- [ ] **Step 3: Implement log functions**

Append to `src/factorysoftware/state.py`:
```python
from datetime import datetime, timezone


def _log_path(project_root: Path) -> Path:
    return _factory_dir(project_root) / "log.jsonl"


def append_log(project_root: Path, event_type: str, data: dict) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
    }
    with _log_path(project_root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(project_root: Path) -> list[dict]:
    path = _log_path(project_root)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
```

Add `import json` to the top imports of `state.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/state.py tests/test_state.py
git commit -m "feat: add append-only log.jsonl read/write"
```

---

### Task 4: Board generation (`.factory/board.md`)

**Files:**
- Create: `src/factorysoftware/state.py` (extend)
- Create: `tests/test_board.py`

**Interfaces:**
- Consumes: `read_log(project_root) -> list[dict]` (Task 3).
- Produces:
  - `generate_board(project_root: Path) -> str`
  - `write_board(project_root: Path) -> None`

- [ ] **Step 1: Write failing tests**

`tests/test_board.py`:
```python
from pathlib import Path

from factorysoftware.state import append_log, generate_board, write_board


def test_generate_board_no_events(tmp_path: Path):
    board = generate_board(tmp_path)
    assert "Tablero de la Fábrica" in board
    assert "no editar a mano" in board


def test_generate_board_shows_phase_gate_status(tmp_path: Path):
    append_log(tmp_path, "phase_gate", {"phase": "requirements", "result": "approved", "iterations": 1})
    board = generate_board(tmp_path)
    assert "Requerimientos" in board
    assert "✅" in board


def test_generate_board_shows_epic_table(tmp_path: Path):
    append_log(
        tmp_path,
        "pipeline_step",
        {"phase": "construction", "step_id": "task_execution", "scope": "EPIC-1", "estado": "iniciado"},
    )
    append_log(
        tmp_path,
        "pipeline_step",
        {"phase": "construction", "step_id": "pr_gate", "scope": "EPIC-2", "estado": "completado"},
    )
    board = generate_board(tmp_path)
    assert "EPIC-1" in board
    assert "EPIC-2" in board
    assert "task_execution" in board


def test_write_board_creates_file_and_overwrites(tmp_path: Path):
    write_board(tmp_path)
    board_path = tmp_path / ".factory" / "board.md"
    assert board_path.exists()
    board_path.write_text("edición manual del usuario", encoding="utf-8")
    write_board(tmp_path)
    assert "edición manual" not in board_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_board.py -v`
Expected: FAIL (no `generate_board`/`write_board`)

- [ ] **Step 3: Implement board generation**

Append to `src/factorysoftware/state.py`:
```python
_PHASE_ORDER = ["requirements", "architecture", "construction", "qa"]
_PHASE_LABELS = {
    "requirements": "Requerimientos",
    "architecture": "Arquitectura",
    "construction": "Construcción",
    "qa": "QA",
}


def _phase_status_icon(events: list[dict], phase: str) -> str:
    gates = [
        e for e in events
        if e["event_type"] == "phase_gate" and e["data"].get("phase") == phase
    ]
    if not gates:
        return "⚪ no iniciado"
    last = gates[-1]
    if last["data"].get("result") == "approved":
        return "✅ completo"
    return "🟡 en progreso"


def _epic_rows(events: list[dict], phase: str) -> list[tuple[str, str]]:
    steps = [
        e for e in events
        if e["event_type"] == "pipeline_step"
        and e["data"].get("phase") == phase
        and e["data"].get("scope")
        and e["data"]["scope"] != "all"
    ]
    latest_by_epic: dict[str, dict] = {}
    for e in steps:
        latest_by_epic[e["data"]["scope"]] = e["data"]
    rows = []
    for epic, data in sorted(latest_by_epic.items()):
        estado = "🟢 en progreso" if data.get("estado") == "iniciado" else "✅ completo"
        rows.append((epic, f"{data.get('step_id', '')} — {estado}"))
    return rows


def generate_board(project_root: Path) -> str:
    events = read_log(project_root)
    lines = ["# Tablero de la Fábrica (auto-generado, no editar a mano)", ""]
    for phase in _PHASE_ORDER:
        lines.append(f"### {_PHASE_LABELS[phase]}: {_phase_status_icon(events, phase)}")
    rows = []
    for phase in _PHASE_ORDER:
        rows.extend(_epic_rows(events, phase))
    if rows:
        lines.append("")
        lines.append("## Detalle por unidad")
        lines.append("")
        lines.append("| Unidad | Paso |")
        lines.append("|---|---|")
        for epic, detail in rows:
            lines.append(f"| {epic} | {detail} |")
    return "\n".join(lines) + "\n"


def write_board(project_root: Path) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    (_factory_dir(project_root) / "board.md").write_text(
        generate_board(project_root), encoding="utf-8"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_board.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/state.py tests/test_board.py
git commit -m "feat: generate .factory/board.md from log events"
```

---

### Task 5: Content models + parser

**Files:**
- Create: `src/factorysoftware/content.py`
- Create: `tests/test_content.py`

**Interfaces:**
- Produces:
  - `class StepDecl(BaseModel)`: `id: str`, `depende_de: list[str] = []`, `fan_out: str | None = None`, `paralelizable: bool = False`, `rol: str | None = None`
  - `class PhaseContent(BaseModel)`: `id: str`, `unidad_principal: str | None = None`, `flujo_skill_name: str = "flujo"`, `steps: list[StepDecl]`, `preamble: str`, `sections: dict[str, str]`
  - `parse_content(path: Path) -> PhaseContent`

Content file format (this is the interface future phase-content work must
follow): YAML frontmatter between `---` markers with `id`,
`unidad_principal` (optional), `flujo_skill_name` (optional), `steps` (list
of step dicts); markdown body with one `## Paso: <step_id>` heading per
declared step, everything before the first such heading is the preamble.

- [ ] **Step 1: Write failing tests**

`tests/test_content.py`:
```python
from pathlib import Path

from factorysoftware.content import PhaseContent, StepDecl, parse_content


FIXTURE = """\
---
id: requirements
steps:
  - id: prd
    depende_de: []
    fan_out: null
    paralelizable: false
  - id: epics
    depende_de: [prd]
    fan_out: null
    paralelizable: false
    rol: null
---
Preámbulo de la fase de Requerimientos.

## Paso: prd

Instrucciones del paso PRD.

## Paso: epics

Instrucciones del paso Épicas.
"""

FIXTURE_WITH_UNIT = """\
---
id: construction
unidad_principal: slide
flujo_skill_name: e2e
steps:
  - id: task_planning
    depende_de: []
    fan_out: "una por Épica"
    paralelizable: true
  - id: construction_audit
    depende_de: [task_planning]
    fan_out: null
    paralelizable: false
    rol: Auditor
---
Preámbulo de Construcción.

## Paso: task_planning

Planificá.

## Paso: construction_audit

Auditá.
"""


def test_parse_content_basic(tmp_path: Path):
    p = tmp_path / "requirements.md"
    p.write_text(FIXTURE, encoding="utf-8")
    content = parse_content(p)
    assert content.id == "requirements"
    assert content.unidad_principal is None
    assert content.flujo_skill_name == "flujo"
    assert [s.id for s in content.steps] == ["prd", "epics"]
    assert content.steps[1].depende_de == ["prd"]
    assert "Preámbulo" in content.preamble
    assert "Instrucciones del paso PRD" in content.sections["prd"]
    assert "Instrucciones del paso Épicas" in content.sections["epics"]


def test_parse_content_with_unit_and_role(tmp_path: Path):
    p = tmp_path / "construction.md"
    p.write_text(FIXTURE_WITH_UNIT, encoding="utf-8")
    content = parse_content(p)
    assert content.unidad_principal == "slide"
    assert content.flujo_skill_name == "e2e"
    assert content.steps[0].fan_out == "una por Épica"
    assert content.steps[0].paralelizable is True
    assert content.steps[1].rol == "Auditor"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_content.py -v`
Expected: FAIL (no module `factorysoftware.content`)

- [ ] **Step 3: Implement `content.py`**

```python
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel

_SECTION_RE = re.compile(r"^## Paso: (?P<id>\S+)\s*$", re.MULTILINE)


class StepDecl(BaseModel):
    id: str
    depende_de: list[str] = []
    fan_out: str | None = None
    paralelizable: bool = False
    rol: str | None = None


class PhaseContent(BaseModel):
    id: str
    unidad_principal: str | None = None
    flujo_skill_name: str = "flujo"
    steps: list[StepDecl]
    preamble: str
    sections: dict[str, str]


def parse_content(path: Path) -> PhaseContent:
    text = path.read_text(encoding="utf-8")
    _, frontmatter_raw, body = text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_raw)
    steps = [StepDecl(**s) for s in frontmatter["steps"]]

    matches = list(_SECTION_RE.finditer(body))
    preamble = body[: matches[0].start()].strip() if matches else body.strip()
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group("id")] = body[start:end].strip()

    return PhaseContent(
        id=frontmatter["id"],
        unidad_principal=frontmatter.get("unidad_principal"),
        flujo_skill_name=frontmatter.get("flujo_skill_name", "flujo"),
        steps=steps,
        preamble=preamble,
        sections=sections,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_content.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content.py tests/test_content.py
git commit -m "feat: parse phase content markdown+YAML into PhaseContent"
```

---

### Task 6: Skill map builder

**Files:**
- Create: `src/factorysoftware/render.py`
- Create: `tests/test_render.py`

**Interfaces:**
- Consumes: `PhaseContent`, `StepDecl` (Task 5).
- Produces: `build_skill_map(content: PhaseContent) -> dict[str, str]`

- [ ] **Step 1: Write failing tests**

`tests/test_render.py`:
```python
from factorysoftware.content import PhaseContent, StepDecl
from factorysoftware.render import build_skill_map


def _content(unidad_principal=None, flujo_skill_name="flujo"):
    return PhaseContent(
        id="requirements",
        unidad_principal=unidad_principal,
        flujo_skill_name=flujo_skill_name,
        steps=[
            StepDecl(id="prd", depende_de=[]),
            StepDecl(id="epics", depende_de=["prd"]),
            StepDecl(id="audit_loop", depende_de=["epics"], rol="Auditor"),
        ],
        preamble="Preámbulo.",
        sections={
            "prd": "Hacé el PRD.",
            "epics": "Hacé las épicas.",
            "audit_loop": "Auditá.",
        },
    )


def test_manual_skills_one_per_step():
    skills = build_skill_map(_content())
    assert "requirements-prd" in skills
    assert "requirements-epics" in skills
    assert "requirements-audit_loop" in skills
    assert "Hacé el PRD." in skills["requirements-prd"]
    assert "Preámbulo." in skills["requirements-prd"]


def test_flujo_skill_contains_all_sections_in_order():
    skills = build_skill_map(_content())
    flujo = skills["requirements-flujo"]
    assert flujo.index("Hacé el PRD.") < flujo.index("Hacé las épicas.") < flujo.index("Auditá.")


def test_flujo_skill_uses_custom_name():
    skills = build_skill_map(_content(flujo_skill_name="e2e"))
    assert "requirements-e2e" in skills
    assert "requirements-flujo" not in skills


def test_no_slide_or_auditor_without_unidad_principal():
    skills = build_skill_map(_content())
    assert not any(k.endswith("-slide") for k in skills)
    assert "requirements-auditor" not in skills


def test_slide_and_auditor_present_with_unidad_principal():
    skills = build_skill_map(_content(unidad_principal="slide"))
    assert "requirements-slide" in skills
    assert "requirements-auditor" in skills


def test_auditor_skill_only_has_auditor_role_sections():
    skills = build_skill_map(_content(unidad_principal="slide"))
    auditor = skills["requirements-auditor"]
    assert "Auditá." in auditor
    assert "Hacé el PRD." not in auditor
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_render.py -v`
Expected: FAIL (no module `factorysoftware.render`)

- [ ] **Step 3: Implement `render.py`**

```python
from __future__ import annotations

from factorysoftware.content import PhaseContent

_AUDITOR_ROLES = {"Auditor", "Auditor Integral"}


def _joined_sections(content: PhaseContent) -> str:
    return "\n\n".join(content.sections[s.id] for s in content.steps)


def build_skill_map(content: PhaseContent) -> dict[str, str]:
    skills: dict[str, str] = {}

    for step in content.steps:
        skill_id = f"{content.id}-{step.id}"
        skills[skill_id] = f"{content.preamble}\n\n{content.sections[step.id]}\n"

    flujo_id = f"{content.id}-{content.flujo_skill_name}"
    skills[flujo_id] = (
        f"{content.preamble}\n\n{_joined_sections(content)}\n\n"
        "(Ejecutar todos los pasos anteriores en orden, encadenados, sin "
        "parar a esperar confirmación entre pasos intermedios.)\n"
    )

    if content.unidad_principal:
        slide_id = f"{content.id}-{content.unidad_principal}"
        skills[slide_id] = (
            f"{content.preamble}\n\n{_joined_sections(content)}\n\n"
            "(Ejecutar acotado a la unidad recibida como argumento de invocación.)\n"
        )

        auditor_sections = "\n\n".join(
            content.sections[s.id] for s in content.steps if s.rol in _AUDITOR_ROLES
        )
        skills[f"{content.id}-auditor"] = f"{content.preamble}\n\n{auditor_sections}\n"

    return skills
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_render.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/render.py tests/test_render.py
git commit -m "feat: build 4-skill-type map from PhaseContent"
```

---

### Task 7: ProviderAdapter protocol

**Files:**
- Create: `src/factorysoftware/adapters/base.py`
- Create: `tests/test_adapters.py`

**Interfaces:**
- Produces: `class ProviderAdapter(Protocol)` with `name: str`,
  `detect(self, project_root: Path) -> bool`,
  `target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]`,
  `render(self, skill_id: str, content_md: str) -> str`.

- [ ] **Step 1: Write failing test**

`tests/test_adapters.py`:
```python
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter


class _FakeAdapter:
    name = "fake"

    def detect(self, project_root: Path) -> bool:
        return True

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {sid: project_root / f"{sid}.md" for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return content_md


def test_fake_adapter_satisfies_protocol(tmp_path: Path):
    adapter: ProviderAdapter = _FakeAdapter()
    assert adapter.detect(tmp_path) is True
    assert adapter.target_paths(tmp_path, ["a"]) == {"a": tmp_path / "a.md"}
    assert adapter.render("a", "x") == "x"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adapters.py -v`
Expected: FAIL (no module `factorysoftware.adapters.base`)

- [ ] **Step 3: Implement `adapters/base.py`**

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]: ...

    def render(self, skill_id: str, content_md: str) -> str: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/base.py tests/test_adapters.py
git commit -m "feat: define ProviderAdapter protocol"
```

---

### Task 8: Claude Code adapter

**Files:**
- Create: `src/factorysoftware/adapters/claude_code.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Consumes: `ProviderAdapter` protocol shape (Task 7).
- Produces: `class ClaudeCodeAdapter`, `name = "claude_code"`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
from factorysoftware.adapters.claude_code import ClaudeCodeAdapter


def test_claude_code_detect_true_when_dot_claude_dir(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    assert ClaudeCodeAdapter().detect(tmp_path) is True


def test_claude_code_detect_false_when_absent(tmp_path: Path):
    assert ClaudeCodeAdapter().detect(tmp_path) is False


def test_claude_code_target_paths_one_dir_per_skill(tmp_path: Path):
    paths = ClaudeCodeAdapter().target_paths(tmp_path, ["requirements-prd", "requirements-flujo"])
    assert paths["requirements-prd"] == tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md"
    assert paths["requirements-flujo"] == tmp_path / ".claude" / "skills" / "requirements-flujo" / "SKILL.md"


def test_claude_code_render_adds_frontmatter():
    rendered = ClaudeCodeAdapter().render("requirements-prd", "Hacé el PRD.")
    assert rendered.startswith("---\n")
    assert "name: requirements-prd" in rendered
    assert "description:" in rendered
    assert "Hacé el PRD." in rendered
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k claude_code`
Expected: FAIL (no module `factorysoftware.adapters.claude_code`)

- [ ] **Step 3: Implement `adapters/claude_code.py`**

```python
from __future__ import annotations

from pathlib import Path


class ClaudeCodeAdapter:
    name = "claude_code"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".claude").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {
            sid: project_root / ".claude" / "skills" / sid / "SKILL.md"
            for sid in skill_ids
        }

    def render(self, skill_id: str, content_md: str) -> str:
        description = f"Factory skill: {skill_id}"
        return f"---\nname: {skill_id}\ndescription: {description}\n---\n\n{content_md}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/claude_code.py tests/test_adapters.py
git commit -m "feat: add Claude Code adapter (multi-file, SKILL.md)"
```

---

### Task 9: Claude Code Git Flow hook installer

**Files:**
- Modify: `src/factorysoftware/adapters/claude_code.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Produces: `ClaudeCodeAdapter.install_gitflow_hook(self, project_root: Path) -> list[Path]`
  (returns the list of files it wrote, for the manifest).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
import json


def test_install_gitflow_hook_writes_guard_script(tmp_path: Path):
    written = ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    guard = tmp_path / ".claude" / "hooks" / "gitflow-guard.sh"
    assert guard in written
    assert guard.exists()
    assert "git commit" in guard.read_text(encoding="utf-8")
    assert "main" in guard.read_text(encoding="utf-8")


def test_install_gitflow_hook_registers_in_settings(tmp_path: Path):
    ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    pretooluse = settings["hooks"]["PreToolUse"]
    assert any(entry["matcher"] == "Bash" for entry in pretooluse)


def test_install_gitflow_hook_merges_existing_settings(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"otherSetting": True}), encoding="utf-8"
    )
    ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings["otherSetting"] is True
    assert "hooks" in settings
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k gitflow_hook`
Expected: FAIL (no `install_gitflow_hook` method)

- [ ] **Step 3: Implement the hook installer**

Append to `src/factorysoftware/adapters/claude_code.py`:
```python
import json

_GUARD_SCRIPT = """\
#!/bin/sh
input=$(cat)
cmd=$(printf '%s' "$input" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)
case "$cmd" in
  *"git commit"*|*"git push"*)
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ "$branch" = "main" ] || [ "$branch" = "develop" ]; then
      echo "Bloqueado: commit/push directo a $branch prohibido por Git Flow. Usa una rama feature/*." >&2
      exit 2
    fi
    ;;
esac
exit 0
"""


class ClaudeCodeAdapter:
    # ... (existing name/detect/target_paths/render above)

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        hooks_dir = project_root / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        guard_path = hooks_dir / "gitflow-guard.sh"
        guard_path.write_text(_GUARD_SCRIPT, encoding="utf-8")
        guard_path.chmod(0o755)

        settings_path = project_root / ".claude" / "settings.json"
        settings = {}
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
        settings["hooks"]["PreToolUse"].append(
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": str(guard_path)}],
            }
        )
        settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

        return [guard_path, settings_path]
```

Note: this appends to `ClaudeCodeAdapter`, don't duplicate the class — add
the method and the `import json` / `_GUARD_SCRIPT` constant to the existing
file from Task 8.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/claude_code.py tests/test_adapters.py
git commit -m "feat: install PreToolUse hook blocking direct commits to main/develop"
```

---

### Task 10: Registry — provider autodetection

**Files:**
- Create: `src/factorysoftware/adapters/registry.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Consumes: `ProviderAdapter` (Task 7), `ClaudeCodeAdapter` (Task 8).
- Produces:
  - `ALL_ADAPTERS: list[ProviderAdapter]`
  - `detect(project_root: Path, adapters: list[ProviderAdapter] | None = None) -> list[ProviderAdapter]`
  - `select(names: list[str], adapters: list[ProviderAdapter] | None = None) -> list[ProviderAdapter]`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
from factorysoftware.adapters import registry


class _AlwaysYes:
    name = "always_yes"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


class _AlwaysNo:
    name = "always_no"
    def detect(self, project_root): return False
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


def test_detect_returns_all_matching_adapters(tmp_path: Path):
    found = registry.detect(tmp_path, adapters=[_AlwaysYes(), _AlwaysNo()])
    assert [a.name for a in found] == ["always_yes"]


def test_detect_returns_multiple_when_several_match(tmp_path: Path):
    found = registry.detect(tmp_path, adapters=[_AlwaysYes(), _AlwaysYes()])
    assert len(found) == 2


def test_detect_empty_when_none_match(tmp_path: Path):
    assert registry.detect(tmp_path, adapters=[_AlwaysNo()]) == []


def test_select_by_name_overrides_detection(tmp_path: Path):
    selected = registry.select(["always_no"], adapters=[_AlwaysYes(), _AlwaysNo()])
    assert [a.name for a in selected] == ["always_no"]


def test_all_adapters_includes_claude_code():
    names = [a.name for a in registry.ALL_ADAPTERS]
    assert "claude_code" in names


class _Raises:
    name = "raises"
    def detect(self, project_root): raise OSError("permission denied")
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


def test_detect_skips_adapter_that_raises_and_keeps_others(tmp_path: Path, capsys):
    found = registry.detect(tmp_path, adapters=[_Raises(), _AlwaysYes()])
    assert [a.name for a in found] == ["always_yes"]
    assert "raises" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k "registry or detect or select"`
Expected: FAIL (no module `factorysoftware.adapters.registry`)

- [ ] **Step 3: Implement `adapters/registry.py`**

```python
from __future__ import annotations

import sys
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.adapters.claude_code import ClaudeCodeAdapter

ALL_ADAPTERS: list[ProviderAdapter] = [ClaudeCodeAdapter()]


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/registry.py tests/test_adapters.py
git commit -m "feat: add provider registry with detect() and select()"
```

---

### Task 11: `write_skills` — grouping and file writing

**Files:**
- Create: `src/factorysoftware/installer.py`
- Create: `tests/test_installer.py`

**Interfaces:**
- Consumes: `ProviderAdapter` (Task 7), `ManifestFile`/`compute_hash` (Task 2).
- Produces: `write_skills(project_root: Path, adapter: ProviderAdapter, skill_map: dict[str, str]) -> list[ManifestFile]`

Design note for this task: single-file providers (added in later tasks)
map multiple `skill_id`s to the *same* target path via `target_paths`. When
that happens, `write_skills` groups by path, concatenates the rendered
content for all skill_ids sharing that path (sorted by skill_id for
determinism), writes the file once, and records **one** `ManifestFile` per
unique path with `skill_id` set to the sorted, comma-joined list of the
skill_ids it contains — so the manifest hash always matches exactly what's
on disk.

- [ ] **Step 1: Write failing tests**

`tests/test_installer.py`:
```python
from pathlib import Path

from factorysoftware.installer import write_skills
from factorysoftware.state import compute_hash


class _MultiFileAdapter:
    name = "multi"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        return {sid: project_root / f"{sid}.md" for sid in skill_ids}
    def render(self, skill_id, content_md):
        return f"# {skill_id}\n{content_md}"


class _SingleFileAdapter:
    name = "single"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        target = project_root / "combined.md"
        return {sid: target for sid in skill_ids}
    def render(self, skill_id, content_md):
        return f"## {skill_id}\n{content_md}"


def test_write_skills_one_file_per_skill(tmp_path: Path):
    files = write_skills(tmp_path, _MultiFileAdapter(), {"a": "content a", "b": "content b"})
    assert (tmp_path / "a.md").read_text(encoding="utf-8") == "# a\ncontent a"
    assert (tmp_path / "b.md").read_text(encoding="utf-8") == "# b\ncontent b"
    assert len(files) == 2
    assert {f.skill_id for f in files} == {"a", "b"}


def test_write_skills_groups_single_file_adapter(tmp_path: Path):
    files = write_skills(tmp_path, _SingleFileAdapter(), {"a": "content a", "b": "content b"})
    combined = tmp_path / "combined.md"
    text = combined.read_text(encoding="utf-8")
    assert "## a\ncontent a" in text
    assert "## b\ncontent b" in text
    assert text.index("## a") < text.index("## b")
    assert len(files) == 1
    assert files[0].skill_id == "a,b"
    assert files[0].hash == compute_hash(text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_installer.py -v`
Expected: FAIL (no module `factorysoftware.installer`)

- [ ] **Step 3: Implement `installer.py` (write_skills only)**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_installer.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/installer.py tests/test_installer.py
git commit -m "feat: write_skills groups multi-skill single-file targets deterministically"
```

---

### Task 12: `install_all` orchestration

**Files:**
- Modify: `src/factorysoftware/installer.py`
- Modify: `tests/test_installer.py`

**Interfaces:**
- Consumes: `write_skills` (Task 11), `parse_content` (Task 5),
  `build_skill_map` (Task 6), `Manifest`/`write_manifest` (Task 2).
- Produces: `install_all(project_root: Path, content_dir: Path, adapters: list[ProviderAdapter]) -> Manifest`

- [ ] **Step 1: Write failing test**

Append to `tests/test_installer.py`:
```python
from factorysoftware.installer import install_all
from factorysoftware.state import read_manifest

_FIXTURE_PHASE = """\
---
id: requirements
steps:
  - id: prd
    depende_de: []
---
Preámbulo.

## Paso: prd

Hacé el PRD.
"""


def test_install_all_writes_files_and_manifest(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")

    manifest = install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert manifest.providers == ["multi"]
    assert len(manifest.files) == 2  # requirements-prd, requirements-flujo
    assert read_manifest(tmp_path) == manifest
    assert (tmp_path / "requirements-prd.md").exists()
    assert (tmp_path / "requirements-flujo.md").exists()


class _UnwritableAdapter:
    name = "unwritable"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        return {sid: project_root / "nope" / f"{sid}.md" for sid in skill_ids}
    def render(self, skill_id, content_md):
        raise OSError("simulated permission denied")


def test_install_all_skips_adapter_that_fails_to_write(tmp_path: Path, capsys):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")

    manifest = install_all(tmp_path, content_dir, adapters=[_UnwritableAdapter(), _MultiFileAdapter()])

    assert manifest.providers == ["unwritable", "multi"]
    assert (tmp_path / "requirements-prd.md").exists()  # multi still wrote its files
    assert "unwritable" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_installer.py -v -k install_all`
Expected: FAIL (no `install_all`)

- [ ] **Step 3: Implement `install_all`**

Append to `src/factorysoftware/installer.py`:
```python
import sys
from datetime import datetime, timezone

from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map
from factorysoftware.state import Manifest, write_manifest

_VERSION = "0.1.0"


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_installer.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/installer.py tests/test_installer.py
git commit -m "feat: install_all renders every content file for every adapter"
```

---

### Task 13: `update_all` — hash-safe re-render

**Files:**
- Modify: `src/factorysoftware/installer.py`
- Modify: `tests/test_installer.py`

**Interfaces:**
- Consumes: everything from Task 12 plus `read_manifest` (Task 2).
- Produces: `update_all(project_root: Path, content_dir: Path, adapters: list[ProviderAdapter]) -> tuple[Manifest, list[str]]`
  (manifest, list of skipped-path warnings).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_installer.py`:
```python
from factorysoftware.installer import update_all


def test_update_all_overwrites_untouched_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    (content_dir / "requirements.md").write_text(
        _FIXTURE_PHASE.replace("Hacé el PRD.", "Hacé el PRD actualizado."), encoding="utf-8"
    )
    manifest, warnings = update_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert "Hacé el PRD actualizado." in (tmp_path / "requirements-prd.md").read_text(encoding="utf-8")
    assert warnings == []


def test_update_all_skips_user_edited_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    (tmp_path / "requirements-prd.md").write_text("edición manual del usuario", encoding="utf-8")
    (content_dir / "requirements.md").write_text(
        _FIXTURE_PHASE.replace("Hacé el PRD.", "Hacé el PRD actualizado."), encoding="utf-8"
    )
    manifest, warnings = update_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert (tmp_path / "requirements-prd.md").read_text(encoding="utf-8") == "edición manual del usuario"
    assert any("requirements-prd" in w for w in warnings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_installer.py -v -k update_all`
Expected: FAIL (no `update_all`)

- [ ] **Step 3: Implement `update_all`**

Append to `src/factorysoftware/installer.py`:
```python
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
            paths = adapter.target_paths(project_root, skill_ids)
            by_path: dict[Path, list[str]] = {}
            for sid in skill_ids:
                by_path.setdefault(paths[sid], []).append(sid)

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
```

Add `from factorysoftware.state import ManifestFile, compute_hash, read_manifest`
to the existing imports at the top of `installer.py` (extend the line
already importing `Manifest, write_manifest` from Task 12).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_installer.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/installer.py tests/test_installer.py
git commit -m "feat: update_all preserves user-edited files, warns instead of overwriting"
```

---

### Task 14: `uninstall_all`

**Files:**
- Modify: `src/factorysoftware/installer.py`
- Modify: `tests/test_installer.py`

**Interfaces:**
- Produces: `uninstall_all(project_root: Path) -> list[str]` (returns list
  of warnings for skipped files).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_installer.py`:
```python
from factorysoftware.installer import uninstall_all
from factorysoftware.state import read_manifest as _read_manifest_for_test


def test_uninstall_all_removes_manifest_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert not (tmp_path / "requirements-prd.md").exists()
    assert not (tmp_path / "requirements-flujo.md").exists()
    assert _read_manifest_for_test(tmp_path) is None


def test_uninstall_all_skips_user_edited_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])
    (tmp_path / "requirements-prd.md").write_text("edición manual", encoding="utf-8")

    warnings = uninstall_all(tmp_path)

    assert (tmp_path / "requirements-prd.md").exists()
    assert any("requirements-prd" in w for w in warnings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_installer.py -v -k uninstall_all`
Expected: FAIL (no `uninstall_all`)

- [ ] **Step 3: Implement `uninstall_all`**

Append to `src/factorysoftware/installer.py`:
```python
def uninstall_all(project_root: Path) -> list[str]:
    manifest = read_manifest(project_root)
    if manifest is None:
        return []

    warnings: list[str] = []
    for f in manifest.files:
        path = project_root / f.path
        if not path.exists():
            continue
        on_disk_hash = compute_hash(path.read_text(encoding="utf-8"))
        if on_disk_hash != f.hash:
            warnings.append(f"{f.path} (skill(s): {f.skill_id}) fue editado a mano, no se borra")
            continue
        path.unlink()

    if not warnings:
        (project_root / ".factory" / "manifest.json").unlink(missing_ok=True)

    return warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_installer.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/installer.py tests/test_installer.py
git commit -m "feat: uninstall_all removes only manifest-owned, untouched files"
```

---

### Task 15: CLI — `init` and `update` commands

**Files:**
- Create: `src/factorysoftware/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `registry.detect`/`registry.select` (Task 10), `install_all`/`update_all` (Tasks 12-13), `append_log` (Task 3).
- Produces: `build_parser() -> argparse.ArgumentParser`, `main(argv: list[str] | None = None) -> int`.

For this task, `init`/`update` operate against a `content_dir` resolved as
`Path(__file__).parent / "content"` by default, overridable via
`--content-dir` for testing (this flag is a test seam, not user-facing
documentation — the spec doesn't require it, but "no real content yet"
makes it necessary to test the CLI without the package's real content
directory existing).

- [ ] **Step 1: Write failing tests**

`tests/test_cli.py`:
```python
from pathlib import Path

from factorysoftware.cli import main


_FIXTURE_PHASE = """\
---
id: requirements
steps:
  - id: prd
    depende_de: []
---
Preámbulo.

## Paso: prd

Hacé el PRD.
"""


def _make_content_dir(tmp_path: Path) -> Path:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    return content_dir


def test_init_with_no_detected_provider_and_no_override_errors(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    code = main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code != 0
    assert "ningún proveedor" in capsys.readouterr().err.lower()


def test_init_with_providers_override_installs(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    code = main([
        "init", "--project-root", str(tmp_path), "--content-dir", str(content_dir),
        "--providers", "claude_code",
    ])
    assert code == 0
    assert (tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md").exists()
    assert (tmp_path / ".factory" / "manifest.json").exists()


def test_init_twice_behaves_like_update(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    assert code == 0


def test_update_without_prior_init_errors(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    code = main(["update", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code != 0
    assert "init" in capsys.readouterr().err.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL (no module `factorysoftware.cli`)

- [ ] **Step 3: Implement `cli.py` (init/update)**

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from factorysoftware.adapters import registry
from factorysoftware.installer import install_all, update_all
from factorysoftware.state import read_manifest


def _default_content_dir() -> Path:
    return Path(__file__).parent / "content"


def _resolve_adapters(project_root: Path, providers_override: list[str] | None):
    if providers_override:
        return registry.select(providers_override)
    return registry.detect(project_root)


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    content_dir = Path(args.content_dir) if args.content_dir else _default_content_dir()

    if read_manifest(project_root) is not None:
        return cmd_update(args)

    providers_override = args.providers.split(",") if args.providers else None
    adapters = _resolve_adapters(project_root, providers_override)
    if not adapters:
        print(
            "No se detectó ningún proveedor en este proyecto. "
            "Usá --providers <nombre> para forzar uno.",
            file=sys.stderr,
        )
        return 1

    install_all(project_root, content_dir, adapters)
    print(f"Instalado para: {', '.join(a.name for a in adapters)}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    content_dir = Path(args.content_dir) if args.content_dir else _default_content_dir()

    manifest = read_manifest(project_root)
    if manifest is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1

    providers_override = args.providers.split(",") if getattr(args, "providers", None) else None
    adapters = _resolve_adapters(project_root, providers_override)
    if not adapters:
        adapters = registry.select(manifest.providers)

    _, warnings = update_all(project_root, content_dir, adapters)
    for w in warnings:
        print(f"Advertencia: {w}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="factory")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn in (("init", cmd_init), ("update", cmd_update)):
        p = sub.add_parser(name)
        p.add_argument("--project-root", default=".")
        p.add_argument("--content-dir", default=None)
        p.add_argument("--providers", default=None)
        p.set_defaults(func=fn)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/cli.py tests/test_cli.py
git commit -m "feat: add factory init/update CLI commands"
```

---

### Task 16: CLI — `uninstall` command

**Files:**
- Modify: `src/factorysoftware/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `uninstall_all` (Task 14).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_cli.py`:
```python
def test_uninstall_without_prior_init_errors(tmp_path: Path, capsys):
    code = main(["uninstall", "--project-root", str(tmp_path)])
    assert code != 0
    assert "init" in capsys.readouterr().err.lower()


def test_uninstall_after_init_removes_files(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["uninstall", "--project-root", str(tmp_path)])
    assert code == 0
    assert not (tmp_path / ".claude" / "skills" / "requirements-prd").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v -k uninstall`
Expected: FAIL (no `uninstall` subcommand)

- [ ] **Step 3: Implement `cmd_uninstall` and wire it**

Add to `src/factorysoftware/cli.py`:
```python
from factorysoftware.installer import install_all, update_all, uninstall_all  # extend existing import


def cmd_uninstall(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    if read_manifest(project_root) is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1
    warnings = uninstall_all(project_root)
    for w in warnings:
        print(f"Advertencia: {w}", file=sys.stderr)
    return 0
```

In `build_parser`, add a third subparser:
```python
    p = sub.add_parser("uninstall")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_uninstall)
```
(add this alongside the existing `for name, fn in (...)` loop, or extend
the loop's tuple with `("uninstall", cmd_uninstall)` and special-case that
`uninstall` doesn't take `--content-dir`/`--providers` — simplest: keep
`uninstall` as a separate explicit `sub.add_parser` call as shown above,
right after the loop.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/cli.py tests/test_cli.py
git commit -m "feat: add factory uninstall CLI command"
```

---

### Task 17: CLI — `status` (`--write`, `--step`), `log`, and `metrics.json`

**Files:**
- Modify: `src/factorysoftware/state.py`
- Modify: `src/factorysoftware/cli.py`
- Modify: `tests/test_state.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `read_manifest`/`read_log`/`write_board`/`append_log` (Tasks 2-4).
- Produces (state.py):
  - `query_step_status(project_root: Path, phase: str, step_id: str, fan_out_index: int | None = None) -> str`
    (`"completado"` or `"pendiente"`)
  - `compute_metrics(project_root: Path) -> dict` (skill invocation counts)
  - `write_metrics(project_root: Path) -> None`
- Produces (cli.py): `cmd_status`, `cmd_log` wired into `build_parser`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_state.py`:
```python
from factorysoftware.state import compute_metrics, query_step_status, write_metrics


def test_query_step_status_pendiente_when_no_event(tmp_path: Path):
    assert query_step_status(tmp_path, "requirements", "prd") == "pendiente"


def test_query_step_status_completado_after_event(tmp_path: Path):
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "prd", "estado": "completado"})
    assert query_step_status(tmp_path, "requirements", "prd") == "completado"


def test_query_step_status_fan_out_needs_all_instances_completado(tmp_path: Path):
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "hu_por_epica", "fan_out_index": 0, "estado": "completado"})
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "hu_por_epica", "fan_out_index": 1, "estado": "iniciado"})
    assert query_step_status(tmp_path, "requirements", "hu_por_epica") == "pendiente"
    assert query_step_status(tmp_path, "requirements", "hu_por_epica", fan_out_index=0) == "completado"
    assert query_step_status(tmp_path, "requirements", "hu_por_epica", fan_out_index=1) == "pendiente"


def test_compute_metrics_counts_invocations_per_skill(tmp_path: Path):
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "prd", "estado": "completado"})
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "prd", "estado": "iniciado"})
    metrics = compute_metrics(tmp_path)
    assert metrics["skill_invocations"]["requirements.prd"] == 2


def test_write_metrics_creates_file(tmp_path: Path):
    write_metrics(tmp_path)
    assert (tmp_path / ".factory" / "metrics.json").exists()
```

Append to `tests/test_cli.py`:
```python
import json as _json


def test_log_command_appends_event(tmp_path: Path):
    code = main([
        "log", "pipeline_step",
        "--project-root", str(tmp_path),
        "--data", _json.dumps({"phase": "requirements", "step_id": "prd", "estado": "completado"}),
    ])
    assert code == 0
    events = _json.loads((tmp_path / ".factory" / "log.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert events["event_type"] == "pipeline_step"
    assert events["data"]["step_id"] == "prd"


def test_status_without_manifest_errors(tmp_path: Path, capsys):
    code = main(["status", "--project-root", str(tmp_path)])
    assert code != 0
    assert "init" in capsys.readouterr().err.lower()


def test_status_prints_summary(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["status", "--project-root", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "claude_code" in out
    assert (tmp_path / ".factory" / "metrics.json").exists()


def test_status_write_generates_board(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["status", "--project-root", str(tmp_path), "--write"])
    assert code == 0
    assert (tmp_path / ".factory" / "board.md").exists()


def test_status_step_prints_pendiente_or_completado(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["status", "--project-root", str(tmp_path), "--step", "requirements.prd"])
    assert code == 0
    assert capsys.readouterr().out.strip() == "pendiente"
    main([
        "log", "pipeline_step", "--project-root", str(tmp_path),
        "--data", _json.dumps({"phase": "requirements", "step_id": "prd", "estado": "completado"}),
    ])
    code = main(["status", "--project-root", str(tmp_path), "--step", "requirements.prd"])
    assert capsys.readouterr().out.strip() == "completado"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py tests/test_cli.py -v -k "status or log or metrics or step_status"`
Expected: FAIL (no `query_step_status`/`compute_metrics`/`write_metrics`, no `status`/`log` subcommands)

- [ ] **Step 3: Implement `state.py` additions**

Append to `src/factorysoftware/state.py`:
```python
def query_step_status(
    project_root: Path, phase: str, step_id: str, fan_out_index: int | None = None
) -> str:
    events = [
        e for e in read_log(project_root)
        if e["event_type"] == "pipeline_step"
        and e["data"].get("phase") == phase
        and e["data"].get("step_id") == step_id
    ]
    if fan_out_index is not None:
        matching = [e for e in events if e["data"].get("fan_out_index") == fan_out_index]
        if not matching:
            return "pendiente"
        return "completado" if matching[-1]["data"].get("estado") == "completado" else "pendiente"

    if not events:
        return "pendiente"
    latest_by_index: dict = {}
    for e in events:
        latest_by_index[e["data"].get("fan_out_index")] = e
    all_done = all(e["data"].get("estado") == "completado" for e in latest_by_index.values())
    return "completado" if all_done else "pendiente"


def compute_metrics(project_root: Path) -> dict:
    events = read_log(project_root)
    invocations: dict[str, int] = {}
    for e in events:
        if e["event_type"] != "pipeline_step":
            continue
        phase = e["data"].get("phase")
        step_id = e["data"].get("step_id")
        if not phase or not step_id:
            continue
        key = f"{phase}.{step_id}"
        invocations[key] = invocations.get(key, 0) + 1
    return {"skill_invocations": invocations}


def write_metrics(project_root: Path) -> None:
    _factory_dir(project_root).mkdir(parents=True, exist_ok=True)
    (_factory_dir(project_root) / "metrics.json").write_text(
        json.dumps(compute_metrics(project_root), indent=2), encoding="utf-8"
    )
```

- [ ] **Step 4: Implement `cmd_status` and `cmd_log`**

Add to `src/factorysoftware/cli.py`:
```python
import json

from factorysoftware.state import (  # extend existing import
    append_log, read_log, write_board, query_step_status, write_metrics,
)


def cmd_status(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    manifest = read_manifest(project_root)
    if manifest is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1

    if args.step:
        phase, step_id = args.step.split(".", 1)
        print(query_step_status(project_root, phase, step_id, args.fan_out_index))
        return 0

    if args.write:
        write_board(project_root)
        print("Tablero regenerado en .factory/board.md")
        return 0

    write_metrics(project_root)
    print(f"Versión instalada: {manifest.version}")
    print(f"Proveedores: {', '.join(manifest.providers)}")
    events = read_log(project_root)
    print(f"Eventos registrados: {len(events)}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    data = json.loads(args.data) if args.data else {}
    append_log(project_root, args.event_type, data)
    return 0
```

In `build_parser`:
```python
    p = sub.add_parser("status")
    p.add_argument("--project-root", default=".")
    p.add_argument("--write", action="store_true")
    p.add_argument("--step", default=None, help="<phase>.<step_id>")
    p.add_argument("--fan-out-index", type=int, default=None)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("log")
    p.add_argument("event_type")
    p.add_argument("--project-root", default=".")
    p.add_argument("--data", default=None)
    p.set_defaults(func=cmd_log)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_state.py tests/test_cli.py -v`
Expected: PASS (13 tests in `test_state.py`, 11 tests in `test_cli.py`)

- [ ] **Step 6: Commit**

```bash
git add src/factorysoftware/state.py src/factorysoftware/cli.py tests/test_state.py tests/test_cli.py
git commit -m "feat: add factory status (--write, --step), log, and metrics.json"
```

---

### Task 18: Copilot adapter (secondary, single-file)

**Files:**
- Create: `src/factorysoftware/adapters/copilot.py`
- Modify: `src/factorysoftware/adapters/registry.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Produces: `class CopilotAdapter`, `name = "copilot"`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
from factorysoftware.adapters.copilot import CopilotAdapter


def test_copilot_detect_true_with_dot_github(tmp_path: Path):
    (tmp_path / ".github").mkdir()
    assert CopilotAdapter().detect(tmp_path) is True


def test_copilot_detect_false_when_absent(tmp_path: Path):
    assert CopilotAdapter().detect(tmp_path) is False


def test_copilot_target_paths_all_same_file(tmp_path: Path):
    paths = CopilotAdapter().target_paths(tmp_path, ["requirements-prd", "requirements-flujo"])
    assert paths["requirements-prd"] == paths["requirements-flujo"] == tmp_path / ".github" / "copilot-instructions.md"


def test_copilot_render_adds_heading():
    rendered = CopilotAdapter().render("requirements-prd", "Hacé el PRD.")
    assert rendered.startswith("## requirements-prd")
    assert "Hacé el PRD." in rendered
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k copilot`
Expected: FAIL (no module `factorysoftware.adapters.copilot`)

- [ ] **Step 3: Implement `adapters/copilot.py` and register it**

`src/factorysoftware/adapters/copilot.py`:
```python
from __future__ import annotations

from pathlib import Path


class CopilotAdapter:
    name = "copilot"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".github").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        target = project_root / ".github" / "copilot-instructions.md"
        return {sid: target for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return f"## {skill_id}\n\n{content_md}"
```

In `src/factorysoftware/adapters/registry.py`, add the import and append to
`ALL_ADAPTERS`:
```python
from factorysoftware.adapters.copilot import CopilotAdapter

ALL_ADAPTERS: list[ProviderAdapter] = [ClaudeCodeAdapter(), CopilotAdapter()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/copilot.py src/factorysoftware/adapters/registry.py tests/test_adapters.py
git commit -m "feat: add GitHub Copilot adapter (single-file, best-effort)"
```

---

### Task 19: Codex and OpenCode adapters (secondary, single-file `AGENTS.md`)

**Files:**
- Create: `src/factorysoftware/adapters/codex.py`
- Create: `src/factorysoftware/adapters/opencode.py`
- Modify: `src/factorysoftware/adapters/registry.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Produces: `class CodexAdapter` (`name = "codex"`), `class OpenCodeAdapter` (`name = "opencode"`).

OpenCode is implemented identically to Codex per the spec's own flag
("tratado como Codex para el adapter básico v1 — verificar contra la
documentación vigente antes de implementar"). Both detect via presence of
an `AGENTS.md` file at the project root, or install one if absent — but
detection must not be a false-negative trap: if `AGENTS.md` doesn't exist
yet, this adapter still shouldn't claim the project (that would make every
project "detect" as Codex). `detect()` returns `False` when nothing points
to Codex/OpenCode specifically; these two adapters are meant to be reached
mainly via `--providers` override, documented as such.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
from factorysoftware.adapters.codex import CodexAdapter
from factorysoftware.adapters.opencode import OpenCodeAdapter


def test_codex_detect_false_without_marker(tmp_path: Path):
    assert CodexAdapter().detect(tmp_path) is False


def test_codex_detect_true_with_codex_marker(tmp_path: Path):
    (tmp_path / ".codex").mkdir()
    assert CodexAdapter().detect(tmp_path) is True


def test_codex_target_paths_all_same_agents_md(tmp_path: Path):
    paths = CodexAdapter().target_paths(tmp_path, ["a", "b"])
    assert paths["a"] == paths["b"] == tmp_path / "AGENTS.md"


def test_codex_render_is_plain_no_frontmatter():
    rendered = CodexAdapter().render("requirements-prd", "Hacé el PRD.")
    assert not rendered.startswith("---")
    assert "Hacé el PRD." in rendered


def test_opencode_target_paths_same_as_codex(tmp_path: Path):
    paths = OpenCodeAdapter().target_paths(tmp_path, ["a"])
    assert paths["a"] == tmp_path / "AGENTS.md"


def test_opencode_detect_false_without_marker(tmp_path: Path):
    assert OpenCodeAdapter().detect(tmp_path) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k "codex or opencode"`
Expected: FAIL (no such modules)

- [ ] **Step 3: Implement both adapters and register them**

`src/factorysoftware/adapters/codex.py`:
```python
from __future__ import annotations

from pathlib import Path


class CodexAdapter:
    name = "codex"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".codex").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        target = project_root / "AGENTS.md"
        return {sid: target for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return f"## {skill_id}\n\n{content_md}"
```

`src/factorysoftware/adapters/opencode.py`:
```python
from __future__ import annotations

from pathlib import Path


class OpenCodeAdapter:
    name = "opencode"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".opencode").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        target = project_root / "AGENTS.md"
        return {sid: target for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return f"## {skill_id}\n\n{content_md}"
```

In `registry.py`:
```python
from factorysoftware.adapters.codex import CodexAdapter
from factorysoftware.adapters.opencode import OpenCodeAdapter

ALL_ADAPTERS: list[ProviderAdapter] = [
    ClaudeCodeAdapter(), CopilotAdapter(), CodexAdapter(), OpenCodeAdapter(),
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (24 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/codex.py src/factorysoftware/adapters/opencode.py src/factorysoftware/adapters/registry.py tests/test_adapters.py
git commit -m "feat: add Codex and OpenCode adapters (single-file AGENTS.md, best-effort)"
```

---

### Task 20: Antigravity adapter (primary, grounded in prior research)

**Files:**
- Create: `src/factorysoftware/adapters/antigravity.py`
- Modify: `src/factorysoftware/adapters/registry.py`
- Modify: `tests/test_adapters.py`

**Interfaces:**
- Produces: `class AntigravityAdapter` (`name = "antigravity"`),
  `AntigravityAdapter.install_gitflow_hook(self, project_root: Path) -> list[Path]`.

**Before writing code**, re-verify this against Antigravity's current
public documentation (a web search) — the layout below is grounded in a
real installer script (`powers/INSTALL-ANTIGRAVITY.ps1`) observed in the
sibling `FabricaAgenticaClaude` repo during this project's research, not
official docs, so treat it as a strong starting point to confirm, not a
fact to assume blindly. That script installs project-level skills to
`.agents/skills/<id>/SKILL.md` and command mirrors to `.agents/commands/`,
and references a `.agents/hooks.json` for pre-execution hooks — mirroring
Claude Code's own layout under a different root directory. If current
research contradicts this, update the paths below before implementing; if
research is inconclusive, ship this version but log a `TODO` visible in
`factory status` output (not a silent assumption) — see Step 3's
`confidence` note.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_adapters.py`:
```python
from factorysoftware.adapters.antigravity import AntigravityAdapter


def test_antigravity_detect_true_with_dot_agents(tmp_path: Path):
    (tmp_path / ".agents").mkdir()
    assert AntigravityAdapter().detect(tmp_path) is True


def test_antigravity_detect_false_when_absent(tmp_path: Path):
    assert AntigravityAdapter().detect(tmp_path) is False


def test_antigravity_target_paths_mirrors_claude_code_layout(tmp_path: Path):
    paths = AntigravityAdapter().target_paths(tmp_path, ["requirements-prd"])
    assert paths["requirements-prd"] == tmp_path / ".agents" / "skills" / "requirements-prd" / "SKILL.md"


def test_antigravity_render_adds_frontmatter():
    rendered = AntigravityAdapter().render("requirements-prd", "Hacé el PRD.")
    assert "name: requirements-prd" in rendered
    assert "Hacé el PRD." in rendered


def test_antigravity_install_gitflow_hook_writes_hooks_json(tmp_path: Path):
    written = AntigravityAdapter().install_gitflow_hook(tmp_path)
    hooks_path = tmp_path / ".agents" / "hooks.json"
    assert hooks_path in written
    assert hooks_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters.py -v -k antigravity`
Expected: FAIL (no module `factorysoftware.adapters.antigravity`)

- [ ] **Step 3: Implement `adapters/antigravity.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

# confidence: grounded in a real-world installer observed during research
# (FabricaAgenticaClaude's powers/INSTALL-ANTIGRAVITY.ps1), not official
# Antigravity docs. Re-verify before relying on this in production.

_GUARD_SCRIPT = """\
#!/bin/sh
input=$(cat)
cmd=$(printf '%s' "$input" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)
case "$cmd" in
  *"git commit"*|*"git push"*)
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ "$branch" = "main" ] || [ "$branch" = "develop" ]; then
      echo "Bloqueado: commit/push directo a $branch prohibido por Git Flow. Usa una rama feature/*." >&2
      exit 2
    fi
    ;;
esac
exit 0
"""


class AntigravityAdapter:
    name = "antigravity"

    def detect(self, project_root: Path) -> bool:
        return (project_root / ".agents").is_dir()

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {
            sid: project_root / ".agents" / "skills" / sid / "SKILL.md"
            for sid in skill_ids
        }

    def render(self, skill_id: str, content_md: str) -> str:
        description = f"Factory skill: {skill_id}"
        return f"---\nname: {skill_id}\ndescription: {description}\n---\n\n{content_md}"

    def install_gitflow_hook(self, project_root: Path) -> list[Path]:
        hooks_dir = project_root / ".agents"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        guard_path = hooks_dir / "gitflow-guard.sh"
        guard_path.write_text(_GUARD_SCRIPT, encoding="utf-8")
        guard_path.chmod(0o755)

        hooks_json_path = hooks_dir / "hooks.json"
        hooks_config = {}
        if hooks_json_path.exists():
            hooks_config = json.loads(hooks_json_path.read_text(encoding="utf-8"))
        hooks_config.setdefault("preExec", []).append(
            {"matcher": "bash", "command": str(guard_path)}
        )
        hooks_json_path.write_text(json.dumps(hooks_config, indent=2), encoding="utf-8")

        return [guard_path, hooks_json_path]
```

In `registry.py`:
```python
from factorysoftware.adapters.antigravity import AntigravityAdapter

ALL_ADAPTERS: list[ProviderAdapter] = [
    ClaudeCodeAdapter(), AntigravityAdapter(), CopilotAdapter(), CodexAdapter(), OpenCodeAdapter(),
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters.py -v`
Expected: PASS (29 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/adapters/antigravity.py src/factorysoftware/adapters/registry.py tests/test_adapters.py
git commit -m "feat: add Antigravity adapter, grounded in observed real-world installer layout"
```

---

### Task 21: End-to-end integration test + package entry point verification

**Files:**
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 1-20.

- [ ] **Step 1: Write failing integration test**

Append to `tests/test_cli.py`:
```python
def test_full_lifecycle_init_update_uninstall(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".github").mkdir()

    code = main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code == 0
    assert (tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()

    (content_dir / "requirements.md").write_text(
        _FIXTURE_PHASE.replace("Hacé el PRD.", "Hacé el PRD (v2)."), encoding="utf-8"
    )
    code = main(["update", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code == 0
    assert "v2" in (tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md").read_text(encoding="utf-8")

    code = main(["status", "--project-root", str(tmp_path), "--write"])
    assert code == 0
    assert (tmp_path / ".factory" / "board.md").exists()

    code = main(["uninstall", "--project-root", str(tmp_path)])
    assert code == 0
    assert not (tmp_path / ".claude" / "skills" / "requirements-prd").exists()
    assert not (tmp_path / ".factory" / "manifest.json").exists()
```

Note: this test relies on autodetection (no `--providers` override) —
both `.claude` and `.github` exist in the fixture, so `registry.detect`
should match `claude_code` and `copilot` simultaneously, exercising the
"install for both at once" behavior from the core spec.

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `pytest tests/test_cli.py -v -k full_lifecycle`
Expected: Likely PASS already, since every piece was built and tested in
isolation — this test's job is to catch any integration gap the unit tests
missed (e.g., wrong argument order, a path mismatch between two modules).
If it fails, fix the integration bug it surfaces before proceeding.

- [ ] **Step 3: Run the entire test suite**

Run: `pytest -v`
Expected: PASS (all ~60+ tests across all modules)

- [ ] **Step 4: Verify the installed console script works**

Run: `factory --help`
Expected: prints usage with `init`, `update`, `uninstall`, `status`, `log`
subcommands (confirms the `pyproject.toml` `[project.scripts]` entry point
from Task 1 actually resolves to `cli.main`).

- [ ] **Step 5: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add end-to-end init/update/status/uninstall lifecycle test"
```

---

## What this plan does not build (by design, per spec scope)

- Real phase content (`content/advisor.md`, `content/requirements.md`,
  etc.) — separate follow-up work once each phase's content-authoring
  effort starts, using the `PhaseContent` YAML+markdown format this plan
  defines.
- `factory validate <phase>` — each phase spec defines its own structural
  checks; those subcommands get added when that phase's content pack is
  built, not here.
- Deployment execution, project-type packs — explicitly deferred in the
  core spec's non-goals.
