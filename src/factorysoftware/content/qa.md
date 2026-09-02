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

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: qa_branch_setup

Crea `feature/qa-coverage-<slug>` desde `develop` (con todas las Épicas de Construcción ya mergeadas a esta altura). Mecánico, sin juicio de agente.

## Paso: integration_tests

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: nfr_tests

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: security_tests

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

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

