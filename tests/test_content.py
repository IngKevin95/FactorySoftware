from pathlib import Path

from factorysoftware.content import PhaseContent, StepDecl, parse_content


FIXTURE = """\
---
id: requirements
steps:
  - id: prd
    depende_de: []
    fan_out: null
    paralelizable: false
  - id: epics
    depende_de: [prd]
    fan_out: null
    paralelizable: false
    rol: null
---
Preámbulo de la fase de Requerimientos.

## Paso: prd

Instrucciones del paso PRD.

## Paso: epics

Instrucciones del paso Épicas.
"""

FIXTURE_WITH_UNIT = """\
---
id: construction
unidad_principal: slide
flujo_skill_name: e2e
steps:
  - id: task_planning
    depende_de: []
    fan_out: "una por Épica"
    paralelizable: true
  - id: construction_audit
    depende_de: [task_planning]
    fan_out: null
    paralelizable: false
    rol: Auditor
---
Preámbulo de Construcción.

## Paso: task_planning

Planificá.

## Paso: construction_audit

Auditá.
"""


def test_parse_content_basic(tmp_path: Path):
    p = tmp_path / "requirements.md"
    p.write_text(FIXTURE, encoding="utf-8")
    content = parse_content(p)
    assert content.id == "requirements"
    assert content.unidad_principal is None
    assert content.flujo_skill_name == "flujo"
    assert [s.id for s in content.steps] == ["prd", "epics"]
    assert content.steps[1].depende_de == ["prd"]
    assert "Preámbulo" in content.preamble
    assert "Instrucciones del paso PRD" in content.sections["prd"]
    assert "Instrucciones del paso Épicas" in content.sections["epics"]


def test_parse_content_with_unit_and_role(tmp_path: Path):
    p = tmp_path / "construction.md"
    p.write_text(FIXTURE_WITH_UNIT, encoding="utf-8")
    content = parse_content(p)
    assert content.unidad_principal == "slide"
    assert content.flujo_skill_name == "e2e"
    assert content.steps[0].fan_out == "una por Épica"
    assert content.steps[0].paralelizable is True
    assert content.steps[1].rol == "Auditor"
