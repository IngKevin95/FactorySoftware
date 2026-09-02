---
id: construction
unidad_principal: EPIC-N
flujo_skill_name: e2e
steps:
  - id: audit_triage
    depende_de: ['worktree_integration']
  - id: branch_setup
    depende_de: ['plan_integral_audit']
  - id: construction_audit
    depende_de: ['audit_triage']
  - id: construction_integral_audit
    depende_de: ['construction_audit']
  - id: plan_audit
    depende_de: ['task_planning']
  - id: plan_integral_audit
    depende_de: ['plan_audit']
  - id: pr_gate
    depende_de: ['wiring_check']
  - id: task_execution
    depende_de: ['branch_setup']
  - id: task_planning
    depende_de: []
  - id: wiring_check
    depende_de: ['construction_integral_audit']
  - id: worktree_integration
    depende_de: ['task_execution']
---

Content pack de la fábrica para la fase de construction.

## Paso: audit_triage

Decide qué dimensiones de auditoría se disparan para la épica.
- Siempre: `functionality` y `practices`.
- `security`: si se tocan archivos de auth, input externo, o hubo tareas con rol `seguridad`.
- `efficiency`: si hay loops anidados, queries nuevas o alta complejidad.
- **Salida:** Loguea decisión vía `factory log audit_triage`.

## Paso: branch_setup

Prepara la rama de la épica.
- Crea `feature/EPIC-N-<slug>`.
- Si existe `architecture/ui-prototype` y fue aprobada, la base es esa rama; sino `develop`.
- **Dependencias:** Si `depende_de_epicas` no está vacío, verifica mecánicamente (`git merge-base --is-ancestor`) que estén en develop. Si faltan, informa y queda en espera sin bloquear.
- **Nombres de rama por tarea/fix:** `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$` (minúsculas, guiones). Ej. `feat/user-login`, `fix/duplicate-observation-insert`.

## Paso: construction_audit

Auditoría multidimensional con tope de 3 iteraciones compartidas:
1. **Funcionalidad:** Tests unitarios pasan. Tareas del plan tienen código real. `traceability.md` tiene "Implementado". Código respeta contrato de API/Screen. Criterio G/W/T cumplido.
2. **Prácticas:** Reglas de Beck, SOLID, GoF, detección de sobreingeniería.
3. **Seguridad:** Validación de input, auth, sin secretos expuestos.
4. **Eficiencia:** Uso idiomático del framework, evitado problema N+1, costo por función razonable.

## Paso: construction_integral_audit

Auditoría integral final antes de PR.
- **Fidelidad al negocio:** Código respeta intención real de las HU.
- **Cobertura ADR:** Ninguna ADR aplicada parcialmente.
- **Scope Creep:** Sin código huérfano.
- **Release Completo:** Corre contra estado actual de `develop` (con épicas ya mergeadas) para evitar regresiones lógicas y fallas transversales de integración.

## Paso: plan_audit

Audita TODOS los planes de épica juntos.
- **Dependencias entre épicas:** Detecta si comparten entidades de datos o tienen dependencias directas en HU. Escribe `depende_de_epicas` en cada plan.
- **Validaciones mecánicas:** Las referencias en `implementa` deben existir, no dependencias circulares, roles coherentes con ADRs.
- **Validaciones semánticas:** Sin conflictos de escritura concurrente entre épicas. Granularidad (Beck).

## Paso: plan_integral_audit

Auditor Integral contra Arquitectura.
- **Validaciones:** Todo API/SCREEN está cubierto por al menos una tarea.
- **Scope Creep:** Ninguna tarea planifica trabajo no respaldado por un API/SCREEN/ADR real.
- **ADRs:** Las decisiones fundacionales de despliegue están reflejadas en las tareas.

## Paso: pr_gate

Abre Pull Request de `feature/EPIC-N-...` hacia `develop` usando merge commit (`--no-ff`).
- **Una causa, un PR:** si la épica mezcla correcciones de causas independientes (bugs no relacionados entre sí), sepáralas en PRs distintos en vez de agruparlas por conveniencia.
- **Cierre de sesión:** antes de dar la épica por lista, registrar vía `factory log memory --data '{"tipo": "session_summary", "objetivo": ..., "logrado": ..., "siguiente": ...}'`.
Espera la aprobación manual del usuario.

## Paso: task_execution

Construcción de código y TDD por tarea.
- **Regla:** Código + tests unitarios en ciclo red-green-refactor por cada `TASK-N.M`.
- **Ejecución:** Trabaja en worktrees aislados cuando son paralelizables. 
- **Retry:** Máximo 3 intentos si los tests no pasan de rojo a verde.
- **Commits por unidad de trabajo:** un commit = un comportamiento/fix/migración/doc entregable, no por tipo de archivo (nunca "add models" → "add services" → "add tests" por separado). Tests y docs viajan en el mismo commit que el cambio que verifican/explican. Mensaje en Conventional Commits, explicando el resultado, no la lista de archivos.
- **Presupuesto de PR:** si la tarea acumula más de 400 líneas cambiadas (additions + deletions), particionar en PRs encadenados en vez de forzar un PR único.
- **Memoria de decisiones:** si la tarea implicó una decisión de diseño no obvia o el fix de un bug con causa raíz no evidente, registrar vía `factory log memory --data '{"tipo": "decision|bugfix", "que": ..., "por_que": ..., "donde": ...}'` para que quede disponible en sesiones futuras.

## Paso: task_planning

Arma el grafo de tareas por rol (frontend, backend, data, seguridad, automatizaciones, mobile) para una Épica.
- **Prerequisitos:** `docs/requirements/PRD.md`, HUs de la épica, `API-N.md`, `SCREEN-N.md`.
- **Salida:** `docs/construction/plan/EPIC-N-plan.md` con tareas, cada una indicando su rol, implementa, depende_de, descripcion, estado.
- **Despacho por rol:** si el proveedor soporta subagentes nativos (instalados por la fábrica en `.claude/agents/<rol>.md` o `.opencode/agents/<rol>.md`), cada tarea de `task_execution` se despacha al agente `role-<rol>` correspondiente en vez de ejecutarse con el agente genérico — así el rol solo ve su propio alcance y sus propias reglas duras (ver `content/roles/*.md`). Si el proveedor no soporta subagentes, el mismo agente ejecuta la tarea aplicando manualmente las reglas del rol indicado.

## Paso: wiring_check

Verificación adversarial de cableado, previa a `pr_gate`. Es el gate de cierre: `pr_gate` no arranca hasta que este paso termine sin hallazgos.

- **Postura:** asume que la épica está incompleta y buscá evidencia de lo contrario. No es una relectura del código propio ("se ve bien"), es un intento activo de refutar que está lista: stubs, TODOs, rutas de UI sin cablear al backend, criterios de aceptación de HU sin una prueba real que los cubra.
- **Contexto:** si el host soporta subagentes/contexto aislado, correlo en uno nuevo, sin el historial de la sesión que escribió el código — reduce el sesgo de "ya sé que esto funciona". Si no hay esa capacidad, igual ejecutá el checklist como si fuera la primera vez que ves el código.
- **Checklist mecánico:** por cada escenario Given/When/Then de las HU de la épica y por cada punto de integración entre capas nuevas, registrar un ítem con `factory slice wiring add --epic EPIC-N <id> <ref> --by wiring_check`. Pasa a `passing` solo tras ejecutar una prueba real (no inspección visual) con `factory slice wiring status --epic EPIC-N <id> passing --evidence "<comando/resultado>" --by wiring_check`.
- **Salida:** si queda algún ítem en `failing`, se reporta como hallazgo y `pr_gate` espera; no se abre PR con cableado sin verificar. Si todos pasan, `factory slice gate --epic EPIC-N wiring_verified true --by wiring_check`.

## Paso: worktree_integration

Integra mecánicamente los worktrees de las tareas completadas a la rama de la épica.
Si hay conflicto real, es señal de falla en `plan_audit`. Se reporta como hallazgo retroactivo y no se hace un merge ciego.

