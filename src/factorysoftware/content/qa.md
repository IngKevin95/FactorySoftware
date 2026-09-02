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

Content pack de la fábrica para la fase de qa.

## Paso: qa_audit

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: qa_integral_audit

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: coverage_gap_analysis

Arma `docs/qa/plan.md`: la lista de `TEST-N` que faltan para que el 100% de la funcionalidad declarada en Requerimientos quede probado más allá de lo unitario ya cubierto en Construcción.

- Lee `docs/requirements/traceability.md`: qué HU ya tienen test unitario pero no integración/e2e donde corresponda.
- Lee `docs/requirements/flujos/FLUJO-N.md`: qué flujos de negocio no tienen todavía un e2e real corriendo.
- Lee `docs/architecture/constraints.md`: qué `NFR-N` no tienen verificación real medida todavía.
- **Salida:** `docs/qa/plan.md` con una entrada por cada `TEST-N` faltante. Cada entrada: `id` (`TEST-N`), `tipo` (`integration`|`e2e`|`nfr`|`security`), `cubre` (ids de HU para `integration`, un `FLUJO-N` para `e2e`, un `NFR-N` para `nfr`, o `general` para `security`), `depende_de` (otros `TEST-N`, si aplica), `estado: pendiente`.
- **Definición operativa de "100% de cobertura":** no es porcentaje de líneas. Es que toda HU no retirada tenga, para cada criterio Given/When/Then, al menos un test real referenciado en la columna "Casos de prueba" de `traceability.md` — verificación de referencia cruzada, no métrica estadística.

## Paso: e2e_tests

Una instancia por `TEST-N` de tipo `e2e` — una por cada `FLUJO-N` sin cobertura. Sigue la secuencia de HU declarada en `docs/requirements/flujos/FLUJO-N.md`, usando la navegación real de las pantallas (ya debe honrar el flujo, verificado en la fase de Arquitectura). El criterio de éxito no es que cada HU aislada pase — es el **criterio de éxito del flujo completo** declarado en el propio `FLUJO-N.md` (un flujo puede fallar aunque cada HU pase sus tests por separado, ej. un dato que una HU guarda no es el que otra espera leer después).

## Paso: qa_branch_setup

Crea `feature/qa-coverage-<slug>` desde `develop` (con todas las Épicas de Construcción ya mergeadas a esta altura). Mecánico, sin juicio de agente.

## Paso: integration_tests

Una instancia por `TEST-N` de tipo `integration` en `docs/qa/plan.md`. Toma como base los tests unitarios que ya escribió Construcción — no los repite, agrega la integración entre las unidades reales del stack (DB real o de test, servicios reales entre sí, sin mocks de la propia capa que se está integrando). Vive en `tests/integration/` o la convención del stack del proyecto (QA no inventa su propia carpeta).

## Paso: nfr_tests

Una instancia por `TEST-N` de tipo `nfr` — una por cada `NFR-N` de `docs/architecture/constraints.md` sin verificación real todavía. Corre el test de carga/performance/lo que corresponda al NFR concreto y **mide de verdad**, nunca estima. Registra el resultado con:

`factory log audit_evidence --data '{"nfr": "NFR-N", "medido": <valor real medido>, "objetivo": "<Medida de respuesta declarada en constraints.md>", "cumple": true|false, "git_head": "<git rev-parse HEAD>"}'`

Si `cumple` es `false`, es hallazgo **Bloqueante** — nunca "se documenta y se sigue". Se escala al usuario mostrando medido vs. objetivo; la resolución puede requerir volver a Construcción (optimizar) o a Arquitectura (revisar la ADR o el NFR mismo). QA no "arregla" el sistema para que el número cierre, solo mide y reporta con honestidad.

## Paso: security_tests

Pasada única y holística sobre todo el sistema integrado (no por-épica, a diferencia de `audit_security` de Construcción): SAST/dependency scanning más escenarios de seguridad puntuales que solo son visibles con el sistema completo (ej. un endpoint de una épica combinado con datos de otra puede abrir un camino que ninguna auditoría por-épica ve sola). Todo hallazgo tiene severidad (Bloqueante/Mayor/Menor). Todo hallazgo **Bloqueante** pasa por el mecanismo `advisor_block` del núcleo antes de seguir — nunca queda "reportado nomás" sin confirmación explícita del usuario:

`factory log advisor_block --data '{"category": "seguridad", "reason": "...", "user_override": true|false}'`

## Paso: traceability_update

# traceability_update

Completa la columna "Casos de prueba" del documento `docs/requirements/traceability.md` referenciando explícitamente los IDs de los tests reales (integración, e2e) creados/verificados en los pasos anteriores.
Asegura que la tabla finalice completa de forma mecánica y precisa.

## Paso: pr_gate

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

