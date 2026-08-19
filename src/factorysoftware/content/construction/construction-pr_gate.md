---
id: construction
steps:
  - id: pr_gate
    depende_de: [construction_integral_audit]
---

# Skill: construction-pr_gate

Abre Pull Request de `feature/EPIC-N-...` hacia `develop` usando merge commit (`--no-ff`).
Espera la aprobación manual del usuario.
