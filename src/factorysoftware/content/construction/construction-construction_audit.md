---
id: construction
steps:
  - id: construction_audit
    depende_de: [audit_triage]
---

# Skill: construction-construction_audit

Auditoría multidimensional con tope de 3 iteraciones compartidas:
1. **Funcionalidad:** Tests unitarios pasan. Tareas del plan tienen código real. `traceability.md` tiene "Implementado". Código respeta contrato de API/Screen. Criterio G/W/T cumplido.
2. **Prácticas:** Reglas de Beck, SOLID, GoF, detección de sobreingeniería.
3. **Seguridad:** Validación de input, auth, sin secretos expuestos.
4. **Eficiencia:** Uso idiomático del framework, evitado problema N+1, costo por función razonable.
