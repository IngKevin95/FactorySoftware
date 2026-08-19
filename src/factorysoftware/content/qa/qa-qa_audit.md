---
id: qa
steps:
  - id: qa_audit
---

# qa_audit

Ejecuta el ciclo de auditoría estándar, con un tope de 3 iteraciones, a través de cuatro roles o subtareas:
1. `audit_coverage` (mecánico): Verifica que toda HU no retirada tenga "Casos de prueba" no vacía, y que los IDs existan realmente. Todo Given/When/Then debe estar cubierto.
2. `audit_nfr_compliance` (mecánico): Verifica que todo NFR tenga evidencia en `audit_evidence` y cumpla la métrica; de lo contrario, es hallazgo Bloqueante.
3. `audit_test_quality` (agéntico): Valida semánticamente que los tests no sean triviales, ejerciten negocio real, y no tengan patrones frágiles (ej. `sleep` fijo).
4. `audit_security_findings` (agéntico): Valida que todo hallazgo de `security_tests` tenga severidad, y bloquea vía `advisor_block` si hay riesgo crítico sin confirmación explícita del usuario.
