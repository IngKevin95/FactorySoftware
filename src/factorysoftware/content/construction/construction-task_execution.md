---
id: construction
steps:
  - id: task_execution
    depende_de: [branch_setup]
---

# Skill: construction-task_execution

Construcción de código y TDD por tarea.
- **Regla:** Código + tests unitarios en ciclo red-green-refactor por cada `TASK-N.M`.
- **Ejecución:** Trabaja en worktrees aislados cuando son paralelizables. 
- **Retry:** Máximo 3 intentos si los tests no pasan de rojo a verde.
