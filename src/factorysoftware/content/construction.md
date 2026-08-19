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
    depende_de: ['construction_integral_audit']
  - id: task_execution
    depende_de: ['branch_setup']
  - id: task_planning
    depende_de: []
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
Espera la aprobación manual del usuario.

## Paso: task_execution

Construcción de código y TDD por tarea.
- **Regla:** Código + tests unitarios en ciclo red-green-refactor por cada `TASK-N.M`.
- **Ejecución:** Trabaja en worktrees aislados cuando son paralelizables. 
- **Retry:** Máximo 3 intentos si los tests no pasan de rojo a verde.

## Paso: task_planning

Arma el grafo de tareas por rol (frontend, backend, data, seguridad, automatizaciones, mobile) para una Épica.
- **Prerequisitos:** `docs/requirements/PRD.md`, HUs de la épica, `API-N.md`, `SCREEN-N.md`.
- **Salida:** `docs/construction/plan/EPIC-N-plan.md` con tareas, cada una indicando su rol, implementa, depende_de, descripcion, estado.

## Paso: worktree_integration

Integra mecánicamente los worktrees de las tareas completadas a la rama de la épica.
Si hay conflicto real, es señal de falla en `plan_audit`. Se reporta como hallazgo retroactivo y no se hace un merge ciego.

