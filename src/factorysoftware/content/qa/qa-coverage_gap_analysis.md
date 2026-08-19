---
id: qa
steps:
  - id: coverage_gap_analysis
---

# coverage_gap_analysis

Lee `traceability.md` para identificar qué HU ya tienen test unitario pero carecen de tests de integración o end-to-end (e2e) donde corresponda.
Revisa `flujos/FLUJO-N.md` para determinar cuáles flujos de negocio no tienen e2e todavía.
Verifica `constraints.md` para identificar qué NFR-N carecen de verificación real (test de carga/performance).
Arma el archivo `docs/qa/plan.md` con la lista de tareas `TEST-N` que faltan (id, tipo: integration|e2e|nfr|security, cubre, depende_de, estado).
