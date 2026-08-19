from __future__ import annotations
from pathlib import Path

from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map

CONTENT_PATH = (
    Path(__file__).parent.parent
    / "src" / "factorysoftware" / "content" / "requirements" / "requirements.md"
)

ALL_STEP_IDS = ["prd", "epics", "hu_por_epica", "traceability", "flujos", "audit_loop"]

ALL_SKILL_IDS = {
    "requirements-prd",
    "requirements-epics",
    "requirements-hu_por_epica",
    "requirements-traceability",
    "requirements-flujos",
    "requirements-audit_loop",
    "requirements-flujo",
}


def test_parses_without_error():
    content = parse_content(CONTENT_PATH)
    assert content.id == "requirements"


def test_all_steps_declared_in_order():
    content = parse_content(CONTENT_PATH)
    assert [s.id for s in content.steps] == ALL_STEP_IDS


def test_step_dependencies_match_spec():
    content = parse_content(CONTENT_PATH)
    by_id = {s.id: s for s in content.steps}
    assert by_id["prd"].depende_de == []
    assert by_id["epics"].depende_de == ["prd"]
    assert by_id["hu_por_epica"].depende_de == ["epics"]
    assert by_id["hu_por_epica"].paralelizable is True
    assert by_id["traceability"].depende_de == ["hu_por_epica"]
    assert by_id["flujos"].depende_de == ["hu_por_epica"]
    assert set(by_id["audit_loop"].depende_de) == {"traceability", "flujos"}


def test_skill_map_has_exactly_the_expected_skills():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert set(skills) == ALL_SKILL_IDS


def test_no_unidad_principal_no_slide_no_auditor_skills():
    # Requirements has no unidad_principal (per spec) so it must NOT expose
    # requirements-slide or requirements-auditor variants.
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert content.unidad_principal is None
    assert not any(k.endswith("-slide") for k in skills)
    assert "requirements-auditor" not in skills


def test_prd_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert "docs/requirements/PRD.md" in skills["requirements-prd"]
    assert "Problema" in skills["requirements-prd"]


def test_epics_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert "docs/requirements/epics/EPIC-N.md" in skills["requirements-epics"]
    assert "sugerencia_transversal" in skills["requirements-epics"]


def test_hu_por_epica_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert "docs/requirements/stories/HU-N.M.md" in skills["requirements-hu_por_epica"]
    assert "Given/When/Then" in skills["requirements-hu_por_epica"]


def test_traceability_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert "docs/requirements/traceability.md" in skills["requirements-traceability"]
    assert "Componentes de arquitectura" in skills["requirements-traceability"]


def test_flujos_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert "docs/requirements/flujos/FLUJO-N.md" in skills["requirements-flujos"]
    assert "Criterio de exito" in skills["requirements-flujos"]


def test_audit_loop_skill_content_matches_section():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    audit = skills["requirements-audit_loop"]
    assert "factory validate requirements" in audit
    assert "approved_by" in audit
    assert "Arquitectura" in audit


def test_flujo_orchestrator_chains_all_six_steps():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    orchestrator = skills["requirements-flujo"]
    for marker in [
        "docs/requirements/PRD.md",
        "EPIC-N.md",
        "HU-N.M.md",
        "traceability.md",
        "FLUJO-N.md",
        "approved_by",
    ]:
        assert marker in orchestrator, f"orchestrator missing content referencing {marker}"
