from __future__ import annotations
from pathlib import Path

from factorysoftware.content import parse_content
from factorysoftware.render import build_skill_map

CONTENT_PATH = (
    Path(__file__).parent.parent
    / "src" / "factorysoftware" / "content" / "requirements" / "requirements.md"
)


def test_parses_without_error():
    content = parse_content(CONTENT_PATH)
    assert content.id == "requirements"


def test_declared_steps_so_far():
    content = parse_content(CONTENT_PATH)
    assert [s.id for s in content.steps] == [
        "prd", "epics", "hu_por_epica", "traceability", "flujos",
    ]


def test_skill_map_keys_so_far():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    assert set(skills) == {
        "requirements-prd",
        "requirements-epics",
        "requirements-hu_por_epica",
        "requirements-traceability",
        "requirements-flujos",
        "requirements-flujo",
    }


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


def test_flujo_orchestrator_chains_all_steps_so_far():
    content = parse_content(CONTENT_PATH)
    skills = build_skill_map(content)
    orchestrator = skills["requirements-flujo"]
    for marker in ["docs/requirements/PRD.md", "EPIC-N.md", "HU-N.M.md", "traceability.md", "FLUJO-N.md"]:
        assert marker in orchestrator, f"orchestrator missing content referencing {marker}"
