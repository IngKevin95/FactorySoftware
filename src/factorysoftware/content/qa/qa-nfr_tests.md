---
id: qa
steps:
  - id: nfr_tests
---

# nfr_tests

Corre los tests de carga/performance o la verificación real correspondiente a cada `NFR-N`.
Se instancia por cada `TEST-N` de tipo `nfr` del `plan.md`.
Debe loguear el valor medido vía factory log `audit_evidence` (usando `git_head`). Esto no es un code review, es una medición real del sistema en ejecución.
