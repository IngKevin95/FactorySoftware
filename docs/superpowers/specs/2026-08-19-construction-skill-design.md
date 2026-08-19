# Skill de Construcción — Diseño

Estado: aprobado
Subsistema: 4 de N (fase de contenido: Construcción) — depende del núcleo,
Requerimientos y Arquitectura:
- `docs/superpowers/specs/2026-08-19-factory-core-design.md`
- `docs/superpowers/specs/2026-08-19-requirements-skill-design.md`
- `docs/superpowers/specs/2026-08-19-architecture-skill-design.md`

## Propósito

Content pack que toma los contratos congelados de Arquitectura (ADRs,
`data-model.md`, `API-N.md`, `SCREEN-N.md`) y las HU de Requerimientos, y
construye el código real, épica por épica, con planificación de tareas por
rol (frontend/backend/data/automatizaciones/mobile/seguridad/...), ejecución
paralela aislada por rama/worktree, TDD por tarea, y gate de aprobación vía
Pull Request siguiendo el Git Flow del proyecto.

## No-objetivos

- Tests de integración/e2e y auditoría de cobertura total — fase de QA (spec
  futuro), que toma el código + los `API-N.md`/`SCREEN-N.md` como su propio
  contrato a validar.
- Redefinir contratos de Arquitectura o alcance de Requerimientos — son
  inputs de solo lectura.
- Ejecutar el despliegue real (el "cómo desplegar" ya quedó decidido como
  ADR en Arquitectura; ejecutar ese despliegue en un entorno real es un
  subsistema aparte, no cubierto todavía — ver preguntas abiertas).

## Convención de Git asumida (flag de diseño)

Este spec asume Git Flow (`feature/<slug>` desde `develop`, merge a
`develop` vía PR con merge commit `--no-ff`, nunca squash/rebase) porque es
la convención declarada en el `CLAUDE.md` de este usuario. Un proyecto que
use otra convención (trunk-based, GitHub flow simple) necesitaría que este
paso lea la convención real del proyecto en vez de asumir Git Flow siempre
— queda como pregunta abierta para cuando la fábrica se use en un proyecto
sin esa convención declarada; v1 la asume fija.

## Artefactos y ubicación

```
docs/construction/
  plan/
    EPIC-1-plan.md
    EPIC-2-plan.md
    ...
```

El código real vive en el árbol normal del proyecto (`src/`, o la
convención que el propio proyecto/stack ya tenga) — Construcción no inventa
una carpeta propia para el código, solo para los planes de tareas.

### `plan/EPIC-N-plan.md`

Frontmatter: `id` (`EPIC-N`), `estado`. Cuerpo: lista de tareas.

Cada tarea:
- `id`: `TASK-N.M`
- `rol`: `frontend` | `backend` | `data` | `automatizaciones` | `mobile` |
  `seguridad` | ... (el conjunto real de roles lo determina la naturaleza
  del proyecto y el stack elegido en Arquitectura, no una lista fija de la
  skill)
- `implementa`: ids de `API-N`/`SCREEN-N`/entidad de `data-model.md` que
  esta tarea construye
- `depende_de`: ids de otras `TASK-N.M` (dentro o fuera de la misma épica)
- `descripcion`: qué hace concretamente
- `estado`: pendiente/en progreso/completa/bloqueada

## Rama y aislamiento de trabajo paralelo

- Una rama `feature/EPIC-N-<slug>` por Épica, creada desde `develop`.
- Las tareas de una misma épica que el plan marca como independientes entre
  sí (sin relación de `depende_de`) se ejecutan en **git worktrees**
  aislados (mecanismo estándar de Git, sin herramienta adicional — ver
  `superpowers:using-git-worktrees`), cada uno arrancando desde el estado
  actual de `feature/EPIC-N-<slug>`. Al terminar, cada worktree se integra
  (merge local, sin squash) a la rama de la épica antes de auditar el
  resultado combinado.
- Tareas con dependencia real (ej. la tarea de backend que expone el
  endpoint antes que la tarea de frontend que lo consume) corren en serie,
  en el mismo worktree o directo en la rama de la épica.

## Frontera con QA: TDD dentro de Construcción

Cada tarea de código entrega **código + sus tests unitarios**, ciclo
red-green-refactor (coherente con las reglas de Beck ya vigentes en el
proyecto: "Passes Tests" es la primera regla). Construcción es responsable
de que la unidad que construye tenga su propia red de tests unitarios antes
de darse por completa. QA (fase futura) no reescribe estos tests; los toma
como base y agrega integración, e2e, y la auditoría de cobertura total
contra `traceability.md`.

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

Los pasos marcados "mecánico" son determinísticos (comandos de git/test
runner, sin necesidad de juicio de un agente) y se ejecutan como tool calls
directos, no requieren despacho de subagente aunque tengan fan-out. Los
marcados "agéntico" sí requieren razonamiento y siguen la regla de despacho
del núcleo (subagente paralelo si el proveedor lo soporta, serie si no).

```
- id: task_planning [agéntico]
  depende_de: []
  fan_out: "una instancia por cada Épica no retirada de Requerimientos"
  paralelizable: true
  # cada instancia solo ve las HU de su propia épica y los API-N/SCREEN-N
  # que las implementan — arma el grafo de tareas por rol

- id: plan_audit [agéntico, rol: Auditor]
  depende_de: [task_planning]
  fan_out: null
  paralelizable: false
  # ve TODOS los planes de épica juntos — necesario para detectar
  # conflictos entre épicas (ej. dos épicas tocando la misma entidad de
  # datos al mismo tiempo), algo que ninguna instancia aislada del paso
  # anterior puede ver por sí sola

- id: plan_integral_audit [agéntico, rol: Auditor Integral]
  depende_de: [plan_audit]
  fan_out: null
  paralelizable: false
  # valida los planes contra Arquitectura completa: todo ADR/API/pantalla
  # relevante queda cubierto por al menos una tarea, ninguna tarea inventa
  # trabajo sin respaldo en un API-N/SCREEN-N/entidad real (ver checklist)

- id: branch_setup [mecánico]
  depende_de: [plan_integral_audit]
  fan_out: "una instancia por Épica con plan aprobado"
  paralelizable: true
  # crea feature/EPIC-N-<slug> desde develop

- id: task_execution [agéntico]
  depende_de: [branch_setup]
  fan_out: "una instancia por TASK-N.M, respetando depende_de del plan de su épica"
  paralelizable: true
  # código + tests unitarios (TDD) por tarea, en worktree aislado cuando es
  # paralelizable con otras tareas de la misma épica

- id: worktree_integration [mecánico]
  depende_de: [task_execution]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # merge de los worktrees de tareas completas a la rama de la épica

- id: construction_audit [agéntico, rol: Auditor]
  depende_de: [worktree_integration]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # código cumple contratos, tests unitarios pasan, reglas de Beck
  # respetadas, traceability.md actualizado

- id: construction_integral_audit [agéntico, rol: Auditor Integral]
  depende_de: [construction_audit]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # última pasada antes del PR: el código de la épica sigue fiel a la
  # intención de negocio de sus HU y a las decisiones de las ADR que le
  # aplican, no solo a la letra del contrato técnico (ver checklist)

- id: pr_gate [mecánico + pregunta al usuario]
  depende_de: [construction_integral_audit]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # abre PR de feature/EPIC-N-... a develop (merge commit, --no-ff);
  # pregunta al usuario si lo aprueba acá o lo revisa manualmente — ESTE
  # PR es el gate de aprobación humana de la fase, no un paso aparte
```

## Checklist del auditor

### `plan_audit`

Estructurales (mecánicas):

1. Toda `TASK-N.M` en `implementa` referencia un `API-N`/`SCREEN-N`/entidad
   real de `data-model.md`.
2. Sin referencias circulares en `depende_de`, ni dentro de una épica ni
   entre épicas.
3. Todo `rol` usado es coherente con el stack elegido en las ADR de
   Arquitectura (ej. no aparece `mobile` si ninguna ADR contempla una app
   móvil).

Semánticas:

4. Ninguna tarea de una épica entra en conflicto de escritura concurrente
   sobre la misma entidad/migración con una tarea de otra épica que corre en
   paralelo (si lo detecta, se fuerza una dependencia explícita entre ambas
   o se escala).
5. Granularidad de tareas razonable según Beck (Fewest Elements): ninguna
   tarea está fragmentada en abstracciones prematuras, ninguna tarea agrupa
   responsabilidades no relacionadas.

### `construction_audit`

Estructurales (mecánicas):

1. Todos los tests unitarios de la épica pasan (se corre el test runner
   real del stack, no se infiere).
2. Toda `TASK-N.M` del plan de la épica tiene cambios de código
   correspondientes (sin tareas marcadas completas sin diff real).
3. `traceability.md` de Requerimientos queda con una columna "Implementado"
   marcada para toda HU cubierta por esta épica.

Semánticas:

4. El código respeta el contrato congelado de cada `API-N.md`/`SCREEN-N.md`
   sin drift silencioso (si el código necesita desviarse del contrato, eso
   es un hallazgo que se escala, no un ajuste que se hace y se documenta
   después).
5. Reglas de Beck respetadas: sin abstracciones no pedidas, sin
   duplicación, sin implementaciones a medias.
6. Ninguna acción de riesgo crítico (seguridad, pérdida de datos, acciones
   irreversibles) se tomó sin pasar por el mecanismo `advisor_block` del
   núcleo.

### `plan_integral_audit` (rol: Auditor Integral, contra Arquitectura)

i. Todo `API-N`/`SCREEN-N`/entidad de `data-model.md` relevante para las
   épicas en curso queda cubierto por al menos una `TASK-N.M` — un contrato
   de Arquitectura sin ninguna tarea que lo construya es un hallazgo
   bloqueante.
ii. Ninguna tarea planifica trabajo que no está respaldado por un
   `API-N`/`SCREEN-N`/entidad/ADR real (alcance inventado en la
   planificación).
iii. Las ADR fundacionales (stack, artefactos/método de despliegue) están
   reflejadas en cómo se plantean las tareas (ej. si la ADR de despliegue
   elige contenedores, ninguna tarea asume un modelo de despliegue
   distinto).

### `construction_integral_audit` (rol: Auditor Integral, contra Arquitectura + Requerimientos)

iv. El código de la épica sigue siendo fiel a la intención de negocio de
   cada HU que implementa (no solo pasa los tests, sino que un lector
   humano reconocería el criterio de aceptación Given/When/Then cumplido en
   el comportamiento real).
v. Ninguna ADR quedó parcialmente aplicada (ej. la ADR de despliegue exige
   configuración de contenedor y el código no la incluye).
vi. No hay funcionalidad construida que no esté respaldada por ninguna HU
   ni ADR (scope creep en código, no solo en documentación).

## Extensión del CLI del núcleo

`factory validate construction [--epic EPIC-N]` — corre las verificaciones
estructurales de `plan_audit` y `construction_audit` (incluyendo correr el
test runner real del proyecto y revisar su exit code), cruzando
`docs/construction/plan/` con `docs/architecture/` y
`docs/requirements/traceability.md`.

## Manejo de errores / casos borde

- Una tarea no logra pasar de rojo a verde tras varios intentos: retry
  acotado a 3 intentos dentro de la tarea misma (mismo tope que el loop de
  auditoría del núcleo); si sigue en rojo, esa tarea queda `bloqueada` y se
  escala sin frenar las demás tareas independientes de la misma épica.
- Conflicto real al integrar un worktree a la rama de la épica: señal de que
  `plan_audit` no detectó una dependencia real entre esas tareas — se trata
  como hallazgo retroactivo de auditoría (se loguea, se corrige la
  dependencia en el plan, no se resuelve el conflicto "a ciegas" con
  `git merge -X ours` ni similar).
- El código necesita desviarse de un contrato ya aprobado en Arquitectura:
  hallazgo bloqueante de la verificación semántica 4, se escala con la
  propuesta de cambio de contrato — no se cambia `API-N.md` desde
  Construcción sin que quede como decisión explícita y trazable.

## Testing

pytest, cero IO externo real (sin correr git/test-runners reales del
proyecto objetivo dentro de los tests del propio `factorysoftware` — se
mockean), fixtures de árbol de documentos en `tmp_path`:

- `test_validate_construction.py`: casos positivos y un caso negativo por
  cada verificación estructural de `plan_audit` (1–3) y `construction_audit`
  (1–3).

## Preguntas abiertas para specs futuros

- Ejecutar el despliegue real (más allá de la ADR de método/artefactos) no
  está cubierto — si se necesita, es un subsistema aparte.
- Detectar la convención de Git real del proyecto en vez de asumir Git Flow
  fijo queda pendiente si la fábrica se usa en un proyecto con otra
  convención.
- QA (próximo spec) debe definir cómo consume `docs/construction/plan/` y el
  código resultante para armar sus propios casos de integración/e2e, y cómo
  cierra la columna de cobertura total en `traceability.md`.
