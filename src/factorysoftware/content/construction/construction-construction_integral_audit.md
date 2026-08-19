---
id: construction
steps:
  - id: construction_integral_audit
    depende_de: [construction_audit]
---

# Skill: construction-construction_integral_audit

Auditoría integral final antes de PR.
- **Fidelidad al negocio:** Código respeta intención real de las HU.
- **Cobertura ADR:** Ninguna ADR aplicada parcialmente.
- **Scope Creep:** Sin código huérfano.
- **Release Completo:** Corre contra estado actual de `develop` (con épicas ya mergeadas) para evitar regresiones lógicas y fallas transversales de integración.
