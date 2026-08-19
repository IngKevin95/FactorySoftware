---
id: qa
steps:
  - id: coverage_gap_analysis
  - id: qa_branch_setup
  - id: integration_tests
  - id: e2e_tests
  - id: nfr_tests
  - id: security_tests
  - id: traceability_update
  - id: qa_audit
  - id: qa_integral_audit
  - id: pr_gate
---

# qa-slide

Orquestador de QA limitado al alcance de una Épica.

- **Parámetros:** `epic_id` (obligatorio, ej. `EPIC-3`).
- **Comportamiento:** "Corrée QA solo de lo que tocó la Épica".
- `coverage_gap_analysis` filtra a HU/NFR pertenecientes exclusivamente a esa Épica, así como los `FLUJO-N` que estén **completamente** contenidos en ella (flujos que cruzan épicas se excluyen en este modo).
- Crea una rama dedicada: `feature/qa-coverage-epic-<numero>-<slug>`.
- Finaliza abriendo un PR específico e independiente para este slide.
