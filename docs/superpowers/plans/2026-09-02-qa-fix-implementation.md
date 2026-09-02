# QA Content Pack Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reparar `content/qa.md` (8 de sus 10 pasos comparten hoy texto copy-pasteado del paso `qa-slide`, sin la lógica real de cada uno) y reemplazar el stub `validate_qa()` (hoy `return []` sin condición alguna) por los 4 checks mecánicos que ya define `docs/superpowers/specs/2026-08-19-qa-skill-design.md`. Esto cierra el hallazgo bloqueante encontrado en la radiografía previa a construir: hoy la fase de QA da instrucciones idénticas para tareas completamente distintas (escribir un test de integración vs. medir un NFR vs. correr seguridad) y no hay ningún gate mecánico que lo detecte.

**Architecture:** Igual que el plan de frontend (`2026-09-01-frontend-fidelity-and-wiring-evidence.md`), todo el cambio vive en el content pack (`content/qa.md`) y en el módulo Python que ya sostiene su validación (`qa/validator.py`). No se agrega infraestructura nueva: la evidencia de NFR reutiliza el mecanismo genérico `factory log <event_type> --data '<json>'` que ya existe (`cli.py::cmd_log` → `state.append_log`), tal como el spec de QA ya lo asume (`factory log audit_evidence`). `render.py`/`content.py` no cambian.

**Tech Stack:** Python 3.11+, pytest, PyYAML >= 6.0.

**Spec:** `docs/superpowers/specs/2026-08-19-qa-skill-design.md`. Este plan implementa su pipeline completo de contenido (sección "Pipeline de ejecución") y sus checks mecánicos 1–4 del checklist del auditor; no toca `audit_test_quality`/`audit_security_findings`/`qa_integral_audit` (checks 5–9, i–iii), que son 100% semánticos por diseño del propio spec y no tienen contraparte mecánica que implementar en Python — quedan como prosa para el agente, igual que `audit_practices` en Construcción.

**Orden de ejecución respecto al otro plan:** este plan corre **primero**. Recién después de que sus tasks cierren en verde se ejecuta `docs/superpowers/plans/2026-09-01-frontend-fidelity-and-wiring-evidence.md` — las dos fases son independientes entre sí (QA no toca `construction.md` ni `roles/frontend.md`), pero el usuario pidió el orden QA→frontend explícitamente, así que se respeta esa secuencia aunque técnicamente pudieran correr en cualquier orden.

## Global Constraints

- Python >= 3.11; cero IO externo real en tests — `tmp_path` fixtures, nunca se corren test-runners/SAST reales del proyecto objetivo dentro de los tests de `factorysoftware`.
- PyYAML >= 6.0, ya en `pyproject.toml` — no se agregan dependencias.
- Tests en `tests/` (flat).
- `content/qa.md` debe seguir siendo parseable por `parse_content` sin cambios en `content.py`.
- No se agrega ningún comando nuevo al CLI — `factory validate qa` y `factory log <event_type>` ya existen y son suficientes; `cmd_validate_qa` en `cli.py` no necesita tocarse (su firma ya llama `validate_qa(Path(args.project_root))`, y este plan no cambia la firma de `validate_qa`).

---

### Task 1: `content/qa.md` — frontmatter completo con grafo de dependencias real

**Files:**
- Modify: `src/factorysoftware/content/qa.md`
- Modify: `tests/test_content.py`

**Motivación:** el frontmatter actual de `qa.md` solo tiene `id: <paso>` por cada paso, sin `depende_de`/`fan_out`/`paralelizable` — a diferencia de `requirements.md` y `construction.md`, que sí declaran el grafo completo. Sin esto, el núcleo no puede saber que `integration_tests`/`e2e_tests`/`nfr_tests`/`security_tests` corren en paralelo entre sí (todas dependen solo de `qa_branch_setup`), ni que `qa_audit` no puede arrancar antes de que las 4 terminen.

- [ ] **Step 1: Write the failing regression test**

```python
# agregar a tests/test_content.py

def test_qa_content_pack_has_full_dependency_graph():
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "qa.md"
    )
    content = parse_content(content_path)
    by_id = {s.id: s for s in content.steps}
    assert by_id["coverage_gap_analysis"].depende_de == []
    assert by_id["qa_branch_setup"].depende_de == ["coverage_gap_analysis"]
    for step_id in ("integration_tests", "e2e_tests", "nfr_tests", "security_tests"):
        assert by_id[step_id].depende_de == ["qa_branch_setup"]
    assert set(by_id["traceability_update"].depende_de) == {
        "integration_tests", "e2e_tests", "nfr_tests", "security_tests"
    }
    assert by_id["qa_audit"].depende_de == ["traceability_update"]
    assert by_id["qa_audit"].rol == "Auditor"
    assert by_id["qa_integral_audit"].depende_de == ["qa_audit"]
    assert by_id["qa_integral_audit"].rol == "Auditor Integral"
    assert by_id["pr_gate"].depende_de == ["qa_integral_audit"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k qa_content_pack_has_full_dependency_graph`
Expected: FAIL — `KeyError` o `AssertionError`, el frontmatter actual no tiene esos campos.

- [ ] **Step 3: Replace the frontmatter of `content/qa.md`**

Reemplazar únicamente el bloque de frontmatter (entre los `---`), dejando el cuerpo (`## Paso: ...`) sin tocar todavía — eso lo hacen las Tasks 2–4:

```yaml
---
id: qa
unidad_principal: EPIC-N
flujo_skill_name: flujo
steps:
  - id: coverage_gap_analysis
    depende_de: []
    fan_out: null
    paralelizable: false
  - id: qa_branch_setup
    depende_de: ['coverage_gap_analysis']
    fan_out: null
    paralelizable: false
  - id: integration_tests
    depende_de: ['qa_branch_setup']
    fan_out: "una instancia por TEST-N de tipo integration"
    paralelizable: true
  - id: e2e_tests
    depende_de: ['qa_branch_setup']
    fan_out: "una instancia por TEST-N de tipo e2e"
    paralelizable: true
  - id: nfr_tests
    depende_de: ['qa_branch_setup']
    fan_out: "una instancia por TEST-N de tipo nfr"
    paralelizable: true
  - id: security_tests
    depende_de: ['qa_branch_setup']
    fan_out: null
    paralelizable: false
  - id: traceability_update
    depende_de: ['integration_tests', 'e2e_tests', 'nfr_tests', 'security_tests']
    fan_out: null
    paralelizable: false
  - id: qa_audit
    depende_de: ['traceability_update']
    fan_out: null
    paralelizable: true
    rol: Auditor
  - id: qa_integral_audit
    depende_de: ['qa_audit']
    fan_out: null
    paralelizable: false
    rol: Auditor Integral
  - id: pr_gate
    depende_de: ['qa_integral_audit']
    fan_out: null
    paralelizable: false
---
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -v -k qa_content_pack_has_full_dependency_graph`
Expected: PASS (el cuerpo todavía tiene el bug de contenido duplicado, pero eso no afecta este test — solo mira el frontmatter)

- [ ] **Step 5: Run full content test suite to confirm nothing else broke**

Run: `pytest tests/test_content.py -v`
Expected: PASS (todos)

- [ ] **Step 6: Commit**

```bash
git add src/factorysoftware/content/qa.md tests/test_content.py
git commit -m "fix(qa): frontmatter con grafo de dependencias real del pipeline"
```

---

### Task 2: `content/qa.md` — contenido real de `coverage_gap_analysis` y `qa_branch_setup`

**Files:**
- Modify: `src/factorysoftware/content/qa.md`
- Modify: `tests/test_content.py`

**Motivación:** hoy ambos pasos tienen el texto genérico de "qa-slide" que en realidad describe el modo de invocación por unidad, no la lógica del paso. `coverage_gap_analysis` es el paso que decide **qué falta probar** — es el corazón de la fase; sin su contenido real, no hay forma de que el agente sepa cómo armar `docs/qa/plan.md`.

- [ ] **Step 1: Write the failing regression test**

```python
# agregar a tests/test_content.py

def test_qa_coverage_gap_analysis_has_real_content_not_duplicated_stub():
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "qa.md"
    )
    content = parse_content(content_path)
    gap = content.sections["coverage_gap_analysis"].lower()
    branch = content.sections["qa_branch_setup"].lower()
    assert "test-n" in gap
    assert "docs/qa/plan.md" in gap
    assert gap != branch  # ya no son el mismo texto duplicado
    assert "feature/qa-coverage" in branch
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k qa_coverage_gap_analysis_has_real_content`
Expected: FAIL

- [ ] **Step 3: Replace the two sections in `content/qa.md`**

Reemplazar `## Paso: coverage_gap_analysis` y `## Paso: qa_branch_setup` (el resto del archivo queda igual por ahora):

```markdown
## Paso: coverage_gap_analysis

Arma `docs/qa/plan.md`: la lista de `TEST-N` que faltan para que el 100% de la funcionalidad declarada en Requerimientos quede probado más allá de lo unitario ya cubierto en Construcción.

- Lee `docs/requirements/traceability.md`: qué HU ya tienen test unitario pero no integración/e2e donde corresponda.
- Lee `docs/requirements/flujos/FLUJO-N.md`: qué flujos de negocio no tienen todavía un e2e real corriendo.
- Lee `docs/architecture/constraints.md`: qué `NFR-N` no tienen verificación real medida todavía.
- **Salida:** `docs/qa/plan.md` con una entrada por cada `TEST-N` faltante. Cada entrada: `id` (`TEST-N`), `tipo` (`integration`|`e2e`|`nfr`|`security`), `cubre` (ids de HU para `integration`, un `FLUJO-N` para `e2e`, un `NFR-N` para `nfr`, o `general` para `security`), `depende_de` (otros `TEST-N`, si aplica), `estado: pendiente`.
- **Definición operativa de "100% de cobertura":** no es porcentaje de líneas. Es que toda HU no retirada tenga, para cada criterio Given/When/Then, al menos un test real referenciado en la columna "Casos de prueba" de `traceability.md` — verificación de referencia cruzada, no métrica estadística.

## Paso: qa_branch_setup

Crea `feature/qa-coverage-<slug>` desde `develop` (con todas las Épicas de Construcción ya mergeadas a esta altura). Mecánico, sin juicio de agente.
</markdown>
```

(No incluir la etiqueta `</markdown>` literal al pegar — es solo un marcador de fin de bloque para quien lea este plan.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/qa.md tests/test_content.py
git commit -m "fix(qa): contenido real de coverage_gap_analysis y qa_branch_setup"
```

---

### Task 3: `content/qa.md` — contenido real de `integration_tests`, `e2e_tests`, `nfr_tests`, `security_tests`

**Files:**
- Modify: `src/factorysoftware/content/qa.md`
- Modify: `tests/test_content.py`

**Motivación:** son las 4 dimensiones de trabajo real de QA — hoy comparten el mismo texto de `qa-slide`, así que un agente no tiene forma de distinguir "escribir un test de integración" de "medir un NFR contra su umbral declarado".

- [ ] **Step 1: Write the failing regression test**

```python
# agregar a tests/test_content.py

def test_qa_four_test_dimensions_have_distinct_real_content():
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "qa.md"
    )
    content = parse_content(content_path)
    integration = content.sections["integration_tests"]
    e2e = content.sections["e2e_tests"]
    nfr = content.sections["nfr_tests"]
    security = content.sections["security_tests"]

    texts = [integration, e2e, nfr, security]
    assert len(set(texts)) == 4  # las 4 son distintas entre sí

    assert "flujo-n" in e2e.lower()
    assert "audit_evidence" in nfr.lower()
    assert "medida de respuesta" in nfr.lower()
    assert "advisor_block" in security.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k qa_four_test_dimensions_have_distinct_real_content`
Expected: FAIL

- [ ] **Step 3: Replace the four sections in `content/qa.md`**

```markdown
## Paso: integration_tests

Una instancia por `TEST-N` de tipo `integration` en `docs/qa/plan.md`. Toma como base los tests unitarios que ya escribió Construcción — no los repite, agrega la integración entre las unidades reales del stack (DB real o de test, servicios reales entre sí, sin mocks de la propia capa que se está integrando). Vive en `tests/integration/` o la convención del stack del proyecto (QA no inventa su propia carpeta).

## Paso: e2e_tests

Una instancia por `TEST-N` de tipo `e2e` — una por cada `FLUJO-N` sin cobertura. Sigue la secuencia de HU declarada en `docs/requirements/flujos/FLUJO-N.md`, usando la navegación real de las pantallas (ya debe honrar el flujo, verificado en la fase de Arquitectura). El criterio de éxito no es que cada HU aislada pase — es el **criterio de éxito del flujo completo** declarado en el propio `FLUJO-N.md` (un flujo puede fallar aunque cada HU pase sus tests por separado, ej. un dato que una HU guarda no es el que otra espera leer después).

## Paso: nfr_tests

Una instancia por `TEST-N` de tipo `nfr` — una por cada `NFR-N` de `docs/architecture/constraints.md` sin verificación real todavía. Corre el test de carga/performance/lo que corresponda al NFR concreto y **mide de verdad**, nunca estima. Registra el resultado con:

`factory log audit_evidence --data '{"nfr": "NFR-N", "medido": <valor real medido>, "objetivo": "<Medida de respuesta declarada en constraints.md>", "cumple": true|false, "git_head": "<git rev-parse HEAD>"}'`

Si `cumple` es `false`, es hallazgo **Bloqueante** — nunca "se documenta y se sigue". Se escala al usuario mostrando medido vs. objetivo; la resolución puede requerir volver a Construcción (optimizar) o a Arquitectura (revisar la ADR o el NFR mismo). QA no "arregla" el sistema para que el número cierre, solo mide y reporta con honestidad.

## Paso: security_tests

Pasada única y holística sobre todo el sistema integrado (no por-épica, a diferencia de `audit_security` de Construcción): SAST/dependency scanning más escenarios de seguridad puntuales que solo son visibles con el sistema completo (ej. un endpoint de una épica combinado con datos de otra puede abrir un camino que ninguna auditoría por-épica ve sola). Todo hallazgo tiene severidad (Bloqueante/Mayor/Menor). Todo hallazgo **Bloqueante** pasa por el mecanismo `advisor_block` del núcleo antes de seguir — nunca queda "reportado nomás" sin confirmación explícita del usuario:

`factory log advisor_block --data '{"category": "seguridad", "reason": "...", "user_override": true|false}'`
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/qa.md tests/test_content.py
git commit -m "fix(qa): contenido real de integration/e2e/nfr/security tests"
```

---

### Task 4: `content/qa.md` — contenido real de `qa_audit`, `qa_integral_audit`, `pr_gate`

**Files:**
- Modify: `src/factorysoftware/content/qa.md`
- Modify: `tests/test_content.py`

- [ ] **Step 1: Write the failing regression test**

```python
# agregar a tests/test_content.py

def test_qa_audit_steps_have_distinct_real_content():
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "qa.md"
    )
    content = parse_content(content_path)
    qa_audit = content.sections["qa_audit"]
    qa_integral = content.sections["qa_integral_audit"]
    pr_gate = content.sections["pr_gate"]

    assert len({qa_audit, qa_integral, pr_gate}) == 3
    assert "audit_coverage" in qa_audit.lower()
    assert "audit_nfr_compliance" in qa_audit.lower()
    assert "flujo-n" in qa_integral.lower()
    assert "develop" in pr_gate.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k qa_audit_steps_have_distinct_real_content`
Expected: FAIL

- [ ] **Step 3: Replace the three sections in `content/qa.md`**

```markdown
## Paso: qa_audit

Auditoría con tope de 3 iteraciones compartidas, 4 sub-checks — 2 mecánicos, 2 semánticos, las 4 corren en paralelo cuando el proveedor lo soporta:

1. **`audit_coverage`** (mecánico — correr `factory validate qa --project-root .`): toda HU no retirada en `traceability.md` tiene "Casos de prueba" no vacío con ids que existen de verdad; todo criterio Given/When/Then de cada HU está cubierto por al menos un test.
2. **`audit_nfr_compliance`** (mecánico — mismo comando): todo `NFR-N` de `constraints.md` tiene un evento `audit_evidence` logueado con `git_head` vigente, y su valor medido cumple la "Medida de respuesta" declarada.
3. **`audit_test_quality`** (semántico): los tests no son triviales (sin asserts vacíos, sin solo verificar "no explota"), ejercitan comportamiento real de negocio (no detalles de implementación frágiles ante un refactor válido), sin `sleep` fijo ni dependencia de orden de ejecución entre tests.
4. **`audit_security_findings`** (semántico): todo hallazgo de `security_tests` tiene severidad asignada; todo hallazgo Bloqueante pasó por `advisor_block` — ninguno queda reportado sin la confirmación explícita del usuario.

## Paso: qa_integral_audit

Último paso agéntico antes del gate. Coherencia entre lo que QA probó y lo que Requerimientos/Arquitectura/Construcción declararon:

i. Todo `FLUJO-N.md` de Requerimientos tiene al menos un test e2e real corriendo y pasando — no alcanza con que el archivo del test exista.
ii. Ningún NFR ni flujo quedó "cubierto" solo en `docs/qa/plan.md` sin que `traceability_update` lo haya reflejado en `traceability.md` — ambos documentos deben ser consistentes entre sí.
iii. El sistema integrado en `develop` (con QA ya sumado) sigue siendo coherente con las ADR de Arquitectura — si una solución de test reveló que una decisión arquitectónica no se sostiene en la práctica, queda documentado como hallazgo a escalar, nunca en silencio.

## Paso: pr_gate

Abre Pull Request de `feature/qa-coverage-<slug>` (o `feature/qa-coverage-epic-<numero>-<slug>` en modo `qa-slide`) hacia `develop`, merge commit (`--no-ff`). Espera la aprobación manual del usuario — este PR es el gate de aprobación humana de la fase, no un paso aparte.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -v`
Expected: PASS (todos los tests de `test_content.py`, incluyendo los de las Tasks 1–4 de este plan)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/qa.md tests/test_content.py
git commit -m "fix(qa): contenido real de qa_audit, qa_integral_audit y pr_gate"
```

---

### Task 5: `validate_qa()` — implementar los 4 checks mecánicos reales

**Files:**
- Modify: `src/factorysoftware/qa/validator.py`
- Modify: `tests/test_validate_qa.py`

**Interfaces:**
- Produces: `validate_qa(project_root: Path) -> list[str]` (misma firma que hoy — `cli.py::cmd_validate_qa` no necesita cambios).

**Motivación:** hoy la función es `return []` sin condición. Implementar los checks 1–4 del spec, con la misma forma que ya usan `validate_architecture`/`validate_requirements` (parseo de frontmatter YAML, lectura de `traceability.md`, lectura de `.factory/log.jsonl`).

- [ ] **Step 1: Write the failing tests**

```python
# reemplazar tests/test_validate_qa.py completo

import json
from pathlib import Path
import pytest
from factorysoftware.qa.validator import validate_qa

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _traceability(rows: list[tuple[str, str, str]]) -> str:
    # rows: (hu_id, epic_id, casos_de_prueba)
    header = "| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |\n|---|---|---|---|---|\n"
    body = "\n".join(f"| {hu} | {epic} | draft | {tests} | _n/a_ |" for hu, epic, tests in rows)
    return header + body

def _hu_with_gwt(n_scenarios: int) -> str:
    return "\n".join(f"Given a{i} When b{i} Then c{i}" for i in range(n_scenarios))

@pytest.fixture
def base(tmp_path: Path) -> Path:
    req = tmp_path / "docs" / "requirements"
    _write(req / "stories" / "HU-1.1.md", "---\nid: HU-1.1\n---\n" + _hu_with_gwt(1))
    _write(req / "traceability.md", _traceability([("HU-1.1", "EPIC-1", "TEST-1")]))
    tests_dir = tmp_path / "tests"
    _write(tests_dir / "integration" / "test_1.py", "def TEST-1(): pass")
    return tmp_path

def test_validate_qa_clean(base):
    assert validate_qa(base) == []

def test_hu_without_casos_de_prueba_is_reported(base):
    _write(base / "docs" / "requirements" / "traceability.md",
           _traceability([("HU-1.1", "EPIC-1", "_pendiente (fase QA)_")]))
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "Casos de prueba" in e for e in errors)

def test_gwt_scenarios_without_enough_tests_referenced(base):
    _write(base / "docs" / "requirements" / "stories" / "HU-1.1.md",
           "---\nid: HU-1.1\n---\n" + _hu_with_gwt(2))
    # solo un TEST-1 referenciado en traceability, pero la HU tiene 2 escenarios GWT
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "criterio" in e.lower() for e in errors)

def test_nfr_without_audit_evidence_is_reported(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    errors = validate_qa(tmp_path)
    assert any("NFR-1" in e and "audit_evidence" in e.lower() for e in errors)

def test_nfr_with_evidence_not_cumple_is_bloqueante(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    log_path = tmp_path / ".factory" / "log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": "2026-09-02T00:00:00Z", "event_type": "audit_evidence",
        "data": {"nfr": "NFR-1", "medido": "350ms", "objetivo": "p95 < 200ms",
                  "cumple": False, "git_head": "abc123"},
    }
    log_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    errors = validate_qa(tmp_path)
    assert any("NFR-1" in e and "no cumple" in e.lower() for e in errors)

def test_nfr_with_evidence_cumple_is_clean(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    log_path = tmp_path / ".factory" / "log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": "2026-09-02T00:00:00Z", "event_type": "audit_evidence",
        "data": {"nfr": "NFR-1", "medido": "150ms", "objetivo": "p95 < 200ms",
                  "cumple": True, "git_head": "abc123"},
    }
    log_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    errors = validate_qa(tmp_path)
    assert errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validate_qa.py -v`
Expected: FAIL (varios — `validate_qa` hoy siempre devuelve `[]`, así que los tests negativos fallan por no reportar nada)

- [ ] **Step 3: Write minimal implementation**

```python
# src/factorysoftware/qa/validator.py
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


_GWT_RE = re.compile(r"\bGiven\b.*?\bWhen\b.*?\bThen\b")
_TRACE_ROW_RE = re.compile(r"^\|\s*(HU-\d+\.\d+)\s*\|[^|]*\|[^|]*\|([^|]*)\|")
_NFR_ROW_RE = re.compile(r"\|\s*(NFR-\d+)\s*\|")


def validate_qa(project_root: Path) -> list[str]:
    errors: list[str] = []
    docs = project_root / "docs"

    trace_path = docs / "requirements" / "traceability.md"
    trace_tests: dict[str, list[str]] = {}
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            m = _TRACE_ROW_RE.match(line.strip())
            if not m:
                continue
            hu_id, cell = m.group(1), m.group(2).strip()
            if cell.startswith("_") and cell.endswith("_"):
                trace_tests[hu_id] = []
                errors.append(
                    f"Check 1: HU '{hu_id}' has no 'Casos de prueba' referenced in traceability.md"
                )
            else:
                trace_tests[hu_id] = [t.strip() for t in cell.split(",") if t.strip()]

    stories_dir = docs / "requirements" / "stories"
    if stories_dir.exists():
        for hu_path in stories_dir.glob("HU-*.md"):
            if "retiradas" in hu_path.parts:
                continue
            text = hu_path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            hu_id = fm.get("id", hu_path.stem)
            n_scenarios = len(_GWT_RE.findall(text))
            n_tests = len(trace_tests.get(hu_id, []))
            if n_scenarios > 0 and n_tests < n_scenarios:
                errors.append(
                    f"Check 2: HU '{hu_id}' has {n_scenarios} G/W/T criteria but only "
                    f"{n_tests} test(s) referenced in traceability.md"
                )

    constraints_path = docs / "architecture" / "constraints.md"
    nfr_ids: set[str] = set()
    if constraints_path.exists():
        nfr_ids = set(_NFR_ROW_RE.findall(constraints_path.read_text(encoding="utf-8")))

    log_path = project_root / ".factory" / "log.jsonl"
    evidence_by_nfr: dict[str, dict] = {}
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event_type") != "audit_evidence":
                continue
            data = entry.get("data", {})
            nfr = data.get("nfr")
            if nfr:
                evidence_by_nfr[nfr] = data

    for nfr in sorted(nfr_ids):
        evidence = evidence_by_nfr.get(nfr)
        if evidence is None or not evidence.get("git_head"):
            errors.append(
                f"Check 3: NFR '{nfr}' has no audit_evidence event with git_head in log.jsonl"
            )
            continue
        if not evidence.get("cumple", False):
            errors.append(
                f"Check 4: NFR '{nfr}' does not cumple its objective "
                f"(medido={evidence.get('medido')!r}, objetivo={evidence.get('objetivo')!r})"
            )

    return errors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validate_qa.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/qa/validator.py tests/test_validate_qa.py
git commit -m "fix(qa): implementar los 4 checks mecánicos de validate_qa"
```

---

### Task 6: Full suite verde y verificación end-to-end del content pack de QA

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -v`
Expected: todos los tests pasan (preexistentes + los ~16 nuevos de las Tasks 1–5).

- [ ] **Step 2: Verificar instalación end-to-end**

```bash
cd /tmp && rm -rf qa-smoke-test && mkdir qa-smoke-test && cd qa-smoke-test
git init -q && mkdir .claude
python -m factorysoftware.cli install --providers claude_code
```

Expected: sin excepción; `.claude/skills/qa-*/SKILL.md` refleja los 10 pasos con contenido real y distinto (confirmar con un `grep -c` rápido que no queden dos archivos con el mismo cuerpo).

- [ ] **Step 3: Commit final si quedó algo suelto**

Si algo no cierra en verde, corregir y commitear como `fix(qa): ...` describiendo el ajuste puntual.

---

## Siguiente paso

Con este plan cerrado en verde, continuar con `docs/superpowers/plans/2026-09-01-frontend-fidelity-and-wiring-evidence.md` (sus 6 tasks, sin cambios respecto a como quedó escrito).
