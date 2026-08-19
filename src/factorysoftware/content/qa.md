---
id: qa
unidad_principal: EPIC-N
steps:
  - id: qa_audit
  - id: qa_integral_audit
  - id: coverage_gap_analysis
  - id: e2e_tests
  - id: qa_branch_setup
  - id: integration_tests
  - id: nfr_tests
  - id: security_tests
  - id: traceability_update
  - id: pr_gate
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

