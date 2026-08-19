---
id: construction
steps:
  - id: branch_setup
    depende_de: [plan_integral_audit]
---

# Skill: construction-branch_setup

Prepara la rama de la épica.
- Crea `feature/EPIC-N-<slug>`.
- Si existe `architecture/ui-prototype` y fue aprobada, la base es esa rama; sino `develop`.
- **Dependencias:** Si `depende_de_epicas` no está vacío, verifica mecánicamente (`git merge-base --is-ancestor`) que estén en develop. Si faltan, informa y queda en espera sin bloquear.
