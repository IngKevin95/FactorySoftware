# Frontend Fidelity, Usability y Evidencia Mecánica de Cableado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar tres huecos concretos de `content/construction.md` frente a lo que ya probó `FabricaAgenticaClaude/factory-spec-build` (repo de referencia, no se porta código, solo criterio — ver `docs/CREDITS.md`): (1) el gate `wiring_check` no exige evidencia mecánica vigente, solo relato del agente; (2) `construction_audit` no tiene dimensión de fidelidad visual ni de usabilidad para slices con UI; (3) el catálogo de roles (`VALID_ROLES`) no se valida contra los content packs reales de `content/roles/`, así que un rol mal escrito en un plan pasa desapercibido hasta ejecución.

**Architecture:** Todo el cambio vive en content packs (`content/construction.md`, `content/roles/frontend.md`) más las dos piezas Python que ya sostienen la fase de construcción: `construction/triage.py` (qué dimensiones se disparan) y `construction/validator.py` (qué se valida mecánicamente). No se agrega infraestructura nueva (ni scripts externos, ni cambios de installer/adapters) — la evidencia mecánica de `wiring_check` se resuelve con comandos `git`/test-runner que el propio agente corre inline vía su tool de Bash, documentados como protocolo en el content pack, igual que ya hace `task_execution` con TDD. `render.py`/`content.py` no cambian: ya son genéricos respecto a cuántas secciones tiene un paso.

**Tech Stack:** Python 3.11+, pytest, PyYAML >= 6.0, markdown con frontmatter YAML (formato ya establecido por `content.py`).

**Spec:** `docs/superpowers/specs/2026-08-19-construction-skill-design.md` (spec base de la fase); este plan la extiende sin reabrirla — no cambia el pipeline de pasos (`steps:` del frontmatter de `construction.md` queda igual), solo profundiza el contenido de `wiring_check` y `construction_audit`, y agrega chequeos mecánicos nuevos al validador existente.

## Global Constraints

- Python >= 3.11; cero IO externo real en tests de `factorysoftware` — todo con `tmp_path`, nunca se corre git/test-runners reales dentro de los tests del propio paquete.
- PyYAML >= 6.0, ya en `pyproject.toml` — no se agregan dependencias.
- Tests en `tests/` (flat), conftest y fixtures existentes reutilizables donde aplique.
- `content/construction.md` debe seguir siendo parseable por `parse_content` sin cambios en `content.py`: todo paso nuevo de contenido va **dentro** de una sección `## Paso: <id>` ya declarada en el frontmatter, no se agregan `id`s de paso nuevos (evita tocar el pipeline `steps:` y el fan-out ya definido en el spec base).
- No se agregan roles nuevos al catálogo (`VALID_ROLES` sigue siendo `backend, data, frontend, seguridad, automatizaciones, mobile`) — este plan valida el catálogo existente contra los content packs reales, no lo amplía.
- Prioridad explícita del usuario: eficiencia y calidad de software por encima de cobertura exhaustiva — cada dimensión nueva se dispara solo quirúrgicamente (triage condicional), nunca corre en todo slice sin motivo, igual que `security`/`efficiency` ya hacen hoy.

---

### Task 1: Validador de catálogo de roles contra content packs reales

**Files:**
- Modify: `src/factorysoftware/construction/validator.py`
- Modify: `tests/test_validate_construction.py`

**Interfaces:**
- Consumes: nada nuevo (reutiliza `validate_construction(project_root: Path) -> list[str]`, ya existente).
- Produces: `validate_construction` ahora acepta un segundo parámetro opcional `content_roles_dir: Path | None = None`; si se pasa, valida que cada `rol:` usado en las tareas tenga un archivo `<rol>.md` en ese directorio (no solo que esté en `VALID_ROLES`). Cuando es `None` (default), el comportamiento es idéntico al actual — no rompe callers existentes (`cli.py`).

**Motivación (para quien implemente, no hace falta releerla en otro lado):** hoy `VALID_ROLES` es un `set` hardcodeado en `validator.py`. Si mañana se agrega `content/roles/qa.md` y se usa `rol: qa` en un plan, el validador lo rechaza aunque el content pack ya exista — o al revés, si se borra `content/roles/mobile.md` pero `VALID_ROLES` sigue teniendo `"mobile"`, un plan puede usar un rol sin agente real detrás y nadie se entera hasta que `task_planning` intenta despachar y no encuentra el content pack. Este check cierra ese hueco de forma puramente mecánica (leer archivos, no juicio de agente).

- [ ] **Step 1: Write the failing tests**

```python
# agregar al final de tests/test_validate_construction.py

def test_role_without_content_pack_is_reported(tmp_path, docs):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "backend.md").write_text("rol backend", encoding="utf-8")
    # "frontend" se usa en el plan pero no tiene content pack en roles_dir
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: frontend\n- implementa: API-1\n- depende_de: []"))
    errors = validate_construction(docs, content_roles_dir=roles_dir)
    assert any("frontend" in e and "content pack" in e.lower() for e in errors)

def test_role_with_content_pack_is_clean(tmp_path, docs):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "backend.md").write_text("rol backend", encoding="utf-8")
    errors = validate_construction(docs, content_roles_dir=roles_dir)
    assert errors == []

def test_role_check_skipped_when_no_roles_dir_given(docs):
    # comportamiento actual sin cambios: sin content_roles_dir, no valida existencia de pack
    errors = validate_construction(docs)
    assert errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validate_construction.py -v -k role_without_content_pack or role_with_content_pack or role_check_skipped`
Expected: FAIL — `validate_construction() got an unexpected keyword argument 'content_roles_dir'`

- [ ] **Step 3: Write minimal implementation**

En `src/factorysoftware/construction/validator.py`, cambiar la firma y agregar el chequeo al final de la función, antes del `return errors`:

```python
def validate_construction(
    project_root: Path, content_roles_dir: Path | None = None
) -> list[str]:
    errors = []

    # ... (todo el cuerpo existente sin cambios hasta el bloque de roles) ...

    for task_id, t in tasks.items():
        if t["rol"] and t["rol"] not in VALID_ROLES:
            errors.append(f"Task {task_id} has invalid role: {t['rol']}")
        elif t["rol"] and content_roles_dir is not None:
            pack = content_roles_dir / f"{t['rol']}.md"
            if not pack.exists():
                errors.append(
                    f"Task {task_id} uses role '{t['rol']}' with no content pack "
                    f"at {pack} — no hay agente real para despachar esta tarea"
                )

        if t["implementa"] and t["implementa"] not in valid_impls:
            errors.append(f"Task {task_id} references missing implementation: {t['implementa']}")

    # ... (resto sin cambios) ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validate_construction.py -v`
Expected: PASS (todos, incluyendo los 4 tests preexistentes — confirma que no rompiste el comportamiento por defecto)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/construction/validator.py tests/test_validate_construction.py
git commit -m "feat(construction): validar rol de tarea contra content pack real"
```

---

### Task 2: CLI expone `content_roles_dir` en `factory validate construction`

**Files:**
- Modify: `src/factorysoftware/cli.py`
- Modify: `tests/test_cli_validate_construction.py`

**Interfaces:**
- Consumes: `validate_construction(project_root, content_roles_dir=...)` de Task 1.
- Produces: nada nuevo expuesto a otros módulos — es el punto de entrada CLI.

**Contexto confirmado (ya verificado, no hace falta releer):** `cli.py:152-153` tiene hoy:

```python
def cmd_validate_construction(args: argparse.Namespace) -> int:
    errors = validate_construction(Path(args.project_root))
```

Y `main()` se invoca en los tests existentes como `main(["validate", "construction", "--project-root", str(tmp_path)])`, devolviendo un int (exit code) — sin captura de stdout. Ese es el patrón a seguir, ya confirmado leyendo `tests/test_cli_validate_construction.py` en el repo real.

- [ ] **Step 1: Write the failing test**

```python
# agregar a tests/test_cli_validate_construction.py
from pathlib import Path
import yaml
from factorysoftware.cli import main

def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def test_cli_validate_construction_fails_on_role_without_content_pack(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(arch / "apis" / "API-1.md", _fm({"id": "API-1"}))
    _write(cons / "EPIC-1-plan.md", _fm(
        {"id": "EPIC-1", "estado": "draft", "depende_de_epicas": []},
        "### TASK-1.1\n- rol: frontend\n- implementa: API-1\n- depende_de: []",
    ))
    # rol "frontend" SÍ está en VALID_ROLES, pero acá no se valida contra el
    # roles/ empaquetado real del paquete instalado (que sí tiene frontend.md) —
    # este test confirma que el exit code sigue siendo 0 en el caso normal,
    # y sirve de fixture base para el siguiente test negativo si hiciera falta
    # forzar un rol ausente del roles/ empaquetado (fuera de alcance: VALID_ROLES
    # y el contenido de content/roles/ están sincronizados por diseño en este
    # repo, así que un rol de VALID_ROLES siempre tiene pack — el chequeo de
    # Task 1 cubre la regresión si algún día se desincronizan).
    assert main(["validate", "construction", "--project-root", str(tmp_path)]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_validate_construction.py -v -k role_without_content_pack`
Expected: PASS incluso antes del cambio (es un test de no-regresión, no de la feature en sí — la feature real de Task 1/2 ya quedó cubierta por los tests unitarios de `validator.py` en Task 1; este test solo confirma que conectar `content_roles_dir` en el CLI no rompe el caso feliz). Si tras escribir el Step 3 el test sigue en verde, es la confirmación esperada, no una señal de que el test está mal escrito.

- [ ] **Step 3: Write minimal implementation**

En `cli.py`, cambiar la línea 153 para pasar el `content/roles/` empaquetado del propio paquete:

```python
def cmd_validate_construction(args: argparse.Namespace) -> int:
    content_roles_dir = Path(__file__).parent / "content" / "roles"
    errors = validate_construction(Path(args.project_root), content_roles_dir=content_roles_dir)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_validate_construction.py -v`
Expected: PASS (2 preexistentes + 1 nuevo)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/cli.py tests/test_cli_validate_construction.py
git commit -m "feat(construction): CLI valida rol contra roles/ empaquetado"
```

---

### Task 3: Triage dispara `fidelity` y `usability` para slices de UI

**Files:**
- Modify: `src/factorysoftware/construction/triage.py`
- Modify: `tests/test_audit_triage.py`

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `decide_dimensions(diff_text: str, plan_text: str) -> list[str]` ahora puede incluir `"fidelity"` y/o `"usability"` además de las 4 dimensiones existentes.

**Motivación:** hoy `construction_audit` solo tiene 4 dimensiones (`functionality`, `practices`, `security`, `efficiency`) — ninguna mide si la UI construida se parece al `SCREEN-N.md`/prototipo aprobado, ni si es usable (Krug). El repo de referencia (`FabricaAgenticaClaude/factory-spec-build`) resuelve esto con dos agentes separados (`ux-fidelity-reviewer`, `ux-krug-reviewer`); acá se integra como dos dimensiones más del mismo `construction_audit`, disparadas condicionalmente — nunca en slices sin UI, para no violar la prioridad de eficiencia.

- [ ] **Step 1: Write the failing tests**

```python
# agregar a tests/test_audit_triage.py

def test_decide_dimensions_fidelity_frontend_role():
    diff_text = "some standard code"
    plan_text = "rol: frontend"
    result = decide_dimensions(diff_text, plan_text)
    assert "fidelity" in result
    assert "usability" in result

def test_decide_dimensions_fidelity_ui_file_paths():
    diff_text = "src/components/UserCard.tsx"
    plan_text = "plan"
    result = decide_dimensions(diff_text, plan_text)
    assert "fidelity" in result
    assert "usability" in result

def test_decide_dimensions_no_fidelity_without_ui_signal():
    diff_text = "src/services/billing.py"
    plan_text = "rol: backend"
    result = decide_dimensions(diff_text, plan_text)
    assert "fidelity" not in result
    assert "usability" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_audit_triage.py -v -k fidelity`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/factorysoftware/construction/triage.py
import re

_UI_PATH_RE = re.compile(r'\.(tsx|jsx|vue|svelte)$|/components/|/screens/|/views/', re.MULTILINE)

def decide_dimensions(diff_text: str, plan_text: str) -> list[str]:
    dims = ["functionality", "practices"]

    if "auth/" in diff_text or "rol: seguridad" in plan_text:
        dims.append("security")

    if re.search(r'for.*for', diff_text, flags=re.DOTALL) or "SELECT" in diff_text:
        dims.append("efficiency")

    if "rol: frontend" in plan_text or "rol: mobile" in plan_text or _UI_PATH_RE.search(diff_text):
        dims.append("fidelity")
        dims.append("usability")

    return dims
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_audit_triage.py -v`
Expected: PASS (9 tests: 6 preexistentes + 3 nuevos)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/construction/triage.py tests/test_audit_triage.py
git commit -m "feat(construction): disparar fidelity/usability para slices de UI"
```

---

### Task 4: Content pack — `construction_audit` gana dimensiones `fidelity`/`usability`, `wiring_check` gana evidencia mecánica

**Files:**
- Modify: `src/factorysoftware/content/construction.md`
- Modify: `tests/test_content.py` (agregar fixture/test de regresión, ver Step 1)

**Interfaces:**
- Consumes: nada (es contenido markdown, no código).
- Produces: nada nuevo para otros módulos — `render.py`/`content.py` ya son genéricos y no necesitan cambios; el `parse_content` existente debe seguir aceptando el archivo sin error.

**Motivación:** este es el cambio central que pediste. Dos ediciones puntuales dentro de secciones ya existentes (no se agregan `id`s de paso nuevos al frontmatter — `audit_triage` y `construction_audit` ya existen, solo se profundiza su prosa):

1. `## Paso: construction_audit` — agregar las dos dimensiones nuevas al listado, con su checklist, en el mismo estilo que `Seguridad`/`Eficiencia` ya presentes.
2. `## Paso: wiring_check` — reemplazar el checklist puramente declarativo por el protocolo de evidencia mecánica (inline, sin script externo — el agente corre los comandos él mismo vía su tool de shell y compara hashes).

- [ ] **Step 1: Write a regression test that pins the parseability of the edited file**

```python
# agregar a tests/test_content.py

def test_construction_content_pack_still_parses_after_frontend_edits():
    """Regresión: construction.md real del paquete sigue siendo parseable
    y las nuevas dimensiones quedan en el texto del paso construction_audit,
    y el protocolo de evidencia mecánica queda en wiring_check."""
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "construction.md"
    )
    content = parse_content(content_path)
    assert "construction_audit" in content.sections
    assert "fidelity" in content.sections["construction_audit"].lower()
    assert "usability" in content.sections["construction_audit"].lower()
    assert "wiring_check" in content.sections
    assert "material_hash" in content.sections["wiring_check"].lower() or \
           "git rev-parse head" in content.sections["wiring_check"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k construction_content_pack_still_parses`
Expected: FAIL (el archivo real todavía no tiene ese contenido)

- [ ] **Step 3: Edit `content/construction.md`**

Reemplazar la sección `## Paso: construction_audit` completa por:

```markdown
## Paso: construction_audit

Auditoría multidimensional con tope de 3 iteraciones compartidas entre todas las dimensiones activas para la épica (decididas por `audit_triage`):
1. **Funcionalidad:** Tests unitarios pasan. Tareas del plan tienen código real. `traceability.md` tiene "Implementado". Código respeta contrato de API/Screen. Criterio G/W/T cumplido.
2. **Prácticas:** Reglas de Beck, SOLID, GoF, detección de sobreingeniería.
3. **Seguridad:** Validación de input, auth, sin secretos expuestos.
4. **Eficiencia:** Uso idiomático del framework, evitado problema N+1, costo por función razonable.
5. **Fidelidad visual** (solo si `audit_triage` la activó — slices con `rol: frontend`/`mobile` o diff en rutas de UI): la pantalla construida se compara contra `SCREEN-N.md`/prototipo aprobado, no solo se lee el código. Si hay app corriendo y MCP de inspección de navegador disponible, se usa para screenshot/snapshot real de la app contra el prototipo — comparar layout, componentes presentes, paleta, tipografía, copy estructural y estados (error/vacío/carga). Una desviación **justificada y documentada** (ADR o dato ilustrativo declarado) no es hallazgo; una desviación sin justificar sí. Si no hay forma de verificar visualmente (no hay MCP, la app no corre), el resultado es **INCONCLUSO** y cuenta como hallazgo bloqueante — nunca se asume "fiel" sin haber mirado el render real.
6. **Usabilidad** (mismo trigger que Fidelidad): aplica las heurísticas de Krug ("Don't Make Me Think") — jerarquía visual clara, texto escaneable, convención sobre originalidad, lo clicable se ve clicable, todo estado (carga/error/vacío/foco) es explícito, errores con mensaje accionable. Si hay MCP de inspección de navegador disponible, usarlo para snapshot de accesibilidad (roles/labels/orden de foco) además de lectura de código. Cada hallazgo se clasifica BLOQUEANTE/RECOMENDADO/NIT; solo BLOQUEANTE cuenta para el gate.
```

Reemplazar la sección `## Paso: wiring_check` completa por:

```markdown
## Paso: wiring_check

Verificación adversarial de cableado, previa a `pr_gate`. Es el gate de cierre: `pr_gate` no arranca hasta que este paso termine sin hallazgos.

- **Postura:** asume que la épica está incompleta y buscá evidencia de lo contrario. No es una relectura del código propio ("se ve bien"), es un intento activo de refutar que está lista: stubs, TODOs, rutas de UI sin cablear al backend, criterios de aceptación de HU sin una prueba real que los cubra.
- **Contexto:** si el host soporta subagentes/contexto aislado, correlo en uno nuevo, sin el historial de la sesión que escribió el código — reduce el sesgo de "ya sé que esto funciona". Si no hay esa capacidad, igual ejecutá el checklist como si fuera la primera vez que ves el código.
- **Checklist mecánico:** por cada escenario Given/When/Then de las HU de la épica y por cada punto de integración entre capas nuevas, registrar un ítem con `factory slice wiring add --epic EPIC-N <id> <ref> --by wiring_check`.
- **Evidencia mecánica antes de marcar `passing` (no confiar en el relato del agente):** antes de pasar cualquier ítem a `passing`, corré el comando/test real que lo prueba y anotá su código de salida, y corré `git rev-parse HEAD` en ese mismo instante. Un ítem solo pasa a `passing` con `factory slice wiring status --epic EPIC-N <id> passing --evidence "<comando>; exit=<código>; head=<hash>" --by wiring_check` — el `--evidence` debe citar el comando real corrido, su código de salida (debe ser `0`), y el hash de HEAD del momento de la corrida. Si el código cambió después de correr la evidencia (el `HEAD` actual ya no coincide con el citado), esa evidencia quedó obsoleta: hay que volver a correr el comando antes de confiar en el ítem, sin excepción — no se acredita cableado con evidencia de un commit anterior.
- **Salida:** si queda algún ítem en `failing`, o algún `passing` cuya evidencia no cita comando/exit=0/head coincidente con el HEAD actual, se reporta como hallazgo y `pr_gate` espera; no se abre PR con cableado sin verificar. Si todos pasan con evidencia vigente, `factory slice gate --epic EPIC-N wiring_verified true --by wiring_check`.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py tests/test_validate_construction.py -v`
Expected: PASS (el archivo real parsea, sigue sin `id`s de paso nuevos, y los tests de Task 1 no se ven afectados)

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/construction.md tests/test_content.py
git commit -m "feat(construction): fidelidad visual, usabilidad Krug y evidencia mecánica de cableado"
```

---

### Task 5: Content pack — `roles/frontend.md` gana escalera de madurez de stack y gate explícito de fidelidad/usabilidad

**Files:**
- Modify: `src/factorysoftware/content/roles/frontend.md`
- Modify: `tests/test_content.py` (regresión de parseabilidad del rol, ver Step 1 — el archivo es `is_standalone` por no tener `steps:` en frontmatter, confirmar releyendo `content.py::parse_content` antes de escribir el test)

**Motivación:** el rol frontend ya tenía una línea de "validación visual/E2E... no solo que compile", pero sin guía de qué stack elegir según el tipo de proyecto ni referencia a las heurísticas de Krug que ahora sí corre `construction_audit` (Task 4). Sin esto, el agente de rol frontend no sabe qué decisión de stack tomar ni qué se le va a auditar después — se agrega la escalera de madurez (decisión más simple primero) condensada de `frontend-stacks.md` del repo de referencia, y una remisión explícita a las heurísticas de Krug.

- [ ] **Step 1: Write the failing regression test**

```python
# agregar a tests/test_content.py

def test_frontend_role_pack_still_parses_and_has_stack_ladder():
    from pathlib import Path
    content_path = (
        Path(__file__).parent.parent
        / "src" / "factorysoftware" / "content" / "roles" / "frontend.md"
    )
    content = parse_content(content_path)
    assert content.is_standalone is True  # confirma que sigue sin steps: en frontmatter
    assert "krug" in content.preamble.lower()
    assert "astro" in content.preamble.lower() or "next.js" in content.preamble.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -v -k frontend_role_pack_still_parses`
Expected: FAIL

- [ ] **Step 3: Edit `content/roles/frontend.md`**

Agregar, después de la sección `## Alcance` y antes de `## Reglas duras`, una sección nueva:

```markdown
## Escalera de madurez para elegir stack (más simple primero, subí solo si el proyecto lo pide)

No hay stack "por defecto" fijo — la ADR de Arquitectura ya debería haber decidido esto, pero si tu tarea de rol frontend implica elegir dentro de lo que la ADR dejó abierto, priorizá en este orden y detenete en el primer nivel que resuelve el caso real del proyecto:

1. **¿El proyecto es contenido estático o marketing/landing?** → Astro (zero JS por defecto, más rápido, menor superficie).
2. **¿Es una SPA interna simple, sin necesidad de SSR/SEO?** → Vite + React (o el framework que ya use el resto del proyecto).
3. **¿Es una app con datos server-side, SEO real o necesita SSR/ISR?** → Next.js (Server Components para datos, Client Components solo en el borde interactivo — nunca envolver toda la página en `"use client"` cuando solo un botón necesita interactividad).
4. **Componentes de UI:** preferí una librería ya elegida en la ADR del proyecto. Si no hay ADR al respecto y tenés que proponer una, `shadcn/ui` (Radix + Tailwind, copy-paste, sin lock-in de paquete) es el default razonable para proyectos React nuevos — no reinventés primitivas (modal, dropdown, tooltip) que Radix ya resuelve accesibles.

No agregues una dependencia nueva de componentes/estado/routing si el stack elegido ya trae una forma idiomática de resolverlo — esto es lo mismo que `audit_practices` va a revisar en la dimensión de sobreingeniería.

## Fidelidad y usabilidad (lo que te audita `construction_audit`)

Tu tarea no cierra con "compila y se ve parecido". `construction_audit` corre, cuando tu tarea es de rol frontend, las dimensiones **Fidelidad visual** y **Usabilidad** (ver `content/construction.md`, paso `construction_audit`) — practicá el mismo estándar vos mismo antes de marcar la tarea como completa, así no rebota en la auditoría:

- **Fidelidad:** compará la pantalla real (corriendo) contra `SCREEN-N.md`/prototipo, región por región (layout, componentes presentes, paleta, tipografía, copy, estados). Si tenés un MCP de inspección de navegador disponible, usalo para screenshot/snapshot real — no alcanza con leer tu propio JSX y asumir que se parece.
- **Usabilidad (Krug):** "don't make me think" — jerarquía visual clara, texto escaneable, convención antes que originalidad, lo clicable se ve clicable, todo estado (carga/error/vacío/foco) explícito, errores con mensaje accionable sin exponer datos sensibles.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/factorysoftware/content/roles/frontend.md tests/test_content.py
git commit -m "feat(frontend-role): escalera de madurez de stack y gate de fidelidad/usabilidad"
```

---

### Task 6: Full suite verde y validación end-to-end del paquete instalable

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -v`
Expected: todos los tests pasan (preexistentes + los ~11 nuevos de las Tasks 1, 3, 4, 5; más los de Task 2 si el patrón de CLI existente lo permitió escribir).

- [ ] **Step 2: Verificar que el content pack se instala sin error en un proyecto de prueba**

```bash
cd /tmp && rm -rf factory-smoke-test && mkdir factory-smoke-test && cd factory-smoke-test
git init -q && mkdir .claude
python -m factorysoftware.cli install --providers claude_code
```

Expected: termina sin excepción, y `.claude/skills/` (o `.claude/agents/` para el `role-frontend`) contiene el contenido actualizado — confirma que `_load_skill_map`/`build_skill_map` no rompieron con las ediciones de contenido de las Tasks 4 y 5 (son genéricos, pero esta es la verificación real de extremo a extremo, no solo unitaria).

- [ ] **Step 3: Commit final si quedó algo suelto**

Si Step 1 o Step 2 revelan un ajuste menor, corregirlo y commitear con `fix(construction): ...` describiendo qué se ajustó — no debería hacer falta si cada task anterior cerró en verde.
