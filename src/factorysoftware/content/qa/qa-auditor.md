---
id: qa
steps:
  - id: qa_audit
  - id: qa_integral_audit
---

# qa-auditor

Orquestador en modo standalone enfocado en auditoría, sin crear nuevos tests.

- **Parámetros:** Puede recibir un `epic_id` ("auditá QA de la Épica X") o "todo" ("auditoría general de QA").
- **Comportamiento:** Ejecuta únicamente la secuencia `qa_audit` y `qa_integral_audit` sobre los tests de QA que ya se encuentran implementados y referenciados. Evalúa cobertura, NFRs, calidad de los tests y métricas de seguridad según la selección, pero se abstiene de realizar las fases constructivas (`*_tests`) del pipeline normal.
