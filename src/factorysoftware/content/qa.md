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

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: e2e_tests

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

## Paso: qa_branch_setup

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.

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

