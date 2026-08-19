---
id: construction
steps:
  - id: worktree_integration
    depende_de: [task_execution]
---

# Skill: construction-worktree_integration

Integra mecánicamente los worktrees de las tareas completadas a la rama de la épica.
Si hay conflicto real, es señal de falla en `plan_audit`. Se reporta como hallazgo retroactivo y no se hace un merge ciego.
