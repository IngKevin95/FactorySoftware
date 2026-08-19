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

# qa-flujo

Orquestador principal para la corrida completa de QA ("corrée QA de todo").
No filtra alcance; encadena de principio a fin todo el pipeline: `coverage_gap_analysis` -> `qa_branch_setup` -> ejecución de todos los `*_tests` -> `traceability_update` -> `qa_audit` -> `qa_integral_audit` -> `pr_gate`.
Crea la rama `feature/qa-coverage-<slug>` general.
