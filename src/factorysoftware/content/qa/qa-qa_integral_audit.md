---
id: qa
steps:
  - id: qa_integral_audit
---

# qa_integral_audit

Actúa como Auditor Integral.
1. Verifica que todo `FLUJO-N.md` de Requerimientos tenga al menos un test e2e real corriendo y pasando.
2. Comprueba que ningún NFR ni flujo haya quedado listado solo en `plan.md` sin reflejarse en `traceability.md`.
3. Valida que el sistema integrado en `develop` (con QA sumado) sea coherente con las ADR de Arquitectura, documentando cualquier hallazgo de escalamiento.
