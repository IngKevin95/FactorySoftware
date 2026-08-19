# Architecture Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `architecture` content pack for FactorySoftware - a CLI validator and 11 SKILL.md files that guide an agent through producing technical design, ADRs, Data Models, APIs, and Screen contracts.

**Architecture:** A new subcommand `factory validate architecture` is added to the CLI. It calls `validate_architecture()` in a new module `src/factorysoftware/architecture/validator.py` which performs 6 structural checks on `docs/architecture/` and cross-references `docs/requirements/`. Skill files live in `src/factorysoftware/content/architecture/`.

**Tech Stack:** Python 3.11+, pytest, pathlib, PyYAML 6.0+, argparse.

**Spec:** `docs/superpowers/specs/2026-08-19-architecture-skill-design.md`

## Global Constraints

- Python >= 3.11; no external IO in tests - `tmp_path` fixtures only.
- PyYAML >= 6.0 already in `pyproject.toml` - do not add new dependencies.
- CLI entry point: `factory` (defined in `pyproject.toml`).
- Skill files live in `src/factorysoftware/content/architecture/`.
- All tests go in `tests/` flat.

---

### Task 1: Validator Module - Structural Checks 1-6 & NFR check

**Files:**
- Create: `src/factorysoftware/architecture/__init__.py`
- Create: `src/factorysoftware/architecture/validator.py`
- Create: `tests/test_validate_architecture.py`

**Interfaces:**
- Consumes: nothing
- Produces: `validate_architecture(project_root: Path) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate_architecture.py
import pytest
from pathlib import Path
import yaml
from factorysoftware.architecture.validator import validate_architecture

def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

@pytest.fixture
def docs(tmp_path: Path) -> Path:
    docs_dir = tmp_path / "docs"
    req_dir = docs_dir / "requirements"
    arch_dir = docs_dir / "architecture"
    _write(req_dir / "stories" / "HU-1.1.md", _fm({"id": "HU-1.1", "estado": "draft"}))
    _write(req_dir / "traceability.md", "| HU | Epica | Estado | CP | Componentes de arquitectura |\n|----|-------|--------|----|------------------------------|\n| HU-1.1 | EPIC-1 | draft | _p_ | API-1, SCREEN-1 |")
    _write(arch_dir / "apis" / "API-1.md", _fm({"id": "API-1", "implementa": ["HU-1.1"]}))
    _write(arch_dir / "screens" / "SCREEN-1.md", _fm({"id": "SCREEN-1", "implementa": ["HU-1.1"], "apis_consumidas": ["API-1"]}))
    # dummy prototype to pass check 6
    _write(tmp_path / "prototype" / "SCREEN-1.html", "mock")
    _write(arch_dir / "constraints.md", "| ID | Estímulo |\n|----|----------|\n| NFR-1 | Algo |")
    _write(arch_dir / "adrs" / "ADR-1.md", _fm({"id": "ADR-1", "nfr_aplicados": ["NFR-1"]}))
    return tmp_path

def test_validate_architecture_clean(docs):
    assert validate_architecture(docs) == []

def test_missing_api_for_hu(docs):
    _write(docs / "docs" / "requirements" / "stories" / "HU-1.2.md", _fm({"id": "HU-1.2", "estado": "draft"}, "Anexo endpoint: x"))
    errors = validate_architecture(docs)
    assert any("HU-1.2" in e and "API" in e for e in errors)

def test_missing_screen_for_hu(docs):
    _write(docs / "docs" / "requirements" / "stories" / "HU-1.3.md", _fm({"id": "HU-1.3", "estado": "draft"}, "Anexo pantalla: x"))
    errors = validate_architecture(docs)
    assert any("HU-1.3" in e and "SCREEN" in e for e in errors)

def test_missing_api_in_screen_apis_consumidas(docs):
    _write(docs / "docs" / "architecture" / "screens" / "SCREEN-2.md", _fm({"id": "SCREEN-2", "apis_consumidas": ["API-99"]}))
    errors = validate_architecture(docs)
    assert any("API-99" in e for e in errors)

def test_implementa_inexistent_hu(docs):
    _write(docs / "docs" / "architecture" / "apis" / "API-2.md", _fm({"id": "API-2", "implementa": ["HU-9.9"]}))
    errors = validate_architecture(docs)
    assert any("HU-9.9" in e for e in errors)

def test_missing_prototype_for_screen(docs):
    _write(docs / "docs" / "architecture" / "screens" / "SCREEN-3.md", _fm({"id": "SCREEN-3", "implementa": []}))
    errors = validate_architecture(docs)
    assert any("SCREEN-3" in e and "prototipo" in e.lower() for e in errors)

def test_unattended_nfr(docs):
    _write(docs / "docs" / "architecture" / "constraints.md", "| ID |\n|----|\n| NFR-99 |")
    errors = validate_architecture(docs)
    assert any("NFR-99" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validate_architecture.py -v`
Expected: FAIL (missing validator module)

- [ ] **Step 3: Write minimal implementation**

```python
# src/factorysoftware/architecture/__init__.py
# empty
```

```python
# src/factorysoftware/architecture/validator.py
from pathlib import Path
import yaml
import re

def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}

def validate_architecture(project_root: Path) -> list[str]:
    docs = project_root / "docs"
    arch = docs / "architecture"
    reqs = docs / "requirements"
    errors = []
    
    hu_files = list((reqs / "stories").glob("HU-*.md")) if (reqs / "stories").exists() else []
    hu_active = {f.stem for f in hu_files if "retiradas" not in f.parts}
    
    apis = list((arch / "apis").glob("API-*.md")) if (arch / "apis").exists() else []
    api_ids = {f.stem for f in apis}
    
    screens = list((arch / "screens").glob("SCREEN-*.md")) if (arch / "screens").exists() else []
    screen_ids = {f.stem for f in screens}
    
    # 1. & 2. HU with anexo
    for hu_path in hu_files:
        if "retiradas" in hu_path.parts:
            continue
        text = hu_path.read_text(encoding="utf-8")
        if "anexo endpoint" in text.lower():
            implemented = False
            for api in apis:
                fm = _parse_frontmatter(api.read_text(encoding="utf-8"))
                if hu_path.stem in fm.get("implementa", []):
                    implemented = True
                    break
            if not implemented:
                errors.append(f"Check 1: HU '{hu_path.stem}' requests an endpoint but no API-N.md implements it")
        
        if "anexo pantalla" in text.lower():
            implemented = False
            for screen in screens:
                fm = _parse_frontmatter(screen.read_text(encoding="utf-8"))
                if hu_path.stem in fm.get("implementa", []):
                    implemented = True
                    break
            if not implemented:
                errors.append(f"Check 2: HU '{hu_path.stem}' requests a screen but no SCREEN-N.md implements it")
                
    # 3. apis_consumidas must exist
    for screen in screens:
        fm = _parse_frontmatter(screen.read_text(encoding="utf-8"))
        for api_ref in fm.get("apis_consumidas", []):
            if api_ref not in api_ids:
                errors.append(f"Check 3: {screen.stem} apis_consumidas '{api_ref}' not found")
                
    # 4. implementa valid HU
    for f in apis + screens:
        fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
        for hu in fm.get("implementa", []):
            if hu not in hu_active:
                errors.append(f"Check 4: {f.stem} implements '{hu}' which is not active")

    # 6. screens have prototypes
    proto_dir = project_root / "prototype"
    proto_files = {f.stem for f in proto_dir.glob("*")} if proto_dir.exists() else set()
    for sid in screen_ids:
        if sid not in proto_files:
            errors.append(f"Check 6: SCREEN '{sid}' lacks a UI prototipo in prototype/")

    # Check e: NFR applied
    constraints = arch / "constraints.md"
    nfrs = set()
    if constraints.exists():
        for match in re.finditer(r'\| (NFR-\d+) \|', constraints.read_text(encoding="utf-8")):
            nfrs.add(match.group(1))
            
    adrs = list((arch / "adrs").glob("ADR-*.md")) if (arch / "adrs").exists() else []
    applied_nfrs = set()
    for adr in adrs:
        fm = _parse_frontmatter(adr.read_text(encoding="utf-8"))
        applied_nfrs.update(fm.get("nfr_aplicados", []))
        
    for nfr in nfrs - applied_nfrs:
        errors.append(f"Check e: NFR '{nfr}' is not applied in any ADR")
            
    return errors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validate_architecture.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/architecture/ tests/test_validate_architecture.py
git commit -m "feat(architecture): add structural validator checks 1-6"
```

---

### Task 2: CLI Subcommand - `factory validate architecture`

**Files:**
- Modify: `src/factorysoftware/cli.py`
- Create: `tests/test_cli_validate_architecture.py`

**Interfaces:**
- Consumes: `validate_architecture(project_root: Path)` from Task 1

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_validate_architecture.py
import pytest
from pathlib import Path
from factorysoftware.cli import main

def test_cli_validate_architecture(tmp_path, capsys):
    code = main(["validate", "architecture", "--project-root", str(tmp_path)])
    assert code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_validate_architecture.py -v`
Expected: FAIL (argument error)

- [ ] **Step 3: Write minimal implementation**

Modify `src/factorysoftware/cli.py` to add `architecture` under `validate` subparsers:

```python
from factorysoftware.architecture.validator import validate_architecture as _validate_arch

def cmd_validate_architecture(args) -> int:
    errors = _validate_arch(Path(args.project_root))
    for e in errors:
        print(e)
    return 1 if errors else 0

# inside build_parser():
# Add `architecture` parser to the existing `validate_sub` created in requirements
    p = validate_sub.add_parser("architecture")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_validate_architecture)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_validate_architecture.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/cli.py tests/test_cli_validate_architecture.py
git commit -m "feat(architecture): add factory validate architecture CLI"
```

---

### Task 3: Skill Files - Constraints & ADRs

**Files:**
- Create: `src/factorysoftware/content/architecture/architecture-constraints.md`
- Create: `src/factorysoftware/content/architecture/architecture-adrs.md`
- Create: `src/factorysoftware/content/architecture/architecture-adrs_audit.md`

- [ ] **Step 1: Create constraints skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-constraints.md -->
---
id: architecture
steps:
  - id: constraints
    depende_de: []
---

# Skill: architecture-constraints

Crea `docs/architecture/constraints.md`.

## Verificaciones
- Preguntar restricciones duras, blandas y escenarios NFR.

## Salida
Archivo Markdown con 3 secciones y tabla de NFRs.
```

- [ ] **Step 2: Create ADRs skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-adrs.md -->
---
id: architecture
steps:
  - id: adrs
    depende_de: [constraints]
---

# Skill: architecture-adrs

Crea `docs/architecture/adrs/ADR-N.md`. Obligatorio definir Stack Tecnológico y Método de despliegue.

## Frontmatter
`id`, `estado`, `restricciones_aplicadas`, `nfr_aplicados`.

## Estructura
Contexto, Restricciones, Alternativas, Decisión, Recomendación, Consecuencias.
```

- [ ] **Step 3: Create adrs_audit skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-adrs_audit.md -->
---
id: architecture
steps:
  - id: adrs_audit
    depende_de: [adrs]
---

# Skill: architecture-adrs_audit

Checkpoint temprano. Verifica fundamentos teóricos reales, no violación de restricciones, existencia de NFRs en ADRs.
```

- [ ] **Step 4: Commit**

```bash
git add src/factorysoftware/content/architecture/architecture-constraints.md src/factorysoftware/content/architecture/architecture-adrs.md src/factorysoftware/content/architecture/architecture-adrs_audit.md
git commit -m "feat(architecture): add constraints and ADRs skills"
```

---

### Task 4: Skill Files - Overview, Data Model, APIs

**Files:**
- Create: `src/factorysoftware/content/architecture/architecture-overview.md`
- Create: `src/factorysoftware/content/architecture/architecture-data_model.md`
- Create: `src/factorysoftware/content/architecture/architecture-apis.md`

- [ ] **Step 1: Create overview skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-overview.md -->
---
id: architecture
steps:
  - id: overview
    depende_de: [adrs_audit]
---

# Skill: architecture-overview
Crea `docs/architecture/architecture-overview.md` con Mermaid C4.
```

- [ ] **Step 2: Create data_model skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-data_model.md -->
---
id: architecture
steps:
  - id: data_model
    depende_de: [overview]
---

# Skill: architecture-data_model
Crea `docs/architecture/data-model.md` con Mermaid ER.
```

- [ ] **Step 3: Create apis skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-apis.md -->
---
id: architecture
steps:
  - id: apis
    depende_de: [data_model]
---

# Skill: architecture-apis
Genera `API-N.md`. Instancia por cada HU con anexo de endpoint.
```

- [ ] **Step 4: Commit**

```bash
git add src/factorysoftware/content/architecture/architecture-overview.md src/factorysoftware/content/architecture/architecture-data_model.md src/factorysoftware/content/architecture/architecture-apis.md
git commit -m "feat(architecture): add overview, data model, apis skills"
```

---

### Task 5: Skill Files - Screens & UI Prototype

**Files:**
- Create: `src/factorysoftware/content/architecture/architecture-screens.md`
- Create: `src/factorysoftware/content/architecture/architecture-ui_prototype.md`

- [ ] **Step 1: Create screens skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-screens.md -->
---
id: architecture
steps:
  - id: screens
    depende_de: [apis]
---

# Skill: architecture-screens
Genera `SCREEN-N.md`. Instancia por cada HU con anexo de pantalla.
```

- [ ] **Step 2: Create UI prototype skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-ui_prototype.md -->
---
id: architecture
steps:
  - id: ui_prototype
    depende_de: [screens]
---

# Skill: architecture-ui_prototype
Crea código real corrible en rama `architecture/ui-prototype` bajo directorio `prototype/`.
```

- [ ] **Step 3: Commit**

```bash
git add src/factorysoftware/content/architecture/architecture-screens.md src/factorysoftware/content/architecture/architecture-ui_prototype.md
git commit -m "feat(architecture): add screens and ui prototype skills"
```

---

### Task 6: Skill Files - Audits & Flow

**Files:**
- Create: `src/factorysoftware/content/architecture/architecture-gap_check_and_traceability.md`
- Create: `src/factorysoftware/content/architecture/architecture-integral_audit.md`
- Create: `src/factorysoftware/content/architecture/architecture-flujo.md`

- [ ] **Step 1: Create gap check skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-gap_check_and_traceability.md -->
---
id: architecture
steps:
  - id: gap_check_and_traceability
    depende_de: [apis, screens, ui_prototype]
---

# Skill: architecture-gap_check_and_traceability
Verifica completitud estructural (1-6) y semántica (7-11). Actualiza `traceability.md`.
```

- [ ] **Step 2: Create integral audit skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-integral_audit.md -->
---
id: architecture
steps:
  - id: integral_audit
    depende_de: [gap_check_and_traceability]
---

# Skill: architecture-integral_audit
Valida que PRD esté cubierto y no haya scope creep (i-iv).
```

- [ ] **Step 3: Create flujo skill**

```markdown
<!-- src/factorysoftware/content/architecture/architecture-flujo.md -->
---
id: architecture
steps:
  - id: flujo
    depende_de: []
---

# Skill: architecture-flujo
Orquestador que encadena desde `constraints` hasta `integral_audit`.
```

- [ ] **Step 4: Commit**

```bash
git add src/factorysoftware/content/architecture/architecture-gap_check_and_traceability.md src/factorysoftware/content/architecture/architecture-integral_audit.md src/factorysoftware/content/architecture/architecture-flujo.md
git commit -m "feat(architecture): add audit and flujo orchestration skills"
```
