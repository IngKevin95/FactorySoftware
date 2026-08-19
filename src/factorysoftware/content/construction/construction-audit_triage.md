---
id: construction
steps:
  - id: audit_triage
    depende_de: [worktree_integration]
---

# Skill: construction-audit_triage

Decide qué dimensiones de auditoría se disparan para la épica.
- Siempre: `functionality` y `practices`.
- `security`: si se tocan archivos de auth, input externo, o hubo tareas con rol `seguridad`.
- `efficiency`: si hay loops anidados, queries nuevas o alta complejidad.
- **Salida:** Loguea decisión vía `factory log audit_triage`.
