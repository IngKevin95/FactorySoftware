---
id: construction
steps:
  - id: plan_audit
    depende_de: [task_planning]
---

# Skill: construction-plan_audit

Audita TODOS los planes de épica juntos.
- **Dependencias entre épicas:** Detecta si comparten entidades de datos o tienen dependencias directas en HU. Escribe `depende_de_epicas` en cada plan.
- **Validaciones mecánicas:** Las referencias en `implementa` deben existir, no dependencias circulares, roles coherentes con ADRs.
- **Validaciones semánticas:** Sin conflictos de escritura concurrente entre épicas. Granularidad (Beck).
